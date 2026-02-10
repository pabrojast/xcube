#!/bin/bash
# ==============================================================================
# Kubernetes Deployment Script for Ukraine LWQ xcube Service
# ==============================================================================
# This script deploys the xcube service to a Kubernetes cluster with all 
# required resources: namespace, secrets, configmaps, deployment, service, and ingress
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="xcube-ukraine"
K8S_DIR="$(dirname "$0")"

# ==============================================================================
# Helper Functions
# ==============================================================================

print_header() {
    echo -e "\n${BLUE}===================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ==============================================================================
# Validation Functions
# ==============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    print_success "kubectl found: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    print_success "Connected to Kubernetes cluster"
    
    # Display cluster info
    print_info "Cluster: $(kubectl config current-context)"
}

check_azure_credentials() {
    print_header "Checking Azure Credentials"
    
    if [ -z "$AZURE_STORAGE_ACCOUNT_NAME" ]; then
        print_warning "AZURE_STORAGE_ACCOUNT_NAME not set. Using default from secret."
    else
        print_success "AZURE_STORAGE_ACCOUNT_NAME: $AZURE_STORAGE_ACCOUNT_NAME"
    fi
    
    if [ -z "$AZURE_STORAGE_ACCOUNT_KEY" ]; then
        print_warning "AZURE_STORAGE_ACCOUNT_KEY not set. Make sure it's configured in k8s/01-secret.yaml"
    else
        print_success "AZURE_STORAGE_ACCOUNT_KEY is set (hidden)"
    fi
}

# ==============================================================================
# Deployment Functions
# ==============================================================================

apply_manifest() {
    local file=$1
    local description=$2
    
    if [ ! -f "$file" ]; then
        print_error "File not found: $file"
        return 1
    fi
    
    print_info "Applying $description..."
    if kubectl apply -f "$file"; then
        print_success "$description applied"
        return 0
    else
        print_error "Failed to apply $description"
        return 1
    fi
}

deploy_all() {
    print_header "Deploying xcube Ukraine LWQ Service"
    
    # Apply manifests in order
    apply_manifest "$K8S_DIR/00-namespace.yaml" "Namespace"
    
    # Wait for namespace to be ready
    print_info "Waiting for namespace to be ready..."
    kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/$NAMESPACE --timeout=30s
    
    apply_manifest "$K8S_DIR/01-secret.yaml" "Secret (Azure credentials)"
    apply_manifest "$K8S_DIR/02-configmap.yaml" "ConfigMap (xcube config)"
    apply_manifest "$K8S_DIR/03-deployment.yaml" "Deployment"
    apply_manifest "$K8S_DIR/04-service.yaml" "Service"
    apply_manifest "$K8S_DIR/05-ingress.yaml" "Ingress"
    
    print_success "All resources applied successfully"
}

wait_for_deployment() {
    print_header "Waiting for Deployment to be Ready"
    
    print_info "Waiting for deployment rollout..."
    if kubectl rollout status deployment/xcube-ukraine-deployment -n $NAMESPACE --timeout=5m; then
        print_success "Deployment is ready"
    else
        print_error "Deployment rollout failed or timed out"
        return 1
    fi
    
    # Wait for at least one pod to be ready
    print_info "Waiting for pods to be ready..."
    if kubectl wait --for=condition=ready pod -l app=xcube-ukraine -n $NAMESPACE --timeout=5m; then
        print_success "Pods are ready"
    else
        print_error "Pods failed to become ready"
        return 1
    fi
}

show_status() {
    print_header "Deployment Status"
    
    echo -e "${BLUE}Pods:${NC}"
    kubectl get pods -n $NAMESPACE -o wide
    
    echo -e "\n${BLUE}Services:${NC}"
    kubectl get services -n $NAMESPACE
    
    echo -e "\n${BLUE}Ingress:${NC}"
    kubectl get ingress -n $NAMESPACE
    
    echo -e "\n${BLUE}HPA (Horizontal Pod Autoscaler):${NC}"
    kubectl get hpa -n $NAMESPACE 2>/dev/null || echo "No HPA found (may take a moment to appear)"
}

