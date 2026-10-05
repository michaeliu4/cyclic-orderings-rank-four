#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--inputs-only" ) ]]; then
  echo "Usage: bash replay.sh [--inputs-only]" >&2; exit 2
fi
python3 -E prepare_inputs.py
python3 -E .replay-work/validate_old14_cnf.py | tee .replay-work/input-validation.log
if [[ "${1:-}" == "--inputs-only" ]]; then
  echo "Input-byte and complete clause validation finished; proof checkers deliberately not run."
  exit 0
fi
cc -O2 checkers/rupcheck.c -o .replay-work/rupcheck
cc -O2 checkers/drat-trim.c -o .replay-work/drat-trim
.replay-work/rupcheck .replay-work/query-old14.cnf .replay-work/query-old14.drup --ignore-deletions | tee .replay-work/rup.log
grep -q '^VERIFIED: empty clause derived by RUP$' .replay-work/rup.log
.replay-work/drat-trim .replay-work/query-old14.cnf .replay-work/query-old14.drup | tee .replay-work/drat.log
tr '\r' '\n' < .replay-work/drat.log | grep -q '^s VERIFIED$'
echo 'CHECKED universal prescribed-old14 insertion; the n18 consequence also uses THEOREM.md dependencies.'
