#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-xcube-ukraine-chl}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CONTAINER_NAME="${CONTAINER_NAME:-xcube-ukraine-chl-service}"
PORT="${PORT:-8080}"
DATA_DIR="${DATA_DIR:-/home/pabrojast/Proyectos/stacprocess-ihp/data/terrascope_all_grids_full_history_zarr}"
DATASET_ID="${DATASET_ID:-ua_chl_virtual_stations}"
VARIABLE_NAME="${VARIABLE_NAME:-CHL}"
DAILY_DATASET_ID="${DAILY_DATASET_ID:-ua_chl_daily}"
WMTS_DEFAULT_DATASET_ID="${WMTS_DEFAULT_DATASET_ID:-ua_chl_monthly}"
DATA_STORE_ID="${DATA_STORE_ID:-file}"
STORE_IDENTIFIER="${STORE_IDENTIFIER:-}"
STORE_ROOT="${STORE_ROOT:-}"
RUNTIME_CONFIG_PATH="${RUNTIME_CONFIG_PATH:-$SCRIPT_DIR/.generated/xcube_ukraine_chl_runtime_config.yml}"
ABFS_TILE_IDS="${ABFS_TILE_IDS:-36TVS,36TWS,36TWT,36TXT,36UUA,36UUB,36UUV,36UVV,36UWU,36UWV,36UXU}"
ABFS_ACCOUNT_NAME_TEMPLATE="${ABFS_ACCOUNT_NAME_TEMPLATE:-\${AZURE_STORAGE_ACCOUNT_NAME}}"
ABFS_ACCOUNT_KEY_TEMPLATE="${ABFS_ACCOUNT_KEY_TEMPLATE:-\${AZURE_STORAGE_ACCOUNT_KEY}}"
ABFS_CONNECTION_STRING_TEMPLATE="${ABFS_CONNECTION_STRING_TEMPLATE:-}"
ABFS_ANON="${ABFS_ANON:-0}"
AZURE_STORAGE_ACCOUNT_NAME="${AZURE_STORAGE_ACCOUNT_NAME:-}"
AZURE_STORAGE_ACCOUNT_KEY="${AZURE_STORAGE_ACCOUNT_KEY:-}"
AZURE_STORAGE_CONNECTION_STRING="${AZURE_STORAGE_CONNECTION_STRING:-}"
CPU_LIMIT="${CPU_LIMIT:-2}"
MEM_LIMIT="${MEM_LIMIT:-4g}"
MEM_SWAP="${MEM_SWAP:-6g}"
PID_LIMIT="${PID_LIMIT:-256}"
BUILD_NICE_LEVEL="${BUILD_NICE_LEVEL:-15}"
NO_HEALTHCHECK="${NO_HEALTHCHECK:-1}"
RAW_LEVELS_STORE="${RAW_LEVELS_STORE:-chl_mosaic_ts.levels}"
DAILY_MOSAIC_STORE="${DAILY_MOSAIC_STORE:-chl_mosaic_daily.zarr}"
DAILY_LEVELS_STORE="${DAILY_LEVELS_STORE:-chl_mosaic_daily.levels}"
MONTHLY_MOSAIC_STORE="${MONTHLY_MOSAIC_STORE:-chl_mosaic_monthly.zarr}"
MONTHLY_LEVELS_STORE="${MONTHLY_LEVELS_STORE:-chl_mosaic_monthly.levels}"
DAILY_PYTHON_BIN="${DAILY_PYTHON_BIN:-/home/pabrojast/Proyectos/stacprocess-ihp/.venv/bin/python}"
DAILY_CHUNKS="${DAILY_CHUNKS:-time=1,y=256,x=256}"
DAILY_FREQ="${DAILY_FREQ:-D}"
DAILY_OVERWRITE="${DAILY_OVERWRITE:-0}"
DAILY_CONSOLIDATE="${DAILY_CONSOLIDATE:-1}"
DAILY_GENERATE_LEVELS="${DAILY_GENERATE_LEVELS:-1}"
DAILY_LEVELS_LINK="${DAILY_LEVELS_LINK:-1}"
DAILY_LEVELS_REPLACE="${DAILY_LEVELS_REPLACE:-1}"
DAILY_LEVELS_TILE_SIZE="${DAILY_LEVELS_TILE_SIZE:-256}"
DAILY_LEVELS_AGG_METHODS="${DAILY_LEVELS_AGG_METHODS:-mean}"
MONTHLY_PYTHON_BIN="${MONTHLY_PYTHON_BIN:-/home/pabrojast/Proyectos/stacprocess-ihp/.venv/bin/python}"
MONTHLY_CHUNKS="${MONTHLY_CHUNKS:-time=1,y=256,x=256}"
MONTHLY_FREQ="${MONTHLY_FREQ:-MS}"
MONTHLY_OVERWRITE="${MONTHLY_OVERWRITE:-0}"
MONTHLY_CONSOLIDATE="${MONTHLY_CONSOLIDATE:-1}"
MONTHLY_GENERATE_LEVELS="${MONTHLY_GENERATE_LEVELS:-1}"
MONTHLY_LEVELS_LINK="${MONTHLY_LEVELS_LINK:-1}"
MONTHLY_LEVELS_REPLACE="${MONTHLY_LEVELS_REPLACE:-1}"
MONTHLY_LEVELS_TILE_SIZE="${MONTHLY_LEVELS_TILE_SIZE:-256}"
MONTHLY_LEVELS_AGG_METHODS="${MONTHLY_LEVELS_AGG_METHODS:-mean}"
TEST_MAX_VALIDS="${TEST_MAX_VALIDS:-50}"
TEST_START_DATE="${TEST_START_DATE:-2024-01-01}"
TEST_END_DATE="${TEST_END_DATE:-2024-02-01}"
TEST_TIMEOUT_SECS="${TEST_TIMEOUT_SECS:-180}"
READY_RETRIES="${READY_RETRIES:-30}"
READY_SLEEP_SECS="${READY_SLEEP_SECS:-2}"
BATCH_BBOX_MIN_LON="${BATCH_BBOX_MIN_LON:-22.0}"
BATCH_BBOX_MIN_LAT="${BATCH_BBOX_MIN_LAT:-44.0}"
BATCH_BBOX_MAX_LON="${BATCH_BBOX_MAX_LON:-40.5}"
BATCH_BBOX_MAX_LAT="${BATCH_BBOX_MAX_LAT:-52.5}"
BATCH_TILES_X="${BATCH_TILES_X:-2}"
BATCH_TILES_Y="${BATCH_TILES_Y:-2}"
BATCH_MONTHS_PER_REQUEST="${BATCH_MONTHS_PER_REQUEST:-1}"
BATCH_DAYS_PER_REQUEST="${BATCH_DAYS_PER_REQUEST:-0}"
BATCH_AGG_METHODS="${BATCH_AGG_METHODS:-mean,count}"
BATCH_CONTINUE_ON_ERROR="${BATCH_CONTINUE_ON_ERROR:-0}"
BATCH_OUTPUT="${BATCH_OUTPUT:-}"
PRECOMPUTED_DIR="${PRECOMPUTED_DIR:-$SCRIPT_DIR/precomputed/chl_results}"
PRECOMPUTED_CONTAINER_DIR="${PRECOMPUTED_CONTAINER_DIR:-/home/xcube/ukraine_chl_service/precomputed/chl_results}"
PRECOMPUTED_ROUTE="${PRECOMPUTED_ROUTE:-/precomputed}"
PRECOMPUTED_BIND_MOUNT="${PRECOMPUTED_BIND_MOUNT:-0}"
PRECOMPUTED_MOUNT_MODE="${PRECOMPUTED_MOUNT_MODE:-ro}"
TEST_PRECOMPUTED_PRODUCT="${TEST_PRECOMPUTED_PRODUCT:-ua_chl}"
TEST_PRECOMPUTED_AREA="${TEST_PRECOMPUTED_AREA:-kyiv_reservoir}"
TEST_PRECOMPUTED_TIME_GRAIN="${TEST_PRECOMPUTED_TIME_GRAIN:-raw}"
PRECOMPUTE_AREAS_FILE="${PRECOMPUTE_AREAS_FILE:-$SCRIPT_DIR/precomputed/chl_reference_areas.json}"
PRECOMPUTE_OUTPUT_DIR="${PRECOMPUTE_OUTPUT_DIR:-$SCRIPT_DIR/precomputed/chl_results}"
PRECOMPUTE_START_DATE="${PRECOMPUTE_START_DATE:-auto}"
PRECOMPUTE_END_DATE="${PRECOMPUTE_END_DATE:-auto}"
PRECOMPUTE_MAX_VALIDS="${PRECOMPUTE_MAX_VALIDS:-60}"
PRECOMPUTE_DAYS_PER_REQUEST="${PRECOMPUTE_DAYS_PER_REQUEST:-30}"
PRECOMPUTE_TIME_GRAIN="${PRECOMPUTE_TIME_GRAIN:-raw}"
PRECOMPUTE_TIMEOUT_SECS="${PRECOMPUTE_TIMEOUT_SECS:-240}"
PRECOMPUTE_METADATA_RETRIES="${PRECOMPUTE_METADATA_RETRIES:-2}"
PRECOMPUTE_AUTO_END_OFFSET_DAYS="${PRECOMPUTE_AUTO_END_OFFSET_DAYS:-1}"
PRECOMPUTE_CONTINUE_ON_ERROR="${PRECOMPUTE_CONTINUE_ON_ERROR:-1}"

