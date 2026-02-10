#!/usr/bin/env python3
"""
Estrategias para mejorar visualización en zoom alto (8+)
con datos dispersos (solo 0.12% de pixels válidos)
"""

import xarray as xr
import numpy as np
import fsspec

# Configuración de Azure
AZURE_ACCOUNT_NAME = "ihpwinsdata"
AZURE_ACCOUNT_KEY = "<AZURE_STORAGE_ACCOUNT_KEY>"

print("=" * 70)
print("🔍 ESTRATEGIAS PARA MEJORAR VISUALIZACIÓN EN ZOOM ALTO")
print("=" * 70)
print()

# Abrir dataset
print("1️⃣ Abriendo dataset...")
storage_options = {
    'account_name': AZURE_ACCOUNT_NAME,
    'account_key': AZURE_ACCOUNT_KEY
}

zarr_url = "abfs://data/xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr"
ds = xr.open_zarr(fsspec.get_mapper(zarr_url, **storage_options), consolidated=True)
print("   ✅ Dataset abierto")
print()

print("2️⃣ Analizando distribución espacial de datos...")
# Cargar primer timestamp
var = ds['turbidity_mean'].isel(time=0)
data = var.values

# Crear máscara de datos válidos
valid_mask = ~np.isnan(data)
print(f"   Total pixels: {data.size:,}")
print(f"   Pixels válidos: {np.sum(valid_mask):,} ({100*np.sum(valid_mask)/data.size:.4f}%)")
print()

print("=" * 70)
print("💡 ESTRATEGIAS POSIBLES")
print("=" * 70)
print()

print("ESTRATEGIA 1: Interpolación Espacial")
print("-" * 70)
print("   Llenar áreas sin datos con interpolación de vecinos cercanos")
print()
print("   Ventajas:")
print("   ✅ Tiles con datos en zoom alto")
print("   ✅ Transiciones suaves entre lagos")
print("   ✅ Mejor visualización continua")
print()
print("   Desventajas:")
print("   ❌ Datos 'inventados' (no reales)")
print("   ❌ Puede confundir interpretación")
print("   ❌ Requiere reprocesar el zarr")
print()
print("   Implementación:")
print("   ds_interp = ds.interpolate_na(dim='lon', method='nearest')")
print("   ds_interp = ds_interp.interpolate_na(dim='lat', method='nearest')")
print()

print("ESTRATEGIA 2: Rasterización con Buffer")
print("-" * 70)
print("   Expandir pixels de lagos con un buffer visual")
print()
print("   Ventajas:")
print("   ✅ Lagos más visibles en zoom alto")
print("   ✅ No inventa valores, solo amplía pixels existentes")
print()
print("   Desventajas:")
print("   ❌ Lagos parecen más grandes de lo que son")
print("   ❌ Requiere reprocesar")
print()
print("   Implementación:")
print("   from scipy.ndimage import maximum_filter")
print("   expanded = maximum_filter(data, size=3)  # Buffer de 3 pixels")
print()

print("ESTRATEGIA 3: Tiles con Opacidad Variable")
print("-" * 70)
print("   Usar transparencia en áreas sin datos")
print()
print("   Ventajas:")
print("   ✅ Se ve el mapa base bajo los tiles")
print("   ✅ No confunde - transparente = sin datos")
print("   ✅ No requiere reprocesar zarr")
print()
print("   Desventajas:")
print("   ⚠️  Requiere configurar ColorMappings")
print()
print("   Implementación en xcube config:")
print("   ColorMappings:")
print("     turbidity_mean:")
print("       ColorBar: 'viridis'")
print("       ValueRange: [0, 100]")
print("       Opacity: 0.8  # Transparencia")
print()

print("ESTRATEGIA 4: Limitar Zoom en WMTS Capabilities (servidor)")
print("-" * 70)
print("   Configurar MaxZoom a nivel de servidor web")
print()
print("   Ventajas:")
print("   ✅ Evita generar tiles innecesarios")
print("   ✅ WMTS Capabilities refleja el límite")
print()
print("   Desventajas:")
print("   ❌ xcube no soporta MaxLevel nativamente")
print("   ❌ Requeriría modificar código de xcube")
print()
print("   Alternativa NGINX:")
print("   location ~ /tile/.*/[8-9]/ { return 404; }  # Bloquear zoom 8+")
print()

print("ESTRATEGIA 5: Tiles Vectoriales (ideal pero complejo)")
print("-" * 70)
print("   Convertir lagos a vectores (polígonos)")
print()
print("   Ventajas:")
print("   ✅ Lagos visibles en cualquier zoom")
print("   ✅ Renderizado nítido sin importar escala")
print("   ✅ Más eficiente para datos dispersos")
print()
print("   Desventajas:")
print("   ❌ Requiere stack tecnológico diferente")
print("   ❌ No usa WMTS raster")
print("   ❌ Necesita tile server vectorial (MapBox, etc)")
print()

print()
print("=" * 70)
print("🎯 RECOMENDACIÓN PARA ESTE CASO")
print("=" * 70)
print()
print("Dado que:")
print("   • Solo 0.12% de pixels tienen datos")
print("   • Los lagos son entidades discretas (no continuas)")
print("   • Zoom 6-7 ya funciona bien")
print()
print("MEJOR OPCIÓN: Estrategia 3 + 4 (Transparencia + Limitar Zoom)")
print()
print("Implementación práctica:")
print("   1. Configurar opacidad en ColorMappings (ya funciona)")
print("   2. Limitar zoom en el visor HTML (maxZoom: 7)")
print("   3. Opcionalmente: bloquear zoom 8+ en NGINX Ingress")
print()
print("ALTERNATIVA si quieres zoom alto:")
print("   Estrategia 2 (Buffer) + Reprocesar zarr")
print("   - Expandir cada pixel de lago 2-3 pixels")
print("   - Lagos serán más visibles en zoom alto")
print("   - Mantiene valores reales, solo amplifica visualmente")
print()

print("=" * 70)
print("💻 ¿QUIERES QUE IMPLEMENTE ALGUNA ESTRATEGIA?")
print("=" * 70)
print()
print("Opciones:")
print("   A) Configurar opacidad en ColorMappings (rápido, sin reprocesar)")
print("   B) Crear script para aplicar buffer y reprocesar zarr (más trabajo)")
print("   C) Configurar NGINX para bloquear zoom 8+ (intermedio)")
print("   D) Solo limitar en visor HTML (ya hecho)")
print()
