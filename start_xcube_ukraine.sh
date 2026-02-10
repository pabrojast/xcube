#!/bin/bash

# =============================================================================
# xcube Server Startup Script for Ukraine LWQ Dataset
# =============================================================================
# This script configures and starts the xcube server to serve the Ukraine
# Lake Water Quality dataset from Azure Blob Storage.
#
# Dataset: ukraine_lwq.zarr
# Source: Azure Blob Storage (ihpwinsdata/data)
# Service: WMTS + Time Series API
# =============================================================================

# Activate xcube conda environment
source ~/miniforge3/etc/profile.d/conda.sh
conda activate xcube

# Set Azure Storage connection string
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=ihpwinsdata;AccountKey=<AZURE_STORAGE_ACCOUNT_KEY>;EndpointSuffix=core.windows.net"

# Set Azure Storage Account Name (required by adlfs)
export AZURE_STORAGE_ACCOUNT_NAME="ihpwinsdata"
export AZURE_STORAGE_ACCOUNT_KEY="<AZURE_STORAGE_ACCOUNT_KEY>"

# Optional: Set logging level
export XCUBE_LOG_LEVEL="DEBUG"

# Print startup information
echo "=========================================="
echo "Starting xcube server for Ukraine LWQ Dataset"
echo "=========================================="
echo "Configuration: xcube_ukraine_config.yml"
echo "Address: 0.0.0.0:8080"
echo "Dataset: ukraine_lwq.zarr"
echo "Storage: Azure Blob Storage"
echo ""
echo "Available endpoints:"
echo "  - Datasets: http://localhost:8080/datasets"
echo "  - WMTS Capabilities: http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml"
echo "  - Time Series: http://localhost:8080/timeseries/ukraine_lwq/{variable}"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start xcube server with verbose logging
xcube serve -vvv \
  --config xcube_ukraine_config.yml \
  --address 0.0.0.0 \
  --port 8080
