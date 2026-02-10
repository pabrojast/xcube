#!/bin/bash

# ============================================================================
# Script para probar WMTS tiles en la región con datos válidos
# Región: Sur de Ucrania (44-45°N, 28-30°E) donde hay lagos
# ============================================================================

echo "========================================================================"
echo "🧪 PROBANDO WMTS TILES EN LA REGIÓN CORRECTA (SUR DE UCRANIA)"
echo "========================================================================"
echo ""

BASE_URL="https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq"

# Región con datos: [44.14-45.12°N, 28.70-29.67°E]
# Centro: [44.628°N, 29.184°E]

# Para WorldCRS84Quad:
# Zoom 9: cada tile = 0.703125°
# Zoom 10: cada tile = 0.3515625°
# Zoom 11: cada tile = 0.17578125°

echo "1️⃣ Calculando tiles para la región con lagos..."
echo ""

# Centro: lat=44.628, lon=29.184
# 
# Zoom 10 (recomendado para lagos):
# tile_x = (lon + 180) / 0.3515625 = (29.184 + 180) / 0.3515625 ≈ 595
# tile_y = (90 - lat) / 0.3515625 = (90 - 44.628) / 0.3515625 ≈ 129

echo "📍 Centro de la región: lat=44.628°N, lon=29.184°E"
echo ""
echo "2️⃣ Probando tiles en zoom 10 (mejor resolución para lagos)..."
echo ""

# Tiles alrededor del centro
for y in 128 129 130; do
  for x in 594 595 596; do
    URL="${BASE_URL}/turbidity_mean/WorldCRS84Quad/10/$y/$x.png"
    RESPONSE=$(curl -s -w "\n%{http_code}\n%{size_download}" "$URL" -o "/tmp/tile_z10_y${y}_x${x}.png")
    HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
    SIZE=$(echo "$RESPONSE" | tail -1)
    
    if [ $SIZE -gt 1000 ]; then
      echo "   ✅ Tile Z=10, Y=$y, X=$x: $SIZE bytes - CON DATOS!"
      file "/tmp/tile_z10_y${y}_x${x}.png"
    elif [ $HTTP_CODE -eq 200 ]; then
      echo "   ⚪ Tile Z=10, Y=$y, X=$x: $SIZE bytes - vacío (sin lagos en este tile)"
    else
      echo "   ❌ Tile Z=10, Y=$y, X=$x: HTTP $HTTP_CODE"
    fi
  done
done

echo ""
echo "3️⃣ Probando tiles en zoom 9 (vista más amplia)..."
echo ""

# Zoom 9: tile_x ≈ 297, tile_y ≈ 64
for y in 63 64 65; do
  for x in 296 297 298; do
    URL="${BASE_URL}/turbidity_mean/WorldCRS84Quad/9/$y/$x.png"
    RESPONSE=$(curl -s -w "\n%{http_code}\n%{size_download}" "$URL" -o "/tmp/tile_z9_y${y}_x${x}.png")
    HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
    SIZE=$(echo "$RESPONSE" | tail -1)
    
    if [ $SIZE -gt 1000 ]; then
      echo "   ✅ Tile Z=9, Y=$y, X=$x: $SIZE bytes - CON DATOS!"
    elif [ $HTTP_CODE -eq 200 ]; then
      echo "   ⚪ Tile Z=9, Y=$y, X=$x: $SIZE bytes - vacío"
    else
      echo "   ❌ Tile Z=9, Y=$y, X=$x: HTTP $HTTP_CODE"
    fi
  done
done

echo ""
echo "4️⃣ Probando con otras variables..."
echo ""

# Probar Rw1610_rep en el centro
URL="${BASE_URL}/Rw1610_rep/WorldCRS84Quad/10/129/595.png"
RESPONSE=$(curl -s -w "\n%{http_code}\n%{size_download}" "$URL" -o "/tmp/tile_rw1610_center.png")
HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
SIZE=$(echo "$RESPONSE" | tail -1)

echo "   Variable Rw1610_rep (Z=10, Y=129, X=595):"
if [ $SIZE -gt 1000 ]; then
  echo "   ✅ $SIZE bytes - CON DATOS!"
  file "/tmp/tile_rw1610_center.png"
else
  echo "   ⚪ $SIZE bytes - vacío"
fi

echo ""
echo "========================================================================"
echo "✅ PRUEBA COMPLETADA"
echo "========================================================================"
echo ""
echo "💡 INTERPRETACIÓN DE RESULTADOS:"
echo ""
echo "   - Tiles > 1KB: Contienen datos de lagos (PNG con colores)"
echo "   - Tiles = 334 bytes: Sin lagos en esa área (PNG vacío/blanco)"
echo "   - HTTP 502/503: Servicio temporalmente no disponible"
echo ""
echo "   Los tiles 'vacíos' son NORMALES - significan que no hay lagos"
echo "   en esa coordenada específica. Los lagos están dispersos."
echo ""
echo "📂 Tiles guardados en /tmp/tile_*.png"
echo ""
echo "🗺️  Para visualizar en navegador:"
echo "   1. Abrir: ukraine_lwq_viewer_production.html"
echo "   2. O URL: https://data.dev-wins.com/xcube/"
echo "   3. Centrado en: [44.628°N, 29.184°E] zoom 9"
echo ""
