#!/usr/bin/env python3
"""Build a daily CHL mosaic Zarr from the raw CHL mosaic Zarr."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import xarray as xr
import zarr
from numcodecs import Blosc

LOGGER = logging.getLogger("chl_mosaic_to_daily_zarr")

DEFAULT_INPUT = Path(
    "/home/pabrojast/Proyectos/stacprocess-ihp/data/terrascope_all_grids_full_history_zarr/chl_mosaic_ts.zarr"
)
DEFAULT_OUTPUT = Path(
    "/home/pabrojast/Proyectos/stacprocess-ihp/data/terrascope_all_grids_full_history_zarr/chl_mosaic_daily.zarr"
)
DEFAULT_VARIABLE = "CHL"
DEFAULT_FREQ = "D"
DEFAULT_CHUNKS = {"time": 1, "y": 256, "x": 256}
DEFAULT_COMPLETE_MARKER = ".daily_complete.json"


def parse_chunks(raw: str) -> dict[str, int]:
    chunks = dict(DEFAULT_CHUNKS)
    if not raw:
        return chunks
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        if "=" not in token:
            raise ValueError(
                f"Invalid chunk token {token!r}. Use format 'time=1,y=256,x=256'."
            )
        key, value = token.split("=", 1)
        key = key.strip().lower()
        if key not in chunks:
            raise ValueError(f"Unsupported chunk key {key!r}. Allowed: time,y,x.")
        size = int(value.strip())
        if size <= 0:
            raise ValueError(f"Chunk size for {key!r} must be > 0.")
        chunks[key] = size
    return chunks


def _open_zarr(path: Path) -> xr.Dataset:
    try:
        return xr.open_zarr(path.as_posix(), consolidated=True)
    except (ValueError, KeyError):
        return xr.open_zarr(path.as_posix(), consolidated=False)


def _validate_dims(var: xr.DataArray) -> tuple[str, str, str]:
    if var.ndim != 3:
        raise ValueError(f"Expected 3D variable (time,y,x), got dims={var.dims!r}")
    if "time" not in var.dims:
        raise ValueError("Expected a 'time' dimension")
    if "y" not in var.dims or "x" not in var.dims:
        raise ValueError("Expected spatial dimensions 'y' and 'x'")
    return "time", "y", "x"


def _aggregate_daily_sparse(src_var: xr.DataArray, freq: str) -> xr.DataArray:
    daily = src_var.astype(np.float32).resample(time=freq).mean(
        skipna=True, keep_attrs=True
    )
    # Keep only days that actually contain data.
    return daily.dropna(dim="time", how="all")


def build_daily_mosaic(
    *,
    input_path: Path,
    output_path: Path,
    variable: str,
    freq: str,
    chunks: dict[str, int],
    overwrite: bool,
    consolidate: bool,
    complete_marker: str,
) -> dict[str, object]:
    if not input_path.is_dir():
        raise FileNotFoundError(f"Input mosaic not found: {input_path}")

    if output_path.exists():
        if not overwrite:
            raise FileExistsError(f"Output exists and --overwrite not set: {output_path}")
        if output_path.is_dir():
            shutil.rmtree(output_path)
        else:
            output_path.unlink()

    with _open_zarr(input_path) as ds:
        if variable not in ds.data_vars:
            raise ValueError(f"Variable {variable!r} not found in {input_path}")

        src_var = ds[variable]
        _, y_name, x_name = _validate_dims(src_var)

        LOGGER.info(
            "Input variable %s dims=%s shape=%s chunks=%s",
            variable,
            src_var.dims,
            tuple(int(v) for v in src_var.shape),
            src_var.chunks,
        )

        # Keep only days with observations; this avoids a very long sequence
        # of all-NaN daily slices for days with no acquisitions.
        daily = _aggregate_daily_sparse(src_var, freq=freq)

        out_ds = daily.to_dataset(name=variable)
        out_ds.attrs = dict(ds.attrs)
        out_ds[variable].attrs = dict(src_var.attrs)
        if "spatial_ref" in ds:
            out_ds["spatial_ref"] = ds["spatial_ref"]

        fill_value = out_ds[variable].attrs.get("_FillValue", np.nan)
        try:
            fill_value = np.float32(fill_value)
        except (TypeError, ValueError):
            fill_value = np.float32(np.nan)

        encoding = {
            variable: {
                "dtype": np.float32,
                "chunks": (chunks["time"], chunks["y"], chunks["x"]),
                "compressor": Blosc(cname="zstd", clevel=3, shuffle=Blosc.SHUFFLE),
                "_FillValue": fill_value,
            }
        }

        LOGGER.info(
            "Writing daily mosaic %s with chunks=(%d,%d,%d)",
            output_path,
            chunks["time"],
            chunks["y"],
            chunks["x"],
        )
        out_ds.to_zarr(
            output_path.as_posix(),
            mode="w",
            encoding=encoding,
            consolidated=False,
            zarr_format=2,
        )

        if consolidate:
            zarr.consolidate_metadata(output_path.as_posix())

        time_values = out_ds["time"].values
        result = {
            "store": output_path.as_posix(),
            "source_store": input_path.as_posix(),
            "variable": variable,
            "freq": freq,
            "rows_time": int(time_values.size),
            "first_time": str(time_values[0]) if time_values.size else None,
            "last_time": str(time_values[-1]) if time_values.size else None,
            "shape": {
                "time": int(out_ds.sizes["time"]),
                "y": int(out_ds.sizes[y_name]),
                "x": int(out_ds.sizes[x_name]),
            },
            "chunks": {
                "time": int(chunks["time"]),
                "y": int(chunks["y"]),
                "x": int(chunks["x"]),
            },
            "consolidated_metadata": bool(consolidate),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    marker = output_path / complete_marker
    marker.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create daily CHL mosaic Zarr from the raw CHL mosaic Zarr."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Raw CHL mosaic Zarr.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output daily CHL mosaic Zarr.",
    )
    parser.add_argument("--variable", default=DEFAULT_VARIABLE)
    parser.add_argument(
        "--freq",
        default=DEFAULT_FREQ,
        help="Datetime floor frequency used for grouping (default: D).",
    )
    parser.add_argument(
        "--chunks",
        default="time=1,y=256,x=256",
        help="Output chunking, e.g. 'time=1,y=256,x=256'.",
    )
    parser.add_argument(
        "--complete-marker",
        default=DEFAULT_COMPLETE_MARKER,
        help="Completion marker JSON file written inside output store.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--consolidate", action="store_true")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    chunks = parse_chunks(args.chunks)
    result = build_daily_mosaic(
        input_path=args.input.expanduser().resolve(),
        output_path=args.output.expanduser().resolve(),
        variable=args.variable,
        freq=args.freq,
        chunks=chunks,
        overwrite=bool(args.overwrite),
        consolidate=bool(args.consolidate),
        complete_marker=args.complete_marker,
    )
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