print_help() {
  cat <<EOF
Usage: ./docker_ukraine_chl.sh <command>

Commands:
  build      Build image and embed local Terrascope CHL Zarr tiles
  run        Run container (replaces previous one if it exists)
  run-azure  Run container using Azure Blob/ABFS as data source
  stop       Stop container
  logs       Show container logs
  status     Show container status
  test-basic Check API/openapi, datasets list, one tile, and virtual dataset metadata
  test-area  Run a polygon timeseries request against the CHL dataset
  test-precomputed Check static /precomputed JSON endpoint for one reference area
  inspect-precomputed List precomputed JSON files visible inside the container
  precompute-full Regenerate reference-area precomputed JSON for full available range (auto)
  build-daily-store Build daily CHL mosaic/levels from raw CHL mosaic (host data dir)
  build-monthly-store Build monthly CHL mosaic/levels from raw CHL mosaic (host data dir)
  test-area-batch Run batched area timeseries (split by time + bbox tiles)
  clean      Remove container
  help       Show this help

Environment overrides:
  DATA_DIR=/path/to/terrascope_all_grids_full_history_zarr
  DATA_STORE_ID=file|abfs
  STORE_IDENTIFIER=terrascope_chl_local|terrascope_chl_abfs
  STORE_ROOT=/local/path or data/xcube/terrascope_all_grids_full_history_zarr
  RUNTIME_CONFIG_PATH=./.generated/xcube_ukraine_chl_runtime_config.yml
  ABFS_TILE_IDS=36TVS,36TWS,...
  ABFS_ACCOUNT_NAME_TEMPLATE=\${AZURE_STORAGE_ACCOUNT_NAME}
  ABFS_ACCOUNT_KEY_TEMPLATE=\${AZURE_STORAGE_ACCOUNT_KEY}
  ABFS_CONNECTION_STRING_TEMPLATE=\${AZURE_STORAGE_CONNECTION_STRING}
  ABFS_ANON=0|1
  AZURE_STORAGE_ACCOUNT_NAME=...
  AZURE_STORAGE_ACCOUNT_KEY=...
  AZURE_STORAGE_CONNECTION_STRING=...
  PORT=8080
  IMAGE_NAME=xcube-ukraine-chl
  IMAGE_TAG=latest
  CPU_LIMIT=2
  MEM_LIMIT=4g
  MEM_SWAP=6g
  PID_LIMIT=256
  BUILD_NICE_LEVEL=15
  NO_HEALTHCHECK=1
  DAILY_DATASET_ID=ua_chl_daily
  WMTS_DEFAULT_DATASET_ID=ua_chl_monthly
  RAW_LEVELS_STORE=chl_mosaic_ts.levels
  DAILY_MOSAIC_STORE=chl_mosaic_daily.zarr
  DAILY_LEVELS_STORE=chl_mosaic_daily.levels
  MONTHLY_MOSAIC_STORE=chl_mosaic_monthly.zarr
  MONTHLY_LEVELS_STORE=chl_mosaic_monthly.levels
  DAILY_PYTHON_BIN=/home/pabrojast/Proyectos/stacprocess-ihp/.venv/bin/python
  DAILY_CHUNKS=time=1,y=256,x=256
  DAILY_FREQ=D
  DAILY_OVERWRITE=0
  DAILY_CONSOLIDATE=1
  DAILY_GENERATE_LEVELS=1
  DAILY_LEVELS_LINK=1
  DAILY_LEVELS_REPLACE=1
  DAILY_LEVELS_TILE_SIZE=256
  DAILY_LEVELS_AGG_METHODS=mean
  MONTHLY_PYTHON_BIN=/home/pabrojast/Proyectos/stacprocess-ihp/.venv/bin/python
  MONTHLY_CHUNKS=time=1,y=256,x=256
  MONTHLY_FREQ=MS
  MONTHLY_OVERWRITE=0
  MONTHLY_CONSOLIDATE=1
  MONTHLY_GENERATE_LEVELS=1
  MONTHLY_LEVELS_LINK=1
  MONTHLY_LEVELS_REPLACE=1
  MONTHLY_LEVELS_TILE_SIZE=256
  MONTHLY_LEVELS_AGG_METHODS=mean
  TEST_MAX_VALIDS=50
  TEST_START_DATE=2024-01-01
  TEST_END_DATE=2024-02-01
  TEST_TIMEOUT_SECS=180
  READY_RETRIES=30
  READY_SLEEP_SECS=2
  BATCH_BBOX_MIN_LON=22.0
  BATCH_BBOX_MIN_LAT=44.0
  BATCH_BBOX_MAX_LON=40.5
  BATCH_BBOX_MAX_LAT=52.5
  BATCH_TILES_X=2
  BATCH_TILES_Y=2
  BATCH_MONTHS_PER_REQUEST=1
  BATCH_DAYS_PER_REQUEST=0
  BATCH_AGG_METHODS=mean,count
  BATCH_CONTINUE_ON_ERROR=0
  BATCH_OUTPUT=/tmp/chl_batch_output.json
  PRECOMPUTED_DIR=/home/pabrojast/Proyectos/xcube/precomputed/chl_results
  PRECOMPUTED_CONTAINER_DIR=/home/xcube/ukraine_chl_service/precomputed/chl_results
  PRECOMPUTED_ROUTE=/precomputed
  PRECOMPUTED_BIND_MOUNT=0
  PRECOMPUTED_MOUNT_MODE=ro
  TEST_PRECOMPUTED_PRODUCT=ua_chl
  TEST_PRECOMPUTED_AREA=kyiv_reservoir
  TEST_PRECOMPUTED_TIME_GRAIN=raw
  PRECOMPUTE_AREAS_FILE=./precomputed/chl_reference_areas.json
  PRECOMPUTE_OUTPUT_DIR=./precomputed/chl_results
  PRECOMPUTE_START_DATE=auto
  PRECOMPUTE_END_DATE=auto
  PRECOMPUTE_MAX_VALIDS=60
  PRECOMPUTE_DAYS_PER_REQUEST=30
  PRECOMPUTE_TIME_GRAIN=raw
  PRECOMPUTE_TIMEOUT_SECS=240
  PRECOMPUTE_METADATA_RETRIES=2
  PRECOMPUTE_AUTO_END_OFFSET_DAYS=1
  PRECOMPUTE_CONTINUE_ON_ERROR=1
EOF
}

