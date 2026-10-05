# Cyclic orderings of uniformly dense rank-four matroids

Exact finite proof files for the paper *Cyclic orderings of uniformly dense rank-four matroids*. These files supply the three finite inputs used in the V1 manuscript. The mathematical reductions and coverage arguments are in Section 6; Appendix C describes the replay. The theorem concerns rank four and its dual corank-four case.

## Verification

Requirements: Python 3.10 or later (standard library only), Bash, a C compiler available as `cc`, and the usual Unix `tee`, `grep` and `tr` utilities. No SAT solver or package installation is required. After downloading the repository, run from its root:

```sh
python3 -E replay.py
```

The command checks the input hashes, reconstructs an isolated working copy, validates the matroid meaning of every input clause, and replays all three refutations with the forward RUP checker and DRAT-trim. Generated files and logs are written under `_generated/`, which is ignored by Git. The saved inputs are not changed. The largest replay may take several minutes.

| Finite case | Variables | Input clauses | RUP additions |
|---|---:|---:|---:|
| Ten elements | 200 | 6,068 | 75 |
| Fourteen elements | 987 | 93,200 | 4,805 |
| Insertion into a prescribed fourteen-element order | 3,060 | 427,359 | 277,282 |

The RUP counts exclude input clauses and deletion records and include the final empty clause. Each case must report `VERIFIED: empty clause derived by RUP` and `s VERIFIED`. The forward checker ignores deletions; DRAT-trim may warn about unmatched deletions. All three saved verified cores use zero RAT lemmas. These checks establish the finite contradictions; their deduction to the matroid theorem is supplied in the paper.

For component checks:

```sh
python3 -E replay.py --manifest-only
python3 -E replay.py --inputs-only
python3 -E replay.py --basecases-only
```

The first checks byte identity, the second also validates the clauses, and the third replays the ten- and fourteen-element proofs. Only the full command includes the prescribed-order insertion proof.

## Files

- `inputs/basecases/`: ten- and fourteen-element formulas, refutations, compressed clause justifications, validator and replay driver.
- `inputs/old14/`: the prescribed-order insertion formula and refutation, compressed inputs, validator and replay driver.
- `inputs/checkers/`: the C checker sources. Third-party copyright and permission notices are retained.
- `INPUT-MANIFEST.json`: exact input identities and their source mapping.

The original drivers mention archival proof documents in their messages. Those documents are not needed to execute the checks; the paper gives the relevant mathematical arguments. Discovery scripts, solver binaries and historical run logs are not included.
