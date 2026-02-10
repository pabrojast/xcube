# 🎉 Ukraine LWQ Service - Resumen de Configuración

## ✅ Servicio Completado y Funcional

El servicio xcube para el dataset **Ukraine Lake Water Quality (LWQ100)** desde Azure Blob Storage está completamente configurado y funcionando.

## 📁 Archivos Creados

### 1. **xcube_ukraine_config.yml**
Archivo de configuración principal de xcube con:
- ✅ DataStore configurado para Azure Blob Storage (abfs)
- ✅ Dataset `ukraine_lwq` con path correcto
- ✅ Estilos `default` y `enhanced` con ColorMappings para todas las variables
- ✅ BoundingBox de Ucrania [22.0, 44.0, 40.5, 52.5]

### 2. **start_xcube_ukraine.sh**
Script de inicio que:
- ✅ Activa automáticamente el entorno conda `xcube`
- ✅ Configura variables de entorno de Azure Storage
- ✅ Inicia el servidor en puerto 8080
- ✅ Muestra información de endpoints disponibles

### 3. **UKRAINE_LWQ_SERVICE.md**
Documentación completa que incluye:
- 📊 Información del dataset y variables
- 🚀 Guía de inicio rápido
- 📡 Documentación de todos los endpoints API
- 🗺️ Ejemplos de integración (Leaflet, OpenLayers, Python)
- 🔍 Comandos de verificación
- 🛠️ Troubleshooting

### 4. **ukraine_lwq_viewer.html**
Visualizador web interactivo con:
- 🗺️ Mapa Leaflet con capa WMTS
- 📊 Gráficos de series temporales con Chart.js
- 🎨 Control de variables, fechas y estilos
- 📍 Click en mapa para obtener series temporales
- 🎚️ Control de opacidad de capas

### 5. **TROUBLESHOOTING.md**
Guía de solución de problemas con:
- ⚠️ Explicación del warning de mldataset
- 🔧 Soluciones a errores comunes
- 📝 Checklist de verificación

### 6. **QUICK_START.md**
Guía rápida de inicio con:
- 🚀 Pasos de instalación
- ▶️ Comandos de inicio
- ✅ Verificación del servicio
- 🌐 Acceso al visualizador

## 🌐 Endpoints Disponibles

### Servidor Principal
```
http://localhost:8080
```

### API Endpoints
```
GET  /datasets                           # Lista de datasets
GET  /datasets/ukraine_lwq               # Metadata del dataset
GET  /wmts/1.0.0/WMTSCapabilities.xml   # Capabilities WMTS
GET  /tiles/{dataset}/{var}/{z}/{y}/{x}  # Tiles WMTS
POST /timeseries/{dataset}/{var}         # Series temporales (GeoJSON Point)
GET  /openapi.html                       # Documentación API
```

## 📊 Variables Disponibles

| Variable | Descripción | Unidades | Rango |
|----------|-------------|----------|-------|
| `turbidity_mean` | Turbidez media | FNU | 0-100 |
| `Rw490_rep` | Reflectancia 490nm (azul) | sr⁻¹ | 0-0.1 |
| `Rw560_rep` | Reflectancia 560nm (verde) | sr⁻¹ | 0-0.1 |
| `Rw665_rep` | Reflectancia 665nm (rojo) | sr⁻¹ | 0-0.1 |
| `Rw842_rep` | Reflectancia 842nm (NIR) | sr⁻¹ | 0-0.08 |
| `Rw1610_rep` | Reflectancia 1610nm (SWIR) | sr⁻¹ | 0-0.05 |
| `Rw2190_rep` | Reflectancia 2190nm (SWIR) | sr⁻¹ | 0-0.05 |

## 🎨 Estilos Disponibles

### default
- Turbidity: viridis (0-100)
- Reflectancias: plasma (rangos específicos)

### enhanced
- Turbidity: YlOrRd (0-150)
- Rw490: Blues, Rw560: Greens, Rw665: Reds
- Rw842: RdPu, Rw1610/Rw2190: YlOrBr

## 🚀 Inicio Rápido

### 1. Iniciar el Servidor
```bash
cd /home/pabrojast/Proyectos/xcube
./start_xcube_ukraine.sh
```