ensure_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is not installed"
    exit 1
  fi
}

build_image() {
  ensure_docker
  local levels_dir
  local levels_num_levels
  local levels_stores
  if [ ! -d "$DATA_DIR" ]; then
    echo "Data directory not found: $DATA_DIR"
    exit 1
  fi
  if [ ! -f "$DATA_DIR/chl_mosaic_ts.zarr/.mosaic_complete.json" ]; then
    echo "WARNING: '$DATA_DIR/chl_mosaic_ts.zarr/.mosaic_complete.json' not found."
    echo "         Build will fallback to virtual dataset mode (less stable/slow)."
    echo "         Run scripts/chl_to_zarr_and_mosaic.sh in stacprocess-ihp first."
  fi
  levels_dir="$DATA_DIR/$RAW_LEVELS_STORE"
  if [ -f "$levels_dir/.zlevels" ]; then
    levels_num_levels="$(jq -r '.num_levels // "unknown"' "$levels_dir/.zlevels" 2>/dev/null || echo "unknown")"
    levels_stores="$(find "$levels_dir" -maxdepth 1 -type d -name '*.zarr' | wc -l | tr -d ' ')"
    if [ "$levels_stores" -gt 0 ]; then
      echo "Levels detected: $levels_dir (num_levels=${levels_num_levels}, stores=${levels_stores})"
    else
      echo "WARNING: '$levels_dir' exists but no '*.zarr' levels were found."
      echo "         Build may fallback to mosaic or virtual mode depending on readiness."
    fi
  else
    echo "WARNING: '$levels_dir/.zlevels' not found."
    echo "         Build may fallback to mosaic or virtual mode depending on readiness."
  fi

  if [ -f "$DATA_DIR/$MONTHLY_LEVELS_STORE/.zlevels" ]; then
    echo "Monthly levels detected: $DATA_DIR/$MONTHLY_LEVELS_STORE"
  else
    echo "Monthly levels NOT detected: $DATA_DIR/$MONTHLY_LEVELS_STORE"
    echo "  -> WMTS default-friendly monthly layer (ua_chl_monthly) will not be published."
  fi
  if [ -f "$DATA_DIR/$DAILY_LEVELS_STORE/.zlevels" ]; then
    echo "Daily levels detected: $DATA_DIR/$DAILY_LEVELS_STORE"
  else
    echo "Daily levels NOT detected: $DATA_DIR/$DAILY_LEVELS_STORE"
    echo "  -> Daily layer (ua_chl_daily) will not be published."
  fi
  echo "Building image ${IMAGE_NAME}:${IMAGE_TAG}"
  echo "Data source: $DATA_DIR"

  # buildx does not expose CPU/RAM build flags like `--memory` or `--cpu-quota`.
  # Lower process priority to reduce desktop freezes during large context copies.
  BUILD_PREFIX=()
  if command -v ionice >/dev/null 2>&1; then
    BUILD_PREFIX+=(ionice -c3)
  fi
  if command -v nice >/dev/null 2>&1; then
    BUILD_PREFIX+=(nice -n "$BUILD_NICE_LEVEL")
  fi

  "${BUILD_PREFIX[@]}" docker buildx build --load \
    -f Dockerfile.ukraine.chl \
    --build-context "terrascope_chl_data=$DATA_DIR" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    --progress=plain \
    .
}

