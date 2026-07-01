#!/bin/bash
# Run all three test cases. Each emits its own RESULT.md.
# Exit 0 only if every case passes.

set -e
SCAFFOLD_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEST_ROOT="$SCAFFOLD_ROOT/tests"
SCRIPTS="$SCAFFOLD_ROOT/scripts"
ASSETS="$SCAFFOLD_ROOT/assets"

pass_count=0
fail_count=0

run_case() {
  local id="$1"
  local case_dir="$TEST_ROOT/$id"
  local result_file="$case_dir/RESULT.md"
  echo ""
  echo "=== $id ==="

  if [ ! -f "$case_dir/test.sh" ]; then
    echo "  SKIP — no test.sh"
    return
  fi

  if bash "$case_dir/test.sh" > "$case_dir/test.log" 2>&1; then
    echo "  PASS"
    pass_count=$((pass_count+1))
    echo "# $id — PASS" > "$result_file"
  else
    echo "  FAIL — see $case_dir/test.log"
    fail_count=$((fail_count+1))
    echo "# $id — FAIL" > "$result_file"
    cat "$case_dir/test.log" >> "$result_file"
  fi
}

for case_path in "$TEST_ROOT"/e*-*/; do
  id="$(basename "$case_path")"
  run_case "$id"
done

echo ""
echo "=== SUMMARY ==="
echo "PASS: $pass_count"
echo "FAIL: $fail_count"

if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
exit 0
