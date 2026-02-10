# 🚀 Production Deployment Guide - data.dev-wins.com/xcube

## Configuración de Producción

Este documento describe el deployment de producción del servicio Ukraine LWQ xcube en **data.dev-wins.com/xcube** con TLS habilitado.

---

## 📋 Resumen de Configuración

| Parámetro | Valor |
|-----------|-------|
| **Hostname** | data.dev-wins.com |
| **Path** | /xcube |
| **URL completa** | https://data.dev-wins.com/xcube/ |
| **TLS/HTTPS** | ✅ Habilitado (Let's Encrypt) |
| **Certificate** | Automático via cert-manager |
| **Namespace** | xcube-ukraine |
| **Replicas** | 2-10 (HPA) |
| **Ingress Class** | nginx |

---

## 🔐 Requisitos Previos

### 1. cert-manager ya instalado ✅
```bash
# Verificar que existe el ClusterIssuer
kubectl get clusterissuer letsencrypt-prod
```

### 2. DNS configurado ✅
El dominio `data.dev-wins.com` debe apuntar al Load Balancer de tu Ingress Controller.

### 3. Azure Credentials configuradas
Edita `k8s/01-secret.yaml` con tus credenciales:
```bash
echo -n "ihpwinsdata" | base64
echo -n "tu-azure-account-key" | base64
echo -n "tu-connection-string" | base64
```

---

## 🚀 Deployment Paso a Paso

### Paso 1: Actualizar Credenciales de Azure

```bash
cd /home/pabrojast/Proyectos/xcube/k8s

# Editar el secret
nano 01-secret.yaml

# Actualizar los valores base64 de:
# - account-name
# - account-key
# - connection-string
```

### Paso 2: Desplegar todos los recursos

```bash
# Opción A: Usar el script automatizado (recomendado)
./deploy.sh deploy

# Opción B: Deployment manual
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-secret.yaml
kubectl apply -f 02-configmap.yaml
kubectl apply -f 03-deployment.yaml
kubectl apply -f 04-service.yaml
kubectl apply -f 05-ingress.yaml
```

### Paso 3: Verificar el Deployment

```bash
# Ver todos los recursos
kubectl get all -n xcube-ukraine

# Ver el Ingress
kubectl get ingress -n xcube-ukraine

# Ver el certificado TLS
kubectl get certificate -n xcube-ukraine

# Describir el Ingress
kubectl describe ingress xcube-ukraine-ingress -n xcube-ukraine
```

### Paso 4: Esperar el Certificado TLS

```bash
# Monitorear el proceso de emisión del certificado
kubectl get certificate -n xcube-ukraine -w

# Ver detalles del certificado
kubectl describe certificate xcube-ukraine-tls -n xcube-ukraine

# Ver los CertificateRequest
kubectl get certificaterequest -n xcube-ukraine
```

El certificado debería estar listo en 2-5 minutos. Estado esperado:
```
NAME                READY   SECRET              AGE
xcube-ukraine-tls   True    xcube-ukraine-tls   2m
```

### Paso 5: Probar el Servicio

```bash
# Probar HTTP (debería redirigir a HTTPS)
curl -I http://data.dev-wins.com/xcube/datasets

# Probar HTTPS
curl https://data.dev-wins.com/xcube/datasets

# Ver información del dataset
curl https://data.dev-wins.com/xcube/datasets/ukraine_lwq | jq

# Descargar un tile WMTS
curl "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/3/4/2.png" -o tile.png

# Probar time series (requiere GeoJSON)
curl -X POST https://data.dev-wins.com/xcube/timeseries/ukraine_lwq/turbidity_mean \
  -H "Content-Type: application/json" \
  -d '{"type": "Point", "coordinates": [30.5, 50.4]}' | jq
```

---

## 🌐 URLs de Producción

### API Endpoints

| Endpoint | URL | Método |
|----------|-----|--------|
| **Lista de datasets** | https://data.dev-wins.com/xcube/datasets | GET |
| **Info del dataset** | https://data.dev-wins.com/xcube/datasets/ukraine_lwq | GET |
| **WMTS Tiles** | https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/{var}/{z}/{y}/{x}.png | GET |
| **Time Series** | https://data.dev-wins.com/xcube/timeseries/ukraine_lwq/{var} | POST |

### Visor Web

Abre en tu navegador:
```
file:///home/pabrojast/Proyectos/xcube/ukraine_lwq_viewer_production.html
```

Este visor está preconfigurado con:
- Base URL: `https://data.dev-wins.com/xcube`
- Dataset: `ukraine_lwq`
- Variables: turbidity_mean, Rw490_rep, Rw560_rep, etc.

---

## 🔧 Configuración del Ingress

El archivo `k8s/05-ingress.yaml` está configurado con:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: xcube-ukraine-ingress
  namespace: xcube-ukraine
  annotations:
    # Certificado automático
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    
    # Timeouts (1 hora)
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "3600"
    
    # Body size (500MB)
    nginx.ingress.kubernetes.io/proxy-body-size: 500M
    
    # Buffering deshabilitado
    nginx.ingress.kubernetes.io/proxy-request-buffering: "off"
    nginx.ingress.kubernetes.io/proxy-buffering: "off"
    
    # CORS habilitado
    nginx.ingress.kubernetes.io/enable-cors: "true"
    
    # SSL redirect
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    
spec:
  ingressClassName: nginx
  tls:
    - hosts:
      - data.dev-wins.com
      secretName: xcube-ukraine-tls
  rules:
  - host: "data.dev-wins.com"
    http:
      paths:
      - path: "/xcube(/|$)(.*)"
        pathType: ImplementationSpecific
        backend:
          service:
            name: xcube-ukraine-service
            port:
              number: 80
```

### Path Rewriting

El Ingress usa la anotación:
```yaml
nginx.ingress.kubernetes.io/rewrite-target: /$2
```

Esto significa:
- Request: `https://data.dev-wins.com/xcube/datasets`
- Se reescribe a: `http://xcube-ukraine-service/datasets`
- Pero xcube está configurado con `--prefix /xcube`
- Por lo tanto, internamente maneja: `/xcube/datasets`

---

## 📊 Monitoreo

### Ver Logs

```bash
# Logs de todos los pods
kubectl logs -n xcube-ukraine -l app=xcube-ukraine -f

# Logs de un pod específico
POD=$(kubectl get pods -n xcube-ukraine -l app=xcube-ukraine -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n xcube-ukraine $POD -f
```

### Ver Estado de los Pods

```bash
# Estado básico
kubectl get pods -n xcube-ukraine

# Estado detallado
kubectl describe pods -n xcube-ukraine

# Recursos utilizados
kubectl top pods -n xcube-ukraine
```

### Ver HPA (Auto-scaling)

```bash
# Estado del HPA
kubectl get hpa -n xcube-ukraine

# Detalles del HPA
kubectl describe hpa xcube-ukraine-hpa -n xcube-ukraine

# Monitorear en tiempo real
watch kubectl get hpa -n xcube-ukraine
```

### Ver Métricas del Ingress

```bash
# Ver eventos del Ingress
kubectl describe ingress xcube-ukraine-ingress -n xcube-ukraine

# Ver logs del Ingress Controller
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f
```

---

## 🔄 Operaciones Comunes

### Reiniciar el Servicio

```bash
# Rolling restart (sin downtime)
kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine

# Ver progreso
kubectl rollout status deployment/xcube-ukraine-deployment -n xcube-ukraine
```

### Escalar Manualmente

```bash
# Escalar a 5 replicas
kubectl scale deployment/xcube-ukraine-deployment -n xcube-ukraine --replicas=5

# Ver los pods escalando
kubectl get pods -n xcube-ukraine -w
```

### Actualizar Configuración

```bash
# Editar el ConfigMap
kubectl edit configmap xcube-ukraine-config -n xcube-ukraine

# O aplicar el archivo modificado
kubectl apply -f k8s/02-configmap.yaml

# Reiniciar para aplicar cambios
kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine
```

### Actualizar Credenciales de Azure

```bash
# Editar el secret
nano k8s/01-secret.yaml

# Aplicar
kubectl apply -f k8s/01-secret.yaml

# Reiniciar pods para usar las nuevas credenciales
kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine
```

### Renovar Certificado TLS

```bash
# El certificado se renueva automáticamente, pero si necesitas forzar:
kubectl delete certificate xcube-ukraine-tls -n xcube-ukraine

# Volver a aplicar el Ingress
kubectl apply -f k8s/05-ingress.yaml

# Monitorear
kubectl get certificate -n xcube-ukraine -w
```

---

## 🐛 Troubleshooting

### Problema: Certificado no se genera

**Síntomas:**
```bash
kubectl get certificate -n xcube-ukraine
# READY = False
```

**Solución:**
```bash
# Ver detalles del certificado
kubectl describe certificate xcube-ukraine-tls -n xcube-ukraine

# Ver CertificateRequest
kubectl get certificaterequest -n xcube-ukraine

# Ver logs de cert-manager
kubectl logs -n cert-manager -l app=cert-manager -f

# Verificar que el ClusterIssuer existe
kubectl get clusterissuer letsencrypt-prod
```

### Problema: 404 Not Found en /xcube

**Síntomas:**
```bash
curl https://data.dev-wins.com/xcube/datasets
# 404 Not Found
```

**Solución:**
```bash
# Verificar que el servicio está funcionando
kubectl get svc -n xcube-ukraine

# Verificar que los pods están healthy
kubectl get pods -n xcube-ukraine

# Probar el servicio directamente (port-forward)
kubectl port-forward -n xcube-ukraine service/xcube-ukraine-service 8080:80

# En otra terminal
curl http://localhost:8080/xcube/datasets

# Si funciona localmente, el problema está en el Ingress
```

### Problema: 502 Bad Gateway

**Síntomas:**
```bash
curl https://data.dev-wins.com/xcube/datasets
# 502 Bad Gateway
```

**Solución:**
```bash
# Ver logs de los pods
kubectl logs -n xcube-ukraine -l app=xcube-ukraine --tail=50

# Ver si los pods están ready
kubectl get pods -n xcube-ukraine

# Ver endpoints del servicio
kubectl get endpoints -n xcube-ukraine

# Si no hay endpoints, los pods no están pasando health checks
kubectl describe pods -n xcube-ukraine
```

### Problema: SSL Certificate Error

**Síntomas:**
- El navegador muestra "No seguro" o error de certificado

**Solución:**
```bash
# Ver estado del certificado
kubectl get certificate -n xcube-ukraine

# Ver secret del certificado
kubectl get secret xcube-ukraine-tls -n xcube-ukraine

# Verificar el certificado
kubectl get secret xcube-ukraine-tls -n xcube-ukraine -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout
```

### Problema: Pods en CrashLoopBackOff

**Síntomas:**
```bash
kubectl get pods -n xcube-ukraine
# STATUS = CrashLoopBackOff
```

**Solución:**
```bash
# Ver logs del pod que falla
kubectl logs -n xcube-ukraine <pod-name>

# Ver logs del contenedor anterior (antes del crash)
kubectl logs -n xcube-ukraine <pod-name> --previous

# Ver descripción del pod
kubectl describe pod -n xcube-ukraine <pod-name>

# Causas comunes:
# 1. Credenciales de Azure incorrectas
# 2. ConfigMap con sintaxis inválida
# 3. Falta la imagen de Docker (si usas custom image)
```

---

## 🔐 Seguridad

### Validar Configuración TLS

```bash
# Probar con curl
curl -v https://data.dev-wins.com/xcube/datasets 2>&1 | grep -i ssl

# Probar con openssl
openssl s_client -connect data.dev-wins.com:443 -servername data.dev-wins.com

# Verificar el grado SSL (externo)
# https://www.ssllabs.com/ssltest/analyze.html?d=data.dev-wins.com
```

### Rotación de Credenciales

Se recomienda rotar las credenciales de Azure cada 90 días:

```bash
# 1. Obtener nuevas credenciales de Azure
# 2. Codificar en base64
echo -n "nueva-key" | base64

# 3. Actualizar el secret
nano k8s/01-secret.yaml

# 4. Aplicar
kubectl apply -f k8s/01-secret.yaml

# 5. Reiniciar
kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine
```

### Network Policies (Opcional)

Para mayor seguridad, limitar el tráfico de red:

```yaml
# k8s/06-network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: xcube-ukraine-netpol
  namespace: xcube-ukraine
spec:
  podSelector:
    matchLabels:
      app: xcube-ukraine
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
```

---

## 📈 Performance

### Configuración Actual

- **Replicas**: 2 mínimo, 10 máximo (HPA)
- **CPU**: 250m request, 1000m limit
- **Memory**: 512Mi request, 2Gi limit
- **HPA Target**: 70% CPU

### Optimización

Si experimentas alta carga:

```bash
# Opción 1: Escalar manualmente (temporal)
kubectl scale deployment/xcube-ukraine-deployment -n xcube-ukraine --replicas=10

# Opción 2: Ajustar HPA (permanente)
kubectl edit hpa xcube-ukraine-hpa -n xcube-ukraine
# Cambiar minReplicas y maxReplicas

# Opción 3: Aumentar recursos por pod
kubectl edit deployment xcube-ukraine-deployment -n xcube-ukraine
# Aumentar resources.limits y resources.requests
```

### Métricas

```bash
# CPU y memoria por pod
kubectl top pods -n xcube-ukraine

# Métricas de HPA
kubectl get hpa -n xcube-ukraine -o yaml

# Eventos de escalado
kubectl describe hpa xcube-ukraine-hpa -n xcube-ukraine
```

---

## 📝 Checklist de Producción

Antes de considerar el deployment como completo:

- [ ] Credenciales de Azure actualizadas en `01-secret.yaml`
- [ ] Deployment aplicado: `./deploy.sh deploy`
- [ ] Todos los pods en estado `Running`
- [ ] Certificado TLS en estado `Ready`
- [ ] Ingress tiene un ADDRESS asignado
- [ ] DNS apunta al Load Balancer del Ingress
- [ ] HTTPS funciona: `curl https://data.dev-wins.com/xcube/datasets`
- [ ] HTTP redirige a HTTPS automáticamente
- [ ] WMTS tiles se cargan correctamente
- [ ] Time series API funciona (POST con GeoJSON)
- [ ] Visor web carga correctamente
- [ ] HPA está funcionando: `kubectl get hpa -n xcube-ukraine`
- [ ] Logs no muestran errores: `kubectl logs -n xcube-ukraine -l app=xcube-ukraine`
- [ ] Monitoreo configurado (opcional)
- [ ] Backups configurados (opcional)
- [ ] Alertas configuradas (opcional)

---

## 🎉 ¡Deployment Completo!

Tu servicio Ukraine LWQ xcube está ahora en producción en:

**🌐 https://data.dev-wins.com/xcube/**

### Endpoints Disponibles:

- 📋 Datasets: https://data.dev-wins.com/xcube/datasets
- 🗺️ WMTS: https://data.dev-wins.com/xcube/wmts/1.0.0/tile/...
- 📊 Time Series: https://data.dev-wins.com/xcube/timeseries/... (POST)

### Gestión:

```bash
# Estado
./k8s/deploy.sh status

# Logs
./k8s/deploy.sh logs

# Escalar
./k8s/deploy.sh scale 5

# Reiniciar
./k8s/deploy.sh restart

# Limpiar (⚠️ cuidado!)
./k8s/deploy.sh cleanup
```

---

**Documentación relacionada:**
- `k8s/README.md` - Guía rápida
- `k8s/K8S_GUIDE.md` - Guía completa
- `K8S_DEPLOYMENT_SUMMARY.md` - Resumen general
- `ukraine_lwq_viewer_production.html` - Visor web
