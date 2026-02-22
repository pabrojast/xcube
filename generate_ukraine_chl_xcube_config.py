#!/usr/bin/env python3
"""
Generate an xcube service config for local Terrascope CHL Zarr tiles.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_ZARR_ROOT = Path(
    "/home/pabrojast/Proyectos/stacprocess-ihp/data/terrascope_all_grids_full_history_zarr"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "xcube_ukraine_chl_local_config.yml"
DEFAULT_COMPUTE_SCRIPT = "compute_ukraine_chl_virtual_dataset.py"
DEFAULT_MOSAIC_STORE = "chl_mosaic_ts.zarr"
DEFAULT_LEVELS_STORE = "chl_mosaic_ts.levels"
DEFAULT_DAILY_MOSAIC_STORE = "chl_mosaic_daily.zarr"
DEFAULT_DAILY_LEVELS_STORE = "chl_mosaic_daily.levels"
DEFAULT_MONTHLY_MOSAIC_STORE = "chl_mosaic_monthly.zarr"
DEFAULT_MONTHLY_LEVELS_STORE = "chl_mosaic_monthly.levels"
DEFAULT_PRECOMPUTED_DIR = "precomputed/chl_results"
DEFAULT_PRECOMPUTED_ROUTE = "/precomputed"
DEFAULT_STORE_ID = "file"
DEFAULT_FILE_STORE_IDENTIFIER = "terrascope_chl_local"
DEFAULT_ABFS_STORE_IDENTIFIER = "terrascope_chl_abfs"
DEFAULT_ABFS_ROOT = "data/xcube/terrascope_all_grids_full_history_zarr"
DEFAULT_ABFS_ACCOUNT_NAME = "${AZURE_STORAGE_ACCOUNT_NAME}"
DEFAULT_ABFS_ACCOUNT_KEY = "${AZURE_STORAGE_ACCOUNT_KEY}"
MOSAIC_COMPLETE_MARKER = ".mosaic_complete.json"
COMBINED_DATASET_ID = "ua_chl_virtual_stations"
DEFAULT_DAILY_DATASET_ID = "ua_chl_daily"
DEFAULT_MONTHLY_DATASET_ID = "ua_chl_monthly"
DEFAULT_TILE_IDS = (
    "36TVS",
    "36TWS",
    "36TWT",
    "36TXT",
    "36UUA",
    "36UUB",
    "36UUV",
    "36UVV",
    "36UWU",
    "36UWV",
    "36UXU",
)


def _discover_tiles(root: Path) -> list[tuple[str, str]]:
    tiles: list[tuple[str, str]] = []
    for zarr_path in sorted(root.glob("*_chl_ts.zarr")):
        if not zarr_path.is_dir():
            continue
        dataset_name = zarr_path.name
        tile_id = dataset_name.removesuffix("_chl_ts.zarr")
        tiles.append((tile_id, dataset_name))
    return tiles


def _parse_tile_ids(raw_tile_ids: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for token in raw_tile_ids.split(","):
        tile_id = token.strip().upper()
        if not tile_id or tile_id in seen:
            continue
        seen.add(tile_id)
        values.append(tile_id)
    return values


def _tiles_from_ids(tile_ids: list[str]) -> list[tuple[str, str]]:
    return [(tile_id, f"{tile_id}_chl_ts.zarr") for tile_id in tile_ids]


def _is_mosaic_ready(mosaic_path: Path, allow_incomplete: bool) -> bool:
    if not mosaic_path.is_dir():
        return False
    if allow_incomplete:
        return True
    if (mosaic_path / MOSAIC_COMPLETE_MARKER).is_file():
        return True
    # Backward compatibility for previously generated consolidated mosaics.
    if (mosaic_path / ".zmetadata").is_file():
        return True
    return False


def _is_levels_ready(levels_path: Path) -> bool:
    if not levels_path.is_dir():
        return False

    zlevels_path = levels_path / ".zlevels"
    if zlevels_path.is_file():
        try:
            zlevels = json.loads(zlevels_path.read_text(encoding="utf-8"))
            num_levels = int(zlevels.get("num_levels", 0))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False
        if num_levels < 1:
            return False

        # For xcube levels:
        # - level 0 is usually a .link to the source mosaic (0.link), or 0.zarr
        # - levels >=1 are stored as "<n>.zarr"
        if not ((levels_path / "0.link").is_file() or (levels_path / "0.zarr").is_dir()):
            return False
        for level_idx in range(1, num_levels):
            if not (levels_path / f"{level_idx}.zarr").is_dir():
                return False
        return True

    # Backward-compatible fallback for old/untracked layouts.
    if (levels_path / ".zmetadata").is_file() and (levels_path / "0.zarr").is_dir():
        return True
    return any(
        child.is_dir() and child.name.endswith(".zarr")
        for child in levels_path.iterdir()
    )


def _normalize_route_path(route_path: str) -> str:
    route = route_path.strip()
    if not route:
        raise SystemExit("--precomputed-route must not be empty")
    if not route.startswith("/"):
        route = "/" + route
    while len(route) > 1 and route.endswith("/"):
        route = route[:-1]
    return route


def _resolve_static_store_path(
    *,
    zarr_root: Path,
    mosaic_store: str,
    levels_store: str,
    force_virtual: bool,
    allow_incomplete_mosaic: bool,
    assume_available: bool = False,
) -> tuple[bool, str, str]:
    """Resolve which static store to use.

    Returns:
        (use_static, store_path, mode)
        mode is one of "levels", "mosaic", or "virtual".
    """
    mosaic_path = zarr_root / mosaic_store
    levels_path = zarr_root / levels_store if levels_store else None

    if force_virtual:
        return False, mosaic_store, "virtual"

    # Remote/object stores cannot be inspected as local paths here.
    # Assume declared stores are available and prefer levels over mosaic.
    if assume_available:
        if levels_store:
            return True, levels_store, "levels"
        if mosaic_store:
            return True, mosaic_store, "mosaic"
        return False, mosaic_store, "virtual"

    if levels_path is not None and _is_levels_ready(levels_path):
        return True, levels_store, "levels"

    if _is_mosaic_ready(
        mosaic_path,
        allow_incomplete=allow_incomplete_mosaic,
    ):
        return True, mosaic_store, "mosaic"

    return False, mosaic_store, "virtual"


def _build_yaml(
    store_id: str,
    store_identifier: str,
    store_root: str,
    abfs_account_name: str,
    abfs_account_key: str,
    abfs_connection_string: str,
    abfs_anon: bool,
    tiles: list[tuple[str, str]],
    compute_script: str,
    raw_dataset_id: str,
    use_static_raw: bool,
    raw_static_store_path: str,
    publish_daily: bool,
    daily_dataset_id: str,
    daily_static_store_path: str | None,
    publish_monthly: bool,
    monthly_dataset_id: str,
    monthly_static_store_path: str | None,
    hide_raw_when_monthly: bool,
    entrypoint_dataset_id: str | None,
    precomputed_dir: str | None,
    precomputed_route: str | None,
) -> str:
    raw_hidden = publish_monthly and hide_raw_when_monthly

    lines: list[str] = []
    lines.append("# Auto-generated by generate_ukraine_chl_xcube_config.py")
    if store_id == "abfs":
        lines.append("# Terrascope CHL tiles (Ukraine, Azure Blob Storage via ABFS).")
    else:
        lines.append("# Terrascope CHL tiles (Ukraine, local filesystem store).")
    if publish_daily:
        lines.append("# Publishes daily CHL composite for fast day-level browsing.")
    if publish_monthly:
        lines.append("# Publishes monthly CHL composite as default layer for WMTS UX.")
    if use_static_raw:
        lines.append("# Publishes static CHL mosaic dataset for raw timeseries queries.")
    else:
        lines.append("# Publishes virtual-stations CHL dataset for raw timeseries queries.")
    lines.append("")
    if entrypoint_dataset_id:
        lines.append(f'EntrypointDatasetId: "{entrypoint_dataset_id}"')
        lines.append("")
    if precomputed_dir and precomputed_route:
        lines.append("static_routes:")
        lines.append(f'  - path: "{precomputed_route}"')
        lines.append(f'    dir_path: "{precomputed_dir}"')
        lines.append("")
    lines.append("DataStores:")
    lines.append(f"  - Identifier: {store_identifier}")
    lines.append(f"    StoreId: {store_id}")
    lines.append("    StoreParams:")
    lines.append(f'      root: "{store_root}"')
    if store_id == "file":
        lines.append("      max_depth: 1")
    elif store_id == "abfs":
        lines.append("      storage_options:")
        if abfs_connection_string:
            lines.append(f'        connection_string: "{abfs_connection_string}"')
        else:
            if abfs_account_name:
                lines.append(f'        account_name: "{abfs_account_name}"')
            if abfs_account_key:
                lines.append(f'        account_key: "{abfs_account_key}"')
        if abfs_anon:
            lines.append("        anon: true")
    lines.append("    Datasets:")

    for tile_id, dataset_name in tiles:
        lines.append(f"      - Identifier: ua_chl_{tile_id}")
        lines.append(f'        Title: "Ukraine CHL Tile {tile_id}"')
        lines.append("        BoundingBox: [22.0, 44.0, 40.5, 52.5]")
        lines.append(f'        Path: "{dataset_name}"')
        lines.append("        Variables:")
        lines.append("          - CHL")
        lines.append("        Hidden: true")
        lines.append("        Style: chl_default")
        lines.append("        AccessControl:")
        lines.append("          RequiredScopes: []")

    if use_static_raw:
        lines.append(f"      - Identifier: {raw_dataset_id}")
        lines.append('        Title: "Ukraine CHL Instantaneous (Advanced)"')
        lines.append("        BoundingBox: [22.0, 44.0, 40.5, 52.5]")
        lines.append(f'        Path: "{raw_static_store_path}"')
        lines.append("        Variables:")
        lines.append("          - CHL")
        if raw_hidden:
            lines.append("        Hidden: true")
        lines.append("        Style: chl_default")
        lines.append("        AccessControl:")
        lines.append("          RequiredScopes: []")

    if publish_daily and daily_static_store_path:
        lines.append(f"      - Identifier: {daily_dataset_id}")
        lines.append('        Title: "Ukraine CHL Daily Composite"')
        lines.append("        BoundingBox: [22.0, 44.0, 40.5, 52.5]")
        lines.append(f'        Path: "{daily_static_store_path}"')
        lines.append("        Variables:")
        lines.append("          - CHL")
        lines.append("        Style: chl_default")
        lines.append("        AccessControl:")
        lines.append("          RequiredScopes: []")

    if publish_monthly and monthly_static_store_path:
        lines.append(f"      - Identifier: {monthly_dataset_id}")
        lines.append('        Title: "Ukraine CHL Monthly Composite (Recommended)"')
        lines.append("        BoundingBox: [22.0, 44.0, 40.5, 52.5]")
        lines.append(f'        Path: "{monthly_static_store_path}"')
        lines.append("        Variables:")
        lines.append("          - CHL")
        lines.append("        Style: chl_default")
        lines.append("        AccessControl:")
        lines.append("          RequiredScopes: []")

    if not use_static_raw:
        lines.append("")
        lines.append("Datasets:")
        lines.append(f"  - Identifier: {raw_dataset_id}")
        lines.append('    Title: "Ukraine CHL Instantaneous (Advanced)"')
        lines.append("    BoundingBox: [22.0, 44.0, 40.5, 52.5]")
        lines.append("    FileSystem: memory")
        lines.append(f'    Path: "{compute_script}"')
        lines.append("    Function: compute_dataset")
        lines.append("    InputDatasets:")
        for tile_id, _ in tiles:
            lines.append(f"      - ua_chl_{tile_id}")
        lines.append("    Variables:")
        lines.append("      - CHL")
        if raw_hidden:
            lines.append("    Hidden: true")
        lines.append("    Style: chl_default")
        lines.append("    AccessControl:")
        lines.append("      RequiredScopes: []")

    lines.append("")
    lines.append("Styles:")
    lines.append("  - Identifier: chl_default")
    lines.append("    ColorMappings:")
    lines.append("      CHL:")
    lines.append('        ColorBar: "viridis"')
    lines.append("        ValueRange: [0.0, 120.0]")
    lines.append("")
    lines.append("  - Identifier: chl_high")
    lines.append("    ColorMappings:")
    lines.append("      CHL:")
    lines.append('        ColorBar: "inferno"')
    lines.append("        ValueRange: [0.0, 300.0]")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate xcube YAML for Ukraine CHL datasets (file or ABFS stores)."
    )
    parser.add_argument(
        "--zarr-root",
        type=Path,
        default=DEFAULT_ZARR_ROOT,
        help=(
            "Directory containing *_chl_ts.zarr tile stores when using local file store. "
            "For ABFS, it is optional unless local tile discovery is desired."
        ),
    )
    parser.add_argument(
        "--store-id",
        default=DEFAULT_STORE_ID,
        choices=("file", "abfs"),
        help="Store backend to publish in DataStores.",
    )
    parser.add_argument(
        "--store-identifier",
        default="",
        help="Optional DataStore identifier override.",
    )
    parser.add_argument(
        "--store-root",
        default="",
        help=(
            "Optional StoreParams.root override. "
            "For ABFS, default is container/prefix path."
        ),
    )
    parser.add_argument(
        "--allow-missing-zarr-root",
        action="store_true",
        help="Allow missing --zarr-root (useful for remote ABFS-only config generation).",
    )
    parser.add_argument(
        "--tile-ids",
        default="",
        help=(
            "Comma-separated tile IDs to publish as hidden tile datasets, "
            "e.g. '36TVS,36TWS'. If omitted, auto-discovery is attempted."
        ),
    )
    parser.add_argument(
        "--abfs-account-name",
        default=DEFAULT_ABFS_ACCOUNT_NAME,
        help=(
            "ABFS account_name (can use env template like ${AZURE_STORAGE_ACCOUNT_NAME})."
        ),
    )
    parser.add_argument(
        "--abfs-account-key",
        default=DEFAULT_ABFS_ACCOUNT_KEY,
        help=(
            "ABFS account_key (can use env template like ${AZURE_STORAGE_ACCOUNT_KEY})."
        ),
    )
    parser.add_argument(
        "--abfs-connection-string",
        default="",
        help=(
            "ABFS connection_string template. If provided, it is preferred over "
            "account_name/account_key."
        ),
    )
    parser.add_argument(
        "--abfs-anon",
        action="store_true",
        help="Set ABFS storage_options.anon=true.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output YAML config path.",
    )
    parser.add_argument(
        "--compute-script",
        default=DEFAULT_COMPUTE_SCRIPT,
        help="Python script used by the virtual-stations combined dataset.",
    )
    parser.add_argument(
        "--mosaic-store",
        default=DEFAULT_MOSAIC_STORE,
        help=(
            "Mosaic Zarr directory name relative to --zarr-root. "
            "If present, it is used as the combined dataset source."
        ),
    )
    parser.add_argument(
        "--levels-store",
        default=DEFAULT_LEVELS_STORE,
        help=(
            "Optional levels directory name relative to --zarr-root. "
            "If present, it is preferred over --mosaic-store for WMTS tiles."
        ),
    )
    parser.add_argument(
        "--daily-mosaic-store",
        default=DEFAULT_DAILY_MOSAIC_STORE,
        help=(
            "Optional daily-composite mosaic Zarr directory relative to --zarr-root. "
            "Used to publish a day-level CHL dataset when available."
        ),
    )
    parser.add_argument(
        "--daily-levels-store",
        default=DEFAULT_DAILY_LEVELS_STORE,
        help=(
            "Optional daily-composite .levels directory relative to --zarr-root. "
            "If present, it is preferred over --daily-mosaic-store."
        ),
    )
    parser.add_argument(
        "--disable-daily-layer",
        action="store_true",
        help="Disable publishing the daily-composite dataset.",
    )
    parser.add_argument(
        "--monthly-mosaic-store",
        default=DEFAULT_MONTHLY_MOSAIC_STORE,
        help=(
            "Optional monthly-composite mosaic Zarr directory relative to --zarr-root. "
            "Used to publish a user-friendly monthly WMTS layer when available."
        ),
    )
    parser.add_argument(
        "--monthly-levels-store",
        default=DEFAULT_MONTHLY_LEVELS_STORE,
        help=(
            "Optional monthly-composite .levels directory relative to --zarr-root. "
            "If present, it is preferred over --monthly-mosaic-store."
        ),
    )
    parser.add_argument(
        "--disable-monthly-layer",
        action="store_true",
        help="Disable publishing the monthly-composite dataset.",
    )
    parser.add_argument(
        "--force-virtual",
        action="store_true",
        help="Ignore --mosaic-store and always publish the memory virtual dataset.",
    )
    parser.add_argument(
        "--allow-incomplete-mosaic",
        action="store_true",
        help="Publish mosaic even if completion marker is missing.",
    )
    parser.add_argument(
        "--precomputed-dir",
        default=DEFAULT_PRECOMPUTED_DIR,
        help=(
            "Directory to expose as static JSON endpoint. Can be relative "
            "(resolved by xcube base_dir) or absolute."
        ),
    )
    parser.add_argument(
        "--precomputed-route",
        default=DEFAULT_PRECOMPUTED_ROUTE,
        help="URL route path for static precomputed JSON files.",
    )
    parser.add_argument(
        "--disable-precomputed-route",
        action="store_true",
        help="Disable static /precomputed route generation.",
    )
    parser.add_argument(
        "--raw-dataset-id",
        default=COMBINED_DATASET_ID,
        help="Dataset identifier for the raw/instantaneous CHL dataset.",
    )
    parser.add_argument(
        "--daily-dataset-id",
        default=DEFAULT_DAILY_DATASET_ID,
        help="Dataset identifier for the daily-composite CHL dataset.",
    )
    parser.add_argument(
        "--monthly-dataset-id",
        default=DEFAULT_MONTHLY_DATASET_ID,
        help="Dataset identifier for the monthly-composite CHL dataset.",
    )
    parser.add_argument(
        "--entrypoint-dataset-id",
        default="",
        help=(
            "Optional EntrypointDatasetId override. If omitted, monthly dataset is used "
            "when available; otherwise the raw dataset is used."
        ),
    )
    parser.set_defaults(hide_raw_when_monthly=True)
    parser.add_argument(
        "--hide-raw-when-monthly",
        dest="hide_raw_when_monthly",
        action="store_true",
        help="Hide raw dataset from /datasets and WMTS capabilities when monthly exists.",
    )
    parser.add_argument(
        "--show-raw-when-monthly",
        dest="hide_raw_when_monthly",
        action="store_false",
        help="Keep raw dataset visible even when monthly dataset exists.",
    )
    args = parser.parse_args()

    zarr_root = args.zarr_root.expanduser().resolve()
    output_path = args.output.expanduser().resolve()
    store_id = str(args.store_id).strip()
    if store_id not in {"file", "abfs"}:
        raise SystemExit(f"Unsupported --store-id: {store_id!r}")

    if store_id == "file":
        if not zarr_root.exists():
            raise SystemExit(f"Zarr root does not exist: {zarr_root}")
        if not zarr_root.is_dir():
            raise SystemExit(f"Zarr root is not a directory: {zarr_root}")
    elif not args.allow_missing_zarr_root:
        if not zarr_root.exists():
            raise SystemExit(
                f"Zarr root does not exist: {zarr_root}. "
                "Use --allow-missing-zarr-root for ABFS-only generation."
            )
        if not zarr_root.is_dir():
            raise SystemExit(f"Zarr root is not a directory: {zarr_root}")

    tile_ids = _parse_tile_ids(str(args.tile_ids))
    if tile_ids:
        tiles = _tiles_from_ids(tile_ids)
    elif zarr_root.exists() and zarr_root.is_dir():
        tiles = _discover_tiles(zarr_root)
    elif store_id == "abfs":
        tiles = _tiles_from_ids(list(DEFAULT_TILE_IDS))
    else:
        tiles = []
    if not tiles:
        raise SystemExit(
            f"No CHL tile datasets discovered. "
            f"zarr_root={zarr_root} tile_ids={tile_ids!r}"
        )

    mosaic_store = args.mosaic_store.strip()
    if not mosaic_store:
        raise SystemExit("--mosaic-store must not be empty")
    if Path(mosaic_store).is_absolute():
        raise SystemExit("--mosaic-store must be relative to --zarr-root")

    levels_store = args.levels_store.strip()
    if levels_store and Path(levels_store).is_absolute():
        raise SystemExit("--levels-store must be relative to --zarr-root")

    daily_mosaic_store = args.daily_mosaic_store.strip()
    if daily_mosaic_store and Path(daily_mosaic_store).is_absolute():
        raise SystemExit("--daily-mosaic-store must be relative to --zarr-root")
    daily_levels_store = args.daily_levels_store.strip()
    if daily_levels_store and Path(daily_levels_store).is_absolute():
        raise SystemExit("--daily-levels-store must be relative to --zarr-root")

    monthly_mosaic_store = args.monthly_mosaic_store.strip()
    if monthly_mosaic_store and Path(monthly_mosaic_store).is_absolute():
        raise SystemExit("--monthly-mosaic-store must be relative to --zarr-root")
    monthly_levels_store = args.monthly_levels_store.strip()
    if monthly_levels_store and Path(monthly_levels_store).is_absolute():
        raise SystemExit("--monthly-levels-store must be relative to --zarr-root")

    store_identifier = str(args.store_identifier).strip()
    if not store_identifier:
        store_identifier = (
            DEFAULT_FILE_STORE_IDENTIFIER
            if store_id == "file"
            else DEFAULT_ABFS_STORE_IDENTIFIER
        )

    store_root = str(args.store_root).strip()
    if not store_root:
        store_root = (
            zarr_root.as_posix()
            if store_id == "file"
            else DEFAULT_ABFS_ROOT
        )

    abfs_connection_string = str(args.abfs_connection_string).strip()
    abfs_account_name = str(args.abfs_account_name).strip()
    abfs_account_key = str(args.abfs_account_key).strip()
    abfs_anon = bool(args.abfs_anon)
    if store_id == "abfs" and not abfs_anon:
        if not abfs_connection_string and not (
            abfs_account_name or abfs_account_key
        ):
            raise SystemExit(
                "ABFS store requires credentials: "
                "set --abfs-connection-string or --abfs-account-name/--abfs-account-key "
                "(or use --abfs-anon)."
            )

    use_static_raw, raw_static_store_path, raw_mode = _resolve_static_store_path(
        zarr_root=zarr_root,
        mosaic_store=mosaic_store,
        levels_store=levels_store,
        force_virtual=bool(args.force_virtual),
        allow_incomplete_mosaic=bool(args.allow_incomplete_mosaic),
        assume_available=(store_id != "file"),
    )

    publish_daily = False
    daily_static_store_path: str | None = None
    daily_mode = "disabled"
    if not args.disable_daily_layer:
        daily_use_static, daily_store_path, daily_mode = _resolve_static_store_path(
            zarr_root=zarr_root,
            mosaic_store=daily_mosaic_store,
            levels_store=daily_levels_store,
            force_virtual=False,
            allow_incomplete_mosaic=bool(args.allow_incomplete_mosaic),
            assume_available=(store_id != "file"),
        )
        if daily_use_static:
            publish_daily = True
            daily_static_store_path = daily_store_path

    publish_monthly = False
    monthly_static_store_path: str | None = None
    monthly_mode = "disabled"
    if not args.disable_monthly_layer:
        monthly_use_static, monthly_store_path, monthly_mode = _resolve_static_store_path(
            zarr_root=zarr_root,
            mosaic_store=monthly_mosaic_store,
            levels_store=monthly_levels_store,
            force_virtual=False,
            allow_incomplete_mosaic=bool(args.allow_incomplete_mosaic),
            assume_available=(store_id != "file"),
        )
        if monthly_use_static:
            publish_monthly = True
            monthly_static_store_path = monthly_store_path

    precomputed_dir: str | None = None
    precomputed_route: str | None = None
    if not args.disable_precomputed_route:
        precomputed_dir_value = str(args.precomputed_dir).strip()
        if precomputed_dir_value:
            precomputed_dir = precomputed_dir_value
            precomputed_route = _normalize_route_path(args.precomputed_route)

    raw_dataset_id = str(args.raw_dataset_id).strip()
    if not raw_dataset_id:
        raise SystemExit("--raw-dataset-id must not be empty")
    daily_dataset_id = str(args.daily_dataset_id).strip()
    if not daily_dataset_id:
        raise SystemExit("--daily-dataset-id must not be empty")
    monthly_dataset_id = str(args.monthly_dataset_id).strip()
    if not monthly_dataset_id:
        raise SystemExit("--monthly-dataset-id must not be empty")
    if publish_daily and daily_dataset_id == raw_dataset_id:
        raise SystemExit("--daily-dataset-id must be different from --raw-dataset-id")
    if publish_monthly and monthly_dataset_id == raw_dataset_id:
        raise SystemExit("--monthly-dataset-id must be different from --raw-dataset-id")
    if publish_daily and publish_monthly and monthly_dataset_id == daily_dataset_id:
        raise SystemExit("--monthly-dataset-id must be different from --daily-dataset-id")

    entrypoint_dataset_id_arg = str(args.entrypoint_dataset_id).strip()
    if entrypoint_dataset_id_arg:
        entrypoint_dataset_id = entrypoint_dataset_id_arg
    elif publish_monthly:
        entrypoint_dataset_id = monthly_dataset_id
    elif publish_daily:
        entrypoint_dataset_id = daily_dataset_id
    else:
        entrypoint_dataset_id = raw_dataset_id

    yaml_text = _build_yaml(
        store_id=store_id,
        store_identifier=store_identifier,
        store_root=store_root,
        abfs_account_name=abfs_account_name,
        abfs_account_key=abfs_account_key,
        abfs_connection_string=abfs_connection_string,
        abfs_anon=abfs_anon,
        tiles=tiles,
        compute_script=args.compute_script,
        raw_dataset_id=raw_dataset_id,
        use_static_raw=use_static_raw,
        raw_static_store_path=raw_static_store_path,
        publish_daily=publish_daily,
        daily_dataset_id=daily_dataset_id,
        daily_static_store_path=daily_static_store_path,
        publish_monthly=publish_monthly,
        monthly_dataset_id=monthly_dataset_id,
        monthly_static_store_path=monthly_static_store_path,
        hide_raw_when_monthly=bool(args.hide_raw_when_monthly),
        entrypoint_dataset_id=entrypoint_dataset_id,
        precomputed_dir=precomputed_dir,
        precomputed_route=precomputed_route,
    )
    output_path.write_text(yaml_text, encoding="utf-8")

    print(f"Generated {output_path}")
    print(
        f"Store: id={store_id} identifier={store_identifier} "
        f"root={store_root}"
    )
    if store_id == "abfs":
        if abfs_connection_string:
            print("ABFS auth: connection_string")
        elif abfs_anon:
            print("ABFS auth: anon")
        else:
            key_state = "set" if abfs_account_key else "empty"
            print(f"ABFS account_name: {abfs_account_name}")
            print(f"ABFS account_key: {key_state}")
    print(f"Local zarr root (discovery): {zarr_root}")
    print(f"Tile datasets (hidden): {len(tiles)}")
    print(f"Raw dataset: {raw_dataset_id} (mode={raw_mode}, store={raw_static_store_path})")
    if raw_mode == "virtual":
        print(f"Raw virtual compute script: {args.compute_script}")
    if publish_daily:
        print(
            f"Daily dataset: {daily_dataset_id} "
            f"(mode={daily_mode}, store={daily_static_store_path})"
        )
    else:
        print("Daily dataset: not published (store not found or disabled)")
    if publish_monthly:
        print(
            f"Monthly dataset: {monthly_dataset_id} "
            f"(mode={monthly_mode}, store={monthly_static_store_path})"
        )
        print(f"Raw dataset hidden when monthly is present: {bool(args.hide_raw_when_monthly)}")
    else:
        print("Monthly dataset: not published (store not found or disabled)")
    print(f"Entrypoint dataset: {entrypoint_dataset_id}")
    if precomputed_dir and precomputed_route:
        print(f"Precomputed route: {precomputed_route} -> {precomputed_dir}")
    else:
        print("Precomputed route: disabled")
    print("Tiles: " + ", ".join(tile for tile, _ in tiles))


if __name__ == "__main__":
    main()
