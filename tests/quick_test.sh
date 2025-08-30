#!/bin/bash

# TVB - Quick Test
# Schneller Test der wichtigsten Funktionen

echo "🧪 TVB Quick Test"
echo "=================="

# Test 1: Script exists
if [[ -x "./tvb_wrapper.sh" ]]; then
    echo "✅ Script is executable"
else
    echo "❌ Script not executable"
    exit 1
fi

# Test 2: Version works
if ./tvb_wrapper.sh --version &>/dev/null; then
    echo "✅ Version command works"
else
    echo "❌ Version command failed"
    exit 1
fi

# Test 3: Help works
if ./tvb_wrapper.sh -h | grep -q "Usage:"; then
    echo "✅ Help command works"
else
    echo "❌ Help command failed"
    exit 1
fi

# Test 4: Config exists
if [[ -f "tvb-config.ini" ]]; then
    echo "✅ Config file exists"
else
    echo "❌ Config file missing"
    exit 1
fi

# Test 5: Python script exists
if [[ -f "tvb.py" ]]; then
    echo "✅ Python script exists"
else
    echo "❌ Python script missing"
    exit 1
fi

echo ""
echo "🎉 Quick test passed! Ready for full testing."
echo ""
echo "Run full test suite with:"
echo "  ./tests/run_all_tests.sh"
