# 🎯 Configuración de Límites de Zoom en WMTS

## Problema

Los tiles WMTS en zoom 8+ estaban vacíos (334 bytes) porque:
- Los lagos son muy pequeños y dispersos
- Solo ocupan 0.12% del área total
- En zooms altos, los tiles caen en áreas sin lagos

## Solución: Limitar MaxLevel

### 1. Configuración en xcube

**Archivo**: `k8s/02-configmap.yaml` y `xcube_ukraine_config.yml`

```yaml
Datasets:
  - Identifier: ukraine_lwq
    Title: "Ukraine Lake Water Quality - LWQ100 MSI"
    
    # Tile Grid Configuration - limit zoom levels
    TileGrid:
      TileMatrixSet: "WorldCRS84Quad"
      MinLevel: 0    # Zoom mínimo (vista mundial)
      MaxLevel: 7    # Zoom máximo (datos visibles)
```

**Resultado:**
- ✅ Tiles generados solo en zoom 0-7
- ✅ Zoom 8+ no genera tiles (evita tiles vacíos)
- ✅ WMTS Capabilities refleja los límites
- ✅ Clientes WMTS respetan MaxLevel

### 2. Configuración en el Visor HTML

**Archivo**: `ukraine_lwq_viewer_production.html`

```javascript
const CONFIG = {
    defaultZoom: 7,
    minZoom: 0,
    maxZoom: 7,  // Limitar zoom del visor
    // ...
};

// Inicializar mapa con límites
map = L.map('map', {
    minZoom: CONFIG.minZoom,
    maxZoom: CONFIG.maxZoom
}).setView(CONFIG.defaultCenter, CONFIG.defaultZoom);

// Mostrar mensaje al alcanzar zoom máximo
map.on('zoomend', function() {
    if (map.getZoom() >= CONFIG.maxZoom) {
        showInfo('ℹ️ Zoom máximo alcanzado. Datos de lagos visibles hasta zoom 7.');
    }
});
```

**Resultado:**
- ✅ Usuario no puede hacer zoom más allá de 7
- ✅ Mensaje informativo al alcanzar límite
- ✅ Mejor experiencia de usuario (no ve tiles vacíos)

## 🎯 Niveles de Zoom y Cobertura

### WorldCRS84Quad Tile Matrix Set

| Zoom | Resolución | Cobertura por Tile | Estado |
|------|-----------|-------------------|--------|
| 0 | ~180° | Mundo completo | ⚪ Datos muy pequeños |
| 1 | ~90° | Hemisferio | ⚪ Datos muy pequeños |
| 2 | ~45° | Continente | ⚪ Datos dispersos |
| 3 | ~22.5° | País grande | ⚪ Datos dispersos |
| 4 | ~11.25° | País | ⚪ Algunos datos |
| 5 | ~5.6° | Región | ✅ Lagos pequeños visibles |
| 6 | ~2.8° | Región | ✅ Lagos visibles (2909 bytes) |
| 7 | ~1.4° | Subregión | ✅ Lagos claros (5757 bytes) |
| 8 | ~0.7° | Local | ❌ Tiles vacíos (852 bytes) |
| 9+ | < 0.35° | Muy local | ❌ Tiles vacíos (334 bytes) |

### Por qué Zoom 6-7 funcionan

**Zoom 6:** Cada tile cubre ~2.8° x 2.8°
- Área grande → captura múltiples lagos
- Lagos dispersos se agrupan visualmente
- Resultado: PNG con datos (~2-3 KB)

**Zoom 7:** Cada tile cubre ~1.4° x 1.4°
- Balance perfecto entre detalle y cobertura
- Lagos individuales visibles
- Resultado: PNG con datos (~5-6 KB)

**Zoom 8+:** Cada tile cubre < 0.7° x 0.7°
- Área muy pequeña
- Probabilidad alta de caer entre lagos
- Resultado: PNG vacío (334 bytes)

## 🚀 Aplicar Configuración

### Script Automatizado

```bash
chmod +x /home/pabrojast/Proyectos/xcube/apply_zoom_limits.sh
./apply_zoom_limits.sh
```

El script:
1. ✅ Aplica ConfigMap con TileGrid (MaxLevel: 7)
2. ✅ Reinicia deployment
3. ✅ Verifica estado de pods
4. ✅ Muestra comandos de prueba