### 2. Verificar el Servicio
```bash
# Verificar que el servidor responde
curl http://localhost:8080/datasets

# Debería devolver:
# {"datasets": [{"id": "ukraine_lwq", ...}], ...}
```

### 3. Abrir el Visualizador
Abre en tu navegador:
```
file:///home/pabrojast/Proyectos/xcube/ukraine_lwq_viewer.html
```

### 4. Probar Series Temporales
```bash
# POST con GeoJSON Point (Kiev: 50.45°N, 30.52°E)
curl -X POST "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[30.52,50.45]}'
```

## 📝 Notas Importantes

### ⚠️ Warning sobre mldataset
El warning:
```
UserWarning: No data opener found for format 'zarr' and data type 'mldataset'.
Data type is changed to the default data type 'dataset'.
```

**Es normal y no afecta la funcionalidad**. El dataset se abre correctamente como `dataset` estándar. 

### 🔐 Credenciales de Azure
Las credenciales están configuradas en:
- Variables de entorno (script `start_xcube_ukraine.sh`)
- Configuración del DataStore (archivo `xcube_ukraine_config.yml`)

**Para producción**: Usar Azure Key Vault o variables de entorno seguras.

### 🌍 API de Series Temporales
**Importante**: El endpoint de series temporales usa **POST** con GeoJSON Point:
```javascript
// Correcto
fetch('/timeseries/ukraine_lwq/turbidity_mean', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    type: "Point",
    coordinates: [lon, lat]  // Orden: [lon, lat]
  })
})

// Incorrecto (GET no funciona)
fetch('/timeseries/ukraine_lwq/turbidity_mean?lat=50&lon=30')
```

## 🎯 Casos de Uso

### 1. Visualización en Aplicación Web
- Usar `ukraine_lwq_viewer.html` como base
- Modificar estilos y layout según necesidades
- Integrar con tu framework (React, Vue, Angular)

### 2. Análisis en Python
```python
import requests
import pandas as pd

url = "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean"
point = {"type": "Point", "coordinates": [30.52, 50.45]}
response = requests.post(url, json=point)
data = pd.DataFrame(response.json()['result'])
```

### 3. Integración con QGIS
1. Añadir capa WMTS desde URL:
   ```
   http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml
   ```
2. Seleccionar dataset `ukraine_lwq`
3. Elegir variable y estilo

### 4. Cliente OGC Estándar
Cualquier cliente compatible con WMTS puede conectarse:
- QGIS
- ArcGIS Pro
- OpenLayers
- Leaflet
- MapStore
- GeoServer

## 📊 Rendimiento

- **Tile Cache**: 512 MB configurado
- **CORS**: Habilitado para clientes web
- **Zoom Máximo**: Limitado por resolución de 100m
- **Formato**: Zarr optimizado para acceso rápido
- **Almacenamiento**: Azure Blob Storage

## 🔄 Próximos Pasos Sugeridos

1. **Optimización**:
   - Pre-generar tiles para zooms comunes
   - Implementar CDN para distribución
   - Configurar cache de tiles

2. **Seguridad**:
   - Implementar autenticación OAuth2
   - Usar Azure Key Vault para credenciales
   - Habilitar HTTPS

3. **Monitorización**:
   - Configurar logs de acceso
   - Monitorizar costos de egress de Azure
   - Tracking de uso de API

4. **Ampliación**:
   - Añadir más datasets de CLMS
   - Integrar otros servicios (WMS, WFS)
   - Implementar procesamiento on-demand

## 📚 Referencias

- [xcube Documentation](https://xcube.readthedocs.io/)
- [WMTS Standard](https://www.ogc.org/standards/wmts)
- [Copernicus LWQ100](https://land.copernicus.eu/global/products/lwq)
- [Azure Blob Storage](https://docs.microsoft.com/en-us/azure/storage/blobs/)

## 🤝 Soporte

Para problemas o preguntas:
1. Revisar `TROUBLESHOOTING.md`
2. Consultar logs del servidor
3. Verificar conectividad con Azure Storage
4. Revisar documentación de xcube

---

**Estado**: ✅ **Servicio Operacional**

**Última actualización**: 10 de octubre de 2025

**Versión**: 1.0.0
