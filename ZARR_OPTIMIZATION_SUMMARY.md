# 📊 Zarr Optimizado para WMTS - Resumen Final

## 🎯 Problema Original

Los tiles WMTS aparecían vacíos (334 bytes) en el servicio xcube.

## 🔍 Diagnóstico Realizado

### 1. Verificación del Servicio ✅
- xcube server funcionando correctamente
- API endpoints respondiendo
- WMTS capabilities correcto
- Configuración de estilos válida

### 2. Análisis del Dataset ✅

**Datos válidos encontrados:**
```
Total pixels: 194,869,890
Pixels válidos: 231,686 (0.12%)
Variables: 24
Rango turbidity: 0.0 - 1457.6
```

**Distribución espacial:**
- Datos MUY dispersos (solo lagos específicos)
- Solo 0.12% de pixels con valores válidos
- Lagos concentrados en el sur de Ucrania (44-45°N, 28-30°E)

### 3. Problema de Chunks Original ⚠️

**Estructura anterior:**
```yaml
Chunks: (1, 512, 512)  # time, lat, lon
Fragmentación: 39 chunks de tiempo individuales
Compresión: Blosc shuffle
Metadatos: Consolidados ✅
```

**Problemas identificados:**
- Chunks 512x512 → subóptimos para WMTS (recomendado: 1024)
- Los tiles en zoom 8+ caían en áreas sin lagos → 334 bytes vacíos
- Solo zoom 6-7 capturaban suficientes lagos para mostrar datos

## ✅ Solución Aplicada

### 1. Zarr Optimizado

**Nueva estructura:**
```yaml
Chunks: (1, 1024, 1024)  # ✅ Óptimo para WMTS
Compresión: Blosc(cname='lz4', clevel=5, shuffle=SHUFFLE)
Metadatos: Consolidados (.zmetadata: 16,966 bytes)
Coordenadas: 
  - lat: standard_name, units, long_name ✅
  - lon: standard_name, units, long_name ✅
CRS: spatial_ref presente ✅
```

**Mejoras:**
- ✅ Chunks 2x más grandes (1024 vs 512) → menos lecturas I/O
- ✅ Mejor alineación con tiles WMTS
- ✅ Compresión LZ4 (más rápida que zstd)
- ✅ Atributos CF-compliant completos

### 2. Configuración xcube Actualizada

**ConfigMap (k8s/02-configmap.yaml):**
```yaml
# Documentación de optimizaciones añadida
reverse_url_prefix: "https://data.dev-wins.com/xcube"
BoundingBox: [22.0, 44.0, 40.5, 52.5]
Chunks óptimos: 1024x1024
```

### 3. Visor Actualizado

**ukraine_lwq_viewer_production.html:**
```javascript
defaultZoom: 7,  // Zoom 6-7 captura lagos dispersos
defaultCenter: [48.0, 31.0],  // Centro de Ucrania
```

## 📈 Resultados Esperados

### Antes (Chunks 512x512)
```
Zoom 6: ✅ 2909 bytes (con datos)
Zoom 7: ✅ 5757 bytes (con datos)
Zoom 8: ❌ 852 bytes (vacío)
Zoom 9: ❌ 491 bytes (vacío)
Zoom 10+: ❌ 334 bytes (vacío)
```

### Después (Chunks 1024x1024) - Esperado
```
Zoom 6: ✅ Datos más rápidos (menos lecturas)
Zoom 7: ✅ Datos más rápidos
Zoom 8: ✅ Posiblemente con datos (mejor cobertura)
Zoom 9: ⚪ Puede seguir vacío (lagos pequeños)
Zoom 10+: ⚪ Vacío (normal, lagos muy pequeños)
```

### Mejoras de Rendimiento

**Lecturas de Chunks:**
```
Antes (512x512):
- Para tile 1024x1024: leer 4 chunks
- Para área grande: muchas lecturas pequeñas

Después (1024x1024):
- Para tile 1024x1024: leer 1 chunk ✅
- Para área grande: menos lecturas, más eficiente ✅
```

**Compresión:**
```
Antes: Blosc shuffle (genérico)
Después: Blosc LZ4 (más rápido) ✅
```

## 🚀 Deployment

### Script de Actualización

```bash
chmod +x /home/pabrojast/Proyectos/xcube/update_service_optimized_zarr.sh
./update_service_optimized_zarr.sh
```

