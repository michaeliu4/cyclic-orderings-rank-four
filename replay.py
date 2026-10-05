"""Prepare private working copies and run the unchanged archived validators/checkers."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--inputs-only', action='store_true', help='validate bytes and clauses, without proof checking')
p.add_argument('--basecases-only', action='store_true', help='run only the n=10 and n=14 cases')
p.add_argument('--manifest-only', action='store_true', help='verify preserved input bytes without creating outputs')
a = p.parse_args()
entries = json.loads((HERE / 'INPUT-MANIFEST.json').read_text())
for e in entries:
    f = HERE / e['path']
    if f.stat().st_size != e['bytes'] or hashlib.sha256(f.read_bytes()).hexdigest() != e['sha256']:
        raise SystemExit('Input-byte mismatch: ' + e['path'])
print('Exact input bytes verified:', len(entries), flush=True)
if a.manifest_only:
    raise SystemExit(0)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
work = HERE / '_generated' / stamp
shutil.copytree(HERE / 'inputs', work)
base = work / 'basecases'
old = work / 'old14'
for name in ('rupcheck.c', 'drat-trim.c'):
    dest = base / ('originals-attempt2/certificates' if name == 'rupcheck.c' else 'checkers') / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(work / 'checkers' / name, dest)
shutil.copytree(work / 'checkers', old / 'checkers')
for n in (10, 14):
    stem = base / 'originals-attempt2/certificates' / ('single_master_%s_4' % n)
    with gzip.open(stem.with_suffix('.just.gz'), 'rb') as f:
        stem.with_suffix('.just').write_bytes(f.read())
env = os.environ.copy()
# The archived old14 validator uses asserts. Never disable them.
env.pop('PYTHONOPTIMIZE', None)
env.pop('PYTHONPATH', None)
print('Generated working files:', work, flush=True)
def run(cmd, cwd, log):
    with (work / log).open('w') as out:
        process = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end='', flush=True)
            out.write(line)
        if process.wait():
            raise SystemExit('Failed command; see ' + str(work / log))
if a.inputs_only:
    run([sys.executable, '-E', 'independent_basecase_validator.py'], base, 'basecases.log')
else:
    run(['bash', 'replay_checked_basecases.sh'], base, 'basecases.log')
if not a.basecases_only:
    run(['bash', 'replay.sh'] + (['--inputs-only'] if a.inputs_only else []), old, 'old14.log')
print('Requested verification completed.', flush=True)
