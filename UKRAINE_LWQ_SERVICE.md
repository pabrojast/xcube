# Ukraine LWQ Service - xcube WMTS & Time Series API

Servicio xcube configurado para servir el dataset **Ukraine Lake Water Quality (LWQ100)** desde Azure Blob Storage con capacidades WMTS y series temporales.

## 📊 Dataset Information

- **Dataset ID**: `ukraine_lwq`
- **Source**: Azure Blob Storage (`ihpwinsdata/data`)
- **Path**: `xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr`
- **Format**: Zarr
- **Region**: Ukraine
- **Bounding Box**: [22.0°E, 44.0°N, 40.5°E, 52.5°N]
- **Temporal Resolution**: 10-day composites
- **Period**: 2024 onwards
- **Spatial Resolution**: 100m

### Variables

| Variable | Description | Units | Range |
|----------|-------------|-------|-------|
| `turbidity_mean` | Mean turbidity | FNU | 0-100 |
| `Rw490_rep` | Water reflectance at 490nm (blue) | sr⁻¹ | 0-0.1 |
| `Rw560_rep` | Water reflectance at 560nm (green) | sr⁻¹ | 0-0.1 |
| `Rw665_rep` | Water reflectance at 665nm (red) | sr⁻¹ | 0-0.1 |
| `Rw842_rep` | Water reflectance at 842nm (NIR) | sr⁻¹ | 0-0.08 |
| `Rw1610_rep` | Water reflectance at 1610nm (SWIR) | sr⁻¹ | 0-0.05 |
| `Rw2190_rep` | Water reflectance at 2190nm (SWIR) | sr⁻¹ | 0-0.05 |

## 🚀 Quick Start

### Prerequisites

Asegúrate de tener instalados los siguientes paquetes:

```bash
pip install xcube xcube-sh zarr azure-storage-blob fsspec adlfs
```

### Start the Server

```bash
# Activate the xcube conda environment and start the server
./start_xcube_ukraine.sh
```

El servidor estará disponible en: **http://localhost:8080**

**Nota**: El script activa automáticamente el entorno conda `xcube` y configura las credenciales de Azure.

### Verify the Service

```bash
# Check that the server is running and the dataset is available
curl http://localhost:8080/datasets

# Expected output:
# {"datasets": [{"id": "ukraine_lwq", "title": "Ukraine Lake Water Quality - LWQ100 MSI", "bbox": [22.0, 44.0, 40.5, 52.5]}], ...}
```

## 📡 API Endpoints

### 1. Datasets List
```bash
# Get all available datasets
curl http://localhost:8080/datasets

# Get specific dataset metadata
curl http://localhost:8080/datasets/ukraine_lwq
```

**Response example:**
```json
{
  "id": "ukraine_lwq",
  "title": "Ukraine Lake Water Quality - LWQ100 MSI",
  "bbox": [22.0, 44.0, 40.5, 52.5],
  "time_range": ["2024-01-01", "2024-12-31"],
  "variables": ["turbidity_mean", "Rw490_rep", "Rw560_rep", ...]
}
```

### 2. WMTS Capabilities
```bash
# Get WMTS service capabilities (OGC standard)
curl http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml
```

### 3. Tile Access
```
# Get a specific tile
GET http://localhost:8080/wmts/1.0.0/ukraine_lwq/{variable}/{style}/{time}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png
```

**Parameters:**
- `{variable}`: Variable name (e.g., `turbidity_mean`, `Rw490_rep`)
- `{style}`: Style name (e.g., `default`, `enhanced`)
- `{time}`: ISO date (e.g., `2024-01-01`)
- `{TileMatrixSet}`: Projection (e.g., `EPSG:3857`)
- `{TileMatrix}`: Zoom level (0-18)
- `{TileRow}`, `{TileCol}`: Tile coordinates

**Example:**
```bash
curl "http://localhost:8080/wmts/1.0.0/ukraine_lwq/turbidity_mean/default/2024-01-01/EPSG:3857/7/42/67.png" -o tile.png
```

### 4. Time Series API
```bash
# Get time series for a specific point (POST request with GeoJSON)
POST http://localhost:8080/timeseries/ukraine_lwq/{variable}
Content-Type: application/json

Body: GeoJSON Point geometry
```

**Example - Kiev (50.45°N, 30.52°E):**
```bash
curl -X POST "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[30.52,50.45]}'
```

