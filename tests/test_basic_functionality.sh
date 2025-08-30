#!/bin/bash

# TVB - Basic Functionality Tests
# Test grundlegende Funktionen ohne tatsächliches Encoding

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test directory setup
TEST_DIR="./test_output"
mkdir -p "$TEST_DIR"

# Log function
log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

# Success function
success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

# Error function
error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

# Warning function
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test function
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_exit="$3"

    ((TESTS_RUN++))
    log "Running test: $test_name"

    if eval "$command"; then
        if [[ "$expected_exit" == "0" ]] || [[ -z "$expected_exit" ]]; then
            success "$test_name"
        else
            error "$test_name (expected failure but succeeded)"
        fi
    else
        if [[ "$expected_exit" == "1" ]]; then
            success "$test_name (expected failure)"
        else
            error "$test_name (unexpected failure)"
        fi
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up test files..."
    rm -rf "$TEST_DIR"
}

# Trap for cleanup on exit
trap cleanup EXIT

log "🧪 Starting TVB Basic Functionality Tests"
echo "=============================================="

# Test 1: Check if script exists and is executable
run_test "Script exists and is executable" "test -x ./tvb_wrapper.sh"

# Test 2: Version information
run_test "Version command works" "./tvb_wrapper.sh --version"

# Test 3: Help command works
run_test "Help command works" "./tvb_wrapper.sh -h | grep -q 'Usage:'"

# Test 4: Invalid parameter should fail
run_test "Invalid parameter fails" "./tvb_wrapper.sh --invalid-param" "1"

# Test 5: Missing required input parameter should fail
run_test "Missing input parameter fails" "./tvb_wrapper.sh -o /tmp" "1"

# Test 6: Check if Python script can be imported
run_test "Python script can be executed" "python3 tvb.py --version"

# Test 7: Test dry-run with non-existent file (should show error)
run_test "Dry-run with invalid file shows error" "./tvb_wrapper.sh -i nonexistent.mp4 -d -o $TEST_DIR" "1"

# Test 8: Test directory creation
run_test "Output directory creation" "mkdir -p $TEST_DIR/test && rmdir $TEST_DIR/test"

# Test 9: Check config file exists
run_test "Config file exists" "test -f tvb-config.ini"

# Test 10: Check if required tools are available (at least in PATH)
if command -v ruby &> /dev/null; then
    success "Ruby is available"
else
    warning "Ruby not found in PATH"
fi

if command -v HandBrakeCLI &> /dev/null; then
    success "HandBrakeCLI is available"
else
    warning "HandBrakeCLI not found in PATH"
fi

# Test 11: Test config file parsing
run_test "Config file is valid INI" "python3 -c \"import configparser; c = configparser.ConfigParser(); c.read('tvb-config.ini'); print('Config parsed successfully')\""

# Test 12: Test that script shows proper error for missing input
run_test "Proper error message for missing input" "./tvb_wrapper.sh -o $TEST_DIR 2>&1 | grep -q 'error\|Error\|ERROR'"

# Summary
echo ""
echo "=============================================="
log "🧪 Test Summary:"
echo "Total tests run: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 All basic functionality tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed. Please check the output above.${NC}"
    exit 1
fi