generate_runtime_config() {
  local config_cmd
  mkdir -p "$(dirname "$RUNTIME_CONFIG_PATH")"

  config_cmd=(
    python3 "$SCRIPT_DIR/generate_ukraine_chl_xcube_config.py"
    --zarr-root "$DATA_DIR"
    --allow-missing-zarr-root
    --store-id "$DATA_STORE_ID"
    --tile-ids "$ABFS_TILE_IDS"
    --output "$RUNTIME_CONFIG_PATH"
    --compute-script /home/xcube/ukraine_chl_service/compute_ukraine_chl_virtual_dataset.py
    --raw-dataset-id "$DATASET_ID"
    --daily-dataset-id "$DAILY_DATASET_ID"
    --monthly-dataset-id "$WMTS_DEFAULT_DATASET_ID"
    --levels-store "$RAW_LEVELS_STORE"
    --daily-levels-store "$DAILY_LEVELS_STORE"
    --daily-mosaic-store "$DAILY_MOSAIC_STORE"
    --monthly-levels-store "$MONTHLY_LEVELS_STORE"
    --monthly-mosaic-store "$MONTHLY_MOSAIC_STORE"
    --show-raw-when-monthly
    --precomputed-dir "$PRECOMPUTED_CONTAINER_DIR"
    --precomputed-route "$PRECOMPUTED_ROUTE"
  )

  if [ -n "$STORE_IDENTIFIER" ]; then
    config_cmd+=(--store-identifier "$STORE_IDENTIFIER")
  fi
  if [ -n "$STORE_ROOT" ]; then
    config_cmd+=(--store-root "$STORE_ROOT")
  fi

  if [ "$DATA_STORE_ID" = "abfs" ]; then
    if [ "$ABFS_ANON" = "1" ]; then
      config_cmd+=(--abfs-anon)
    elif [ -n "$ABFS_CONNECTION_STRING_TEMPLATE" ]; then
      config_cmd+=(--abfs-connection-string "$ABFS_CONNECTION_STRING_TEMPLATE")
    else
      config_cmd+=(--abfs-account-name "$ABFS_ACCOUNT_NAME_TEMPLATE")
      config_cmd+=(--abfs-account-key "$ABFS_ACCOUNT_KEY_TEMPLATE")
    fi
  fi

  echo "Generating runtime config ($DATA_STORE_ID): $RUNTIME_CONFIG_PATH"
  "${config_cmd[@]}"
}

