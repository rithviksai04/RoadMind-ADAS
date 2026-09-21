#!/usr/bin/env bash
# Usage: ./run_tests.sh [fast]
set -uo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
if [ "${1:-}" = "fast" ]; then exec $PY -m pytest tests/test_features.py -q; fi
$PY -m pytest -q -W ignore::DeprecationWarning
status=$?
$PY tests/run_scenarios.py > /dev/null 2>&1 && echo "Scenario report: tests/results/scenario_report.md (+ scenario_results.csv)"
exit $status