show_logs() {
    print_header "Recent Logs"
    
    local pod=$(kubectl get pods -n $NAMESPACE -l app=xcube-ukraine -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod" ]; then
        print_warning "No pods found"
        return
    fi
    
    print_info "Showing logs from pod: $pod"
    kubectl logs -n $NAMESPACE $pod --tail=50
}

test_service() {
    print_header "Testing Service"
    
    # Get ingress info
    local ingress_ip=$(kubectl get ingress -n $NAMESPACE xcube-ukraine-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    local ingress_host=$(kubectl get ingress -n $NAMESPACE xcube-ukraine-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
    
    local endpoint=""
    if [ -n "$ingress_ip" ]; then
        endpoint="http://$ingress_ip/xcube/datasets"
    elif [ -n "$ingress_host" ]; then
        endpoint="http://$ingress_host/xcube/datasets"
    else
        print_warning "Ingress endpoint not yet available. Try port-forwarding:"
        print_info "kubectl port-forward -n $NAMESPACE service/xcube-ukraine-service 8080:80"
        print_info "Then access: http://localhost:8080/xcube/datasets"
        return
    fi
    
    print_info "Testing endpoint: $endpoint"
    if curl -f -s "$endpoint" > /dev/null; then
        print_success "Service is responding"
        curl -s "$endpoint" | head -20
    else
        print_warning "Service not yet accessible or not responding"
    fi
}

cleanup() {
    print_header "Cleaning Up Deployment"
    
    read -p "This will delete all resources in namespace '$NAMESPACE'. Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleanup cancelled"
        return
    fi
    
    print_info "Deleting namespace and all resources..."
    kubectl delete namespace $NAMESPACE --wait=true
    print_success "Cleanup complete"
}

show_usage() {
    cat << EOF
${BLUE}Ukraine LWQ xcube Service - Kubernetes Deployment Script${NC}

Usage: $0 [COMMAND]

Commands:
    deploy          Deploy all resources to Kubernetes (default)
    status          Show deployment status
    logs            Show recent logs from pods
    test            Test the deployed service
    restart         Restart the deployment (rolling restart)
    scale [N]       Scale deployment to N replicas
    port-forward    Create port-forward to local machine
    cleanup         Delete all resources (prompts for confirmation)
    help            Show this help message

Examples:
    $0 deploy                    # Deploy the service
    $0 status                    # Check deployment status
    $0 scale 5                   # Scale to 5 replicas
    $0 port-forward              # Access service locally
    $0 cleanup                   # Remove all resources

Environment Variables:
    AZURE_STORAGE_ACCOUNT_NAME   Azure storage account name
    AZURE_STORAGE_ACCOUNT_KEY    Azure storage account key

Note: Make sure to update k8s/01-secret.yaml with your Azure credentials
      before deploying.
EOF
}

# ==============================================================================
# Command Handlers
# ==============================================================================

cmd_deploy() {
    check_prerequisites
    check_azure_credentials
    deploy_all
    wait_for_deployment
    show_status
    
    print_header "Deployment Complete"
    print_success "xcube Ukraine LWQ service is now deployed!"
    print_info "Access the service at: http://<your-ingress-ip>/xcube/"
    print_info "Use 'kubectl get ingress -n $NAMESPACE' to get the ingress IP"
    print_info "Or use '$0 port-forward' for local access"
}

cmd_status() {
    check_prerequisites
    show_status
}

cmd_logs() {
    check_prerequisites
    show_logs
}

cmd_test() {
    check_prerequisites
    test_service
}

cmd_restart() {
    check_prerequisites
    print_header "Restarting Deployment"
    kubectl rollout restart deployment/xcube-ukraine-deployment -n $NAMESPACE
    kubectl rollout status deployment/xcube-ukraine-deployment -n $NAMESPACE
    print_success "Deployment restarted"
}

cmd_scale() {
    local replicas=$1
    if [ -z "$replicas" ]; then
        print_error "Please specify number of replicas"
        echo "Usage: $0 scale <number>"
        exit 1
    fi
    
    check_prerequisites
    print_header "Scaling Deployment"
    kubectl scale deployment/xcube-ukraine-deployment -n $NAMESPACE --replicas=$replicas
    print_success "Scaled to $replicas replicas"
    kubectl get pods -n $NAMESPACE -l app=xcube-ukraine
}

cmd_port_forward() {
    check_prerequisites
    print_header "Port Forwarding"
    print_info "Forwarding local port 8080 to service port 80"
    print_info "Access the service at: http://localhost:8080/xcube/datasets"
    print_warning "Press Ctrl+C to stop port forwarding"
    kubectl port-forward -n $NAMESPACE service/xcube-ukraine-service 8080:80
}

cmd_cleanup() {
    check_prerequisites
    cleanup
}

# ==============================================================================
# Main Script
# ==============================================================================

main() {
    local command=${1:-deploy}
    
    case $command in
        deploy)
            cmd_deploy
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs
            ;;
        test)
            cmd_test
            ;;
        restart)
            cmd_restart
            ;;
        scale)
            cmd_scale "$2"
            ;;
        port-forward|forward)
            cmd_port_forward
            ;;
        cleanup|delete)
            cmd_cleanup
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