run_container() {
  ensure_docker
  local runtime_config_container
  if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_NAME"; then
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
  RUN_ARGS=(
    -d
    --name "$CONTAINER_NAME"
    -p "${PORT}:8080"
    --cpus="$CPU_LIMIT"
    --memory="$MEM_LIMIT"
    --pids-limit="$PID_LIMIT"
    -e OMP_NUM_THREADS=1
    -e OPENBLAS_NUM_THREADS=1
    -e MKL_NUM_THREADS=1
    -e NUMEXPR_NUM_THREADS=1
    -e GDAL_NUM_THREADS=1
    -e DASK_NUM_WORKERS=1
    --restart unless-stopped
  )
  if [ -n "$MEM_SWAP" ]; then
    RUN_ARGS+=(--memory-swap="$MEM_SWAP")
  fi
  if [ "$NO_HEALTHCHECK" = "1" ]; then
    RUN_ARGS+=(--no-healthcheck)
  fi
  if [ "$PRECOMPUTED_BIND_MOUNT" = "1" ]; then
    if [ -d "$PRECOMPUTED_DIR" ]; then
      RUN_ARGS+=(-v "${PRECOMPUTED_DIR}:${PRECOMPUTED_CONTAINER_DIR}:${PRECOMPUTED_MOUNT_MODE}")
      echo "Using precomputed bind mount: ${PRECOMPUTED_DIR} -> ${PRECOMPUTED_CONTAINER_DIR} (${PRECOMPUTED_MOUNT_MODE})"
    else
      echo "WARNING: PRECOMPUTED_DIR not found, bind mount disabled: $PRECOMPUTED_DIR"
    fi
  else
    echo "Using precomputed files bundled in image (PRECOMPUTED_BIND_MOUNT=0)"
  fi

  if [ "$DATA_STORE_ID" = "abfs" ]; then
    runtime_config_container="/home/xcube/ukraine_chl_service/xcube_ukraine_chl_runtime_config.yml"
    if [ "$ABFS_ANON" != "1" ]; then
      if [ -n "$ABFS_CONNECTION_STRING_TEMPLATE" ] && [ -z "$AZURE_STORAGE_CONNECTION_STRING" ]; then
        echo "WARNING: ABFS uses connection string template but AZURE_STORAGE_CONNECTION_STRING is empty."
      fi
      if [ -z "$ABFS_CONNECTION_STRING_TEMPLATE" ] && { [ -z "$AZURE_STORAGE_ACCOUNT_NAME" ] || [ -z "$AZURE_STORAGE_ACCOUNT_KEY" ]; }; then
        echo "WARNING: ABFS uses account/key templates but AZURE_STORAGE_ACCOUNT_NAME or AZURE_STORAGE_ACCOUNT_KEY is empty."
      fi
    fi
    generate_runtime_config
    RUN_ARGS+=(-v "${RUNTIME_CONFIG_PATH}:${runtime_config_container}:ro")
    if [ -n "$AZURE_STORAGE_ACCOUNT_NAME" ]; then
      RUN_ARGS+=(-e "AZURE_STORAGE_ACCOUNT_NAME=${AZURE_STORAGE_ACCOUNT_NAME}")
    fi
    if [ -n "$AZURE_STORAGE_ACCOUNT_KEY" ]; then
      RUN_ARGS+=(-e "AZURE_STORAGE_ACCOUNT_KEY=${AZURE_STORAGE_ACCOUNT_KEY}")
    fi
    if [ -n "$AZURE_STORAGE_CONNECTION_STRING" ]; then
      RUN_ARGS+=(-e "AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING}")
    fi
    docker run "${RUN_ARGS[@]}" "${IMAGE_NAME}:${IMAGE_TAG}" \
      xcube serve \
      --config "$runtime_config_container" \
      --address 0.0.0.0 \
      --port 8080 \
      --verbose
  else
    docker run "${RUN_ARGS[@]}" "${IMAGE_NAME}:${IMAGE_TAG}"
  fi
  echo "Container started: $CONTAINER_NAME"
  echo "Datasets URL: http://localhost:${PORT}/datasets"
  echo "Precomputed URL base: http://localhost:${PORT}${PRECOMPUTED_ROUTE}"
  echo "Daily layer (if published): ${DAILY_DATASET_ID}.${VARIABLE_NAME}"
  echo "WMTS default layer (if published): ${WMTS_DEFAULT_DATASET_ID}.${VARIABLE_NAME}"
  if [ "$DATA_STORE_ID" = "abfs" ]; then
    echo "Data source mode: ABFS (Azure Blob)"
    if [ -n "$STORE_ROOT" ]; then
      echo "ABFS root: $STORE_ROOT"
    fi
  else
    echo "Data source mode: file (embedded/local)"
  fi
}

test_area() {
  ensure_docker
  local body
  local qs
  local base_url
  local i
  base_url="http://127.0.0.1:${PORT}"
  qs="aggMethods=mean&responseFormat=contract&maxValids=${TEST_MAX_VALIDS}"
  if [ -n "$TEST_START_DATE" ]; then
    qs="${qs}&startDate=${TEST_START_DATE}"
  fi
  if [ -n "$TEST_END_DATE" ]; then
    qs="${qs}&endDate=${TEST_END_DATE}"
  fi
  body='{"type":"Polygon","coordinates":[[[30.45,50.40],[30.60,50.40],[30.60,50.55],[30.45,50.55],[30.45,50.40]]]}'

  echo "Waiting for API readiness..."
  for i in $(seq 1 "$READY_RETRIES"); do
    if curl -fsS --max-time 10 "${base_url}/openapi.json" >/dev/null 2>&1; then
      break
    fi
    sleep "$READY_SLEEP_SECS"
  done

  echo "Checking datasets list..."
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" \
    "${base_url}/datasets" | jq 'if type=="array" then .[0:5] else . end'

  echo "Checking dataset metadata..."
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" \
    "${base_url}/datasets/${DATASET_ID}" | jq '.id, .title'

  echo "Testing area timeseries..."
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" -X POST \
    "${base_url}/timeseries/${DATASET_ID}/${VARIABLE_NAME}?${qs}" \
    -H "Content-Type: application/json" \
    -d "$body" | jq '.contract, .operation, .hasData, .summary'
}

