# Kubernetes Deployment Files - Ukraine LWQ xcube Service

This folder contains all Kubernetes manifests needed to deploy the Ukraine LWQ xcube service with NGINX Ingress support for `/xcube/` path prefix.

## 📁 Files Overview

| File | Description |
|------|-------------|
| `00-namespace.yaml` | Creates the `xcube-ukraine` namespace |
| `01-secret.yaml` | Azure Storage credentials (account name, key, connection string) |
| `02-configmap.yaml` | xcube server configuration (DataStores, Datasets, Styles) |
| `03-deployment.yaml` | Main deployment with 2-10 replicas, HPA, probes, and resource limits |
| `04-service.yaml` | ClusterIP service with session affinity for load balancing |
| `05-ingress.yaml` | NGINX Ingress for `/xcube/*` path routing with CORS |
| `deploy.sh` | Automated deployment script with multiple commands |
| `K8S_GUIDE.md` | Complete deployment guide and troubleshooting |

## 🚀 Quick Start

### 1. Prerequisites
- Kubernetes cluster (1.19+)
- kubectl installed and configured
- NGINX Ingress Controller installed
- Azure Storage credentials

### 2. Configure Azure Credentials

Edit `01-secret.yaml` and update with your base64-encoded credentials:
```bash
# Encode your credentials
echo -n "ihpwinsdata" | base64
echo -n "your-azure-account-key" | base64
echo -n "your-connection-string" | base64
```

### 3. Deploy

```bash
# Make script executable (if not already)
chmod +x deploy.sh

# Deploy everything
./deploy.sh deploy
```

### 4. Access Service

**Via Ingress (production):**
```bash
# Get Ingress IP
kubectl get ingress -n xcube-ukraine

# Access
curl http://<INGRESS_IP>/xcube/datasets
```

**Via Port Forward (development):**
```bash
./deploy.sh port-forward

# In another terminal
curl http://localhost:8080/xcube/datasets
```

## 📋 Available Commands

The `deploy.sh` script provides these commands:

```bash
./deploy.sh deploy         # Deploy all resources
./deploy.sh status         # Show deployment status
./deploy.sh logs           # View recent logs
./deploy.sh test           # Test the service
./deploy.sh restart        # Rolling restart
./deploy.sh scale 5        # Scale to 5 replicas
./deploy.sh port-forward   # Forward to localhost:8080
./deploy.sh cleanup        # Delete all resources
./deploy.sh help           # Show help
```

## 🔧 Manual Deployment

If you prefer to deploy manually:

```bash
# Apply all manifests in order
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-secret.yaml
kubectl apply -f 02-configmap.yaml
kubectl apply -f 03-deployment.yaml
kubectl apply -f 04-service.yaml
kubectl apply -f 05-ingress.yaml

# Check status
kubectl get all -n xcube-ukraine

# Wait for rollout
kubectl rollout status deployment/xcube-ukraine-deployment -n xcube-ukraine
```

