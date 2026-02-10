# Troubleshooting - Ukraine LWQ Service

## Warning: No data opener found for format 'zarr' and data type 'mldataset'

### Descripción del Warning

```
UserWarning: No data opener found for format 'zarr' and data type 'mldataset'. 
Data type is changed to the default data type 'dataset'.
```

### ¿Qué significa?

Este warning aparece cuando xcube intenta abrir el dataset como un **Multi-Level Dataset (mldataset)** pero el archivo Zarr no tiene la estructura piramidal necesaria para multi-nivel.

Un Multi-Level Dataset contiene múltiples versiones del mismo dataset a diferentes resoluciones (pirámide de resoluciones), similar a los tiles de un mapa web con diferentes niveles de zoom.

### ¿Es un problema?

**No, no es un problema crítico.** El dataset se abre correctamente como un `dataset` estándar y todas las funcionalidades funcionan:

- ✅ Acceso a variables
- ✅ Series temporales
- ✅ Tiles WMTS
- ✅ Visualización en el viewer

### ¿Cómo eliminarlo?

Hay dos opciones:

#### Opción 1: Ignorar el warning (Recomendado)

El warning es informativo y no afecta la funcionalidad. El dataset funciona perfectamente como está.

#### Opción 2: Crear un Multi-Level Dataset

Si deseas crear un dataset multi-nivel para mejorar el rendimiento de visualización a diferentes escalas:

```python
import xcube
from xcube.core.mldataset import MultiLevelDataset
from xcube.core.level import compute_levels

# Abrir dataset original
ds = xcube.core.store.new_data_store("abfs", 
    root="data",
    storage_options={
        "account_name": "ihpwinsdata",
        "account_key": "..."
    }
).open_data("xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr")

# Crear niveles de resolución
ml_ds = compute_levels(ds, num_levels=5)

# Guardar como multi-level dataset
xcube.core.mldataset.write_levels(
    ml_ds, 
    output_path="ukraine_lwq_multilevel.zarr",
    encoding={...}
)
```

#### Opción 3: Especificar explícitamente el formato

En `xcube_ukraine_config.yml`, puedes añadir:

```yaml
Datasets:
  - Identifier: ukraine_lwq
    # ... otras configuraciones ...
    FileSystem: zarr  # Especifica explícitamente el formato
```

Esto ayuda a xcube a identificar el formato más rápidamente, aunque el warning puede persistir.

## Otros Warnings Comunes

### "No CRS found in dataset"

Si ves este warning:
```
UserWarning: No CRS found in dataset, assuming WGS84
```

**Solución**: Añadir CRS explícitamente en la configuración:

```yaml
Datasets:
  - Identifier: ukraine_lwq
    Crs: "EPSG:4326"  # WGS84
```

### "Time coordinate has no standard name"

Si la coordenada temporal no está correctamente identificada:

**Solución**: Verificar que el dataset tenga el atributo `standard_name` en la dimensión temporal:

```python
import xarray as xr
ds = xr.open_zarr("...")
ds.time.attrs['standard_name'] = 'time'
```

## Verificación del Dataset

Para verificar que el dataset se está cargando correctamente:

```bash
# 1. Verificar que el dataset está disponible
curl http://localhost:8080/datasets

# 2. Obtener metadatos del dataset
curl http://localhost:8080/datasets/ukraine_lwq | python -m json.tool | head -50

# 3. Listar variables disponibles
curl http://localhost:8080/datasets/ukraine_lwq | python -c "import sys, json; d=json.load(sys.stdin); print('\\n'.join([v['name'] for v in d['variables']]))"

# 4. Verificar que las tiles se generan correctamente
curl -I "http://localhost:8080/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/7/42/67.png"

# 5. Probar series temporales
curl "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean?lat=50.45&lon=30.52" | python -m json.tool
```

## Logs de Diagnóstico

Para obtener más información sobre el proceso de carga:

```bash
# Iniciar servidor con logging detallado
export XCUBE_LOG_LEVEL="DEBUG"
./start_xcube_ukraine.sh
```

Los logs mostrarán:
- ✅ Escaneo del store de Azure
- ✅ Detección del dataset
- ✅ Apertura del archivo Zarr
- ✅ Identificación de variables y dimensiones
- ⚠️ Warnings (si los hay)

## Performance del Dataset

Si experimentas lentitud al cargar tiles o series temporales:

### Causas comunes:

1. **Chunking no óptimo**: Los chunks del Zarr no están optimizados para acceso espacial
2. **Falta de pirámide de resoluciones**: No hay multi-level dataset
3. **Latencia de red**: Azure Blob Storage está geográficamente distante

### Soluciones:

```python
# Re-chunk el dataset para acceso espacial óptimo
ds_rechunked = ds.chunk({
    'time': 1,
    'lat': 256,
    'lon': 256
})

# Crear Multi-Level Dataset para diferentes zoom levels
ml_ds = compute_levels(ds_rechunked, num_levels=5)

# Guardar optimizado
ml_ds.to_zarr("ukraine_lwq_optimized.zarr", 
              encoding={'Rw490_rep': {'compressor': zarr.Blosc(cname='zstd', clevel=3)}})
```

## Contacto y Soporte

Para más ayuda:
- 📖 [xcube Documentation](https://xcube.readthedocs.io/)
- 💬 [xcube GitHub Issues](https://github.com/dcs4cop/xcube/issues)
- 📧 Email de soporte del proyecto

---

**Última actualización**: 10 de octubre de 2025