test_area_batch() {
  ensure_docker
  local base_url
  base_url="http://127.0.0.1:${PORT}"

  echo "Waiting for API readiness..."
  for i in $(seq 1 "$READY_RETRIES"); do
    if curl -fsS --max-time 10 "${base_url}/openapi.json" >/dev/null 2>&1; then
      break
    fi
    sleep "$READY_SLEEP_SECS"
  done

  if [ -n "$BATCH_OUTPUT" ]; then
    BATCH_ARGS=(
      --base-url "$base_url"
      --dataset-id "$DATASET_ID"
      --var-name "$VARIABLE_NAME"
      --start-date "$TEST_START_DATE"
      --end-date "$TEST_END_DATE"
      --bbox "$BATCH_BBOX_MIN_LON" "$BATCH_BBOX_MIN_LAT" "$BATCH_BBOX_MAX_LON" "$BATCH_BBOX_MAX_LAT"
      --tiles-x "$BATCH_TILES_X"
      --tiles-y "$BATCH_TILES_Y"
      --months-per-request "$BATCH_MONTHS_PER_REQUEST"
      --days-per-request "$BATCH_DAYS_PER_REQUEST"
      --agg-methods "$BATCH_AGG_METHODS"
      --max-valids "$TEST_MAX_VALIDS"
      --timeout-secs "$TEST_TIMEOUT_SECS"
    )
    if [ "$BATCH_CONTINUE_ON_ERROR" = "1" ]; then
      BATCH_ARGS+=(--continue-on-error)
    fi
    python3 scripts/chl_timeseries_batch.py \
      "${BATCH_ARGS[@]}" \
      --output "$BATCH_OUTPUT"
  else
    BATCH_ARGS=(
      --base-url "$base_url" \
      --dataset-id "$DATASET_ID" \
      --var-name "$VARIABLE_NAME" \
      --start-date "$TEST_START_DATE" \
      --end-date "$TEST_END_DATE" \
      --bbox "$BATCH_BBOX_MIN_LON" "$BATCH_BBOX_MIN_LAT" "$BATCH_BBOX_MAX_LON" "$BATCH_BBOX_MAX_LAT" \
      --tiles-x "$BATCH_TILES_X" \
      --tiles-y "$BATCH_TILES_Y" \
      --months-per-request "$BATCH_MONTHS_PER_REQUEST" \
      --days-per-request "$BATCH_DAYS_PER_REQUEST" \
      --agg-methods "$BATCH_AGG_METHODS" \
      --max-valids "$TEST_MAX_VALIDS" \
      --timeout-secs "$TEST_TIMEOUT_SECS"
    )
    if [ "$BATCH_CONTINUE_ON_ERROR" = "1" ]; then
      BATCH_ARGS+=(--continue-on-error)
    fi
    python3 scripts/chl_timeseries_batch.py \
      "${BATCH_ARGS[@]}"
  fi
}

test_precomputed() {
  ensure_docker
  local base_url
  local i
  local date_range
  local namespaced_file
  local namespaced_file_with_grain
  local legacy_file
  local namespaced_url
  local namespaced_url_with_grain
  local legacy_url
  local file_suffix
  base_url="http://127.0.0.1:${PORT}"
  date_range="${TEST_START_DATE}_${TEST_END_DATE}"
  namespaced_file="${TEST_PRECOMPUTED_PRODUCT}__${TEST_PRECOMPUTED_AREA}__${date_range}.json"
  if [ "$TEST_PRECOMPUTED_TIME_GRAIN" = "raw" ]; then
    file_suffix=""
  else
    file_suffix="__${TEST_PRECOMPUTED_TIME_GRAIN}"
  fi
  namespaced_file_with_grain="${TEST_PRECOMPUTED_PRODUCT}__${TEST_PRECOMPUTED_AREA}__${date_range}${file_suffix}.json"
  legacy_file="${TEST_PRECOMPUTED_AREA}_${date_range}.json"
  namespaced_url="${base_url}${PRECOMPUTED_ROUTE}/${TEST_PRECOMPUTED_PRODUCT}/${namespaced_file}"
  namespaced_url_with_grain="${base_url}${PRECOMPUTED_ROUTE}/${TEST_PRECOMPUTED_PRODUCT}/${namespaced_file_with_grain}"
  legacy_url="${base_url}${PRECOMPUTED_ROUTE}/${legacy_file}"

  echo "Waiting for API readiness..."
  for i in $(seq 1 "$READY_RETRIES"); do
    if curl -fsS --max-time 10 "${base_url}/openapi.json" >/dev/null 2>&1; then
      break
    fi
    sleep "$READY_SLEEP_SECS"
  done

  if [ "$TEST_PRECOMPUTED_TIME_GRAIN" != "raw" ]; then
    echo "Trying namespaced precomputed file (${TEST_PRECOMPUTED_TIME_GRAIN}):"
    echo "  ${namespaced_url_with_grain}"
    if curl -fsS --max-time "$TEST_TIMEOUT_SECS" "$namespaced_url_with_grain" | jq '.product.id, .area.id, .hasData, .summary'; then
      return 0
    fi
  fi

  echo "Trying namespaced precomputed file (raw/default):"
  echo "  ${namespaced_url}"
  if curl -fsS --max-time "$TEST_TIMEOUT_SECS" "$namespaced_url" | jq '.product.id, .area.id, .hasData, .summary'; then
    return 0
  fi

  echo "Namespaced file not found, trying legacy file:"
  echo "  ${legacy_url}"
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" "$legacy_url" | jq '.area.id, .hasData, .summary'
}

inspect_precomputed() {
  ensure_docker
  docker exec "$CONTAINER_NAME" sh -lc \
    "echo 'Container precomputed dir:' && ls -la '${PRECOMPUTED_CONTAINER_DIR}' && \
     echo && echo 'Sample JSON files:' && find '${PRECOMPUTED_CONTAINER_DIR}' -type f -name '*.json' | sort | head -n 40"
}

