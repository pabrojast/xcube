#!/bin/bash

# ============================================================================
# Quick Test Script for Ukraine LWQ Service
# ============================================================================
# This script performs basic tests to verify the xcube service is working
# ============================================================================

echo "=========================================="
echo "🧪 Testing Ukraine LWQ Service"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8080"
FAILED=0
PASSED=0

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"
    
    echo -n "Testing $name... "
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $response_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response_code, expected $expected_code)"
        ((FAILED++))
        return 1
    fi
}

# Function to test JSON response
test_json_response() {
    local name="$1"
    local url="$2"
    local jq_filter="$3"
    
    echo -n "Testing $name... "
    
    result=$(curl -s "$url" | python -m json.tool 2>/dev/null | grep -c "$jq_filter")
    
    if [ "$result" -gt 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "📡 Testing API Endpoints..."
echo ""

# Test 1: Server is running
test_endpoint "Server Status" "$BASE_URL/"

# Test 2: Datasets endpoint
test_endpoint "Datasets List" "$BASE_URL/datasets"

# Test 3: Ukraine dataset exists
test_json_response "Ukraine Dataset" "$BASE_URL/datasets" "ukraine_lwq"

# Test 4: Dataset metadata
test_endpoint "Dataset Metadata" "$BASE_URL/datasets/ukraine_lwq"

# Test 5: WMTS Capabilities
test_endpoint "WMTS Capabilities" "$BASE_URL/wmts/1.0.0/WMTSCapabilities.xml"

# Test 6: OpenAPI documentation
test_endpoint "OpenAPI Docs" "$BASE_URL/openapi.html"

# Test 7: Viewer
test_endpoint "Viewer Interface" "$BASE_URL/viewer"

echo ""
echo "🗺️ Testing WMTS Tiles..."
echo ""

# Test 8: Tile for turbidity_mean
test_endpoint "Turbidity Tile" "$BASE_URL/wmts/1.0.0/tile/ukraine_lwq/turbidity_mean/7/42/67.png"

# Test 9: Tile for Rw490_rep
test_endpoint "Rw490 Tile" "$BASE_URL/wmts/1.0.0/tile/ukraine_lwq/Rw490_rep/7/42/67.png"

echo ""
echo "📊 Testing Time Series API..."
echo ""

# Test 10: Time series for Kiev location
test_endpoint "Time Series (Kiev)" "$BASE_URL/timeseries/ukraine_lwq/turbidity_mean?lat=50.45&lon=30.52"

# Test 11: Time series for another location
test_endpoint "Time Series (Dnipro)" "$BASE_URL/timeseries/ukraine_lwq/Rw560_rep?lat=48.5&lon=35.0"

echo ""
echo "🔍 Testing Dataset Content..."
echo ""

# Test 12: Check if variables are listed
echo -n "Checking Variables... "
var_count=$(curl -s "$BASE_URL/datasets/ukraine_lwq" | python -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('variables', [])))" 2>/dev/null)

if [ "$var_count" -gt 5 ]; then
    echo -e "${GREEN}✓ PASSED${NC} ($var_count variables found)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (Only $var_count variables found, expected > 5)"
    ((FAILED++))
fi

# Test 13: Check if time dimension exists
echo -n "Checking Time Dimension... "
has_time=$(curl -s "$BASE_URL/datasets/ukraine_lwq" | grep -c "\"time\"")

if [ "$has_time" -gt 0 ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

# Test 14: Check bounding box
echo -n "Checking Bounding Box... "
bbox=$(curl -s "$BASE_URL/datasets/ukraine_lwq" | python -c "import sys, json; d=json.load(sys.stdin); print(d.get('bbox', []))" 2>/dev/null)

if [[ "$bbox" == *"22.0"* ]] && [[ "$bbox" == *"52.5"* ]]; then
    echo -e "${GREEN}✓ PASSED${NC} ($bbox)"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (Unexpected bbox: $bbox)"
    ((FAILED++))
fi

echo ""
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="
echo ""

TOTAL=$((PASSED + FAILED))

echo "Total tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED${NC}"
else
    echo -e "${GREEN}Failed: $FAILED${NC}"
fi

echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Service is working correctly.${NC}"
    echo ""
    echo "🌐 You can now:"
    echo "  - Open the viewer: file://$(pwd)/ukraine_lwq_viewer.html"
    echo "  - Browse API docs: http://localhost:8080/openapi.html"
    echo "  - Use in QGIS: http://localhost:8080/wmts/1.0.0/WMTSCapabilities.xml"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the service configuration.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Make sure the server is running: ./start_xcube_ukraine.sh"
    echo "  2. Check server logs for errors"
    echo "  3. Verify Azure credentials are correct"
    echo "  4. See TROUBLESHOOTING_UKRAINE.md for more help"
    exit 1
fi
