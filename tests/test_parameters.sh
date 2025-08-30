#!/bin/bash

# TVB - Parameter Combination Tests
# Test verschiedene Kombinationen von Command-Line-Parametern

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test directory
TEST_DIR="./test_param_output"
mkdir -p "$TEST_DIR"

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

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

cleanup() {
    log "Cleaning up test files..."
    rm -rf "$TEST_DIR"
}

trap cleanup EXIT

log "🔧 Starting TVB Parameter Combination Tests"
echo "============================================="

# Test 1: Basic help and version
run_test "Help command" "./tvb_wrapper.sh -h"
run_test "Version command" "./tvb_wrapper.sh --version"

# Test 2: Invalid combinations
run_test "Invalid parameter combination fails" "./tvb_wrapper.sh -i nonexistent.mp4 --invalid" "1"
run_test "Missing input fails" "./tvb_wrapper.sh -o $TEST_DIR" "1"

# Test 3: Format options
run_test "Movie format option" "./tvb_wrapper.sh -i nonexistent.mp4 -f movie -d"
run_test "TV Show format option" "./tvb_wrapper.sh -i nonexistent.mp4 -f tvshow -d"
run_test "Custom format option" "./tvb_wrapper.sh -i nonexistent.mp4 -f custom -d"

# Test 4: Output directory variations
run_test "Relative output path" "./tvb_wrapper.sh -i nonexistent.mp4 -o ./test_out -d"
run_test "Absolute output path" "./tvb_wrapper.sh -i nonexistent.mp4 -o $TEST_DIR -d"

# Test 5: Logging combinations
run_test "Verbose mode" "./tvb_wrapper.sh -i nonexistent.mp4 -v -d"
run_test "Debug mode" "./tvb_wrapper.sh -i nonexistent.mp4 --debug -d"
run_test "Verbose + Debug" "./tvb_wrapper.sh -i nonexistent.mp4 -v --debug -d"

# Test 6: Special modes
run_test "Dry-run mode" "./tvb_wrapper.sh -i nonexistent.mp4 -d"
run_test "Preview mode" "./tvb_wrapper.sh -i nonexistent.mp4 -P -d"
run_test "Merge mode" "./tvb_wrapper.sh -i nonexistent.mp4 -m -d"
run_test "Hibernate mode" "./tvb_wrapper.sh -i nonexistent.mp4 -H -d"

# Test 7: Combined special modes
run_test "Dry-run + Preview" "./tvb_wrapper.sh -i nonexistent.mp4 -d -P"
run_test "Dry-run + Merge" "./tvb_wrapper.sh -i nonexistent.mp4 -d -m"
run_test "Dry-run + Hibernate" "./tvb_wrapper.sh -i nonexistent.mp4 -d -H"

# Test 8: Format + Special modes
run_test "Movie + Dry-run + Verbose" "./tvb_wrapper.sh -i nonexistent.mp4 -f movie -d -v"
run_test "TV Show + Preview + Debug" "./tvb_wrapper.sh -i nonexistent.mp4 -f tvshow -P --debug -d"

# Test 9: Complex combinations
run_test "All options combination" "./tvb_wrapper.sh -i nonexistent.mp4 -o $TEST_DIR -f movie -d -P -m -H -v --debug"

# Test 10: Parameter order independence
run_test "Parameter order 1" "./tvb_wrapper.sh -i nonexistent.mp4 -d -v"
run_test "Parameter order 2" "./tvb_wrapper.sh -v -d -i nonexistent.mp4"

# Test 11: Short vs long parameters
run_test "Short parameters" "./tvb_wrapper.sh -i nonexistent.mp4 -d -v"
run_test "Long parameters" "./tvb_wrapper.sh -i nonexistent.mp4 --dry-run --verbose"

# Test 12: Case sensitivity (should be case sensitive for formats)
run_test "Lowercase format" "./tvb_wrapper.sh -i nonexistent.mp4 -f movie -d"
run_test "Uppercase format fails" "./tvb_wrapper.sh -i nonexistent.mp4 -f MOVIE -d" "1"

# Test 13: Multiple same parameters (should fail)
run_test "Duplicate input parameter fails" "./tvb_wrapper.sh -i file1.mp4 -i file2.mp4 -d" "1"
run_test "Duplicate output parameter fails" "./tvb_wrapper.sh -i nonexistent.mp4 -o /tmp -o /tmp2 -d" "1"

# Test 14: Parameter spacing
run_test "Normal spacing" "./tvb_wrapper.sh -i nonexistent.mp4 -d"
run_test "Clustered short options" "./tvb_wrapper.sh -dv -i nonexistent.mp4" "1"  # This might not work

# Test 15: Quotes handling
run_test "Quoted input path" "./tvb_wrapper.sh -i 'nonexistent.mp4' -d"
run_test "Quoted output path" "./tvb_wrapper.sh -i nonexistent.mp4 -o '$TEST_DIR' -d"

# Test 16: Directory vs File input
run_test "Directory input" "./tvb_wrapper.sh -i /tmp -d -o $TEST_DIR"
run_test "File input with path" "./tvb_wrapper.sh -i /tmp/test.mp4 -d -o $TEST_DIR"

# Summary
echo ""
echo "============================================="
log "🔧 Parameter Test Summary:"
echo "Total tests run: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 All parameter combination tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some parameter tests failed. Please check the output above.${NC}"
    exit 1
fi
