# Kubernetes Deployment Guide - Ukraine LWQ xcube Service

Complete guide for deploying the Ukraine LWQ xcube service to Kubernetes with Ingress support for `/xcube/` path prefix.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [Deployment Options](#deployment-options)
- [Monitoring and Management](#monitoring-and-management)
- [Troubleshooting](#troubleshooting)
- [Production Best Practices](#production-best-practices)

---

## Overview

This Kubernetes deployment provides:
- **Scalable deployment**: 2-10 replicas with Horizontal Pod Autoscaling
- **High availability**: Multiple replicas with session affinity
- **Reverse proxy**: NGINX Ingress for `/xcube/` path prefix
- **Health checks**: Liveness, readiness, and startup probes
- **Resource management**: CPU and memory limits/requests
- **Azure integration**: Secure credential management via Kubernetes secrets

### Architecture

```
Internet
    ↓
NGINX Ingress Controller
    ↓ (routes /xcube/* traffic)
Kubernetes Service (ClusterIP)
    ↓ (load balances with session affinity)
xcube Pods (2-10 replicas)
    ↓ (reads from)
Azure Blob Storage (ukraine_lwq.zarr)
```

---

## Prerequisites

### Required
1. **Kubernetes Cluster** (v1.19+)
   - Minikube, Kind, GKE, EKS, AKS, or any K8s distribution
   - Minimum: 2 CPU cores, 4GB RAM available

2. **kubectl** (v1.19+)
   ```bash
   # Install on Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
   
   # Verify
   kubectl version --client
   ```

3. **NGINX Ingress Controller**
   ```bash
   # Install on generic Kubernetes
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
   
   # Or for Minikube
   minikube addons enable ingress
   
   # Verify
   kubectl get pods -n ingress-nginx
   ```

4. **Azure Storage Credentials**
   - Account name: `ihpwinsdata`
   - Account key: (your Azure storage account key)
   - Connection string format: `DefaultEndpointsProtocol=https;AccountName=...`

### Optional
- **Helm** (v3+) - For more advanced deployments
- **Monitoring tools** - Prometheus, Grafana for observability
- **TLS certificate** - For HTTPS access

---

## Quick Start

### 1. Configure Azure Credentials

Edit `k8s/01-secret.yaml` and update with your Azure credentials:

```yaml
data:
  account-name: aWhwd2luc2RhdGE=  # Base64 of "ihpwinsdata"
  account-key: <YOUR_BASE64_ENCODED_KEY>
  connection-string: <YOUR_BASE64_ENCODED_CONNECTION_STRING>
```

To encode your credentials:
```bash
echo -n "your-account-key" | base64
echo -n "DefaultEndpointsProtocol=https;AccountName=ihpwinsdata;AccountKey=your-key;EndpointSuffix=core.windows.net" | base64
```

### 2. Deploy Everything

```bash
cd k8s
./deploy.sh deploy
```

This will:
- ✓ Check prerequisites
- ✓ Create namespace `xcube-ukraine`
- ✓ Apply all manifests in order
- ✓ Wait for deployment to be ready
- ✓ Show deployment status

### 3. Access the Service

**Option A: Via Ingress (production)**
```bash
# Get Ingress IP
kubectl get ingress -n xcube-ukraine

# Access service
curl http://<INGRESS_IP>/xcube/datasets
```

**Option B: Via Port Forwarding (development)**
```bash
./deploy.sh port-forward

# In another terminal
curl http://localhost:8080/xcube/datasets
```

### 4. Open the Viewer

Use the provided HTML viewer or access APIs directly:
- Datasets: `http://<IP>/xcube/datasets`
- WMTS: `http://<IP>/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/{z}/{y}/{x}.png`
- Time Series: POST `http://<IP>/xcube/timeseries/ukraine_lwq/turbidity_mean`

---

## Detailed Setup

### Step-by-Step Deployment

#### 1. Create Namespace
```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl get namespace xcube-ukraine
```

#### 2. Configure Secrets
```bash
# Edit and apply secret
kubectl apply -f k8s/01-secret.yaml

# Verify (values should be hidden)
kubectl get secret -n xcube-ukraine
kubectl describe secret azure-storage-credentials -n xcube-ukraine
```

#### 3. Apply ConfigMap
```bash
kubectl apply -f k8s/02-configmap.yaml

# View config
kubectl get configmap -n xcube-ukraine xcube-ukraine-config -o yaml
```

#### 4. Deploy Application
```bash
kubectl apply -f k8s/03-deployment.yaml

# Watch deployment progress
kubectl rollout status deployment/xcube-ukraine-deployment -n xcube-ukraine

# Check pods
kubectl get pods -n xcube-ukraine -w
```

#### 5. Create Service
```bash
kubectl apply -f k8s/04-service.yaml

# Test service internally
kubectl run test-pod --rm -it --image=curlimages/curl -n xcube-ukraine -- \
  curl http://xcube-ukraine-service/xcube/datasets
```

#### 6. Configure Ingress
```bash
kubectl apply -f k8s/05-ingress.yaml

# Wait for Ingress IP
kubectl get ingress -n xcube-ukraine -w

# Test Ingress
INGRESS_IP=$(kubectl get ingress -n xcube-ukraine xcube-ukraine-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$INGRESS_IP/xcube/datasets
```

---

## Configuration

### Environment Variables

The deployment uses these environment variables (configured in `03-deployment.yaml`):

```yaml
env:
- name: AZURE_STORAGE_ACCOUNT_NAME
  valueFrom:
    secretKeyRef:
      name: azure-storage-credentials
      key: account-name
- name: AZURE_STORAGE_ACCOUNT_KEY
  valueFrom:
    secretKeyRef:
      name: azure-storage-credentials
      key: account-key
- name: AZURE_STORAGE_CONNECTION_STRING
  valueFrom:
    secretKeyRef:
      name: azure-storage-credentials
      key: connection-string
```

### Resource Limits

Configured in `03-deployment.yaml`:

```yaml
resources:
  limits:
    memory: "2Gi"
    cpu: "1000m"
  requests:
    memory: "512Mi"
    cpu: "250m"
```

Adjust based on your workload:
- **Light usage**: 256Mi-1Gi memory, 100m-500m CPU
- **Medium usage**: 512Mi-2Gi memory, 250m-1000m CPU
- **Heavy usage**: 1Gi-4Gi memory, 500m-2000m CPU

### Horizontal Pod Autoscaling

HPA configuration in `03-deployment.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Scaling behavior**:
- Scales up when CPU > 70%
- Scales down when CPU < 70% (with cooldown)
- Minimum 2 replicas (high availability)
- Maximum 10 replicas (cost control)

---

## Deployment Options

### Using the Deployment Script

The `deploy.sh` script provides several commands:

```bash
# Deploy everything
./deploy.sh deploy

# Check status
./deploy.sh status

# View logs
./deploy.sh logs

# Test service
./deploy.sh test

# Restart deployment (rolling restart)
./deploy.sh restart

# Scale manually
./deploy.sh scale 5

# Port forward to localhost
./deploy.sh port-forward

# Clean up everything
./deploy.sh cleanup
```

### Manual Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply in specific order
for file in k8s/0*.yaml; do
  kubectl apply -f "$file"
done
```

### Helm Chart (Advanced)

For advanced users, consider creating a Helm chart:

```bash
helm create xcube-ukraine
# Copy manifests to templates/
# Add values.yaml with configurable parameters
helm install xcube-ukraine ./xcube-ukraine -n xcube-ukraine --create-namespace
```

---

## Monitoring and Management

### Check Deployment Status

```bash
# Overall status
kubectl get all -n xcube-ukraine

# Detailed pod info
kubectl get pods -n xcube-ukraine -o wide

# Deployment status
kubectl describe deployment xcube-ukraine-deployment -n xcube-ukraine

# HPA status
kubectl get hpa -n xcube-ukraine
kubectl describe hpa xcube-ukraine-hpa -n xcube-ukraine
```

### View Logs

```bash
# Logs from all pods
kubectl logs -n xcube-ukraine -l app=xcube-ukraine

# Logs from specific pod
kubectl logs -n xcube-ukraine <pod-name>

# Follow logs
kubectl logs -n xcube-ukraine -l app=xcube-ukraine -f

# Logs from previous container (if crashed)
kubectl logs -n xcube-ukraine <pod-name> --previous
```

### Execute Commands in Pod

```bash
# Get shell access
kubectl exec -it -n xcube-ukraine <pod-name> -- /bin/bash

# Run one-off command
kubectl exec -n xcube-ukraine <pod-name> -- env

# Test Azure connection
kubectl exec -n xcube-ukraine <pod-name> -- \
  python -c "import fsspec; fs = fsspec.filesystem('abfs'); print(fs.ls('xcube'))"
```

### Performance Monitoring

```bash
# Resource usage
kubectl top pods -n xcube-ukraine
kubectl top nodes

# Events
kubectl get events -n xcube-ukraine --sort-by='.lastTimestamp'

# Watch pod scaling
watch kubectl get pods -n xcube-ukraine
```

---

## Troubleshooting

### Pods Not Starting

**Check pod status:**
```bash
kubectl get pods -n xcube-ukraine
kubectl describe pod -n xcube-ukraine <pod-name>
```

**Common issues:**

1. **ImagePullBackOff**
   - Image doesn't exist or is private
   - Check image name in `03-deployment.yaml`
   - Build and push image: `docker build -t your-registry/xcube-ukraine:latest -f Dockerfile.ukraine .`

2. **CrashLoopBackOff**
   - Application failing to start
   - Check logs: `kubectl logs -n xcube-ukraine <pod-name>`
   - Common causes: Invalid config, Azure credentials wrong, missing dependencies

3. **Pending**
   - Insufficient resources
   - Check: `kubectl describe pod -n xcube-ukraine <pod-name>`
   - Solution: Reduce resource requests or add more nodes

### Ingress Not Working

**Check Ingress status:**
```bash
kubectl get ingress -n xcube-ukraine
kubectl describe ingress -n xcube-ukraine xcube-ukraine-ingress
```

**Common issues:**

1. **No Ingress IP assigned**
   - Ingress controller not running
   - Check: `kubectl get pods -n ingress-nginx`
   - Install if missing (see Prerequisites)

2. **404 errors**
   - Path rewriting issue
   - Check annotation: `nginx.ingress.kubernetes.io/rewrite-target`
   - Test service directly: `kubectl port-forward -n xcube-ukraine service/xcube-ukraine-service 8080:80`

3. **502/503 errors**
   - Backend service unhealthy
   - Check pods: `kubectl get pods -n xcube-ukraine`
   - Check service: `kubectl get endpoints -n xcube-ukraine`

### Azure Connection Issues

**Test Azure connectivity:**
```bash
kubectl exec -n xcube-ukraine <pod-name> -- \
  python -c "
from azure.storage.blob import BlobServiceClient
import os
conn_str = os.environ['AZURE_STORAGE_CONNECTION_STRING']
client = BlobServiceClient.from_connection_string(conn_str)
container = client.get_container_client('data')
print('Connected:', container.exists())
"
```

**Check credentials:**
```bash
# Verify secret exists
kubectl get secret -n xcube-ukraine azure-storage-credentials

# Check if environment variables are set in pod
kubectl exec -n xcube-ukraine <pod-name> -- env | grep AZURE
```

### Performance Issues

1. **High CPU usage**
   - Check HPA: `kubectl get hpa -n xcube-ukraine`
   - HPA should scale automatically
   - Manual scale: `kubectl scale deployment xcube-ukraine-deployment -n xcube-ukraine --replicas=5`

2. **High memory usage**
   - Increase memory limits in `03-deployment.yaml`
   - Check for memory leaks in logs

3. **Slow response times**
   - Check Azure Blob Storage latency
   - Enable tile caching (add PersistentVolume)
   - Increase replicas

---

## Production Best Practices

### Security

1. **Use TLS/HTTPS**
   ```yaml
   # In 05-ingress.yaml, uncomment TLS section
   tls:
   - hosts:
     - your-domain.com
     secretName: xcube-tls-secret
   ```
   
   Create TLS secret:
   ```bash
   kubectl create secret tls xcube-tls-secret \
     --cert=path/to/tls.crt \
     --key=path/to/tls.key \
     -n xcube-ukraine
   ```

2. **Rotate Azure credentials**
   ```bash
   # Update secret
   kubectl create secret generic azure-storage-credentials \
     --from-literal=account-key='new-key' \
     --dry-run=client -o yaml | kubectl apply -n xcube-ukraine -f -
   
   # Restart deployment to pick up new credentials
   kubectl rollout restart deployment/xcube-ukraine-deployment -n xcube-ukraine
   ```

3. **Network Policies**
   ```yaml
   # Create network policy to restrict traffic
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: xcube-ukraine-netpol
     namespace: xcube-ukraine
   spec:
     podSelector:
       matchLabels:
         app: xcube-ukraine
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             name: ingress-nginx
   ```

### High Availability

1. **Pod Disruption Budget**
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: xcube-ukraine-pdb
     namespace: xcube-ukraine
   spec:
     minAvailable: 1
     selector:
       matchLabels:
         app: xcube-ukraine
   ```

2. **Multiple Ingress Controllers**
   - Deploy to multiple availability zones
   - Use external load balancer

3. **Backup and Disaster Recovery**
   - ConfigMap backups: `kubectl get configmap -n xcube-ukraine -o yaml > backup.yaml`
   - Secret backups (encrypted): `kubectl get secret -n xcube-ukraine -o yaml > secrets-backup.yaml`

### Performance Optimization

1. **Enable Tile Caching**
   
   Create PersistentVolumeClaim:
   ```yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: xcube-cache
     namespace: xcube-ukraine
   spec:
     accessModes:
     - ReadWriteMany
     resources:
       requests:
         storage: 100Gi
   ```
   
   Mount in deployment:
   ```yaml
   volumeMounts:
   - name: cache
     mountPath: /tmp/xcube-cache
   volumes:
   - name: cache
     persistentVolumeClaim:
       claimName: xcube-cache
   ```

2. **Optimize Resource Limits**
   - Monitor actual usage: `kubectl top pods -n xcube-ukraine`
   - Adjust limits based on P95 usage + 20% buffer

3. **Connection Pooling**
   - Already configured in deployment with `--processes 4 --address 0.0.0.0`

### Monitoring and Alerting

1. **Prometheus Monitoring**
   ```yaml
   # Add annotations to deployment
   annotations:
     prometheus.io/scrape: "true"
     prometheus.io/port: "8080"
     prometheus.io/path: "/metrics"
   ```

2. **Log Aggregation**
   - Use Fluentd, Loki, or ELK stack
   - Configure log retention policies

3. **Health Check Endpoints**
   - Already configured in `03-deployment.yaml`
   - Liveness: `/xcube/datasets` (checks if service is alive)
   - Readiness: `/xcube/datasets` (checks if service is ready)

### Cost Optimization

1. **Right-size resources**
   - Start small, scale based on metrics
   - Use HPA for automatic scaling

2. **Use spot/preemptible instances**
   - Configure node affinity for non-critical workloads

3. **Clean up unused resources**
   ```bash
   # Remove completed jobs
   kubectl delete jobs --field-selector status.successful=1 -n xcube-ukraine
   
   # Remove old replicasets
   kubectl delete replicaset --all -n xcube-ukraine
   ```

---

## Advanced Topics

### Custom Domain Setup

1. **Update DNS**
   ```bash
   # Get Ingress IP
   INGRESS_IP=$(kubectl get ingress -n xcube-ukraine -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
   
   # Create A record: your-domain.com -> $INGRESS_IP
   ```

2. **Update Ingress**
   ```yaml
   spec:
     rules:
     - host: your-domain.com
       http:
         paths:
         - path: /xcube
   ```

3. **Add TLS certificate**
   ```bash
   # Using cert-manager (recommended)
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   
   # Create ClusterIssuer for Let's Encrypt
   kubectl apply -f - <<EOF
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-prod
   spec:
     acme:
       server: https://acme-v02.api.letsencrypt.org/directory
       email: your-email@example.com
       privateKeySecretRef:
         name: letsencrypt-prod
       solvers:
       - http01:
           ingress:
             class: nginx
   EOF
   
   # Update Ingress with cert-manager annotation
   # cert-manager.io/cluster-issuer: "letsencrypt-prod"
   ```

### Multi-Environment Setup

```bash
# Development
kubectl create namespace xcube-ukraine-dev
kubectl apply -f k8s/ -n xcube-ukraine-dev

# Staging
kubectl create namespace xcube-ukraine-staging
kubectl apply -f k8s/ -n xcube-ukraine-staging

# Production
kubectl create namespace xcube-ukraine-prod
kubectl apply -f k8s/ -n xcube-ukraine-prod
```

### GitOps with ArgoCD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: xcube-ukraine
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/your-repo
    targetRevision: main
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: xcube-ukraine
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

## Summary

You now have a complete Kubernetes deployment for the Ukraine LWQ xcube service with:

- ✅ Scalable architecture (2-10 replicas with HPA)
- ✅ High availability (multiple replicas, health checks)
- ✅ Secure configuration (Kubernetes secrets)
- ✅ Production-ready (resource limits, probes, ingress)
- ✅ Easy management (deployment script with multiple commands)
- ✅ Reverse proxy support (NGINX Ingress with `/xcube/` path)

**Quick commands:**
```bash
# Deploy
./k8s/deploy.sh deploy

# Check status
./k8s/deploy.sh status

# Access locally
./k8s/deploy.sh port-forward

# Clean up
./k8s/deploy.sh cleanup
```

**Access URLs:**
- Production: `http://<INGRESS_IP>/xcube/`
- Development: `http://localhost:8080/xcube/` (with port-forward)

For questions or issues, check the [Troubleshooting](#troubleshooting) section or view logs with `./k8s/deploy.sh logs`.