**Response example:**
```json
{
  "result": [
    {"mean": 12.5, "time": "2024-01-01T00:00:00Z"},
    {"mean": 15.3, "time": "2024-01-11T00:00:00Z"},
    {"mean": 11.8, "time": "2024-01-21T00:00:00Z"}
  ]
}
```

### 5. Variable Metadata
```bash
# Get metadata for a specific variable
curl http://localhost:8080/datasets/ukraine_lwq/variables/turbidity_mean
```

## 🗺️ Web Client Integration

### Leaflet Example

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    #map { height: 600px; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    // Initialize map centered on Ukraine
    const map = L.map('map').setView([48.5, 31.3], 6);
    
    // Add base layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap'
    }).addTo(map);
    
    // Add Ukraine LWQ turbidity layer
    const turbidityLayer = L.tileLayer(
      'http://localhost:8080/wmts/1.0.0/ukraine_lwq/turbidity_mean/default/2024-01-01/EPSG:3857/{z}/{y}/{x}.png',
      {
        attribution: 'Copernicus LWQ100',
        opacity: 0.7,
        maxZoom: 13
      }
    ).addTo(map);
    
    // Click to get time series
    map.on('click', function(e) {
      const lat = e.latlng.lat.toFixed(4);
      const lon = e.latlng.lng.toFixed(4);
      const url = `http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean`;
      
      // Create GeoJSON Point (lon, lat order)
      const geojsonPoint = {
        type: "Point",
        coordinates: [parseFloat(lon), parseFloat(lat)]
      };
      
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(geojsonPoint)
      })
        .then(response => response.json())
        .then(data => {
          const result = data.result;
          console.log('Time Series Data:', result);
          
          // Get latest non-null value
          const validValues = result.filter(item => item.mean !== null);
          const latestValue = validValues.length > 0 
            ? validValues[validValues.length - 1].mean 
            : null;
          
          L.popup()
            .setLatLng(e.latlng)
            .setContent(`
              <b>Turbidity at (${lat}, ${lon})</b><br>
              Latest: ${latestValue !== null ? latestValue.toFixed(2) : 'N/A'} FNU<br>
              <small>Valid points: ${validValues.length} of ${result.length}</small>
            `)
            .openOn(map);
        })
        .catch(err => console.error('Error fetching time series:', err));
    });
  </script>
</body>
</html>
```

### OpenLayers Example

```javascript
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import WMTS from 'ol/source/WMTS';
import WMTSCapabilities from 'ol/format/WMTSCapabilities';

// Fetch WMTS capabilities
fetch('http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml')
  .then(response => response.text())
  .then(text => {
    const parser = new WMTSCapabilities();
    const result = parser.read(text);
    
    // Create WMTS layer
    const wmtsLayer = new TileLayer({
      source: new WMTS(optionsFromCapabilities(result, {
        layer: 'ukraine_lwq',
        matrixSet: 'EPSG:3857'
      }))
    });
    
    // Create map
    const map = new Map({
      target: 'map',
      layers: [wmtsLayer],
      view: new View({
        center: fromLonLat([31.3, 48.5]),
        zoom: 6
      })
    });
  });
```

## 🐍 Python Client Example

```python
import requests
import matplotlib.pyplot as plt
import pandas as pd

# Base URL
BASE_URL = "http://localhost:8080"

# 1. List datasets
response = requests.get(f"{BASE_URL}/datasets")
datasets = response.json()
print("Available datasets:", [d['id'] for d in datasets])

# 2. Get time series for a point (Dnieper River near Kiev)
lat, lon = 50.45, 30.52
variable = "turbidity_mean"

ts_url = f"{BASE_URL}/timeseries/ukraine_lwq/{variable}"
geojson_point = {
    "type": "Point",
    "coordinates": [lon, lat]  # Note: GeoJSON uses [lon, lat] order
}

response = requests.post(ts_url, json=geojson_point)
data = response.json()

# Extract time series data
result = data['result']
df = pd.DataFrame(result)
df['time'] = pd.to_datetime(df['time'])

# Plot time series
plt.figure(figsize=(12, 6))
plt.plot(df['time'], df['mean'], marker='o')
plt.xlabel('Date')
plt.ylabel('Turbidity (FNU)')
plt.title(f'Turbidity Time Series at ({lat}°N, {lon}°E)')
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('turbidity_timeseries.png')
plt.show()

# 3. Get multiple variables for comparison
variables = ['turbidity_mean', 'Rw490_rep', 'Rw560_rep', 'Rw665_rep']
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
axes = axes.flatten()

geojson_point = {"type": "Point", "coordinates": [lon, lat]}

