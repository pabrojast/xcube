# 🚀 Guía Rápida de Deployment con Docker Hub

## Imagen Configurada

La imagen de Docker ya está configurada en el deployment de Kubernetes:

```yaml
# k8s/03-deployment.yaml
image: pabrojast/xcube:ukrainetest
imagePullPolicy: Always
```

---

## Pasos para Deploy Completo

### 1. Build y Push de la Imagen Docker

```bash
# En el directorio del proyecto
cd /home/pabrojast/Proyectos/xcube

# Login en Docker Hub (solo la primera vez)
docker login
# Usuario: pabrojast
# Password: [tu password de Docker Hub]

# Build de la imagen
docker build -f Dockerfile.ukraine -t pabrojast/xcube:ukrainetest .

# Push a Docker Hub
docker push pabrojast/xcube:ukrainetest
```

### 2. Verificar que la Imagen Está en Docker Hub

Visita: https://hub.docker.com/r/pabrojast/xcube/tags

Deberías ver el tag `ukrainetest` listado.

### 3. Actualizar Credenciales de Azure

```bash
cd k8s

# Editar el secret con tus credenciales
nano 01-secret.yaml

# Codificar tus credenciales en base64
echo -n "ihpwinsdata" | base64
echo -n "tu-azure-account-key" | base64
echo -n "tu-connection-string" | base64

# Pegar los valores base64 en 01-secret.yaml
```

### 4. Deploy a Kubernetes

```bash
# Opción A: Usando el script automatizado (recomendado)
./deploy.sh deploy

# Opción B: Manual
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-secret.yaml
kubectl apply -f 02-configmap.yaml
kubectl apply -f 03-deployment.yaml
kubectl apply -f 04-service.yaml
kubectl apply -f 05-ingress.yaml
```

### 5. Verificar el Deploy

```bash
# Ver todos los recursos
kubectl get all -n xcube-ukraine

# Ver pods (deben estar Running)
kubectl get pods -n xcube-ukraine

# Ver logs
kubectl logs -n xcube-ukraine -l app=xcube-ukraine

# Ver ingress
kubectl get ingress -n xcube-ukraine

# Ver certificado TLS (tardará 2-5 minutos)
kubectl get certificate -n xcube-ukraine
```

### 6. Probar el Servicio

```bash
# Esperar a que el certificado esté Ready
kubectl get certificate -n xcube-ukraine -w
# Ctrl+C cuando veas READY = True

# Probar el servicio
curl https://data.dev-wins.com/xcube/datasets

# Obtener info del dataset
curl https://data.dev-wins.com/xcube/datasets/ukraine_lwq | jq

# Descargar un tile
curl "https://data.dev-wins.com/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/3/4/2.png" -o tile.png
```

---

## Comandos Útiles

### Gestión de la Imagen Docker

```bash
# Ver imágenes locales
docker images | grep xcube

# Eliminar imagen local
docker rmi pabrojast/xcube:ukrainetest

# Pull de la imagen
docker pull pabrojast/xcube:ukrainetest

# Rebuild y push (después de cambios)
docker build -f Dockerfile.ukraine -t pabrojast/xcube:ukrainetest .
docker push pabrojast/xcube:ukrainetest

# Forzar re-pull en Kubernetes (si actualizaste la imagen)
kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine
```

### Gestión del Deployment

```bash
# Ver status del deployment
./deploy.sh status

# Ver logs en tiempo real
./deploy.sh logs

# Reiniciar (pull nueva imagen si existe)
./deploy.sh restart

# Escalar
./deploy.sh scale 5

# Port forward para testing local
./deploy.sh port-forward
```

### Troubleshooting

```bash
# Si los pods no inician
kubectl describe pods -n xcube-ukraine

# Ver eventos
kubectl get events -n xcube-ukraine --sort-by='.lastTimestamp'

# Ver logs de un pod específico
kubectl logs -n xcube-ukraine <pod-name>

# Exec en un pod para debug
kubectl exec -it -n xcube-ukraine <pod-name> -- /bin/bash

# Ver si la imagen se descargó correctamente
kubectl describe pod -n xcube-ukraine <pod-name> | grep -A5 "Image"
```

---

## Tags Adicionales (Opcional)

Si quieres crear más tags:

