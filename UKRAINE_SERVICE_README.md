# 🌊 Ukraine Lake Water Quality Service - xcube

Servicio xcube completamente configurado para servir el dataset **Ukraine Lake Water Quality (LWQ100)** desde Azure Blob Storage con capacidades WMTS y series temporales.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![xcube](https://img.shields.io/badge/xcube-1.11.1-green.svg)](https://xcube.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile.ukraine)

---

## 📊 Dataset Information

- **Dataset**: Ukraine Lake Water Quality (LWQ100 MSI)
- **Source**: Copernicus Global Land Service (CGLS)
- **Storage**: Azure Blob Storage (`ihpwinsdata/data`)
- **Format**: Zarr
- **Region**: Ukraine [22.0°E, 44.0°N, 40.5°E, 52.5°N]
- **Resolution**: 100m spatial, 10-day temporal
- **Period**: 2024 onwards

### Variables

| Variable | Description | Units |
|----------|-------------|-------|
| `turbidity_mean` | Mean turbidity | FNU |
| `Rw490_rep` | Water reflectance at 490nm (blue) | sr⁻¹ |
| `Rw560_rep` | Water reflectance at 560nm (green) | sr⁻¹ |
| `Rw665_rep` | Water reflectance at 665nm (red) | sr⁻¹ |
| `Rw842_rep` | Water reflectance at 842nm (NIR) | sr⁻¹ |
| `Rw1610_rep` | Water reflectance at 1610nm (SWIR) | sr⁻¹ |
| `Rw2190_rep` | Water reflectance at 2190nm (SWIR) | sr⁻¹ |

---

## 🚀 Quick Start

### Option 1: Local Installation (Conda)

```bash
# 1. Activate xcube environment
conda activate xcube

# 2. Start the server
./start_xcube_ukraine.sh

# 3. Verify service
curl http://localhost:8080/datasets
```

### Option 2: Docker (Recommended)

```bash
# 1. Build and run
./docker_ukraine.sh build
./docker_ukraine.sh run

# 2. Test endpoints
./docker_ukraine.sh test
```

### Option 3: Docker Compose

```bash
# Start service
docker-compose -f docker-compose.ukraine.yml up -d

# View logs
docker-compose -f docker-compose.ukraine.yml logs -f
```

---

## 🌐 Service URLs

Once running, access:

- **Main API**: http://localhost:8080
- **Datasets List**: http://localhost:8080/datasets
- **WMTS Capabilities**: http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml
- **API Documentation**: http://localhost:8080/openapi.html
- **Web Viewer**: Open `ukraine_lwq_viewer.html` in browser

---

## 📡 API Examples

### Get Datasets

```bash
curl http://localhost:8080/datasets
```

### Get Time Series (POST with GeoJSON)

```bash
curl -X POST "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[30.52,50.45]}'
```

### Get WMTS Tile

```
http://localhost:8080/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/7/42/67.png
```

---

## 📁 Project Structure

```
├── Dockerfile.ukraine            # Docker image definition
├── docker-compose.ukraine.yml    # Docker Compose configuration
├── docker_ukraine.sh             # Docker management script
├── xcube_ukraine_config.yml      # xcube service configuration
├── start_xcube_ukraine.sh        # Local startup script
├── ukraine_lwq_viewer.html       # Interactive web viewer
├── UKRAINE_LWQ_SERVICE.md        # Complete API documentation
├── DOCKER_GUIDE.md               # Docker deployment guide
├── SERVICE_SUMMARY.md            # Service summary
└── TROUBLESHOOTING.md            # Troubleshooting guide
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [UKRAINE_LWQ_SERVICE.md](UKRAINE_LWQ_SERVICE.md) | Complete API documentation with examples |
| [DOCKER_GUIDE.md](DOCKER_GUIDE.md) | Docker deployment and troubleshooting |
| [SERVICE_SUMMARY.md](SERVICE_SUMMARY.md) | Service overview and configuration |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |

---

## 🎨 Web Viewer

Interactive map-based viewer included:

- 🗺️ Leaflet map with WMTS layers
- 📊 Time series charts with Chart.js
- 🎨 Multiple color styles
- 📍 Click-to-query functionality
- 🎚️ Layer opacity control

Open `ukraine_lwq_viewer.html` in your browser after starting the service.

---

## 🐳 Docker Commands

```bash
# Build
./docker_ukraine.sh build

# Run
./docker_ukraine.sh run

# View logs
./docker_ukraine.sh logs

# Test endpoints
./docker_ukraine.sh test

# Stop
./docker_ukraine.sh stop

# Clean up
./docker_ukraine.sh clean-all
```

---

## 🔌 Client Integration

### Python

```python
import requests

url = "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean"
point = {"type": "Point", "coordinates": [30.52, 50.45]}
response = requests.post(url, json=point)
data = response.json()
```

### JavaScript (Leaflet)

```javascript
const wmtsUrl = 'http://localhost:8080/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/{z}/{y}/{x}.png';
L.tileLayer(wmtsUrl, { opacity: 0.7 }).addTo(map);
```

### QGIS

1. Add WMTS Layer
2. Use URL: `http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml`
3. Select `ukraine_lwq` dataset

---

## 🛠️ Requirements

### Local Installation

- Python 3.9+
- Conda/Mamba
- xcube 1.11.1+
- Azure Blob Storage credentials

### Docker Installation

- Docker 20.10+
- Docker Compose 1.29+ (optional)
- 4GB RAM minimum
- 10GB disk space

---

## ⚙️ Configuration

### Azure Storage Credentials

Set in `start_xcube_ukraine.sh` or Docker environment:

```bash
export AZURE_STORAGE_ACCOUNT_NAME="ihpwinsdata"
export AZURE_STORAGE_ACCOUNT_KEY="your_key_here"
```

### Service Configuration

Edit `xcube_ukraine_config.yml` to customize:
- Dataset paths
- Color mappings
- Bounding boxes
- Styles

---

## 🔍 Testing

```bash
# Local
curl http://localhost:8080/datasets
curl http://localhost:8080/datasets/ukraine_lwq

# Docker
./docker_ukraine.sh test

# Time Series
curl -X POST "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[30.52,50.45]}' | jq '.'
```

---

## 🚨 Troubleshooting

### Service won't start

```bash
# Check logs
./docker_ukraine.sh logs
# or
tail -f xcube_server.log
```

### Port already in use

```bash
# Change port in docker run command
docker run -p 8081:8080 ...
```

### Azure connection issues

```bash
# Verify credentials
echo $AZURE_STORAGE_ACCOUNT_NAME
echo $AZURE_STORAGE_ACCOUNT_KEY

# Test connectivity
python -c "from azure.storage.blob import BlobServiceClient; ..."
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

---

## 🎯 Use Cases

1. **Web Applications**: Integrate WMTS tiles into web maps
2. **GIS Software**: Connect QGIS, ArcGIS to WMTS service
3. **Data Analysis**: Extract time series for research
4. **Environmental Monitoring**: Track water quality trends
5. **Reporting**: Generate automated water quality reports

---

## 📊 Performance

- **Tile Cache**: 512 MB configured
- **CORS**: Enabled for web clients
- **Health Checks**: Automated monitoring
- **Restart Policy**: Auto-restart on failure

---

## 🔒 Security Notes

⚠️ **Production Recommendations**:

1. Use Azure Key Vault for credentials
2. Enable HTTPS with valid certificates
3. Implement authentication (OAuth2)
4. Use environment variables for secrets
5. Regular security updates

---

## 🤝 Contributing

Issues and pull requests are welcome!

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

## 👥 Authors

- Pablo Rojas (@pabrojast)

---

## 🙏 Acknowledgments

- [xcube Team](https://github.com/dcs4cop/xcube)
- [Copernicus Global Land Service](https://land.copernicus.eu/)
- [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/)

---

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [UKRAINE_LWQ_SERVICE.md](UKRAINE_LWQ_SERVICE.md)
3. Open an issue on GitHub

---

**Status**: ✅ Operational | **Version**: 1.0.0 | **Last Updated**: 2025-10-10
