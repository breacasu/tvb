#!/bin/bash

# TVB - Run All Tests
# Führt alle verfügbaren Tests aus

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Global counters
TOTAL_TESTS_RUN=0
TOTAL_TESTS_PASSED=0
TOTAL_TESTS_FAILED=0

# Test directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

header() {
    echo -e "${PURPLE}$1${NC}"
    echo "=============================================="
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to run a test script and collect results
run_test_script() {
    local script_name="$1"
    local script_path="tests/$script_name"

    if [[ ! -f "$script_path" ]]; then
        warning "Test script $script_name not found, skipping..."
        return
    fi

    log "Running $script_name..."

    # Make script executable if not already
    chmod +x "$script_path"

    # Run the test script and capture output
    if "$script_path"; then
        success "$script_name completed successfully"
    else
        error "$script_name failed"
        ((TOTAL_TESTS_FAILED++))
    fi

    ((TOTAL_TESTS_RUN++))
}

# Pre-test checks
header "🔍 TVB Pre-Test Checks"

# Check if required files exist
if [[ ! -f "tvb.py" ]]; then
    error "tvb.py not found!"
    exit 1
fi

if [[ ! -f "tvb_wrapper.sh" ]]; then
    error "tvb_wrapper.sh not found!"
    exit 1
fi

if [[ ! -f "tvb-config.ini" ]]; then
    error "tvb-config.ini not found!"
    exit 1
fi

success "All required files found"

# Check if scripts are executable
if [[ ! -x "tvb_wrapper.sh" ]]; then
    warning "tvb_wrapper.sh is not executable, making it executable..."
    chmod +x "tvb_wrapper.sh"
fi

success "Scripts are executable"

# Check Python availability
if command -v python3 &> /dev/null; then
    success "Python 3 is available"
else
    error "Python 3 not found!"
    exit 1
fi

# Run individual test suites
header "🧪 Running TVB Test Suites"

run_test_script "test_basic_functionality.sh"
run_test_script "test_config_options.sh"
run_test_script "test_parameters.sh"
run_test_script "test_error_cases.sh"

# Post-test summary
header "📊 Test Summary"

echo "Test suites completed: $TOTAL_TESTS_RUN"
if [[ $TOTAL_TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 All test suites passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. ✅ Review TVB-TEST-CHECKLIST.md for manual tests"
    echo "2. 🧪 Test with real video files"
    echo "3. 📊 Check statistics and logging"
    echo "4. 🚀 Ready for production use!"
    exit 0
else
    echo -e "${RED}💥 $TOTAL_TESTS_FAILED test suite(s) failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check individual test output above"
    echo "2. Verify tool installations (Ruby, HandBrakeCLI, etc.)"
    echo "3. Check file permissions"
    echo "4. Review log files for details"
    exit 1
fi
