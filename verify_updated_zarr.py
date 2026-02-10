#!/usr/bin/env python3
"""
Script para verificar la nueva estructura del Zarr actualizado
"""

import xarray as xr
import zarr
import fsspec
import numpy as np

# Configuración de Azure
AZURE_ACCOUNT_NAME = "ihpwinsdata"
AZURE_ACCOUNT_KEY = "<AZURE_STORAGE_ACCOUNT_KEY>"

print("=" * 70)
print("🔍 VERIFICANDO ZARR ACTUALIZADO PARA WMTS")
print("=" * 70)
print()

# Abrir con zarr directo
print("1️⃣ Conectando a Azure Blob Storage...")
storage_options = {
    'account_name': AZURE_ACCOUNT_NAME,
    'account_key': AZURE_ACCOUNT_KEY
}

zarr_path = "data/xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr"
store = fsspec.get_mapper(f"abfs://{zarr_path}", **storage_options)
root = zarr.open(store, mode='r')
print(f"   ✅ Zarr abierto: {zarr_path}")
print()

# Verificar metadatos consolidados
print("2️⃣ Verificando metadatos consolidados...")
if '.zmetadata' in store:
    meta_size = len(store['.zmetadata'])
    print(f"   ✅ Metadatos consolidados: {meta_size:,} bytes")
else:
    print(f"   ⚠️  NO consolidados")
print()

# Verificar estructura de chunks
print("3️⃣ Verificando estructura de chunks...")
print()

variables = ['turbidity_mean', 'Rw490_rep', 'Rw1610_rep']
for var_name in variables:
    if var_name in root:
        var = root[var_name]
        print(f"   📊 {var_name}:")
        print(f"      - Shape: {var.shape}")
        print(f"      - Chunks: {var.chunks}")
        print(f"      - Dtype: {var.dtype}")
        print(f"      - Compressor: {var.compressor}")
        
        # Calcular tamaño óptimo de chunks para WMTS
        if len(var.shape) == 3:  # (time, lat, lon)
            time_chunk, lat_chunk, lon_chunk = var.chunks
            print(f"      - Time chunk: {time_chunk}")
            print(f"      - Spatial chunks: {lat_chunk} x {lon_chunk}")
            
            # Verificar si es óptimo para WMTS (512 o 1024)
            if lat_chunk in [512, 1024] and lon_chunk in [512, 1024]:
                print(f"      ✅ Chunks óptimos para WMTS")
            else:
                print(f"      ⚠️  Chunks no óptimos (recomendado: 512 o 1024)")
        print()

# Verificar coordenadas
print("4️⃣ Verificando coordenadas...")
for coord_name in ['time', 'lat', 'lon']:
    if coord_name in root:
        coord = root[coord_name]
        print(f"   📍 {coord_name}:")
        print(f"      - Shape: {coord.shape}")
        print(f"      - Dtype: {coord.dtype}")
        print(f"      - Chunks: {coord.chunks}")
        
        if coord_name == 'time':
            # Mostrar algunos valores
            time_data = coord[:]
            print(f"      - Primeros 3: {time_data[:3]}")
            print(f"      - Últimos 3: {time_data[-3:]}")
        else:
            data = coord[:]
            print(f"      - Rango: [{data[0]:.4f}, {data[-1]:.4f}]")
print()

# Abrir con xarray para verificar
print("5️⃣ Abriendo con xarray...")
zarr_url = "abfs://data/xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr"
ds = xr.open_zarr(fsspec.get_mapper(zarr_url, **storage_options), consolidated=True)
print(f"   ✅ Dataset abierto con xarray")
print(f"   📊 Variables: {len(ds.data_vars)}")
print(f"   📍 Coordenadas: {list(ds.coords.keys())}")
print(f"   📏 Dimensiones: {dict(ds.dims)}")
print()

# Verificar atributos importantes para xcube
print("6️⃣ Verificando atributos para xcube...")
print()

# Atributos de coordenadas
for coord in ['lat', 'lon']:
    if coord in ds:
        print(f"   {coord} attributes:")
        for attr_name in ['standard_name', 'units', 'long_name']:
            if attr_name in ds[coord].attrs:
                print(f"      - {attr_name}: {ds[coord].attrs[attr_name]}")
            else:
                print(f"      ⚠️  Missing: {attr_name}")
        print()

# Verificar CRS
if 'crs' in ds or 'spatial_ref' in ds:
    print(f"   ✅ CRS/spatial_ref presente")
else:
    print(f"   ℹ️  CRS no definido (xcube asumirá EPSG:4326)")
print()

# Probar lectura de una muestra de datos
print("7️⃣ Verificando lectura de datos...")
try:
    # Leer una pequeña región del primer timestamp
    sample = ds['turbidity_mean'].isel(time=0, lat=slice(0, 100), lon=slice(0, 100))
    sample_values = sample.values
    valid_count = np.sum(~np.isnan(sample_values))
    
    print(f"   📊 Muestra (100x100 pixels, tiempo=0):")
    print(f"      - Pixels válidos: {valid_count} / {sample.size}")
    
    if valid_count > 0:
        valid_data = sample_values[~np.isnan(sample_values)]
        print(f"      - Rango: [{np.min(valid_data):.4f}, {np.max(valid_data):.4f}]")
        print(f"      ✅ Datos accesibles")
    else:
        print(f"      ℹ️  Esta región no tiene datos (normal si son lagos dispersos)")
except Exception as e:
    print(f"   ❌ Error leyendo datos: {e}")

print()
print("=" * 70)
print("✅ VERIFICACIÓN COMPLETADA")
print("=" * 70)
print()

# Generar recomendaciones
print("💡 CONFIGURACIÓN RECOMENDADA PARA XCUBE:")
print()
print("   BoundingBox actual del dataset:")
print(f"   - Lat: [{float(ds.lat.min()):.4f}, {float(ds.lat.max()):.4f}]")
print(f"   - Lon: [{float(ds.lon.min()):.4f}, {float(ds.lon.max()):.4f}]")
print()
print("   Chunks actuales:")
for var_name in ['turbidity_mean', 'Rw490_rep']:
    if var_name in ds:
        chunks = ds[var_name].chunks
        print(f"   - {var_name}: time={chunks[0][0]}, lat={chunks[1][0]}, lon={chunks[2][0]}")
print()
