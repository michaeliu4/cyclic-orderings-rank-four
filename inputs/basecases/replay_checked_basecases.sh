#!/usr/bin/env bash
# Replays the saved proof artifacts. No SAT solver or Python packages required.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .replay-bin
cc -O2 originals-attempt2/certificates/rupcheck.c -o .replay-bin/rupcheck
cc -O2 checkers/drat-trim.c -o .replay-bin/drat-trim
python3 independent_basecase_validator.py
for n in 10 14; do
  b="originals-attempt2/certificates/single_master_${n}_4"
  .replay-bin/rupcheck "$b.cnf" "$b.drup" --ignore-deletions | tee "$b.replay-rup.log"
  grep -q '^VERIFIED: empty clause derived by RUP$' "$b.replay-rup.log"
  .replay-bin/drat-trim "$b.cnf" "$b.drup" | tee "$b.replay-drat.log"
  tr '\r' '\n' < "$b.replay-drat.log" | grep -q '^s VERIFIED$'
  echo "CHECKED unrestricted KUM finite base case (n,r)=($n,4), with the analytic coverage proof in BASECASE-10-14-CERTIFICATE-AUDIT.md"
done