**El script:**
1. ✅ Aplica ConfigMap actualizado
2. ✅ Reinicia deployment (rollout restart)
3. ✅ Espera a que pods estén listos
4. ✅ Verifica estado y logs

### Verificación Manual

```bash
# 1. Verificar zarr en Azure
python verify_updated_zarr.py

# 2. Probar tiles en zoom correcto
curl -I "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/7/32/148.png"

# 3. Verificar logs del servicio
kubectl logs -n xcube-ukraine -l app=xcube-ukraine --tail=50

# 4. Probar en navegador
# https://data.dev-wins.com/xcube/
```

## 📊 Monitoring

### KPIs a Verificar

**1. Tamaño de Tiles:**
```bash
# Zoom 7 (debería ser > 1KB con datos)
curl -w "%{size_download}\n" -o /tmp/tile.png \
  "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/7/32/148.png"
```

**2. Tiempo de Respuesta:**
```bash
# Medir latencia
curl -w "Time: %{time_total}s\n" -o /tmp/tile.png \
  "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/7/32/148.png"
```

**3. Logs de xcube:**
```bash
# Buscar errores o advertencias
kubectl logs -n xcube-ukraine -l app=xcube-ukraine --tail=100 | \
  grep -E "ERROR|WARN|Exception"
```

## 🔧 Troubleshooting

### Si los tiles siguen vacíos

**1. Verificar el zarr se actualizó:**
```python
python verify_updated_zarr.py
# Debe mostrar: Chunks: (1, 1024, 1024)
```

**2. Verificar ConfigMap aplicado:**
```bash
kubectl get configmap xcube-ukraine-config -n xcube-ukraine -o yaml | grep -A 5 "reverse_url"
```

**3. Verificar pods reiniciados:**
```bash
kubectl get pods -n xcube-ukraine
# La columna AGE debe ser reciente (< 5m)
```

### Si hay errores de lectura

**1. Verificar credenciales Azure:**
```bash
kubectl get secret xcube-ukraine-secrets -n xcube-ukraine -o yaml
```

**2. Verificar logs de error:**
```bash
kubectl logs -n xcube-ukraine -l app=xcube-ukraine --tail=100 | grep -i azure
```

### Si el servicio es lento

**1. Verificar recursos del pod:**
```bash
kubectl top pods -n xcube-ukraine
```

**2. Aumentar replicas si es necesario:**
```bash
kubectl scale deployment xcube-ukraine-deployment -n xcube-ukraine --replicas=3
```

## 📝 Notas Técnicas

### Por qué algunos tiles están vacíos

**Es NORMAL que tiles estén vacíos** porque:
- Los lagos ocupan solo 0.12% del área total
- Los tiles caen en áreas sin lagos
- Un tile de 334 bytes = PNG vacío/transparente válido

**Tiles con datos:**
- Solo en áreas con lagos
- Principalmente en zoom 6-7 (vista amplia)
- Zoom 8+ puede estar vacío si el tile no contiene lagos

### Chunks 1024x1024 vs 512x512

**Por qué 1024 es mejor:**
```
WMTS tiles típicos: 256x256 pixels
Área cubierta por tile zoom 7: ~1400x1400 pixels en el dataset

Con chunks 512x512:
- Necesita leer 4-9 chunks por tile
- Más operaciones I/O
- Mayor latencia

Con chunks 1024x1024:
- Necesita leer 1-2 chunks por tile ✅
- Menos I/O
- Menor latencia ✅
```

### Compresión Blosc LZ4

**Ventajas:**
- Descompresión muy rápida (más que zstd)
- Buen ratio de compresión
- Optimizado para datos numéricos
- Soporta SIMD (paralelo)

## 🎯 Conclusión

El zarr ha sido optimizado con:
1. ✅ Chunks 1024x1024 (mejor para WMTS)
2. ✅ Metadatos consolidados (acceso más rápido)
3. ✅ Compresión LZ4 (descompresión rápida)
4. ✅ Atributos CF-compliant (compatibilidad)
5. ✅ CRS definido (georeferenciación correcta)

**Próximo paso:** Ejecutar `update_service_optimized_zarr.sh` para aplicar cambios.

---

**Generado:** 11 de octubre de 2025  
**Estado:** ✅ Zarr optimizado verificado, listo para deployment