for idx, var in enumerate(variables):
    ts_url = f"{BASE_URL}/timeseries/ukraine_lwq/{var}"
    response = requests.post(ts_url, json=geojson_point)
    data = response.json()
    
    result = data['result']
    df = pd.DataFrame(result)
    df['time'] = pd.to_datetime(df['time'])
    
    axes[idx].plot(df['time'], df['mean'], marker='o', color=f'C{idx}')
    axes[idx].set_title(var)
    axes[idx].set_xlabel('Date')
    axes[idx].set_ylabel('Mean Value')
    axes[idx].grid(True)
    axes[idx].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('multi_variable_timeseries.png')
plt.show()
```

## 🔍 Verification Commands

```bash
# 1. Check server status
curl -I http://localhost:8080/

# 2. List available datasets
curl http://localhost:8080/datasets | jq '.'

# 3. Get dataset metadata
curl http://localhost:8080/datasets/ukraine_lwq | jq '.'

# 4. Get WMTS capabilities
curl http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml | head -50

# 5. Test time series API (Kiev) - Note: POST request with GeoJSON
curl -X POST "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[30.52,50.45]}' | jq '.'

# 6. Test time series API (Dnieper Reservoir)
curl -X POST "http://localhost:8080/timeseries/ukraine_lwq/Rw560_rep" \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[35.0,48.5]}' | jq '.'

# 7. Download a sample tile
curl "http://localhost:8080/wmts/1.0.0/ukraine_lwq/turbidity_mean/default/2024-01-01/EPSG:3857/7/42/67.png" -o sample_tile.png

# 8. Check available color styles
curl "http://localhost:8080/datasets/ukraine_lwq/variables/turbidity_mean" | jq '.colorMappings'
```

## 🎨 Available Color Mappings

Each variable has multiple color styles available:

### Turbidity
- `default`: viridis (0-100 FNU)
- `high_turbidity`: YlOrRd (0-150 FNU)

### Reflectance Variables
- `default`: plasma (variable-specific range)
- `enhanced`: Band-specific colormaps (Blues, Greens, Reds, etc.)

To use a different style:
```
http://localhost:8080/wmts/1.0.0/ukraine_lwq/turbidity_mean/high_turbidity/{time}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png
```

## 🛠️ Troubleshooting

### Server won't start
```bash
# Check if port 8080 is already in use
lsof -i :8080

# Check Azure credentials
echo $AZURE_STORAGE_CONNECTION_STRING

# Test Azure Storage connectivity
python -c "from azure.storage.blob import BlobServiceClient; client = BlobServiceClient.from_connection_string('$AZURE_STORAGE_CONNECTION_STRING'); print(list(client.list_containers()))"
```

### Cannot access dataset
```bash
# Verify zarr store structure
python -c "import zarr; store = zarr.open('abfs://data/xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr', mode='r'); print(list(store.keys()))"

# Check fsspec installation
pip list | grep -E "(fsspec|adlfs|azure)"
```

### Tiles not rendering
- Check browser console for CORS errors
- Verify the tile URL in browser DevTools
- Check xcube server logs for errors
- Ensure the date in the URL exists in the dataset

## 📚 Additional Resources

- [xcube Documentation](https://xcube.readthedocs.io/)
- [WMTS Standard (OGC)](https://www.ogc.org/standards/wmts)
- [Copernicus LWQ100 Product](https://land.copernicus.eu/global/products/lwq)
- [Azure Blob Storage with Python](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)

## 📝 Notes

- The service uses EPSG:3857 (Web Mercator) projection by default
- Tile cache is configured to 512 MB
- CORS is enabled for web client access
- Maximum zoom level is limited by the dataset's 100m resolution
- Time series queries return all available time steps for the specified location

## 🔒 Security Considerations

⚠️ **Warning**: The Azure Storage credentials in the configuration files are exposed. For production use:

1. Use environment variables or Azure Key Vault
2. Implement proper authentication (OAuth2, API keys)
3. Enable IP whitelisting
4. Use HTTPS with valid certificates
5. Rotate storage account keys regularly

```bash
# Example: Use environment variables only
unset AZURE_STORAGE_ACCOUNT_KEY
# Use Managed Identity or SAS tokens instead
```

## 📊 Performance Tips

- Use tile caching for frequently accessed areas
- Pre-generate tiles for common zoom levels
- Use CDN for tile distribution
- Consider using Cloud Optimized GeoTIFF (COG) format
- Implement request rate limiting
- Monitor Azure Storage egress costs

---

**Support**: For issues or questions, please open an issue in the repository.
