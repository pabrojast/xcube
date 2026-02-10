# 🔒 Solución: Mixed Content Error (HTTP/HTTPS)

## Problema

Al acceder a `https://data.dev-wins.com/xcube/openapi.html`, aparece el error:

```
Mixed Content: The page at 'https://data.dev-wins.com/xcube/openapi.html' 
was loaded over HTTPS, but requested an insecure resource 
'http://data.dev-wins.com/xcube/openapi.json'. 
This request has been blocked; the content must be served over HTTPS.
```

**Causa**: xcube no sabía que estaba detrás de un proxy HTTPS y generaba URLs con `http://` en lugar de `https://`.

---

## ✅ Solución Implementada

Se aplicaron **dos cambios** para resolver el problema:

### 1. Configuración de xcube (`k8s/02-configmap.yaml`)

Agregamos `reverse_url_prefix` al archivo de configuración para que xcube genere URLs correctas:

```yaml
reverse_url_prefix: "https://data.dev-wins.com/xcube"
```

Esta configuración le dice a xcube:
- Generar URLs con el esquema `https://`
- Incluir el hostname completo `data.dev-wins.com`
- Usar el path prefix `/xcube`

### 2. Anotaciones del Ingress (`k8s/05-ingress.yaml`)

Agregamos anotaciones para que NGINX maneje correctamente los redirects:

```yaml
annotations:
  # Forward protocol headers
  nginx.ingress.kubernetes.io/backend-protocol: "HTTP"
  
  # Rewrite HTTP redirects to HTTPS
  nginx.ingress.kubernetes.io/proxy-redirect-from: "~^http://([^/]+)/(.*)$"
  nginx.ingress.kubernetes.io/proxy-redirect-to: "https://$1/$2"
```

Estas anotaciones:
- `backend-protocol: "HTTP"` - El backend es HTTP (pod interno)
- `proxy-redirect-from/to` - Reescribe cualquier redirect de HTTP a HTTPS

---

## 🚀 Aplicar los Cambios

### Paso 1: Actualizar ConfigMap

```bash
cd /home/pabrojast/Proyectos/xcube/k8s

# Aplicar el nuevo ConfigMap
kubectl apply -f 02-configmap.yaml
```

### Paso 2: Actualizar Ingress

```bash
# Aplicar el nuevo Ingress
kubectl apply -f 05-ingress.yaml
```

### Paso 3: Reiniciar Pods

Los pods necesitan reiniciarse para cargar el nuevo ConfigMap:

```bash
# Reiniciar deployment
kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine

# Esperar a que termine
kubectl rollout status deployment/xcube-ukraine-deployment -n xcube-ukraine

# Verificar que los pods están corriendo
kubectl get pods -n xcube-ukraine
```

---

## 🧪 Verificar la Solución

### 1. Probar OpenAPI

```bash
# Descargar openapi.json (debería ser HTTPS)
curl -I https://data.dev-wins.com/xcube/openapi.json

# Debería devolver:
# HTTP/2 200
# content-type: application/json
```

### 2. Abrir en Navegador

```
https://data.dev-wins.com/xcube/openapi.html
```

Ya **NO** debería aparecer el error "Mixed Content". La consola del navegador debería estar limpia.

### 3. Verificar URLs Generadas

Abre la consola de desarrollador (F12) y verifica que:
- Todas las peticiones son HTTPS (icono de candado verde)
- No hay advertencias de "Mixed Content"
- `openapi.json` se carga correctamente

---

## 📝 Explicación Técnica

### ¿Por qué ocurría el error?

1. **Usuario accede**: `https://data.dev-wins.com/xcube/openapi.html` (HTTPS)
2. **openapi.html carga**: Necesita cargar `openapi.json`
3. **xcube genera URL**: `http://data.dev-wins.com/xcube/openapi.json` (HTTP)
4. **Navegador bloquea**: No permite contenido HTTP en página HTTPS

### ¿Cómo se soluciona?

Con `reverse_url_prefix`, xcube ahora:
1. Detecta que debe usar HTTPS
2. Genera URLs correctas: `https://data.dev-wins.com/xcube/openapi.json`
3. Navegador permite la carga (todo es HTTPS)