build_monthly_store() {
  local py_bin
  local raw_mosaic
  local monthly_mosaic
  local monthly_levels
  local monthly_mosaic_rel
  local monthly_levels_rel
  local cmd
  local level_cmd

  py_bin="$MONTHLY_PYTHON_BIN"
  if [ ! -x "$py_bin" ]; then
    py_bin="python3"
  fi

  raw_mosaic="$DATA_DIR/chl_mosaic_ts.zarr"
  monthly_mosaic="$DATA_DIR/$MONTHLY_MOSAIC_STORE"
  monthly_levels="$DATA_DIR/$MONTHLY_LEVELS_STORE"

  if [ ! -d "$raw_mosaic" ]; then
    echo "Raw mosaic not found: $raw_mosaic"
    exit 1
  fi

  cmd=(
    "$py_bin" scripts/chl_mosaic_to_monthly_zarr.py
    --input "$raw_mosaic"
    --output "$monthly_mosaic"
    --freq "$MONTHLY_FREQ"
    --chunks "$MONTHLY_CHUNKS"
    --log-level INFO
  )
  if [ "$MONTHLY_OVERWRITE" = "1" ]; then
    cmd+=(--overwrite)
  fi
  if [ "$MONTHLY_CONSOLIDATE" = "1" ]; then
    cmd+=(--consolidate)
  fi

  echo "Building monthly mosaic store..."
  echo "  python: $py_bin"
  echo "  input:  $raw_mosaic"
  echo "  output: $monthly_mosaic"
  "${cmd[@]}"

  if [ "$MONTHLY_GENERATE_LEVELS" != "1" ]; then
    echo "Skipping monthly levels generation (MONTHLY_GENERATE_LEVELS=0)."
    return 0
  fi

  if ! PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$py_bin" - <<'PY' >/dev/null 2>&1
import importlib
for mod in ("xcube.cli.main", "jsonschema", "rfc3339_validator"):
    importlib.import_module(mod)
import zarr
major = int(str(zarr.__version__).split(".", maxsplit=1)[0])
if major >= 3:
    raise RuntimeError(
        f"Incompatible zarr version {zarr.__version__}; xcube level requires zarr<3"
    )
PY
  then
    echo "Missing Python dependencies for 'xcube level' in: $py_bin"
    echo "Install with:"
    echo "  $py_bin -m pip install jsonschema rfc3339-validator 'zarr<3'"
    exit 1
  fi

  echo "Building monthly .levels pyramid..."
  echo "  output: $monthly_levels"
  monthly_mosaic_rel="$(python3 - <<PY
import os
print(os.path.relpath("$monthly_mosaic", os.getcwd()))
PY
)"
  monthly_levels_rel="$(python3 - <<PY
import os
print(os.path.relpath("$monthly_levels", os.getcwd()))
PY
)"
  echo "  input (relative):  $monthly_mosaic_rel"
  echo "  output (relative): $monthly_levels_rel"

  level_cmd=(
    "$py_bin" -m xcube.cli.main level "$monthly_mosaic_rel"
    --output "$monthly_levels_rel"
    --tile-size "$MONTHLY_LEVELS_TILE_SIZE"
    --agg-methods "$MONTHLY_LEVELS_AGG_METHODS"
  )
  if [ "$MONTHLY_LEVELS_LINK" = "1" ]; then
    level_cmd+=(--link)
  fi
  if [ "$MONTHLY_LEVELS_REPLACE" = "1" ]; then
    level_cmd+=(--replace)
  fi

  if PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" "${level_cmd[@]}"; then
    :
  else
    echo "Failed to run xcube level with '$py_bin'."
    echo "Hint: use MONTHLY_PYTHON_BIN with an environment that has xcube deps,"
    echo "e.g. /home/pabrojast/Proyectos/stacprocess-ihp/.venv/bin/python"
    exit 1
  fi

  echo "Monthly store ready:"
  echo "  - $monthly_mosaic"
  echo "  - $monthly_levels"
}

build_daily_store() {
  local py_bin
  local raw_mosaic
  local daily_mosaic
  local daily_levels
  local daily_mosaic_rel
  local daily_levels_rel
  local cmd
  local level_cmd

  py_bin="$DAILY_PYTHON_BIN"
  if [ ! -x "$py_bin" ]; then
    py_bin="python3"
  fi

  raw_mosaic="$DATA_DIR/chl_mosaic_ts.zarr"
  daily_mosaic="$DATA_DIR/$DAILY_MOSAIC_STORE"
  daily_levels="$DATA_DIR/$DAILY_LEVELS_STORE"

  if [ ! -d "$raw_mosaic" ]; then
    echo "Raw mosaic not found: $raw_mosaic"
    exit 1
  fi

  cmd=(
    "$py_bin" scripts/chl_mosaic_to_daily_zarr.py
    --input "$raw_mosaic"
    --output "$daily_mosaic"
    --freq "$DAILY_FREQ"
    --chunks "$DAILY_CHUNKS"
    --log-level INFO
  )
  if [ "$DAILY_OVERWRITE" = "1" ]; then
    cmd+=(--overwrite)
  fi
  if [ "$DAILY_CONSOLIDATE" = "1" ]; then
    cmd+=(--consolidate)
  fi

  echo "Building daily mosaic store..."
  echo "  python: $py_bin"
  echo "  input:  $raw_mosaic"
  echo "  output: $daily_mosaic"
  "${cmd[@]}"

  if [ "$DAILY_GENERATE_LEVELS" != "1" ]; then
    echo "Skipping daily levels generation (DAILY_GENERATE_LEVELS=0)."
    return 0
  fi

  if ! PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" "$py_bin" - <<'PY' >/dev/null 2>&1
import importlib
for mod in ("xcube.cli.main", "jsonschema", "rfc3339_validator"):
    importlib.import_module(mod)
import zarr
major = int(str(zarr.__version__).split(".", maxsplit=1)[0])
if major >= 3:
    raise RuntimeError(
        f"Incompatible zarr version {zarr.__version__}; xcube level requires zarr<3"
    )
PY
  then
    echo "Missing Python dependencies for 'xcube level' in: $py_bin"
    echo "Install with:"
    echo "  $py_bin -m pip install jsonschema rfc3339-validator 'zarr<3'"
    exit 1
  fi

  echo "Building daily .levels pyramid..."
  echo "  output: $daily_levels"
  daily_mosaic_rel="$(python3 - <<PY
import os
print(os.path.relpath("$daily_mosaic", os.getcwd()))
PY
)"
  daily_levels_rel="$(python3 - <<PY
