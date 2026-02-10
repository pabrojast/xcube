#!/bin/bash

# ============================================================================
# Script para aplicar límites de zoom en el servicio xcube
# Esto evita generar tiles vacíos en zoom 8+
# ============================================================================

echo "========================================================================"
echo "🎯 APLICANDO LÍMITES DE ZOOM (MaxLevel: 7)"
echo "========================================================================"
echo ""

NAMESPACE="xcube-ukraine"
KUBE_DIR="/home/pabrojast/Proyectos/xcube/k8s"

echo "📋 Configuración de límites de zoom:"
echo "   • MinLevel: 0 (vista mundial)"
echo "   • MaxLevel: 7 (datos de lagos visibles)"
echo "   • Zoom 8+: No generará tiles (evita tiles vacíos)"
echo ""

echo "1️⃣ Aplicando ConfigMap actualizado con TileGrid..."
kubectl apply -f "$KUBE_DIR/02-configmap.yaml"
if [ $? -eq 0 ]; then
    echo "   ✅ ConfigMap actualizado con MaxLevel: 7"
else
    echo "   ❌ Error actualizando ConfigMap"
    exit 1
fi
echo ""

echo "2️⃣ Reiniciando deployment para aplicar cambios..."
kubectl rollout restart deployment/xcube-ukraine-deployment -n $NAMESPACE
if [ $? -eq 0 ]; then
    echo "   ✅ Deployment reiniciado"
else
    echo "   ❌ Error reiniciando deployment"
    exit 1
fi
echo ""

echo "3️⃣ Esperando a que los pods estén listos..."
kubectl rollout status deployment/xcube-ukraine-deployment -n $NAMESPACE --timeout=300s
if [ $? -eq 0 ]; then
    echo "   ✅ Pods listos y funcionando"
else
    echo "   ⚠️  Timeout esperando pods"
fi
echo ""

echo "4️⃣ Verificando estado actual..."
kubectl get pods -n $NAMESPACE -l app=xcube-ukraine
echo ""

echo "========================================================================"
echo "✅ LÍMITES DE ZOOM APLICADOS"
echo "========================================================================"
echo ""
echo "🧪 PRUEBAS DE VERIFICACIÓN:"
echo ""
echo "   1. Zoom 7 (DEBE funcionar):"
echo "      curl -I 'https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/7/32/148.png'"
echo ""
echo "   2. Zoom 8 (DEBE retornar 404 o error - fuera de rango):"
echo "      curl -I 'https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/8/64/296.png'"
echo ""
echo "   3. Verificar WMTS Capabilities (MaxLevel debe ser 7):"
echo "      curl -s 'https://data.dev-wins.com/xcube/wmts/1.0.0/WMTSCapabilities.xml' | grep -A 5 'MaxTileRow'"
echo ""
echo "💡 RESULTADO ESPERADO:"
echo "   • Zoom 0-7: Tiles generados correctamente"
echo "   • Zoom 8+: Error o no disponible (evita tiles vacíos)"
echo "   • Visor HTML: No permite zoom más allá de 7"
echo ""
