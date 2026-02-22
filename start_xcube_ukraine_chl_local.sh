#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-$SCRIPT_DIR/xcube_ukraine_chl_local_config.yml}"
ADDRESS="${XCUBE_ADDRESS:-0.0.0.0}"
PORT="${XCUBE_PORT:-8080}"
VERBOSITY="${XCUBE_VERBOSITY:--vv}"
DATASET_ID="${XCUBE_CHL_DATASET_ID:-ua_chl_virtual_stations}"
WMTS_DATASET_ID="${XCUBE_CHL_WMTS_DATASET_ID:-ua_chl_monthly}"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE"
  echo "Generate it with:"
  echo "  python3 \"$SCRIPT_DIR/generate_ukraine_chl_xcube_config.py\""
  exit 1
fi

for conda_sh in \
  "$HOME/miniforge3/etc/profile.d/conda.sh" \
  "$HOME/miniconda3/etc/profile.d/conda.sh" \
  "$HOME/anaconda3/etc/profile.d/conda.sh"; do
  if [ -f "$conda_sh" ]; then
    source "$conda_sh"
    conda activate xcube || true
    break
  fi
done

XCUBE_RUN=()
XCUBE_MODE=""
if command -v xcube >/dev/null 2>&1; then
  XCUBE_BIN="$(command -v xcube)"
  if [ -x "$XCUBE_BIN" ] && [ ! -d "$XCUBE_BIN" ] && "$XCUBE_BIN" serve --help >/dev/null 2>&1; then
    XCUBE_RUN=("$XCUBE_BIN")
    XCUBE_MODE="binary"
  fi
fi
if [ ${#XCUBE_RUN[@]} -eq 0 ] && python3 -c "import xcube.cli.serve" >/dev/null 2>&1; then
  XCUBE_MODE="python_serve_module"
fi
if [ -z "$XCUBE_MODE" ]; then
  echo "Could not find a runnable xcube CLI."
  echo "Install xcube in the active environment or activate your xcube conda env first."
  exit 1
fi

echo "=========================================="
echo "Starting xcube server for local CHL virtual-stations dataset"
echo "=========================================="
echo "Configuration: $CONFIG_FILE"
echo "Address: $ADDRESS:$PORT"
echo "Dataset ID: $DATASET_ID"
echo "WMTS Default Dataset ID: $WMTS_DATASET_ID"
echo "Endpoints:"
echo "  - Datasets: http://localhost:$PORT/datasets"
echo "  - Dataset info: http://localhost:$PORT/datasets/$DATASET_ID"
echo "  - Time series: http://localhost:$PORT/timeseries/$DATASET_ID/CHL"
echo "  - Precomputed JSON base: http://localhost:$PORT/precomputed"
echo "  - WMTS Capabilities: http://localhost:$PORT/wmts/1.0.0/WMTSCapabilities.xml"
echo "  - WMTS layer (recommended): ${WMTS_DATASET_ID}.CHL"
echo "=========================================="

if [ "$XCUBE_MODE" = "binary" ]; then
  exec "${XCUBE_RUN[@]}" serve "$VERBOSITY" \
    --config "$CONFIG_FILE" \
    --address "$ADDRESS" \
    --port "$PORT"
fi

if ! python3 -c "import xcube.server.config" >/dev/null 2>&1; then
  echo "Python environment is missing xcube server dependencies."
  echo "Activate your xcube environment or install dependencies (e.g. pip install -e .)."
  exit 1
fi

exec python3 -c "import sys; from xcube.cli.serve import serve; sys.exit(serve.main(sys.argv[1:], standalone_mode=False) or 0)" \
  "$VERBOSITY" \
  --config "$CONFIG_FILE" \
  --address "$ADDRESS" \
  --port "$PORT"
