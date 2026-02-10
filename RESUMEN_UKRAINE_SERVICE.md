# 🌊 Ukraine LWQ Service - Resumen Ejecutivo

## ✅ Estado del Servicio

**Servicio WMTS xcube para Ukraine Lake Water Quality - COMPLETADO**

- 🟢 Servidor xcube: **FUNCIONANDO** en http://localhost:8080
- 🟢 Dataset: **ACCESIBLE** desde Azure Blob Storage
- 🟢 Variables: **7 variables disponibles** (turbidity + 6 reflectancias)
- 🟢 API: **Todos los endpoints operativos**

---

## 📁 Archivos Creados

### 1. Configuración Principal
- **`xcube_ukraine_config.yml`** - Configuración del servidor y dataset
  - Data store de Azure Blob Storage
  - Dataset `ukraine_lwq` con 7 variables
  - 2 estilos de visualización (default, enhanced)

### 2. Scripts
- **`start_xcube_ukraine.sh`** - Script de inicio del servidor
  - Activa entorno conda `xcube`
  - Configura credenciales de Azure
  - Inicia servidor en puerto 8080

### 3. Documentación
- **`UKRAINE_LWQ_SERVICE.md`** - Documentación completa del servicio
  - Información del dataset
  - Guía de uso de API endpoints
  - Ejemplos de integración (Leaflet, OpenLayers, Python)
  - Comandos de verificación

- **`TROUBLESHOOTING_UKRAINE.md`** - Guía de troubleshooting
  - Explicación de warnings comunes
  - Soluciones a problemas típicos
  - Optimización de performance

### 4. Visualizador Web
- **`ukraine_lwq_viewer.html`** - Aplicación web interactiva
  - Mapa con Leaflet
  - Selector de variables y fechas
  - Gráficos de series temporales con Chart.js
  - Control de estilos y opacidad

---

## 🚀 Uso Rápido

### Iniciar el Servidor

```bash
cd /home/pabrojast/Proyectos/xcube
./start_xcube_ukraine.sh
```

### Verificar que Funciona

```bash
# Listar datasets
curl http://localhost:8080/datasets

# Resultado esperado:
# {"datasets": [{"id": "ukraine_lwq", "title": "Ukraine Lake Water Quality - LWQ100 MSI", ...}]}
```

### Abrir el Visualizador

```
file:///home/pabrojast/Proyectos/xcube/ukraine_lwq_viewer.html
```

---

## 📡 Endpoints Principales

| Endpoint | URL | Descripción |
|----------|-----|-------------|
| **Datasets** | `http://localhost:8080/datasets` | Lista de datasets |
| **Dataset Info** | `http://localhost:8080/datasets/ukraine_lwq` | Metadatos del dataset |
| **WMTS Capabilities** | `http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml` | Capabilities OGC |
| **Tiles** | `http://localhost:8080/wmts/1.0.0/tile/ukraine_lwq/{var}/{z}/{y}/{x}.png` | Tiles de mapa |
| **Time Series** | `http://localhost:8080/timeseries/ukraine_lwq/{var}?lat={lat}&lon={lon}` | Series temporales |
| **OpenAPI** | `http://localhost:8080/openapi.html` | Documentación API |
| **Viewer** | `http://localhost:8080/viewer` | Visualizador web |

---

## 📊 Variables Disponibles

| ID | Descripción | Rango | Unidad |
|----|-------------|-------|--------|
| `turbidity_mean` | Turbidez media | 0-100 | FNU |
| `Rw490_rep` | Reflectancia 490nm (azul) | 0-0.1 | sr⁻¹ |
| `Rw560_rep` | Reflectancia 560nm (verde) | 0-0.1 | sr⁻¹ |
| `Rw665_rep` | Reflectancia 665nm (rojo) | 0-0.1 | sr⁻¹ |
| `Rw842_rep` | Reflectancia 842nm (NIR) | 0-0.08 | sr⁻¹ |
| `Rw1610_rep` | Reflectancia 1610nm (SWIR) | 0-0.05 | sr⁻¹ |
| `Rw2190_rep` | Reflectancia 2190nm (SWIR) | 0-0.05 | sr⁻¹ |

---

## 🎨 Estilos de Visualización

### Default Style
- Turbidez: viridis (0-100 FNU)
- Reflectancias: plasma (rangos específicos por banda)

### Enhanced Style
- Turbidez: YlOrRd (0-150 FNU)
- Reflectancias: colormaps específicos por banda (Blues, Greens, Reds, etc.)