### Verificación Manual

**1. Probar zoom 7 (debe funcionar):**
```bash
curl -I "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/7/32/148.png"
# Esperado: HTTP 200, Content-Length > 1000
```

**2. Probar zoom 8 (debe fallar o retornar error):**
```bash
curl -I "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/8/64/296.png"
# Esperado: HTTP 404 o 400 (fuera de rango)
```

**3. Verificar WMTS Capabilities:**
```bash
curl -s "https://data.dev-wins.com/xcube/wmts/1.0.0/WMTSCapabilities.xml" | \
  grep -A 10 "TileMatrixSetLimits" | head -20
```

Debe mostrar:
```xml
<TileMatrixSetLimits>
  <TileMatrixLimits>
    <TileMatrix>0</TileMatrix>
    ...
  </TileMatrixLimits>
  <TileMatrixLimits>
    <TileMatrix>7</TileMatrix>
    <!-- No debe haber TileMatrix 8+ -->
  </TileMatrixLimits>
</TileMatrixSetLimits>
```

## 🎨 Experiencia de Usuario

### Antes (Sin límites)
```
Usuario hace zoom → Zoom 8, 9, 10... → Tiles vacíos
❌ Confusión: "¿Por qué no veo nada?"
❌ Desperdicio: Genera tiles que nadie usa
❌ Carga innecesaria: Servidor procesa tiles vacíos
```

### Después (Con MaxLevel: 7)
```
Usuario hace zoom → Zoom 7 → Límite alcanzado
✅ Mensaje claro: "Zoom máximo alcanzado"
✅ Solo tiles útiles: Zoom 0-7 con datos
✅ Mejor rendimiento: No procesa tiles innecesarios
```

## 📊 Beneficios

### Rendimiento
- ✅ **Menos procesamiento**: No genera tiles vacíos en zoom 8+
- ✅ **Menos almacenamiento**: Cache solo tiles útiles
- ✅ **Respuestas rápidas**: Rechazo inmediato en zoom fuera de rango

### Experiencia de Usuario
- ✅ **Expectativas claras**: Usuario sabe el límite
- ✅ **Sin confusión**: No ve tiles vacíos
- ✅ **Feedback inmediato**: Mensaje al alcanzar límite

### Mantenimiento
- ✅ **Configuración clara**: MaxLevel documentado
- ✅ **Fácil ajuste**: Cambiar MaxLevel si datos mejoran
- ✅ **Monitoreo simple**: Solo verificar zoom 0-7

## 🔧 Ajustes Futuros

### Si se añaden más datos

Si el dataset se mejora con más lagos o mayor densidad:

```yaml
# Aumentar MaxLevel si zoom 8 tiene suficientes datos
TileGrid:
  TileMatrixSet: "WorldCRS84Quad"
  MinLevel: 0
  MaxLevel: 8  # o 9, según cobertura
```

### Si se optimiza el mapa base

Para diferentes resoluciones de datos:

```yaml
# Ejemplo: Datos de alta resolución
TileGrid:
  TileMatrixSet: "WorldCRS84Quad"
  MinLevel: 4  # Empezar en zoom 4
  MaxLevel: 12  # Permitir mucho zoom
```

## 📝 Referencias

### Documentación xcube
- [Dataset Configuration](https://xcube.readthedocs.io/en/latest/)
- [TileGrid Parameters](https://github.com/dcs4cop/xcube)

### WMTS Specification
- [OGC WMTS 1.0.0](https://www.ogc.org/standards/wmts)
- [TileMatrixSet Definitions](https://docs.opengeospatial.org/is/17-083r2/17-083r2.html)

## ✅ Checklist

Después de aplicar la configuración:

- [ ] ConfigMap actualizado con TileGrid
- [ ] Deployment reiniciado
- [ ] Pods en estado Running
- [ ] Zoom 7 retorna tiles con datos (> 1KB)
- [ ] Zoom 8 retorna error o 404
- [ ] WMTS Capabilities muestra MaxLevel: 7
- [ ] Visor HTML no permite zoom > 7
- [ ] Mensaje informativo aparece al alcanzar límite

---

**Actualizado:** 11 de octubre de 2025  
**Estado:** ✅ Configuración lista para aplicar
