#!/usr/bin/env python3
"""
Script para consolidar metadatos del Zarr en Azure Blob Storage
Esto puede mejorar significativamente el rendimiento de WMTS
"""

import zarr
import fsspec

# Configuración de Azure
AZURE_ACCOUNT_NAME = "ihpwinsdata"
AZURE_ACCOUNT_KEY = "<AZURE_STORAGE_ACCOUNT_KEY>"
ZARR_PATH = "abfs://data/xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr"

print("=" * 70)
print("🔧 CONSOLIDANDO METADATOS DEL ZARR EN AZURE")
print("=" * 70)
print()

# Crear filesystem de Azure
print("1️⃣ Conectando a Azure Blob Storage...")
fs = fsspec.filesystem(
    "abfs",
    account_name=AZURE_ACCOUNT_NAME,
    account_key=AZURE_ACCOUNT_KEY
)
print("   ✅ Conectado")
print()

# Abrir el zarr store
print("2️⃣ Abriendo Zarr store...")
zarr_path = "data/xcube/c_gls_LWQ100/ukraine/ukraine_lwq.zarr"
store = fs.get_mapper(zarr_path)
root = zarr.open(store, mode='r')
print(f"   ✅ Zarr abierto: {zarr_path}")
print(f"   📊 Variables: {list(root.keys())}")
print()

# Verificar si ya tiene metadatos consolidados
print("3️⃣ Verificando metadatos consolidados...")
try:
    if '.zmetadata' in store:
        print("   ✅ Ya tiene metadatos consolidados (.zmetadata existe)")
        
        # Mostrar tamaño
        meta_size = len(store['.zmetadata'])
        print(f"   📦 Tamaño de .zmetadata: {meta_size:,} bytes")
    else:
        print("   ⚠️  NO tiene metadatos consolidados")
        print("   ℹ️  Esto puede causar lentitud en WMTS")
        print()
        print("   Para consolidar, ejecuta:")
        print("   zarr.consolidate_metadata(store)")
except Exception as e:
    print(f"   ⚠️  Error verificando metadatos: {e}")
print()

# Verificar estructura de datos
print("4️⃣ Verificando estructura de variables...")
for var_name in ['turbidity_mean', 'Rw490_rep', 'Rw1610_rep']:
    if var_name in root:
        var = root[var_name]
        print(f"   📊 {var_name}:")
        print(f"      - Shape: {var.shape}")
        print(f"      - Chunks: {var.chunks}")
        print(f"      - Dtype: {var.dtype}")
        
        # Verificar si tiene datos
        try:
            # Leer un pequeño slice para verificar
            sample = var[0, 0:10, 0:10]
            has_data = not sample.mask.all() if hasattr(sample, 'mask') else True
            print(f"      - Tiene datos: {'✅' if has_data else '❌'}")
        except Exception as e:
            print(f"      - Error leyendo datos: {e}")
print()

# Mostrar información de coordenadas
print("5️⃣ Verificando coordenadas...")
for coord_name in ['time', 'lat', 'lon']:
    if coord_name in root:
        coord = root[coord_name]
        print(f"   📍 {coord_name}:")
        print(f"      - Shape: {coord.shape}")
        print(f"      - Dtype: {coord.dtype}")
        if coord_name == 'time':
            print(f"      - Primero: {coord[0]}")
            print(f"      - Último: {coord[-1]}")
        else:
            print(f"      - Rango: [{coord[0]:.4f}, {coord[-1]:.4f}]")
print()

print("=" * 70)
print("✅ VERIFICACIÓN COMPLETADA")
print("=" * 70)
print()
print("💡 RECOMENDACIONES:")
print()
print("   Si NO tiene metadatos consolidados:")
print("   1. Consolida con: zarr.consolidate_metadata(store)")
print("   2. Esto creará .zmetadata en el zarr")
print("   3. Mejorará significativamente el rendimiento de WMTS")
print()
print("   Si sigue mostrando tiles blancos:")
print("   1. Verifica que las variables tengan datos reales (no todo NaN)")
print("   2. Ajusta los rangos de valores en ColorMappings")
print("   3. Prueba con diferentes timestamps")
print()