---

## 🗺️ Región Cubierta

- **Área**: Ucrania
- **Bounding Box**: [22.0°E, 44.0°N, 40.5°E, 52.5°N]
- **Resolución espacial**: 100m
- **Resolución temporal**: Composites de 10 días
- **Período**: 2024 en adelante
- **CRS**: EPSG:4326 (WGS84)

---

## 🔧 Configuración Técnica

### Almacenamiento
- **Tipo**: Azure Blob Storage
- **Cuenta**: ihpwinsdata
- **Contenedor**: data
- **Ruta**: `xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr`
- **Formato**: Zarr

### Servidor
- **Puerto**: 8080
- **Dirección**: 0.0.0.0 (todas las interfaces)
- **Framework**: xcube 1.11.1
- **Entorno**: conda (xcube)

### Dependencias Clave
- xcube
- xcube-sh
- zarr
- azure-storage-blob
- fsspec
- adlfs

---

## ⚠️ Notas Importantes

### Warning Esperado
```
UserWarning: No data opener found for format 'zarr' and data type 'mldataset'.
Data type is changed to the default data type 'dataset'.
```

**Esto es normal** - El dataset no tiene estructura multi-nivel (pirámide de resoluciones), pero funciona perfectamente como dataset estándar. Ver `TROUBLESHOOTING_UKRAINE.md` para más detalles.

### Credenciales
Las credenciales de Azure están codificadas en:
- `xcube_ukraine_config.yml`
- `start_xcube_ukraine.sh`

**Para producción**, se recomienda usar:
- Variables de entorno
- Azure Key Vault
- Managed Identity
- SAS tokens

---

## 📝 Ejemplos de Uso

### Python - Obtener Serie Temporal

```python
import requests
import pandas as pd

url = "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean"
params = {"lat": 50.45, "lon": 30.52}

response = requests.get(url, params=params)
data = response.json()

# Extraer datos
props = data['features'][0]['properties']
df = pd.DataFrame({
    'time': pd.to_datetime(props['time']),
    'turbidity': props['turbidity_mean']
})

print(df.head())
```

### JavaScript - Mapa Leaflet

```javascript
const map = L.map('map').setView([48.5, 31.3], 6);

L.tileLayer('http://localhost:8080/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/{z}/{y}/{x}.png', {
    attribution: 'Copernicus LWQ100',
    opacity: 0.7
}).addTo(map);
```

### QGIS - Añadir Capa WMTS

1. Layer → Add Layer → Add WMS/WMTS Layer
2. New Connection
3. URL: `http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml`
4. OK → Connect → Select layer → Add

---

## 🎯 Próximos Pasos

### Mejoras Opcionales

1. **Crear Multi-Level Dataset** para mejor rendimiento a diferentes zoom levels
2. **Añadir autenticación** para acceso seguro
3. **Configurar HTTPS** con certificado SSL
4. **Desplegar en servidor** permanente (no localhost)
5. **Añadir caché de tiles** para mejorar velocidad
6. **Crear más estilos** de visualización personalizados

### Integración con Otras Herramientas

- ✅ QGIS (añadir como capa WMS/WMTS)
- ✅ ArcGIS (servicios OGC estándar)
- ✅ Google Earth Engine (vía tiles)
- ✅ Jupyter Notebooks (API Python)
- ✅ Web apps (Leaflet, OpenLayers, MapLibre)

---

## 📚 Documentación

- **Documentación principal**: `UKRAINE_LWQ_SERVICE.md`
- **Troubleshooting**: `TROUBLESHOOTING_UKRAINE.md`
- **Configuración**: `xcube_ukraine_config.yml`
- **Visualizador**: `ukraine_lwq_viewer.html`

---

## ✅ Checklist de Verificación

- [x] Servidor xcube instalado y configurado
- [x] Conexión a Azure Blob Storage establecida
- [x] Dataset ukraine_lwq accesible
- [x] Endpoints API funcionando
- [x] WMTS capabilities disponibles
- [x] Series temporales operativas
- [x] Visualizador web creado
- [x] Documentación completa
- [x] Ejemplos de integración
- [x] Script de inicio automatizado

---

**Estado**: ✅ **COMPLETADO Y OPERATIVO**

**Fecha**: 10 de octubre de 2025

**Servicio**: Ukraine Lake Water Quality WMTS & Time Series API

**Contacto**: Ver documentación del proyecto xcube
