#!/usr/bin/env python3
"""
Client-side batched timeseries for large CHL area queries.

Splits one large request into multiple smaller calls:
- temporal chunks (months-per-request)
- spatial tiles over a bbox (tiles-x, tiles-y)

Then combines per-timestamp means using weighted average by "count".
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable
from urllib import error, parse, request


DEFAULT_BASE_URL = "http://127.0.0.1:8080"
DEFAULT_DATASET_ID = "ua_chl_virtual_stations"
DEFAULT_VAR_NAME = "CHL"
DEFAULT_BBOX = (22.0, 44.0, 40.5, 52.5)
DEFAULT_AGG_METHODS = ("mean", "count")
DEFAULT_TIME_GRAIN = "raw"


@dataclass
class TimeAccumulator:
    weighted_mean_sum: float = 0.0
    total_count: float = 0.0


def parse_date(value: str) -> datetime:
    try:
        # Keep naive UTC-style datetime consistent with xcube query strings.
        if len(value) == 10:
            return datetime.strptime(value, "%Y-%m-%d")
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid date/datetime '{value}': {e}") from e


def _normalize_time_key(value: str, time_grain: str) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if time_grain == "raw":
        return text

    try:
        dt = parse_date(text)
    except argparse.ArgumentTypeError:
        return None

    if time_grain == "daily":
        return dt.strftime("%Y-%m-%d")
    if time_grain == "monthly":
        return dt.strftime("%Y-%m-01")
    return text


def add_months(dt: datetime, months: int) -> datetime:
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def iter_time_windows(
    start: datetime, end: datetime, months_per_request: int
) -> Iterable[tuple[datetime, datetime]]:
    current = start
    while current < end:
        nxt = add_months(current, months_per_request)
        if nxt > end:
            nxt = end
        yield current, nxt
        current = nxt


def iter_day_windows(
    start: datetime, end: datetime, days_per_request: int
) -> Iterable[tuple[datetime, datetime]]:
    current = start
    step = timedelta(days=days_per_request)
    while current < end:
        nxt = current + step
        if nxt > end:
            nxt = end
        yield current, nxt
        current = nxt


def iter_bbox_tiles(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float, tiles_x: int, tiles_y: int
) -> Iterable[tuple[float, float, float, float]]:
    dx = (max_lon - min_lon) / tiles_x
    dy = (max_lat - min_lat) / tiles_y
    for iy in range(tiles_y):
        y0 = min_lat + iy * dy
        y1 = min_lat + (iy + 1) * dy
        for ix in range(tiles_x):
            x0 = min_lon + ix * dx
            x1 = min_lon + (ix + 1) * dx
            yield (x0, y0, x1, y1)


def bbox_polygon(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [min_lon, min_lat],
                [max_lon, min_lat],
                [max_lon, max_lat],
                [min_lon, max_lat],
                [min_lon, min_lat],
            ]
        ],
    }


def request_timeseries(
    *,
    base_url: str,
    dataset_id: str,
    var_name: str,
    agg_methods: list[str],
    start_date: str,
    end_date: str,
    max_valids: int,
    timeout_secs: int,
    geometry: dict,
    retries: int,
) -> dict:
    params: list[tuple[str, str]] = []
    for method in agg_methods:
        params.append(("aggMethods", method))
    params.extend(
        [
            ("responseFormat", "contract"),
            ("maxValids", str(max_valids)),
            ("startDate", start_date),
            ("endDate", end_date),
        ]
    )
    query = parse.urlencode(params)
    url = (
        f"{base_url.rstrip('/')}/timeseries/"
        f"{parse.quote(dataset_id)}/{parse.quote(var_name)}?{query}"
    )

    payload = json.dumps(geometry).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with request.urlopen(req, timeout=timeout_secs) as resp:
                body = resp.read().decode("utf-8")
            return json.loads(body)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt < retries:
                time.sleep(min(5, 1 + attempt))
            else:
                break

    assert last_exc is not None
    if isinstance(last_exc, error.HTTPError):
        detail = ""
        try:
            detail = last_exc.read().decode("utf-8")
        except Exception:  # noqa: BLE001
            detail = ""
        raise RuntimeError(
            f"HTTP {last_exc.code} for {url}. Body={detail[:400]}"
        ) from last_exc
    raise RuntimeError(f"Request failed for {url}: {last_exc}") from last_exc


def run_batch(args: argparse.Namespace) -> dict:
    if args.start_date >= args.end_date:
        raise SystemExit("--start-date must be earlier than --end-date")
    if args.tiles_x < 1 or args.tiles_y < 1:
        raise SystemExit("--tiles-x and --tiles-y must be >= 1")
    if args.days_per_request < 0:
        raise SystemExit("--days-per-request must be >= 0")
    if args.days_per_request == 0 and args.months_per_request < 1:
        raise SystemExit("--months-per-request must be >= 1")

    agg_methods = [m.strip().lower() for m in args.agg_methods.split(",") if m.strip()]
    if not agg_methods:
        raise SystemExit("--agg-methods produced an empty set")

    tile_count = args.tiles_x * args.tiles_y
    if tile_count > 1 and ("mean" in agg_methods and "count" not in agg_methods):
        agg_methods.append("count")
    if tile_count > 1:
        unsupported = [m for m in agg_methods if m not in {"mean", "count"}]
        if unsupported:
            raise SystemExit(
                f"Area tiling only supports mean/count for merge. Unsupported: {unsupported}"
            )

    if args.days_per_request > 0:
        windows = list(iter_day_windows(args.start_date, args.end_date, args.days_per_request))
    else:
        windows = list(iter_time_windows(args.start_date, args.end_date, args.months_per_request))
    tiles = list(
        iter_bbox_tiles(
            args.bbox[0], args.bbox[1], args.bbox[2], args.bbox[3], args.tiles_x, args.tiles_y
        )
    )
    expected = len(windows) * len(tiles)
    if expected == 0:
        raise SystemExit("No requests to run (check date range and tile settings).")

    acc: dict[str, TimeAccumulator] = {}
    source_timestamps_seen: set[str] = set()
    total_requests = 0
    failed_requests = 0

    for w_i, (w_start, w_end) in enumerate(windows, start=1):
        start_s = w_start.strftime("%Y-%m-%d")
        end_s = w_end.strftime("%Y-%m-%d")
        for t_i, tile in enumerate(tiles, start=1):
            total_requests += 1
            print(
                f"[{total_requests}/{expected}] window={w_i}/{len(windows)} "
                f"tile={t_i}/{len(tiles)} start={start_s} end={end_s}",
                flush=True,
            )
            geom = bbox_polygon(*tile)
            try:
                response = request_timeseries(
                    base_url=args.base_url,
                    dataset_id=args.dataset_id,
                    var_name=args.var_name,
                    agg_methods=agg_methods,
                    start_date=start_s,
                    end_date=end_s,
                    max_valids=args.max_valids,
                    timeout_secs=args.timeout_secs,
                    geometry=geom,
                    retries=args.retries,
                )
            except Exception as e:  # noqa: BLE001
                failed_requests += 1
                msg = f"Request failed: {e}"
                if args.continue_on_error:
                    print(msg, file=sys.stderr, flush=True)
                    continue
                raise RuntimeError(msg) from e

            for row in response.get("result", []):
                raw_ts = row.get("time")
                if not raw_ts:
                    continue
                mean_value = row.get("mean")
                count_value = row.get("count")

                # If count is absent in single-tile mode, fallback to count=1 weighting.
                if count_value is None:
                    if mean_value is None:
                        continue
                    count = 1.0
                else:
                    count = float(count_value)
                    if math.isnan(count) or count <= 0:
                        continue
                if mean_value is None:
                    continue
                mean = float(mean_value)
                if math.isnan(mean):
                    continue

                ts = _normalize_time_key(raw_ts, args.time_grain)
                if not ts:
                    continue
                source_timestamps_seen.add(str(raw_ts))

                slot = acc.setdefault(ts, TimeAccumulator())
                slot.weighted_mean_sum += mean * count
                slot.total_count += count

    combined_rows: list[dict] = []
    for ts in sorted(acc.keys()):
        slot = acc[ts]
        mean = None
        if slot.total_count > 0:
            mean = slot.weighted_mean_sum / slot.total_count
        combined_rows.append(
            {
                "time": ts,
                "mean": mean,
                "count": slot.total_count,
            }
        )

    return {
        "contract": "xcube-calculations/v1",
        "operation": "timeseries-batch-client",
        "datasetId": args.dataset_id,
        "varName": args.var_name,
        "hasData": bool(combined_rows),
        "summary": {
            "rows": len(combined_rows),
            "sourceRows": len(source_timestamps_seen),
            "requestsTotal": total_requests,
            "requestsFailed": failed_requests,
            "windows": len(windows),
            "tiles": len(tiles),
        },
        "query": {
            "aggMethods": agg_methods,
            "startDate": args.start_date.strftime("%Y-%m-%d"),
            "endDate": args.end_date.strftime("%Y-%m-%d"),
            "timeGrain": args.time_grain,
            "maxValids": args.max_valids,
            "monthsPerRequest": args.months_per_request,
            "daysPerRequest": args.days_per_request,
            "bbox": args.bbox,
            "tilesX": args.tiles_x,
            "tilesY": args.tiles_y,
            "timeoutSecs": args.timeout_secs,
        },
        "result": combined_rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run batched CHL timeseries queries (time windows + bbox tiles) and merge "
            "results to reduce timeout risk on very large requests."
        )
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--dataset-id", default=DEFAULT_DATASET_ID)
    parser.add_argument("--var-name", default=DEFAULT_VAR_NAME)
    parser.add_argument("--start-date", type=parse_date, required=True)
    parser.add_argument("--end-date", type=parse_date, required=True)
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        default=DEFAULT_BBOX,
    )
    parser.add_argument("--tiles-x", type=int, default=2)
    parser.add_argument("--tiles-y", type=int, default=2)
    parser.add_argument("--months-per-request", type=int, default=1)
    parser.add_argument(
        "--days-per-request",
        type=int,
        default=0,
        help="If >0, split by fixed day windows and ignore --months-per-request.",
    )
    parser.add_argument("--agg-methods", default=",".join(DEFAULT_AGG_METHODS))
    parser.add_argument(
        "--time-grain",
        choices=("raw", "daily", "monthly"),
        default=DEFAULT_TIME_GRAIN,
        help=(
            "Temporal normalization for output rows: "
            "raw keeps original timestamps, daily groups by date, monthly groups by month."
        ),
    )
    parser.add_argument("--max-valids", type=int, default=200)
    parser.add_argument("--timeout-secs", type=int, default=120)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_batch(args)
    text = json.dumps(result, ensure_ascii=True, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}")
        print(
            json.dumps(
                {
                    "hasData": result["hasData"],
                    "summary": result["summary"],
                },
                ensure_ascii=True,
            )
        )
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