### Flujo Completo

```
Usuario → https://data.dev-wins.com/xcube/openapi.html
    ↓
NGINX Ingress (TLS termination)
    ↓
xcube pod (puerto 8080)
    ↓
xcube genera URLs con: reverse_url_prefix
    ↓
Retorna: https://data.dev-wins.com/xcube/openapi.json ✅
```

---

## 🔍 Troubleshooting

### Si el error persiste:

**1. Verificar que el ConfigMap se aplicó:**
```bash
kubectl get configmap -n xcube-ukraine xcube-ukraine-config -o yaml | grep reverse_url_prefix
# Debería mostrar: reverse_url_prefix: "https://data.dev-wins.com/xcube"
```

**2. Verificar que los pods se reiniciaron:**
```bash
kubectl get pods -n xcube-ukraine -o wide
# Verificar que AGE es reciente (< 5 minutos)
```

**3. Verificar logs del pod:**
```bash
POD=$(kubectl get pods -n xcube-ukraine -l app=xcube-ukraine -o jsonpath='{.items[0].metadata.name}')
kubectl logs -n xcube-ukraine $POD | grep -i "reverse_url_prefix\|url"
```

**4. Limpiar cache del navegador:**
```bash
# En Chrome/Firefox: Ctrl+Shift+R (hard refresh)
# O abrir ventana de incógnito
```

**5. Verificar Ingress:**
```bash
kubectl describe ingress -n xcube-ukraine xcube-ukraine-ingress | grep -A5 "Annotations"
# Debería mostrar las anotaciones de proxy-redirect
```

---

## 📋 Checklist de Verificación

Después de aplicar los cambios:

- [ ] ConfigMap actualizado con `reverse_url_prefix`
- [ ] Ingress actualizado con anotaciones de proxy-redirect
- [ ] Pods reiniciados (AGE < 5 minutos)
- [ ] `curl https://data.dev-wins.com/xcube/openapi.json` retorna 200
- [ ] Navegador carga `openapi.html` sin errores
- [ ] No hay errores "Mixed Content" en la consola
- [ ] Todas las peticiones son HTTPS (candado verde)
- [ ] OpenAPI UI funciona correctamente
- [ ] Se pueden probar endpoints desde la UI

---

## 🎯 Alternativas Consideradas

### ¿Por qué no usar solo anotaciones de Ingress?

Las anotaciones de NGINX solo reescriben redirects HTTP 3xx, pero no modifican el contenido de las respuestas JSON/HTML. xcube necesita saber internamente que debe generar URLs HTTPS.

### ¿Por qué no usar configuration-snippet?

Tu cluster tiene deshabilitados los `configuration-snippet` por seguridad (decisión del administrador). Por eso usamos:
- Anotaciones estándar de NGINX Ingress
- Configuración nativa de xcube (`reverse_url_prefix`)

### ¿Se puede usar una URL relativa?

**No recomendado**. Si usas:
```yaml
reverse_url_prefix: "/xcube"
```

xcube generará URLs como `/xcube/openapi.json` que funcionan, pero algunos clientes (como openapi.html) pueden tener problemas. Es mejor usar URL absoluta con HTTPS.

---

## 📚 Referencias

- **xcube config schema**: `xcube/server/config.py`
  - `reverse_url_prefix`: Prefix para URLs generadas por xcube
  - `url_prefix`: Prefix para rutas del servidor

- **NGINX Ingress annotations**:
  - `proxy-redirect-from/to`: Reescribe Location headers
  - `backend-protocol`: Protocolo del backend (HTTP/HTTPS)
  - Docs: https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/

---

## ✅ Resultado Final

Después de aplicar estos cambios:

✅ `https://data.dev-wins.com/xcube/openapi.html` carga correctamente  
✅ `https://data.dev-wins.com/xcube/openapi.json` se descarga vía HTTPS  
✅ No hay errores "Mixed Content" en la consola  
✅ OpenAPI UI completamente funcional  
✅ Todos los endpoints generan URLs HTTPS correctas  

---

**Nota**: Si decides cambiar el dominio en el futuro, solo necesitas actualizar `reverse_url_prefix` en el ConfigMap y reiniciar los pods.
