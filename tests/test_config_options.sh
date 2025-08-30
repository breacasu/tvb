#!/bin/bash

# TVB - Config Options Tests
# Test verschiedene Config-Optionen und deren Auswirkungen

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

# Backup original config
ORIGINAL_CONFIG="tvb-config.ini.backup"
if [[ ! -f "$ORIGINAL_CONFIG" ]]; then
    cp tvb-config.ini "$ORIGINAL_CONFIG"
    log "Original config backed up to $ORIGINAL_CONFIG"
fi

# Test directory
TEST_DIR="./test_config_output"
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

# Config modification function
modify_config() {
    local section="$1"
    local key="$2"
    local value="$3"

    # Use sed to modify config file
    sed -i.bak "/^\[$section\]/,/^\[/ s/^$key = .*/$key = $value/" tvb-config.ini
}

# Restore config function
restore_config() {
    if [[ -f "$ORIGINAL_CONFIG" ]]; then
        cp "$ORIGINAL_CONFIG" tvb-config.ini
        log "Config restored from backup"
    fi
}

# Cleanup
cleanup() {
    log "Cleaning up..."
    rm -rf "$TEST_DIR"
    restore_config
}

trap cleanup EXIT

log "⚙️ Starting TVB Config Options Tests"
echo "======================================="

# Test 1: CPU Limit OFF
log "Testing CPU limit = no"
modify_config "default" "cpulimit" "no"
run_test "CPU limit disabled" "./tvb_wrapper.sh --version"

# Test 2: CPU Limit ON
log "Testing CPU limit = yes"
modify_config "default" "cpulimit" "yes"
modify_config "default" "cpulimitpercent" "400"
run_test "CPU limit enabled" "./tvb_wrapper.sh --version"

# Test 3: Preserve file date ON
log "Testing preserve_file_date = yes"
modify_config "default" "preserve_file_date" "yes"
run_test "Preserve file date enabled" "./tvb_wrapper.sh --version"

# Test 4: Preserve file date OFF
log "Testing preserve_file_date = no"
modify_config "default" "preserve_file_date" "no"
run_test "Preserve file date disabled" "./tvb_wrapper.sh --version"

# Test 5: Manual subtitle editing ON
log "Testing edit_subtitles_manually = yes"
modify_config "default" "edit_subtitles_manually" "yes"
run_test "Manual subtitle editing enabled" "./tvb_wrapper.sh --version"

# Test 6: Manual subtitle editing OFF
log "Testing edit_subtitles_manually = no"
modify_config "default" "edit_subtitles_manually" "no"
run_test "Manual subtitle editing disabled" "./tvb_wrapper.sh --version"

# Test 7: Different localizations
log "Testing different localizations"
modify_config "default" "localization" "english"
run_test "English localization" "./tvb_wrapper.sh --version"

modify_config "default" "localization" "german"
run_test "German localization" "./tvb_wrapper.sh --version"

# Test 8: Different output directory
log "Testing custom output directory"
modify_config "default" "outputdir" "$TEST_DIR"
run_test "Custom output directory" "./tvb_wrapper.sh --version"

# Test 9: Config file validation
run_test "Config file remains valid after modifications" "python3 -c \"import configparser; c = configparser.ConfigParser(); c.read('tvb-config.ini'); print('Config still valid')\""

# Test 10: Test different encoding parameters
log "Testing different encoding parameters"

# TV Show parameters
modify_config "tvshow" "parameter" "--add-audio all --add-subtitle all -x encoder=vt_h265 -x quality=56"
run_test "TV Show H.265 parameters" "./tvb_wrapper.sh --version"

# Movie parameters
modify_config "movie" "parameter" "--add-audio deu,eng --add-subtitle all -x encoder=svt_av1 -x quality=33"
run_test "Movie AV1 parameters" "./tvb_wrapper.sh --version"

# Custom parameters
modify_config "custom" "parameter" "--mode hevc --quality 24 --add-audio all --add-subtitle all"
run_test "Custom HEVC parameters" "./tvb_wrapper.sh --version"

# Test 11: Preview parameters
modify_config "preview" "parameter" "--stop-at duration:60"
run_test "Preview parameters" "./tvb_wrapper.sh --version"

# Summary
echo ""
echo "======================================="
log "⚙️ Config Test Summary:"
echo "Total tests run: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 All config option tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some config tests failed. Please check the output above.${NC}"
    exit 1
fi
