#!/bin/bash

# TVB - Error Cases & Edge Cases Tests
# Test Fehlerbehandlung und Grenzfälle

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
TEST_DIR="./test_error_output"
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
    # Remove any test files we created
    rm -f /tmp/test_empty_file
    rm -f /tmp/test_readonly_file
}

trap cleanup EXIT

log "🚨 Starting TVB Error Cases & Edge Cases Tests"
echo "================================================"

# Test 1: Non-existent file
run_test "Non-existent input file fails" "./tvb_wrapper.sh -i /nonexistent/file.mp4 -d" "1"

# Test 2: Non-existent directory
run_test "Non-existent input directory fails" "./tvb_wrapper.sh -i /nonexistent/directory -d" "1"

# Test 3: Empty file
touch /tmp/test_empty_file
run_test "Empty input file fails" "./tvb_wrapper.sh -i /tmp/test_empty_file -d" "1"

# Test 4: Read-only file (if we can create one)
touch /tmp/test_readonly_file
chmod 444 /tmp/test_readonly_file
run_test "Read-only input file fails" "./tvb_wrapper.sh -i /tmp/test_readonly_file -d" "1"

# Test 5: Invalid output directory (read-only parent)
run_test "Invalid output directory fails" "./tvb_wrapper.sh -i /tmp/test_readonly_file -o /nonexistent/path -d" "1"

# Test 6: File with special characters in name
touch "$TEST_DIR/test file with spaces.mp4"
run_test "File with spaces in name" "./tvb_wrapper.sh -i '$TEST_DIR/test file with spaces.mp4' -d"

# Test 7: File with unicode characters
touch "$TEST_DIR/test_ñ_ф_文件.mp4"
run_test "File with unicode characters" "./tvb_wrapper.sh -i '$TEST_DIR/test_ñ_ф_文件.mp4' -d"

# Test 8: Directory without video files
EMPTY_DIR="$TEST_DIR/empty_dir"
mkdir -p "$EMPTY_DIR"
run_test "Directory without video files fails" "./tvb_wrapper.sh -i $EMPTY_DIR -d" "1"

# Test 9: Directory with only non-video files
NONVIDEO_DIR="$TEST_DIR/nonvideo_dir"
mkdir -p "$NONVIDEO_DIR"
touch "$NONVIDEO_DIR/test.txt"
touch "$NONVIDEO_DIR/test.jpg"
run_test "Directory with only non-video files fails" "./tvb_wrapper.sh -i $NONVIDEO_DIR -d" "1"

# Test 10: Invalid format specification
run_test "Invalid format specification fails" "./tvb_wrapper.sh -i /tmp/test_readonly_file -f invalid_format -d" "1"

# Test 11: Out of range CPU limit percentage
log "Testing CPU limit edge cases..."

# Temporarily modify config for testing
cp tvb-config.ini tvb-config.ini.bak

# Test high CPU limit
sed -i.bak 's/cpulimitpercent = 600/cpulimitpercent = 1000/' tvb-config.ini
run_test "High CPU limit percentage works" "./tvb_wrapper.sh --version"

# Test zero CPU limit
sed -i.bak 's/cpulimitpercent = 1000/cpulimitpercent = 0/' tvb-config.ini
run_test "Zero CPU limit percentage works" "./tvb_wrapper.sh --version"

# Restore config
cp tvb-config.ini.bak tvb-config.ini

# Test 12: Network path (might not be available)
# run_test "Network path handling" "./tvb_wrapper.sh -i //server/share/video.mp4 -d" "1"

# Test 13: Very long path
LONG_PATH="$TEST_DIR/"
for i in {1..10}; do
    LONG_PATH="${LONG_PATH}very_long_subdirectory_name_that_might_cause_issues_"
done
LONG_PATH="${LONG_PATH}test.mp4"
mkdir -p "$(dirname "$LONG_PATH")"
touch "$LONG_PATH"
run_test "Very long file path" "./tvb_wrapper.sh -i '$LONG_PATH' -d"

# Test 14: Multiple dots in filename
touch "$TEST_DIR/test.file.with.multiple.dots.mp4"
run_test "Filename with multiple dots" "./tvb_wrapper.sh -i '$TEST_DIR/test.file.with.multiple.dots.mp4' -d"

# Test 15: Hidden files
touch "$TEST_DIR/.hidden_video.mp4"
run_test "Hidden file" "./tvb_wrapper.sh -i '$TEST_DIR/.hidden_video.mp4' -d"

# Test 16: File starting with dash
touch "$TEST_DIR/-dash-start.mp4"
run_test "File starting with dash" "./tvb_wrapper.sh -i '$TEST_DIR/-dash-start.mp4' -d"

# Test 17: Directory permissions
NOACCESS_DIR="$TEST_DIR/no_access"
mkdir -p "$NOACCESS_DIR"
chmod 000 "$NOACCESS_DIR"
run_test "No access directory fails" "./tvb_wrapper.sh -i $NOACCESS_DIR -d" "1"
chmod 755 "$NOACCESS_DIR"  # Restore for cleanup

# Test 18: Symlink handling
touch "$TEST_DIR/real_file.mp4"
ln -s "$TEST_DIR/real_file.mp4" "$TEST_DIR/symlink_file.mp4"
run_test "Symlink file" "./tvb_wrapper.sh -i '$TEST_DIR/symlink_file.mp4' -d"

# Test 19: Hardlink handling
ln "$TEST_DIR/real_file.mp4" "$TEST_DIR/hardlink_file.mp4"
run_test "Hardlink file" "./tvb_wrapper.sh -i '$TEST_DIR/hardlink_file.mp4' -d"

# Test 20: Case sensitivity in extensions
touch "$TEST_DIR/test.MKV"
run_test "Uppercase extension" "./tvb_wrapper.sh -i '$TEST_DIR/test.MKV' -d"

# Test 21: File with same name as directory
mkdir -p "$TEST_DIR/test_dir"
touch "$TEST_DIR/test_dir"  # This creates a file with same name as directory
run_test "File with same name as directory" "./tvb_wrapper.sh -i '$TEST_DIR/test_dir' -d" "1"

# Test 22: Maximum command line length (if possible)
# This would require a very long path, might not be testable easily

# Summary
echo ""
echo "================================================"
log "🚨 Error Cases Test Summary:"
echo "Total tests run: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 All error case tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some error case tests failed. Please check the output above.${NC}"
    exit 1
fi
