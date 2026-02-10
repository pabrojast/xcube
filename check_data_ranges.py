#!/usr/bin/env python3
"""
Script para verificar rangos reales de valores en el dataset
Esto nos ayudará a ajustar los ColorMappings
"""

import xarray as xr
import numpy as np
import fsspec

# Configuración de Azure
AZURE_ACCOUNT_NAME = "ihpwinsdata"
AZURE_ACCOUNT_KEY = "<AZURE_STORAGE_ACCOUNT_KEY>"

print("=" * 70)
print("📊 VERIFICANDO RANGOS DE VALORES EN EL DATASET")
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
print()

# Variables de interés
variables = ['turbidity_mean', 'Rw490_rep', 'Rw560_rep', 'Rw665_rep', 'Rw1610_rep', 'Rw2190_rep']

print("2️⃣ Calculando estadísticas por variable...")
print()

for var_name in variables:
    if var_name not in ds:
        print(f"   ⚠️  Variable {var_name} no encontrada")
        continue
    
    print(f"   📈 {var_name}:")
    var = ds[var_name]
    
    # Tomar un subset para acelerar el cálculo
    # Primer timestamp, región central
    sample = var.isel(time=0, lat=slice(4000, 5000), lon=slice(10000, 11000))
    
    try:
        # Calcular estadísticas ignorando NaN
        valid_data = sample.values[~np.isnan(sample.values)]
        
        if len(valid_data) > 0:
            print(f"      - Min: {np.min(valid_data):.6f}")
            print(f"      - Max: {np.max(valid_data):.6f}")
            print(f"      - Mean: {np.mean(valid_data):.6f}")
            print(f"      - Percentil 2%: {np.percentile(valid_data, 2):.6f}")
            print(f"      - Percentil 98%: {np.percentile(valid_data, 98):.6f}")
            print(f"      - Valores válidos: {len(valid_data):,} / {sample.size:,} ({100*len(valid_data)/sample.size:.1f}%)")
        else:
            print(f"      ⚠️  Sin datos válidos en la muestra")
    except Exception as e:
        print(f"      ⚠️  Error: {e}")
    
    print()

print("3️⃣ Verificando cobertura por timestamp...")
print()

# Verificar cuántos pixels válidos hay por timestamp
for time_idx in [0, 10, 20, 30, 38]:  # Muestra de timestamps
    time_val = ds.time.isel(time=time_idx).values
    
    # Tomar subset de turbidity_mean
    sample = ds['turbidity_mean'].isel(time=time_idx, lat=slice(4000, 5000), lon=slice(10000, 11000))
    valid_count = np.sum(~np.isnan(sample.values))
    total_count = sample.size
    coverage = 100 * valid_count / total_count
    
    print(f"   Time {time_idx} ({time_val}): {valid_count:,}/{total_count:,} pixels válidos ({coverage:.1f}%)")

print()
print("=" * 70)
print("✅ ANÁLISIS COMPLETADO")
print("=" * 70)
print()
print("💡 USA ESTOS RANGOS PARA ColorMappings:")
print("   Ajusta los ValueRange en la configuración de xcube")
print("   para que coincidan con los valores reales del dataset")
print()
