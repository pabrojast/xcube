#!/bin/bash
# Script para diagnosticar el problema de tiles en blanco

echo "==================================================================="
echo "Diagnóstico de WMTS - Ukraine LWQ Dataset"
echo "==================================================================="

BASE_URL="https://data.dev-wins.com/xcube"

echo ""
echo "1. Verificando información del dataset..."
curl -s "${BASE_URL}/datasets/ukraine_lwq" | jq '{
  dimensions: .dimensions,
  variables: (.variables | keys),
  spatial_ref: .spatial_ref,
  bbox: .bbox
}' || echo "Error al obtener info del dataset"

echo ""
echo "2. Verificando variable Rw1610_rep..."
curl -s "${BASE_URL}/datasets/ukraine_lwq/vars/Rw1610_rep" | jq '{
  dims: .dims,
  shape: .shape,
  attrs: .attrs,
  data_type: .data_type
}' || echo "Error al obtener info de la variable"

echo ""
echo "3. Probando tiles en diferentes niveles de zoom..."
for zoom in 3 5 7 10; do
  echo ""
  echo "   Zoom level $zoom:"
  
  # Calcular coordenadas del tile central de Ukraine (aproximadamente)
  # Ukraine está alrededor de lat=49, lon=32
  
  case $zoom in
    3)  x=4; y=2 ;;  # Zoom 3 - vista continental
    5)  x=18; y=10 ;; # Zoom 5 - vista regional  
    7)  x=72; y=42 ;; # Zoom 7 - vista país
    10) x=577; y=336 ;; # Zoom 10 - vista local (tu ejemplo)
  esac
  
  TILE_URL="${BASE_URL}/wmts/1.0.0/tile/ukraine_lwq/Rw1610_rep/WorldCRS84Quad/${zoom}/${y}/${x}.png"
  
  # Descargar tile y verificar tamaño
  TEMP_FILE="/tmp/tile_${zoom}_${y}_${x}.png"
  HTTP_CODE=$(curl -s -o "$TEMP_FILE" -w "%{http_code}" "$TILE_URL")
  FILE_SIZE=$(stat -f%z "$TEMP_FILE" 2>/dev/null || stat -c%s "$TEMP_FILE" 2>/dev/null || echo "0")
  
  echo "   HTTP: $HTTP_CODE | Size: $FILE_SIZE bytes | URL: $TILE_URL"
  
  # Si el archivo es muy pequeño (< 1KB), probablemente está en blanco
  if [ "$FILE_SIZE" -lt 1000 ]; then
    echo "   ⚠️  ADVERTENCIA: Tile muy pequeño, probablemente en blanco"
  else
    echo "   ✓ Tile tiene datos"
  fi
done

echo ""
echo "4. Verificando capabilities WMTS..."
curl -s "${BASE_URL}/wmts/1.0.0/WMTSCapabilities.xml" | grep -A5 "ukraine_lwq" | head -20

echo ""
echo "5. Probando con turbidity_mean (puede tener más datos)..."
TURB_URL="${BASE_URL}/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/5/18/10.png"
TEMP_FILE="/tmp/tile_turbidity.png"
HTTP_CODE=$(curl -s -o "$TEMP_FILE" -w "%{http_code}" "$TURB_URL")
FILE_SIZE=$(stat -f%z "$TEMP_FILE" 2>/dev/null || stat -c%s "$TEMP_FILE" 2>/dev/null || echo "0")
echo "   HTTP: $HTTP_CODE | Size: $FILE_SIZE bytes"
echo "   URL: $TURB_URL"

echo ""
echo "==================================================================="
echo "Diagnóstico completado"
echo "==================================================================="
