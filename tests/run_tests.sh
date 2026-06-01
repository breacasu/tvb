#!/bin/bash
# TVB Test Runner
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "================================================"
echo " TVB Unit Tests"
echo "================================================"
echo ""

# PYTHONPATH für Imports setzen
export PYTHONPATH="$PROJECT_DIR/python:$PYTHONPATH"

# Test-Durchlauf
python3 -m pytest tests/ -v --tb=short 2>/dev/null || python3 -m unittest discover tests/ -v

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed"
else
    echo "❌ Some tests failed"
fi
exit $EXIT_CODE