import os
print(os.path.relpath("$daily_levels", os.getcwd()))
PY
)"
  echo "  input (relative):  $daily_mosaic_rel"
  echo "  output (relative): $daily_levels_rel"

  level_cmd=(
    "$py_bin" -m xcube.cli.main level "$daily_mosaic_rel"
    --output "$daily_levels_rel"
    --tile-size "$DAILY_LEVELS_TILE_SIZE"
    --agg-methods "$DAILY_LEVELS_AGG_METHODS"
  )
  if [ "$DAILY_LEVELS_LINK" = "1" ]; then
    level_cmd+=(--link)
  fi
  if [ "$DAILY_LEVELS_REPLACE" = "1" ]; then
    level_cmd+=(--replace)
  fi

  if PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" "${level_cmd[@]}"; then
    :
  else
    echo "Failed to run xcube level with '$py_bin'."
    echo "Hint: use DAILY_PYTHON_BIN with an environment that has xcube deps,"
    echo "e.g. /home/pabrojast/Proyectos/stacprocess-ihp/.venv/bin/python"
    exit 1
  fi

  echo "Daily store ready:"
  echo "  - $daily_mosaic"
  echo "  - $daily_levels"
}

precompute_full() {
  ensure_docker
  local base_url
  local i
  local cmd
  base_url="http://127.0.0.1:${PORT}"

  if [ ! -f "$PRECOMPUTE_AREAS_FILE" ]; then
    echo "Areas file not found: $PRECOMPUTE_AREAS_FILE"
    exit 1
  fi

  echo "Waiting for API readiness..."
  for i in $(seq 1 "$READY_RETRIES"); do
    if curl -fsS --max-time 10 "${base_url}/openapi.json" >/dev/null 2>&1; then
      break
    fi
    sleep "$READY_SLEEP_SECS"
  done

  mkdir -p "$PRECOMPUTE_OUTPUT_DIR"
  cmd=(
    python3 scripts/precompute_chl_reference_areas.py
    --areas-file "$PRECOMPUTE_AREAS_FILE"
    --output-dir "$PRECOMPUTE_OUTPUT_DIR"
    --base-url "$base_url"
    --start-date "$PRECOMPUTE_START_DATE"
    --end-date "$PRECOMPUTE_END_DATE"
    --max-valids "$PRECOMPUTE_MAX_VALIDS"
    --days-per-request "$PRECOMPUTE_DAYS_PER_REQUEST"
    --time-grain "$PRECOMPUTE_TIME_GRAIN"
    --timeout-secs "$PRECOMPUTE_TIMEOUT_SECS"
    --metadata-retries "$PRECOMPUTE_METADATA_RETRIES"
    --auto-end-offset-days "$PRECOMPUTE_AUTO_END_OFFSET_DAYS"
  )
  if [ "$PRECOMPUTE_CONTINUE_ON_ERROR" = "1" ]; then
    cmd+=(--continue-on-error)
  fi

  echo "Running precompute (areas=$PRECOMPUTE_AREAS_FILE output=$PRECOMPUTE_OUTPUT_DIR grain=$PRECOMPUTE_TIME_GRAIN)..."
  "${cmd[@]}"
}

test_basic() {
  ensure_docker
  local base_url
  local i
  base_url="http://127.0.0.1:${PORT}"

  echo "Waiting for API readiness..."
  for i in $(seq 1 "$READY_RETRIES"); do
    if curl -fsS --max-time 10 "${base_url}/openapi.json" >/dev/null 2>&1; then
      break
    fi
    sleep "$READY_SLEEP_SECS"
  done

  echo "1) /openapi.json"
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" "${base_url}/openapi.json" >/dev/null
  echo "   OK"

  echo "2) /datasets"
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" "${base_url}/datasets" | jq 'if type=="array" then .[0:5] else . end'

  echo "3) /datasets/ua_chl_36TVS"
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" "${base_url}/datasets/ua_chl_36TVS" | jq '.id, .title'

  echo "4) /datasets/${DATASET_ID}"
  curl -fsS --max-time "$TEST_TIMEOUT_SECS" "${base_url}/datasets/${DATASET_ID}" | jq '.id, .title'

  echo "5) /datasets/${WMTS_DEFAULT_DATASET_ID} (optional monthly layer)"
  if curl -fsS --max-time "$TEST_TIMEOUT_SECS" "${base_url}/datasets/${WMTS_DEFAULT_DATASET_ID}" | jq '.id, .title'; then
    :
  else
    echo "   Not available (monthly store not published)."
  fi

  echo "6) /datasets/${DAILY_DATASET_ID} (optional daily layer)"
  if curl -fsS --max-time "$TEST_TIMEOUT_SECS" "${base_url}/datasets/${DAILY_DATASET_ID}" | jq '.id, .title'; then
    :
  else
    echo "   Not available (daily store not published)."
  fi
}

COMMAND="${1:-help}"

case "$COMMAND" in
  build)
    build_image
    ;;
  run)
    run_container
    ;;
  run-azure)
    DATA_STORE_ID="abfs"
    run_container
    ;;
  stop)
    docker stop "$CONTAINER_NAME"
    ;;
  logs)
    docker logs -f "$CONTAINER_NAME"
    ;;
  status)
    docker ps -a --filter "name=${CONTAINER_NAME}" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    ;;
  test-basic)
    test_basic
    ;;
  test-area)
    test_area
    ;;
  test-precomputed)
    test_precomputed
    ;;
  inspect-precomputed)
    inspect_precomputed
    ;;
  precompute-full)
    precompute_full
    ;;
  build-daily-store)
    build_daily_store
    ;;
  build-monthly-store)
    build_monthly_store
    ;;
  test-area-batch)
    test_area_batch
    ;;
  clean)
    docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
    ;;
  help|*)
    print_help
    ;;
esac
