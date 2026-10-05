"""Independently validate every input clause for the old14-plus-basis4 theorem."""
from itertools import combinations,permutations,product
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
n=18;mask=lambda S:sum(1<<x for x in S)
subsets=[None]+[mask(S)for S in combinations(range(n),4)]
var={s:i for i,s in enumerate(subsets)if i}
old=list(range(14));D=list(range(14,18))
forced={mask(old[(i+j)%14]for j in range(4))for i in range(14)}|{mask(D)}
allowed_initial=Counter({(var[b],):1 for b in forced})
for i in range(14):
 rotate=old[i:]+old[:i]
 for f,g in product((False,True),repeat=2):
  a=rotate[:2][::(-1 if f else 1)];b=rotate[2:4][::(-1 if g else 1)]
  for d in permutations(D):
   order=a+list(d)+b+rotate[4:]
   windows={mask(order[(j+k)%n]for k in range(4))for j in range(n)}
   allowed_initial[tuple(sorted(-var[w]for w in windows-forced))]+=1
seen=Counter();ex=0;total=0
for line in (HERE/'query-old14.cnf').read_text().splitlines():
 if line.startswith('p '):
  _,_,nv,nc=line.split();assert int(nv)==3060;declared=int(nc);continue
 if not line or line.startswith('c'):continue
 z=list(map(int,line.split()));assert z.pop()==0;c=tuple(sorted(z));total+=1
 assert all(1<=abs(x)<=3060 for x in c)
 if c in allowed_initial:
  seen[c]+=1;continue
 neg=[-x for x in z if x<0];pos={x for x in z if x>0}
 assert len(neg)==2 and len(pos)==len(z)-2
 a,b=map(subsets.__getitem__,neg)
 valid=False
 for source,target in ((a,b),(b,a)):
  for x in range(n):
   if source>>x&1 and not target>>x&1:
    expected={var[(source^(1<<x))|(1<<y)]for y in range(n)if target>>y&1 and not source>>y&1}
    if pos==expected:valid=True;break
  if valid:break
 assert valid,('not a full basis-exchange axiom',z)
 ex+=1
assert total==declared
assert seen==allowed_initial,(seen-allowed_initial,allowed_initial-seen)
print('PASS:',total,'clauses;',sum(seen.values()),'exact forced/patch clauses;',ex,'exact full basis-exchange clauses.')
print('No density, representability, flat-bound, or nonparallel-pair assumption occurs.')
