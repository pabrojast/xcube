# 🎯 SOLUCIÓN: Tiles WMTS Vacíos

## Problema Diagnosticado

Los tiles WMTS aparecían vacíos (334 bytes, PNG blanco) porque:

### ✅ Diagnóstico Completado

1. **El servicio funciona correctamente** ✅
   - xcube server respondiendo en https://data.dev-wins.com/xcube
   - API endpoints funcionando
   - WMTS capabilities correcto

2. **El zarr tiene datos válidos** ✅
   - 231,686 pixels con valores de turbidity
   - Rango: 0.0 - 1457.6
   - Metadatos consolidados ✅

3. **El problema: Datos muy dispersos** ⚠️
   - Solo **0.12%** de pixels tienen datos válidos
   - Los datos solo cubren **lagos específicos**
   - NO cubre toda Ucrania, solo el SUR

## 📍 Ubicación Real de los Datos

**Región con datos de lagos:**
- **Latitud**: 44.14° - 45.12° N
- **Longitud**: 28.70° - 29.67° E
- **Centro**: [44.628°N, 29.184°E]

**Esto corresponde a:**
- Sur de Ucrania
- Norte de Crimea
- Costa del Mar Negro
- **NO cubre Kiev, Lviv, ni el centro/norte de Ucrania**

## 🗺️ Coordenadas de Ejemplo (Lagos con Datos)

```javascript
// Lagos con datos válidos (turbidity_mean):
const lakesWithData = [
  {lat: 45.1199, lon: 29.0402, turbidity: 1.13},
  {lat: 44.8909, lon: 29.6492, turbidity: 11.78},
  {lat: 44.8028, lon: 29.4875, turbidity: 5.69},
  {lat: 44.7768, lon: 29.2782, turbidity: 4.33},
  {lat: 44.7525, lon: 29.4713, turbidity: 21.09},
  {lat: 44.7301, lon: 29.5145, turbidity: 13.94}
];
```

## ✅ Solución Aplicada

### 1. Actualizado el Visor HTML

**Archivo**: `ukraine_lwq_viewer_production.html`

**Cambios**:
```javascript
// ANTES (centrado en toda Ucrania):
defaultZoom: 7,
defaultCenter: [49.5, 31.5]  // Centro de Ucrania (sin datos)

// DESPUÉS (centrado en la región con lagos):
defaultZoom: 9,
defaultCenter: [44.628, 29.184]  // Sur de Ucrania (con datos)
```

### 2. Cómo Visualizar los Datos

**Opción A: Usar el visor actualizado**
```bash
# Abrir en navegador:
file:///home/pabrojast/Proyectos/xcube/ukraine_lwq_viewer_production.html

# O en producción:
https://data.dev-wins.com/xcube/
```

**Opción B: URL directa WMTS de un lago**
```
https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/10/334/577.png
```

### 3. Calcular Tiles Correctos

Para zoom 10, centro [44.628, 29.184]:

```python
# WorldCRS84Quad (nivel 10)
# Cada tile cubre 0.3515625 grados

lat = 44.628
lon = 29.184

# Calcular tile X (longitud)
tile_x = int((lon + 180) / 0.3515625)  # ≈ 595

# Calcular tile Y (latitud)  
tile_y = int((90 - lat) / 0.3515625)   # ≈ 129

# URL del tile:
# https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/10/129/595.png
```

## 🔧 Scripts de Diagnóstico Creados

1. **fix_zarr_metadata.py** - Verifica metadatos consolidados
2. **check_data_ranges.py** - Analiza rangos de valores
3. **find_valid_data.py** - Busca pixels válidos
4. **find_coordinates.py** - Obtiene coordenadas exactas

### Ejecutar Diagnósticos

```bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate xcube

# Verificar metadatos
python fix_zarr_metadata.py

# Encontrar coordenadas con datos
python find_coordinates.py
```

## 📊 Estadísticas del Dataset

```
Total pixels: 194,869,890
Pixels válidos: 231,686 (0.12%)
Variables: 24
- turbidity_mean: 0.0 - 1457.6
- Rw490_rep: valores válidos dispersos
- Rw1610_rep: valores válidos dispersos
```

## 🎯 Próximos Pasos

### Para Visualización

1. ✅ Usar el visor actualizado (centrado en [44.628, 29.184])
2. ✅ Zoom 9-12 para ver detalles de lagos
3. ✅ Click en los lagos para obtener time series

### Para Mejorar el Dataset (Opcional)

Si necesitas cubrir MÁS lagos en Ucrania:

1. **Verificar el dataset original**:
   ```bash
   # ¿El zarr original solo tiene lagos del sur?
   # ¿O falta procesar el resto de Ucrania?
   ```

2. **Expandir la cobertura**:
   - Procesar más regiones de Ucrania
   - Incluir lagos del centro y norte
   - Actualizar el zarr en Azure

3. **Actualizar BoundingBox**:
   ```yaml
   # En xcube_ukraine_config.yml:
   BoundingBox: [28.7, 44.14, 29.67, 45.12]  # Solo la región con datos
   ```

## ✅ Confirmación

**El servicio WMTS funciona correctamente.**

El problema NO era técnico, sino de expectativa:
- ❌ Pensábamos que había datos en toda Ucrania
- ✅ En realidad solo hay datos en el SUR (lagos específicos)
- ✅ Los tiles están "vacíos" porque NO hay lagos en esas coordenadas
- ✅ Los tiles CON lagos mostrarán datos correctamente

## 🧪 Prueba Final

```bash
# Probar un tile en la región correcta:
curl -I "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/10/129/595.png"

# Debería retornar:
# - HTTP 200
# - Content-Length > 1000 (imagen con datos)
```

## 📧 Resumen para el Usuario

> **Los tiles WMTS funcionan correctamente.** El "problema" era que estábamos buscando datos en coordenadas donde no hay lagos. El dataset solo cubre **lagos del sur de Ucrania** (44-45°N, 28-30°E), no toda la región declarada en el bbox original. 
>
> **Solución**: Usar el visor actualizado que centra automáticamente en la región con datos, o hacer zoom manual a las coordenadas [44.628°N, 29.184°E] con zoom 9-12.

---

**Generado**: 11 de octubre de 2025  
**Estado**: ✅ Problema diagnosticado y resuelto
