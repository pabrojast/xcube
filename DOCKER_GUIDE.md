# 🐳 Docker Deployment Guide - Ukraine LWQ Service

Guía completa para desplegar el servicio xcube de Ukraine Lake Water Quality usando Docker.

## 📋 Tabla de Contenidos

- [Prerrequisitos](#prerrequisitos)
- [Método 1: Script de Bash](#método-1-script-de-bash)
- [Método 2: Docker Compose](#método-2-docker-compose)
- [Método 3: Comandos Docker Manuales](#método-3-comandos-docker-manuales)
- [Verificación](#verificación)
- [Troubleshooting](#troubleshooting)

---

## 🔧 Prerrequisitos

### Instalar Docker

#### Linux
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Verificar instalación
docker --version
```

#### macOS / Windows
- Descargar e instalar [Docker Desktop](https://www.docker.com/products/docker-desktop)

### Instalar Docker Compose (Opcional)

```bash
# Linux
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar
docker-compose --version
```

---

## 🚀 Método 1: Script de Bash (Recomendado)

El método más sencillo usando el script `docker_ukraine.sh`.

### Construir la Imagen

```bash
./docker_ukraine.sh build
```

**Output esperado:**
```
[INFO] Building Docker image: xcube-ukraine-lwq:latest
...
[SUCCESS] Docker image built successfully!
```

### Ejecutar el Servicio

```bash
./docker_ukraine.sh run
```

**Output esperado:**
```
[SUCCESS] Container started successfully!

Service URLs:
  - Main API: http://localhost:8080
  - Datasets: http://localhost:8080/datasets
  - WMTS Capabilities: http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml
  - API Documentation: http://localhost:8080/openapi.html
```

### Comandos Disponibles

```bash
# Ver logs en tiempo real
./docker_ukraine.sh logs

# Ver estado del servicio
./docker_ukraine.sh status

# Probar endpoints
./docker_ukraine.sh test

# Detener el servicio
./docker_ukraine.sh stop

# Reiniciar el servicio
./docker_ukraine.sh restart

# Abrir shell en el contenedor
./docker_ukraine.sh exec

# Limpiar contenedor
./docker_ukraine.sh clean

# Limpiar contenedor e imagen
./docker_ukraine.sh clean-all

# Ayuda
./docker_ukraine.sh help
```

---

## 🐋 Método 2: Docker Compose

### Iniciar el Servicio

```bash
# Build y start en un solo comando
docker-compose -f docker-compose.ukraine.yml up -d --build
```

### Comandos Docker Compose

```bash
# Ver logs
docker-compose -f docker-compose.ukraine.yml logs -f

# Ver estado
docker-compose -f docker-compose.ukraine.yml ps

# Detener servicio
docker-compose -f docker-compose.ukraine.yml down

# Reiniciar servicio
docker-compose -f docker-compose.ukraine.yml restart

# Reconstruir y reiniciar
docker-compose -f docker-compose.ukraine.yml up -d --build --force-recreate
```

---

## 🔨 Método 3: Comandos Docker Manuales

### Build

```bash
docker build \
  -f Dockerfile.ukraine \
  -t xcube-ukraine-lwq:latest \
  .
```

### Run

```bash
docker run -d \
  --name xcube-ukraine-service \
  -p 8080:8080 \
  -e AZURE_STORAGE_ACCOUNT_NAME="ihpwinsdata" \
  -e AZURE_STORAGE_ACCOUNT_KEY="<AZURE_STORAGE_ACCOUNT_KEY>" \
  --restart unless-stopped \
  xcube-ukraine-lwq:latest
```

### Comandos Básicos

```bash
# Ver logs
docker logs -f xcube-ukraine-service

# Ver estado
docker ps | grep xcube-ukraine-service

# Detener
docker stop xcube-ukraine-service

# Iniciar
docker start xcube-ukraine-service

# Reiniciar
docker restart xcube-ukraine-service

# Eliminar contenedor
docker rm -f xcube-ukraine-service

# Eliminar imagen
docker rmi xcube-ukraine-lwq:latest
```

---

## ✅ Verificación

### 1. Health Check

```bash
# Verificar que el contenedor esté healthy
docker ps

# Debería mostrar:
# STATUS: Up X minutes (healthy)
```

### 2. Probar Endpoints

```bash
# Lista de datasets
curl http://localhost:8080/datasets | jq '.'

# Metadata del dataset
curl http://localhost:8080/datasets/ukraine_lwq | jq '.'

# WMTS Capabilities
curl http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml | head -30

# Time Series (POST)
curl -X POST "http://localhost:8080/timeseries/ukraine_lwq/turbidity_mean" \
  -H "Content-Type: application/json" \
  -d '{"type":"Point","coordinates":[30.52,50.45]}' | jq '.result[0:3]'
```

### 3. Abrir en Navegador

- **API Documentation**: http://localhost:8080/openapi.html
- **Datasets**: http://localhost:8080/datasets
- **Viewer**: Abrir `ukraine_lwq_viewer.html` en el navegador

---

## 🛠️ Troubleshooting

### Container no inicia

```bash
# Ver logs del contenedor
docker logs xcube-ukraine-service

# Ver últimos 50 logs
docker logs --tail 50 xcube-ukraine-service

# Ver logs en tiempo real
docker logs -f xcube-ukraine-service
```

**Errores comunes:**
- **Puerto 8080 ocupado**: Cambiar puerto con `-p 8081:8080`
- **Credenciales Azure incorrectas**: Verificar variables de entorno
- **Falta memoria**: Aumentar memoria disponible para Docker

### Puerto ya en uso

```bash
# Encontrar proceso usando el puerto 8080
sudo lsof -i :8080

# O cambiar el puerto
docker run -p 8081:8080 ...
```

### Reconstruir desde cero

```bash
# Limpiar todo
./docker_ukraine.sh clean-all

# O manualmente
docker stop xcube-ukraine-service
docker rm xcube-ukraine-service
docker rmi xcube-ukraine-lwq:latest

# Limpiar cache de build
docker builder prune -a

# Reconstruir
./docker_ukraine.sh build
./docker_ukraine.sh run
```

### Container se detiene inmediatamente

```bash
# Ver por qué se detuvo
docker logs xcube-ukraine-service

# Ejecutar en modo interactivo para debugging
docker run -it --rm \
  -p 8080:8080 \
  xcube-ukraine-lwq:latest \
  /bin/bash
```

### Problemas de red

```bash
# Verificar que el puerto está expuesto
docker port xcube-ukraine-service

# Verificar red
docker network inspect xcube-network

# Reiniciar Docker
sudo systemctl restart docker  # Linux
# O reiniciar Docker Desktop (Mac/Windows)
```

### Credenciales de Azure no funcionan

```bash
# Verificar variables de entorno dentro del contenedor
docker exec xcube-ukraine-service env | grep AZURE

# Actualizar credenciales
docker stop xcube-ukraine-service
docker rm xcube-ukraine-service

# Ejecutar con nuevas credenciales
docker run -d \
  --name xcube-ukraine-service \
  -p 8080:8080 \
  -e AZURE_STORAGE_ACCOUNT_NAME="nuevo_account" \
  -e AZURE_STORAGE_ACCOUNT_KEY="nueva_key" \
  xcube-ukraine-lwq:latest
```

---

## 📊 Monitorización

### Ver uso de recursos

```bash
# Stats en tiempo real
docker stats xcube-ukraine-service

# Info del contenedor
docker inspect xcube-ukraine-service | jq '.[0].State'
```

### Health Check Manual

```bash
# Ejecutar health check
docker exec xcube-ukraine-service curl -f http://localhost:8080/datasets
```

---

## 🔒 Seguridad

### Usar Variables de Entorno desde Archivo

Crear archivo `.env`:
```bash
# .env
AZURE_STORAGE_ACCOUNT_NAME=ihpwinsdata
AZURE_STORAGE_ACCOUNT_KEY=tu_key_aqui
```

Ejecutar con:
```bash
docker run -d \
  --name xcube-ukraine-service \
  -p 8080:8080 \
  --env-file .env \
  xcube-ukraine-lwq:latest
```

O con docker-compose:
```yaml
# docker-compose.ukraine.yml
services:
  ukraine-lwq-service:
    env_file:
      - .env
```

### No exponer credenciales

```bash
# Usar secrets de Docker (Swarm)
echo "tu_key" | docker secret create azure_key -

# O usar Azure Key Vault en producción
```

---

## 🚀 Producción

### Optimizaciones

1. **Multi-stage build** (ya implementado)
2. **Cache de tiles**: Montar volumen
   ```bash
   docker run -d \
     -v /path/to/cache:/cache \
     xcube-ukraine-lwq:latest
   ```
3. **Reverse proxy**: Nginx/Traefik delante
4. **HTTPS**: Usar Let's Encrypt
5. **Load balancer**: Múltiples instancias

### Ejemplo con Nginx

```nginx
server {
    listen 80;
    server_name ukraine-lwq.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📚 Referencias

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [xcube Documentation](https://xcube.readthedocs.io/)
- [Micromamba Docker Images](https://hub.docker.com/r/mambaorg/micromamba)

---

**Última actualización**: 10 de octubre de 2025
