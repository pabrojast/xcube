#!/bin/bash
# Script para verificar las variables del dataset

echo "==================================================================="
echo "Verificando Variables del Dataset"
echo "==================================================================="

BASE_URL="https://data.dev-wins.com/xcube"

echo ""
echo "1. Listando todas las variables disponibles..."
curl -s "${BASE_URL}/datasets/ukraine_lwq" | jq -r '.variables | keys[]' | head -20

echo ""
echo "2. Verificando estructura de una variable específica (turbidity_mean)..."
curl -s "${BASE_URL}/datasets/ukraine_lwq" | jq '.variables.turbidity_mean' 2>/dev/null || echo "Variable turbidity_mean no encontrada"

echo ""
echo "3. Verificando estructura de Rw1610_rep..."
curl -s "${BASE_URL}/datasets/ukraine_lwq" | jq '.variables.Rw1610_rep' 2>/dev/null || echo "Variable Rw1610_rep no encontrada"

echo ""
echo "4. Verificando dimensiones del dataset..."
curl -s "${BASE_URL}/datasets/ukraine_lwq" | jq '.dimensions'

echo ""
echo "5. Probando obtener datos de un punto específico (time series)..."
curl -s -X POST "${BASE_URL}/timeseries/ukraine_lwq/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{"type": "Point", "coordinates": [30.5, 49.5]}' | jq '.result | length' 2>/dev/null && echo "Time series OK" || echo "Time series ERROR"

echo ""
echo "==================================================================="
