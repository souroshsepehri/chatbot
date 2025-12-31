#!/bin/bash
# Run all tests

set -e

echo "🧪 Running all tests..."
echo ""

cd "$(dirname "$0")/.."

# Run pytest with quiet mode
pytest -q

echo ""
echo "✅ All tests passed!"