## 📊 Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│          Internet / Users                       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│     NGINX Ingress Controller                    │
│     (routes /xcube/* traffic)                   │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│     Kubernetes Service (ClusterIP)              │
│     (load balances with session affinity)       │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  xcube Pod 1 │  │  xcube Pod 2 │  ... (2-10 pods)
│  with HPA    │  │  with HPA    │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
┌─────────────────────────────────────────────────┐
│  Azure Blob Storage (ukraine_lwq.zarr)          │
└─────────────────────────────────────────────────┘
```

## ⚙️ Configuration Details

### Resources
- **Requests**: 250m CPU, 512Mi memory
- **Limits**: 1000m CPU, 2Gi memory

### Autoscaling
- **Min replicas**: 2 (high availability)
- **Max replicas**: 10 (cost control)
- **Target CPU**: 70%

### Health Checks
- **Liveness probe**: `/xcube/datasets` every 30s
- **Readiness probe**: `/xcube/datasets` every 10s
- **Startup probe**: `/xcube/datasets` up to 5 minutes

### Ingress
- **Path**: `/xcube(/|$)(.*)`
- **CORS**: Enabled for all origins
- **Proxy timeout**: 600 seconds
- **Max body size**: 50MB

## 🔍 Monitoring

### Check Pods
```bash
kubectl get pods -n xcube-ukraine
kubectl describe pod <pod-name> -n xcube-ukraine
kubectl logs -n xcube-ukraine -l app=xcube-ukraine
```

### Check Scaling
```bash
kubectl get hpa -n xcube-ukraine
kubectl top pods -n xcube-ukraine
```

### Check Ingress
```bash
kubectl get ingress -n xcube-ukraine
kubectl describe ingress xcube-ukraine-ingress -n xcube-ukraine
```

## 🐛 Troubleshooting

### Pods not starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n xcube-ukraine

# Check logs
kubectl logs <pod-name> -n xcube-ukraine

# Check events
kubectl get events -n xcube-ukraine --sort-by='.lastTimestamp'
```

### Ingress not working
```bash
# Check Ingress controller
kubectl get pods -n ingress-nginx

# Test service directly
kubectl port-forward -n xcube-ukraine service/xcube-ukraine-service 8080:80

# Check endpoints
kubectl get endpoints -n xcube-ukraine
```

### Azure connection issues
```bash
# Verify secret
kubectl get secret azure-storage-credentials -n xcube-ukraine

# Check environment variables in pod
kubectl exec -n xcube-ukraine <pod-name> -- env | grep AZURE

# Test Azure connection
kubectl exec -n xcube-ukraine <pod-name> -- \
  python -c "import fsspec; fs = fsspec.filesystem('abfs'); print(fs.ls('xcube'))"
```

## 🔐 Security Notes

1. **Never commit secrets**: The `01-secret.yaml` file contains base64-encoded credentials. Keep it secure!
2. **Use TLS**: For production, enable HTTPS by uncommenting TLS section in `05-ingress.yaml`
3. **Rotate credentials**: Periodically update Azure credentials and restart pods
4. **Network policies**: Consider adding NetworkPolicies for additional security

## 📚 Documentation

See `K8S_GUIDE.md` for:
- Detailed setup instructions
- Advanced configuration options
- Production best practices
- Performance tuning
- Security hardening
- Monitoring and alerting
- Troubleshooting guide

## 🌐 API Endpoints

Once deployed, the service provides these endpoints:

- **Datasets**: `GET http://<IP>/xcube/datasets`
- **Dataset info**: `GET http://<IP>/xcube/datasets/ukraine_lwq`
- **WMTS tiles**: `GET http://<IP>/xcube/wmts/1.0.0/tile/ukraine_lwq/{var}/{z}/{y}/{x}.png`
- **Time series**: `POST http://<IP>/xcube/timeseries/ukraine_lwq/{var}`
  ```json
  {
    "type": "Point",
    "coordinates": [30.5, 50.4]
  }
  ```

## 🆘 Support

If you encounter issues:

1. Check `K8S_GUIDE.md` troubleshooting section
2. View logs: `./deploy.sh logs`
3. Check status: `./deploy.sh status`
4. Test service: `./deploy.sh test`

## 📝 Example Usage

```bash
# Deploy the service
./deploy.sh deploy

# Wait for it to be ready (automatic in deploy command)
kubectl wait --for=condition=ready pod -l app=xcube-ukraine -n xcube-ukraine --timeout=5m

# Get Ingress IP
INGRESS_IP=$(kubectl get ingress -n xcube-ukraine -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test datasets endpoint
curl http://$INGRESS_IP/xcube/datasets

# Test WMTS tile
curl http://$INGRESS_IP/xcube/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/3/4/2.png -o tile.png

# Test time series (POST with GeoJSON)
curl -X POST http://$INGRESS_IP/xcube/timeseries/ukraine_lwq/turbidity_mean \
  -H "Content-Type: application/json" \
  -d '{"type": "Point", "coordinates": [30.5, 50.4]}'

# Scale up for high traffic
./deploy.sh scale 10

# Monitor performance
kubectl top pods -n xcube-ukraine

# View logs
./deploy.sh logs

# Clean up when done
./deploy.sh cleanup
```

## 🔄 Updates and Maintenance

### Update Configuration
```bash
# Edit ConfigMap
kubectl edit configmap xcube-ukraine-config -n xcube-ukraine

# Or apply new config
kubectl apply -f 02-configmap.yaml

# Restart pods to pick up changes
./deploy.sh restart
```

### Update Image
```bash
# Edit deployment
kubectl edit deployment xcube-ukraine-deployment -n xcube-ukraine

# Or update image directly
kubectl set image deployment/xcube-ukraine-deployment \
  xcube-ukraine=your-registry/xcube-ukraine:new-tag \
  -n xcube-ukraine

# Watch rollout
kubectl rollout status deployment/xcube-ukraine-deployment -n xcube-ukraine
```

### Backup Configuration
```bash
# Backup all resources
kubectl get all,configmap,secret,ingress -n xcube-ukraine -o yaml > backup.yaml

# Restore from backup
kubectl apply -f backup.yaml
```

---

**Ready to deploy?** Run `./deploy.sh deploy` and your xcube service will be live! 🚀