```bash
# Tag como latest
docker tag pabrojast/xcube:ukrainetest pabrojast/xcube:latest
docker push pabrojast/xcube:latest

# Tag con versión
docker tag pabrojast/xcube:ukrainetest pabrojast/xcube:v1.0.0
docker push pabrojast/xcube:v1.0.0

# Actualizar deployment para usar otro tag
kubectl set image deployment/xcube-ukraine-deployment \
  xcube-ukraine=pabrojast/xcube:v1.0.0 \
  -n xcube-ukraine
```

---

## Verificación de la Imagen en el Pod

Después del deploy, verifica que se está usando la imagen correcta:

```bash
# Ver qué imagen está usando cada pod
kubectl get pods -n xcube-ukraine -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'

# Deberías ver:
# xcube-ukraine-deployment-xxxxx-yyyyy    pabrojast/xcube:ukrainetest
```

---

## Workflow Completo (Primera Vez)

```bash
# 1. Build y push imagen
cd /home/pabrojast/Proyectos/xcube
docker login
docker build -f Dockerfile.ukraine -t pabrojast/xcube:ukrainetest .
docker push pabrojast/xcube:ukrainetest

# 2. Configurar Azure credentials
cd k8s
nano 01-secret.yaml  # Actualizar con base64 de tus credenciales

# 3. Deploy
./deploy.sh deploy

# 4. Monitorear
kubectl get pods -n xcube-ukraine -w

# 5. Esperar certificado TLS
kubectl get certificate -n xcube-ukraine -w

# 6. Probar
curl https://data.dev-wins.com/xcube/datasets
```

---

## Workflow de Actualización

Si haces cambios en el código y quieres actualizar:

```bash
# 1. Rebuild y push
docker build -f Dockerfile.ukraine -t pabrojast/xcube:ukrainetest .
docker push pabrojast/xcube:ukrainetest

# 2. Forzar restart en K8s (para pull nueva imagen)
kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine

# 3. Ver el rollout
kubectl rollout status deployment/xcube-ukraine-deployment -n xcube-ukraine

# 4. Verificar
kubectl get pods -n xcube-ukraine
curl https://data.dev-wins.com/xcube/datasets
```

---

## Notas Importantes

1. **imagePullPolicy: Always**
   - El deployment está configurado con `imagePullPolicy: Always`
   - Esto significa que Kubernetes siempre intentará pull la última versión del tag
   - Útil durante desarrollo

2. **Docker Hub Rate Limits**
   - Docker Hub tiene límites de pulls (200 pulls/6h para usuarios gratuitos)
   - Si alcanzas el límite, considera usar un registry privado o Docker Hub Pro

3. **Tamaño de la Imagen**
   - La imagen base usa `micromamba` que es más ligera que conda full
   - Tamaño estimado: ~1-2GB
   - Primera descarga tardará unos minutos dependiendo de tu conexión

4. **Seguridad**
   - La imagen está en Docker Hub público
   - No incluye credenciales de Azure (se inyectan vía Kubernetes Secrets)
   - Si necesitas privacidad, usa un registry privado:
     - GitHub Container Registry
     - Azure Container Registry
     - Google Container Registry

---

## Checklist de Deployment

- [ ] Imagen buildeada: `docker build -f Dockerfile.ukraine -t pabrojast/xcube:ukrainetest .`
- [ ] Login en Docker Hub: `docker login`
- [ ] Imagen pusheada: `docker push pabrojast/xcube:ukrainetest`
- [ ] Imagen visible en Docker Hub: https://hub.docker.com/r/pabrojast/xcube
- [ ] Azure credentials actualizadas en `k8s/01-secret.yaml`
- [ ] Deployment aplicado: `./deploy.sh deploy`
- [ ] Pods en estado Running: `kubectl get pods -n xcube-ukraine`
- [ ] Certificado TLS Ready: `kubectl get certificate -n xcube-ukraine`
- [ ] Servicio responde: `curl https://data.dev-wins.com/xcube/datasets`
- [ ] WMTS funciona: tiles se descargan correctamente
- [ ] Time series funciona: POST con GeoJSON retorna datos

---

¡Listo! Tu servicio Ukraine LWQ xcube está configurado para usar Docker Hub y desplegar en Kubernetes.
