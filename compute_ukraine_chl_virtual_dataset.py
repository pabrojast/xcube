#!/usr/bin/env python3
"""
Build one CHL dataset from multiple Terrascope CHL tile datasets.

Used by xcube with ``FileSystem: memory`` to expose a single logical dataset
for area/time-series calculations.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import xarray as xr

_CACHED_COMBINED_DATASET: xr.Dataset | None = None


def _parse_geo_transform(dataset: xr.Dataset):
    spatial_ref = dataset.get("spatial_ref")
    if spatial_ref is None:
        return None

    raw_transform = spatial_ref.attrs.get("GeoTransform")
    if raw_transform is None:
        return None

    if isinstance(raw_transform, str):
        values = raw_transform.split()
    elif isinstance(raw_transform, (tuple, list)):
        values = raw_transform
    else:
        return None

    if len(values) != 6:
        return None

    try:
        return tuple(float(v) for v in values)
    except (TypeError, ValueError):
        return None


def _assign_projected_xy(dataset: xr.Dataset) -> xr.Dataset:
    if "x" not in dataset.dims or "y" not in dataset.dims:
        return dataset

    transform = _parse_geo_transform(dataset)
    if transform is None:
        return dataset

    x0, dx, _, y0, _, dy = transform
    nx = int(dataset.sizes["x"])
    ny = int(dataset.sizes["y"])

    # GDAL geotransform origin is corner-based; xarray coordinates are center-based.
    x = x0 + dx * (0.5 + np.arange(nx, dtype=np.float64))
    y = y0 + dy * (0.5 + np.arange(ny, dtype=np.float64))

    return dataset.assign_coords(x=("x", x), y=("y", y))


def _drop_duplicate_index(dataset: xr.Dataset, dim_name: str) -> xr.Dataset:
    if dim_name not in dataset.dims:
        return dataset
    index = dataset.get_index(dim_name)
    if index.is_unique:
        return dataset
    return dataset.isel({dim_name: ~index.duplicated()})


def _prepare_dataset(dataset: xr.Dataset) -> xr.Dataset:
    if "CHL" not in dataset.data_vars:
        raise ValueError("Input CHL tile does not contain variable 'CHL'")

    kept_vars = ["CHL"]
    if "spatial_ref" in dataset:
        kept_vars.append("spatial_ref")
    prepared = dataset[kept_vars]
    prepared = _assign_projected_xy(prepared)

    # Keep only time normalization here. Sorting/normalizing x/y for each tile
    # can build very large alignment graphs and is not required for most tile
    # stores where x/y are already monotonic.
    for dim_name in ("time",):
        if dim_name in prepared.coords:
            prepared = prepared.sortby(dim_name)
            prepared = _drop_duplicate_index(prepared, dim_name)

    return prepared


def _combine_datasets(datasets: Iterable[xr.Dataset]) -> xr.Dataset:
    dataset_list = list(datasets)
    # Prefer merge to avoid costly coordinate normalization from combine_by_coords
    # on many large CHL tile datasets.
    return xr.merge(
        dataset_list,
        compat="no_conflicts",
        join="outer",
        combine_attrs="drop_conflicts",
    )


def compute_dataset(*tile_datasets: xr.Dataset) -> xr.Dataset:
    global _CACHED_COMBINED_DATASET
    if not tile_datasets:
        raise ValueError("At least one CHL input dataset is required")

    if _CACHED_COMBINED_DATASET is not None:
        return _CACHED_COMBINED_DATASET

    prepared = [_prepare_dataset(ds) for ds in tile_datasets]
    merged = _combine_datasets(prepared)

    for dim_name in ("time",):
        if dim_name in merged.coords:
            merged = merged.sortby(dim_name)
            merged = _drop_duplicate_index(merged, dim_name)

    _CACHED_COMBINED_DATASET = merged
    return _CACHED_COMBINED_DATASET
