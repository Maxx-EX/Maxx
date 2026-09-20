#!/usr/bin/env bash
# Maxx Bootstrap Compiler test runner (Level 1).
# Compiles and runs all .max test files.

set -e
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

echo "=== Maxx Bootstrap Compiler Tests ==="
echo ""

for f in tests/*.max; do
    name=$(basename "$f")
    echo "--- Testing: $name ---"
    if python3 maxxc.py run "$f" 2>&1; then
        echo "  [PASS] $name"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $name"
        FAIL=$((FAIL + 1))
    fi
    echo ""
done

echo "=== Summary: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
