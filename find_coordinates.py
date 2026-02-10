#!/usr/bin/env python3
"""
Script para encontrar las coordenadas exactas de pixels con datos válidos
"""

import xarray as xr
import numpy as np
import fsspec

# Configuración de Azure
AZURE_ACCOUNT_NAME = "ihpwinsdata"
AZURE_ACCOUNT_KEY = "<AZURE_STORAGE_ACCOUNT_KEY>"

print("=" * 70)
print("📍 ENCONTRANDO COORDENADAS DE DATOS VÁLIDOS")
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

# Cargar primer timestamp
print("2️⃣ Cargando turbidity_mean (tiempo=0)...")
var = ds['turbidity_mean'].isel(time=0)
data = var.values
print("   ✅ Datos cargados")
print()

# Encontrar pixels válidos
print("3️⃣ Encontrando pixels válidos...")
valid_mask = ~np.isnan(data)
valid_count = np.sum(valid_mask)
print(f"   ✅ Encontrados {valid_count:,} pixels válidos")
print()

# Obtener coordenadas de algunos pixels válidos
lat_indices, lon_indices = np.where(valid_mask)

# Tomar muestras espaciadas
num_samples = min(20, len(lat_indices))
sample_indices = np.linspace(0, len(lat_indices)-1, num_samples, dtype=int)

print(f"4️⃣ Ejemplos de pixels con datos ({num_samples} muestras):")
print()
print(f"{'#':<4} {'Lat':<10} {'Lon':<10} {'Turbidity':<12} {'Lat_idx':<8} {'Lon_idx':<8}")
print("-" * 70)

coords_list = []
for i, idx in enumerate(sample_indices):
    lat_idx = lat_indices[idx]
    lon_idx = lon_indices[idx]
    
    lat_val = ds.lat.isel(lat=lat_idx).values
    lon_val = ds.lon.isel(lon=lon_idx).values
    data_val = data[lat_idx, lon_idx]
    
    print(f"{i+1:<4} {lat_val:>10.4f} {lon_val:>10.4f} {data_val:>12.4f} {lat_idx:<8} {lon_idx:<8}")
    coords_list.append((lat_val, lon_val, data_val))

print()
print("5️⃣ Calculando extent de datos válidos...")

# Encontrar bbox de datos válidos
valid_lats = ds.lat.isel(lat=lat_indices).values
valid_lons = ds.lon.isel(lon=lon_indices).values

bbox = {
    'lat_min': np.min(valid_lats),
    'lat_max': np.max(valid_lats),
    'lon_min': np.min(valid_lons),
    'lon_max': np.max(valid_lons),
}

print(f"   BoundingBox de datos válidos:")
print(f"   - Latitud: [{bbox['lat_min']:.4f}, {bbox['lat_max']:.4f}]")
print(f"   - Longitud: [{bbox['lon_min']:.4f}, {bbox['lon_max']:.4f}]")
print()

# Calcular el centro
center_lat = (bbox['lat_min'] + bbox['lat_max']) / 2
center_lon = (bbox['lon_min'] + bbox['lon_max']) / 2
print(f"   Centro: lat={center_lat:.4f}, lon={center_lon:.4f}")
print()

print("=" * 70)
print("✅ ANÁLISIS COMPLETADO")
print("=" * 70)
print()
print("💡 PARA VISUALIZAR EN UN MAPA:")
print()
print(f"   1. Centra el mapa en: [{center_lat:.4f}, {center_lon:.4f}]")
print(f"   2. Zoom inicial: nivel 6-8")
print(f"   3. BoundingBox: [[{bbox['lat_min']:.4f}, {bbox['lon_min']:.4f}], [{bbox['lat_max']:.4f}, {bbox['lon_max']:.4f}]]")
print()
print("   Ejemplos de coordenadas con datos:")
for i, (lat, lon, val) in enumerate(coords_list[:5]):
    print(f"   - [{lat:.4f}, {lon:.4f}] = {val:.2f}")
print()
