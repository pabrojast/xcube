#!/usr/bin/env python3
"""
Precompute CHL timeseries for selected reference water areas.

Reads area definitions from JSON and writes one precomputed JSON per area.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib import error, parse, request


DEFAULT_AREAS_FILE = Path("precomputed/chl_reference_areas.json")
DEFAULT_OUTPUT_DIR = Path("precomputed/chl_results")
DEFAULT_BASE_URL = "http://127.0.0.1:8080"
DEFAULT_START_DATE = "auto"
DEFAULT_END_DATE = "auto"
DEFAULT_TIMEOUT_SECS = 300
DEFAULT_MAX_VALIDS = 60
DEFAULT_DAYS_PER_REQUEST = 2
DEFAULT_TILES_X = 1
DEFAULT_TILES_Y = 1
DEFAULT_METADATA_RETRIES = 2
DEFAULT_AUTO_END_OFFSET_DAYS = 1
DEFAULT_TIME_GRAIN = "raw"


@dataclass
class AreaDef:
    area_id: str
    name: str
    area_type: str
    bbox: list[float]


@dataclass
class ResolvedDateRange:
    start_date: str
    end_date: str
    requested_start: str
    requested_end: str
    available_start_time: str | None = None
    available_end_time: str | None = None


def _slugify(value: str) -> str:
    key = re.sub(r"[^0-9A-Za-z]+", "_", value.strip().lower())
    key = re.sub(r"_+", "_", key).strip("_")
    return key or "product"


def _load_areas(path: Path) -> tuple[str, str, str, list[AreaDef]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    product_id = str(payload.get("productId") or "").strip()
    dataset_id = payload.get("datasetId", "ua_chl_virtual_stations")
    variable = payload.get("variable", "CHL")
    if not product_id:
        product_id = f"{dataset_id}_{variable}"
    raw_areas = payload.get("areas", [])
    if not raw_areas:
        raise SystemExit(f"No areas found in {path}")

    areas: list[AreaDef] = []
    for item in raw_areas:
        bbox = item.get("bbox")
        if not isinstance(bbox, list) or len(bbox) != 4:
            raise SystemExit(f"Area {item.get('id')} has invalid bbox: {bbox}")
        areas.append(
            AreaDef(
                area_id=str(item["id"]),
                name=str(item.get("name", item["id"])),
                area_type=str(item.get("type", "area")),
                bbox=[float(v) for v in bbox],
            )
        )
    return product_id, dataset_id, variable, areas


def _http_get_json(url: str, *, timeout_secs: int, retries: int) -> dict:
    req = request.Request(url, method="GET")
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with request.urlopen(req, timeout=timeout_secs) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt < retries:
                continue
            break
    assert last_exc is not None
    if isinstance(last_exc, error.HTTPError):
        detail = ""
        try:
            detail = last_exc.read().decode("utf-8")
        except Exception:  # noqa: BLE001
            detail = ""
        raise RuntimeError(f"HTTP {last_exc.code} GET {url}. Body={detail[:400]}") from last_exc
    raise RuntimeError(f"GET failed for {url}: {last_exc}") from last_exc


def _extract_time_coordinates(payload: dict) -> list[str]:
    coords = payload.get("coordinates")
    if isinstance(coords, list) and coords:
        first = coords[0]
        last = coords[-1]
        if isinstance(first, str) and isinstance(last, str):
            return [str(v) for v in coords if isinstance(v, str)]

    dimensions = payload.get("dimensions")
    if isinstance(dimensions, list):
        for dim in dimensions:
            if not isinstance(dim, dict):
                continue
            if str(dim.get("name")) != "time":
                continue
            dim_coords = dim.get("coordinates")
            if isinstance(dim_coords, list) and dim_coords:
                first = dim_coords[0]
                last = dim_coords[-1]
                if isinstance(first, str) and isinstance(last, str):
                    return [str(v) for v in dim_coords if isinstance(v, str)]
    return []


def _parse_user_date(value: str, *, arg_name: str) -> date:
    v = value.strip()
    try:
        if len(v) == 10:
            return datetime.strptime(v, "%Y-%m-%d").date()
        return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
    except ValueError as e:
        raise SystemExit(f"Invalid {arg_name}: {value!r} ({e})") from e


def _resolve_available_time_range(
    *,
    base_url: str,
    dataset_id: str,
    timeout_secs: int,
    metadata_retries: int,
) -> tuple[str, str]:
    dataset_q = parse.quote(dataset_id, safe="")
    base = base_url.rstrip("/")
    candidate_urls = [
        f"{base}/datasets/{dataset_q}/coords/time",
        f"{base}/datasets/{dataset_q}",
    ]
    last_error: Exception | None = None
    for url in candidate_urls:
        try:
            payload = _http_get_json(url, timeout_secs=timeout_secs, retries=metadata_retries)
            coords = _extract_time_coordinates(payload)
            if coords:
                return coords[0], coords[-1]
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue
    raise SystemExit(
        "Could not resolve available time range from xcube API for dataset "
        f"{dataset_id!r}. Last error: {last_error}"
    )


def _resolve_date_range(
    *,
    start_date_arg: str,
    end_date_arg: str,
    base_url: str,
    dataset_id: str,
    timeout_secs: int,
    metadata_retries: int,
    auto_end_offset_days: int,
) -> ResolvedDateRange:
    start_arg = start_date_arg.strip()
    end_arg = end_date_arg.strip()
    use_auto_start = start_arg.lower() == "auto"
    use_auto_end = end_arg.lower() == "auto"

    available_start_time: str | None = None
    available_end_time: str | None = None
    if use_auto_start or use_auto_end:
        available_start_time, available_end_time = _resolve_available_time_range(
            base_url=base_url,
            dataset_id=dataset_id,
            timeout_secs=timeout_secs,
            metadata_retries=metadata_retries,
        )

    if use_auto_start:
        assert available_start_time is not None
        start_date = _parse_user_date(available_start_time, arg_name="available start time")
    else:
        start_date = _parse_user_date(start_arg, arg_name="--start-date")

    if use_auto_end:
        assert available_end_time is not None
        end_date = _parse_user_date(available_end_time, arg_name="available end time")
        # timeseries batching uses end-date as the right boundary of windows.
        # Add one day by default so the last available sensing day is included.
        end_date = end_date + timedelta(days=auto_end_offset_days)
    else:
        end_date = _parse_user_date(end_arg, arg_name="--end-date")

    if start_date >= end_date:
        raise SystemExit(
            f"Resolved date range is invalid: start={start_date.isoformat()} "
            f"end={end_date.isoformat()} (must be start < end)"
        )

    return ResolvedDateRange(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        requested_start=start_arg,
        requested_end=end_arg,
        available_start_time=available_start_time,
        available_end_time=available_end_time,
    )


def _run_batch(
    *,
    python_bin: str,
    base_url: str,
    dataset_id: str,
    variable: str,
    area: AreaDef,
    start_date: str,
    end_date: str,
    timeout_secs: int,
    max_valids: int,
    days_per_request: int,
    time_grain: str,
    tiles_x: int,
    tiles_y: int,
    continue_on_error: bool,
    output_path: Path,
) -> None:
    x0, y0, x1, y1 = area.bbox
    cmd = [
        python_bin,
        "scripts/chl_timeseries_batch.py",
        "--base-url",
        base_url,
        "--dataset-id",
        dataset_id,
        "--var-name",
        variable,
        "--start-date",
        start_date,
        "--end-date",
        end_date,
        "--bbox",
        str(x0),
        str(y0),
        str(x1),
        str(y1),
        "--tiles-x",
        str(tiles_x),
        "--tiles-y",
        str(tiles_y),
        "--days-per-request",
        str(days_per_request),
        "--time-grain",
        str(time_grain),
        "--max-valids",
        str(max_valids),
        "--timeout-secs",
        str(timeout_secs),
        "--retries",
        "2",
    ]
    if continue_on_error:
        cmd.append("--continue-on-error")
    cmd.extend(
        [
            "--output",
            output_path.as_posix(),
        ]
    )
    subprocess.run(cmd, check=True)


def _attach_metadata(
    output_path: Path,
    *,
    area: AreaDef,
    product_id: str,
    dataset_id: str,
    variable: str,
    date_range: ResolvedDateRange,
) -> None:
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    payload["product"] = {
        "id": product_id,
        "datasetId": dataset_id,
        "variable": variable,
    }
    payload["area"] = {
        "id": area.area_id,
        "name": area.name,
        "type": area.area_type,
        "bbox": area.bbox,
    }
    query = payload.get("query", {})
    if isinstance(query, dict):
        query["requestedStartDate"] = date_range.requested_start
        query["requestedEndDate"] = date_range.requested_end
        if date_range.available_start_time and date_range.available_end_time:
            query["availableStartTime"] = date_range.available_start_time
            query["availableEndTime"] = date_range.available_end_time
        payload["query"] = query
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def _build_manifest_item(*, output_path: Path, area: AreaDef) -> dict:
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    summary = payload.get("summary", {})
    rows = summary.get("rows", 0) if isinstance(summary, dict) else 0
    failed = summary.get("requestsFailed", 0) if isinstance(summary, dict) else 0
    return {
        "file": output_path.name,
        "areaId": area.area_id,
        "areaName": area.name,
        "areaType": area.area_type,
        "hasData": bool(payload.get("hasData", False)),
        "rows": int(rows) if isinstance(rows, int | float) else 0,
        "requestsFailed": int(failed) if isinstance(failed, int | float) else 0,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Precompute CHL results for reference water areas."
    )
    parser.add_argument("--areas-file", type=Path, default=DEFAULT_AREAS_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--python-bin",
        default=sys.executable or "python3",
        help=(
            "Python executable used to run scripts/chl_timeseries_batch.py. "
            "Defaults to current interpreter."
        ),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--timeout-secs", type=int, default=DEFAULT_TIMEOUT_SECS)
    parser.add_argument("--metadata-retries", type=int, default=DEFAULT_METADATA_RETRIES)
    parser.add_argument("--auto-end-offset-days", type=int, default=DEFAULT_AUTO_END_OFFSET_DAYS)
    parser.add_argument("--max-valids", type=int, default=DEFAULT_MAX_VALIDS)
    parser.add_argument("--days-per-request", type=int, default=DEFAULT_DAYS_PER_REQUEST)
    parser.add_argument(
        "--time-grain",
        choices=("raw", "daily", "monthly"),
        default=DEFAULT_TIME_GRAIN,
        help=(
            "Temporal normalization for output rows. "
            "raw keeps source timestamps, daily groups by day, monthly groups by month."
        ),
    )
    parser.add_argument("--tiles-x", type=int, default=DEFAULT_TILES_X)
    parser.add_argument("--tiles-y", type=int, default=DEFAULT_TILES_Y)
    parser.add_argument("--continue-on-error", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    areas_file = args.areas_file.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    product_id, dataset_id, variable, areas = _load_areas(areas_file)
    date_range = _resolve_date_range(
        start_date_arg=args.start_date,
        end_date_arg=args.end_date,
        base_url=args.base_url,
        dataset_id=dataset_id,
        timeout_secs=args.timeout_secs,
        metadata_retries=args.metadata_retries,
        auto_end_offset_days=args.auto_end_offset_days,
    )
    product_key = _slugify(product_id)
    output_dir = output_dir / product_key
    output_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"Loaded {len(areas)} areas from {areas_file} "
        f"(product={product_id}, key={product_key})"
    )
    print(
        f"Resolved date range: {date_range.start_date} -> {date_range.end_date} "
        f"(requested: {date_range.requested_start} -> {date_range.requested_end})"
    )
    print(f"Time grain: {args.time_grain}")
    if date_range.available_start_time and date_range.available_end_time:
        print(
            "Available dataset time range: "
            f"{date_range.available_start_time} -> {date_range.available_end_time}"
        )

    manifest_items: list[dict] = []
    for area in areas:
        suffix = "" if args.time_grain == "raw" else f"__{args.time_grain}"
        out_path = (
            output_dir
            / (
                f"{product_key}__{area.area_id}__"
                f"{date_range.start_date}_{date_range.end_date}{suffix}.json"
            )
        )
        print(f"Precomputing {area.area_id} -> {out_path}")
        _run_batch(
            python_bin=args.python_bin,
            base_url=args.base_url,
            dataset_id=dataset_id,
            variable=variable,
            area=area,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
            timeout_secs=args.timeout_secs,
            max_valids=args.max_valids,
            days_per_request=args.days_per_request,
            time_grain=args.time_grain,
            tiles_x=args.tiles_x,
            tiles_y=args.tiles_y,
            continue_on_error=bool(args.continue_on_error),
            output_path=out_path,
        )
        _attach_metadata(
            out_path,
            area=area,
            product_id=product_id,
            dataset_id=dataset_id,
            variable=variable,
            date_range=date_range,
        )
        manifest_items.append(_build_manifest_item(output_path=out_path, area=area))

    manifest = {
        "productId": product_id,
        "productKey": product_key,
        "datasetId": dataset_id,
        "varName": variable,
        "timeGrain": args.time_grain,
        "startDate": date_range.start_date,
        "endDate": date_range.end_date,
        "requestedStartDate": date_range.requested_start,
        "requestedEndDate": date_range.requested_end,
        "availableStartTime": date_range.available_start_time,
        "availableEndTime": date_range.available_end_time,
        "items": manifest_items,
    }
    manifest_suffix = "" if args.time_grain == "raw" else f"_{args.time_grain}"
    manifest_path = (
        output_dir / f"manifest_{date_range.start_date}_{date_range.end_date}{manifest_suffix}.json"
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Wrote {manifest_path}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
