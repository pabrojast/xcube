#!/bin/bash

# ============================================================================
# Script para actualizar el servicio xcube con el zarr optimizado
# ============================================================================

echo "========================================================================"
echo "🔄 ACTUALIZANDO SERVICIO XCUBE CON ZARR OPTIMIZADO"
echo "========================================================================"
echo ""

NAMESPACE="xcube-ukraine"
KUBE_DIR="/home/pabrojast/Proyectos/xcube/k8s"

# Verificar que estamos en el directorio correcto
if [ ! -d "$KUBE_DIR" ]; then
    echo "❌ Error: Directorio $KUBE_DIR no encontrado"
    exit 1
fi

echo "📋 Cambios aplicados al zarr:"
echo "   ✅ Chunks optimizados: 1024x1024 (antes: 512x512)"
echo "   ✅ Metadatos consolidados"
echo "   ✅ Compresión Blosc/LZ4"
echo "   ✅ Atributos de coordenadas completos"
echo ""

echo "1️⃣ Aplicando ConfigMap actualizado..."
kubectl apply -f "$KUBE_DIR/02-configmap.yaml"
if [ $? -eq 0 ]; then
    echo "   ✅ ConfigMap actualizado"
else
    echo "   ❌ Error actualizando ConfigMap"
    exit 1
fi
echo ""

echo "2️⃣ Reiniciando deployment para cargar nueva configuración..."
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
    echo "   ✅ Pods listos"
else
    echo "   ⚠️  Timeout esperando pods"
fi
echo ""

echo "4️⃣ Verificando estado de los pods..."
kubectl get pods -n $NAMESPACE -l app=xcube-ukraine
echo ""

echo "5️⃣ Verificando logs recientes..."
echo "   (Primeras 10 líneas del log):"
kubectl logs -n $NAMESPACE -l app=xcube-ukraine --tail=10 | head -10
echo ""

echo "========================================================================"
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "========================================================================"
echo ""
echo "💡 PRÓXIMOS PASOS:"
echo ""
echo "   1. Probar tiles WMTS en zoom 6-7:"
echo "      curl -I 'https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/WorldCRS84Quad/7/32/148.png'"
echo ""
echo "   2. Abrir visor actualizado:"
echo "      https://data.dev-wins.com/xcube/"
echo ""
echo "   3. Verificar que los tiles cargan más rápido"
echo "      (chunks 1024x1024 vs 512x512 anteriores)"
echo ""
echo "   4. Si hay problemas, revisar logs:"
echo "      kubectl logs -n $NAMESPACE -l app=xcube-ukraine --tail=50"
echo ""
