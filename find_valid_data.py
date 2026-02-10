#!/usr/bin/env python3
"""
Script para encontrar dónde están los datos válidos en el dataset
"""

import xarray as xr
import numpy as np
import fsspec

# Configuración de Azure
AZURE_ACCOUNT_NAME = "ihpwinsdata"
AZURE_ACCOUNT_KEY = "<AZURE_STORAGE_ACCOUNT_KEY>"

print("=" * 70)
print("🔍 BUSCANDO PIXELS VÁLIDOS EN EL DATASET")
print("=" * 70)
print()

# Abrir dataset
print("1️⃣ Abriendo dataset desde Azure...")
storage_options = {
    'account_name': AZURE_ACCOUNT_NAME,
    'account_key': AZURE_ACCOUNT_KEY
}

zarr_url = "abfs://data/xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr"
ds = xr.open_zarr(fsspec.get_mapper(zarr_url, **storage_options), consolidated=True)
print("   ✅ Dataset abierto")
print(f"   Shape: time={len(ds.time)}, lat={len(ds.lat)}, lon={len(ds.lon)}")
print()

# Buscar datos válidos en el primer timestamp
print("2️⃣ Buscando pixels válidos en turbidity_mean (primer timestamp)...")
var = ds['turbidity_mean'].isel(time=0)

# Buscar en chunks para no cargar todo en memoria
print("   Buscando en diferentes regiones...")

regions = [
    ("Noroeste", slice(0, 2000), slice(0, 5000)),
    ("Noreste", slice(0, 2000), slice(15000, 20595)),
    ("Centro-Oeste", slice(4000, 6000), slice(0, 5000)),
    ("Centro", slice(4000, 6000), slice(10000, 15000)),
    ("Centro-Este", slice(4000, 6000), slice(15000, 20595)),
    ("Suroeste", slice(7000, 9462), slice(0, 5000)),
    ("Sureste", slice(7000, 9462), slice(15000, 20595)),
]

valid_regions = []

for region_name, lat_slice, lon_slice in regions:
    sample = var.isel(lat=lat_slice, lon=lon_slice)
    valid_count = np.sum(~np.isnan(sample.values))
    total = sample.size
    
    if valid_count > 0:
        coverage = 100 * valid_count / total
        print(f"   ✅ {region_name}: {valid_count:,}/{total:,} pixels válidos ({coverage:.2f}%)")
        
        # Encontrar coordenadas de un pixel válido
        valid_mask = ~np.isnan(sample.values)
        if np.any(valid_mask):
            lat_idx, lon_idx = np.where(valid_mask)
            first_lat_idx = lat_slice.start + lat_idx[0]
            first_lon_idx = lon_slice.start + lon_idx[0]
            
            lat_val = ds.lat.isel(lat=first_lat_idx).values
            lon_val = ds.lon.isel(lon=first_lon_idx).values
            data_val = var.isel(lat=first_lat_idx, lon=first_lon_idx).values
            
            print(f"      📍 Ejemplo: lat={lat_val:.4f}, lon={lon_val:.4f}, valor={data_val:.4f}")
            valid_regions.append((region_name, lat_val, lon_val, lat_idx[0], lon_idx[0]))
    else:
        print(f"   ❌ {region_name}: 0 pixels válidos")

print()
print("3️⃣ Estadísticas globales...")

# Cargar todo el primer timestamp (puede tardar)
print("   Cargando datos completos del primer timestamp...")
try:
    all_data = var.values
    valid_total = np.sum(~np.isnan(all_data))
    total_pixels = all_data.size
    coverage = 100 * valid_total / total_pixels
    
    print(f"   Total pixels válidos: {valid_total:,} / {total_pixels:,} ({coverage:.4f}%)")
    
    if valid_total > 0:
        valid_values = all_data[~np.isnan(all_data)]
        print(f"   Rango de valores: [{np.min(valid_values):.4f}, {np.max(valid_values):.4f}]")
        print(f"   Media: {np.mean(valid_values):.4f}")
except Exception as e:
    print(f"   ⚠️  Error cargando datos completos: {e}")

print()
print("=" * 70)
print("✅ BÚSQUEDA COMPLETADA")
print("=" * 70)
print()

if valid_regions:
    print("💡 REGIONES CON DATOS VÁLIDOS:")
    print()
    for region_name, lat, lon, _, _ in valid_regions:
        print(f"   - {region_name}: lat={lat:.4f}°, lon={lon:.4f}°")
    print()
    print("   Para probar WMTS, usa estas coordenadas en tu visor")
else:
    print("⚠️  NO SE ENCONTRARON PIXELS VÁLIDOS")
    print("   Posibles causas:")
    print("   1. El dataset solo contiene NaN/valores nulos")
    print("   2. Problema en el proceso de generación del zarr")
    print("   3. Los datos están enmascarados incorrectamente")
print()
