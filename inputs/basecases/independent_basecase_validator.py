"""Independent bit-mask validator for the recovered rank4 g=2 masters.
No imports from provider validators. Does not use Python assert.
"""
from pathlib import Path
from itertools import combinations
from collections import Counter
import ast,json,hashlib,sys
root=Path(__file__).parent
src=root/'originals-attempt2/certificates'
def require(x,msg):
 if not x: raise RuntimeError(msg)
def bm(vals):
 out=0
 for x in vals:
  require(isinstance(x,int) and x>=0,'invalid element');require(not(out>>x&1),'duplicate element');out|=1<<x
 return out
rows=[]
for n in (10,14):
 m=n//2;r=4;q=2; qi=next(x for x in range(m)if 2*x%m==1)
 G=[(1<<((qi*c)%m))|(1<<((qi*c)%m+m))for c in range(m)]
 forbidden=set();forced=set()
 for j in range(n):
  c=(2*j)%m; H=G[(c+1)%m]
  forbidden.add(H|(1<<j)|(1<<((j+1)%n)))
  forced.add(G[c]|H)
  forced.add(H|(1<<j)|(1<<((j+m+1)%n)))
 require(len(forbidden)==n,'wrong template cardinality')
 require(len(forced)==3*m,'wrong forced cardinality')
 require(not(forbidden&forced),'forced forbidden intersection')
 require(all(x.bit_count()==r for x in forbidden|forced),'wrong template rank')
 masks=[bm(c)for c in combinations(range(n),r)]
 masks=[s for s in masks if s not in forbidden];vid={s:i+1 for i,s in enumerate(masks)}
 b=src/f'single_master_{n}_4';cnf=b.with_suffix('.cnf');just=b.with_suffix('.just')
 lines=cnf.read_text().splitlines();head=lines.pop(0).split()
 require(head[:2]==['p','cnf'] and int(head[2])==len(masks),'header variable count')
 require(int(head[3])==len(lines),'header clause count')
 js=just.read_text().splitlines();require(len(js)==len(lines),'clause justification count')
 counts=Counter();order_witnesses=[]
 for pos,(line,explanation)in enumerate(zip(lines,js),1):
  nums=list(map(int,line.split()));require(nums and nums[-1]==0,'missing terminal zero')
  got=nums[:-1];require(all(1<=abs(x)<=len(masks)for x in got),'literal outside range')
  parts=explanation.split('\t');kind=parts[0];arg=parts[1]if len(parts)>1 else'';counts[kind]+=1
  if kind=='nonempty':want=list(range(1,len(masks)+1))
  elif kind=='forced':
   s=bm(ast.literal_eval(arg));require(s in forced,'unjustified forced basis');want=[vid[s]]
  elif kind=='exch':
   a,basis2,e=map(int,arg.split());require(a in vid and basis2 in vid,'exchange basis not variable');require(a!=basis2 and(a>>e&1)and not(basis2>>e&1),'invalid exchange element')
   choices=[]
   for f in range(n):
    if basis2>>f&1 and not(a>>f&1):
     s=(a^(1<<e))|(1<<f)
     if s in vid:choices.append(vid[s])
     else:require(s in forbidden,'exchange target neither variable nor forbidden')
   want=[-vid[a],-vid[basis2]]+choices
  elif kind=='kum':
   order=list(map(int,arg.split()));require(sorted(order)==list(range(n)),'not a cyclic permutation')
   windows={bm(order[(i+j)%n]for j in range(r))for i in range(n)}
   # A single forbidden template window would make the required blocking clause tautological.
   # Such a line may NOT be strengthened by merely omitting that window.
   require(not(windows&forbidden),'UNSOUND KUM clause: permutation already has forbidden window')
   want=[-vid[s]for s in windows];order_witnesses.append(order)
  else:raise RuntimeError(f'unhandled justification type {kind}')
  require(Counter(want)==Counter(got),f'clause{pos} differs from its mathematical instance')
 gzip=(src/f'single_master_{n}_4.just.gz').read_bytes()
 gitsha=hashlib.sha1(b'blob '+str(len(gzip)).encode()+b'\0'+gzip).hexdigest()
 expected={10:'d988cb32b41ba4f985eb09db5dc960e39dbf8f89',14:'7fe9189505aef03ca5a5123d3d6b8d2ce5316972'}[n]
 require(gitsha==expected,'original Git blob digest mismatch')
 rows.append({'n':n,'rank':4,'variables':len(masks),'clauses':len(lines),'kinds':dict(counts),'forbidden_template_count':len(forbidden),'forced_template_bases':len(forced),'original_gzip_git_blob':gitsha,'original_gzip_sha256':hashlib.sha256(gzip).hexdigest(),'justification_sha256':hashlib.sha256(just.read_bytes()).hexdigest(),'cnf_sha256':hashlib.sha256(cnf.read_bytes()).hexdigest(),'independent_clause_validation':'PASS','all_KUM_witnesses_genuine_permutations_and_avoid_template_nonbases':True})
 print('INDEPENDENT VALIDATION PASS',n,dict(counts),flush=True)
(root/'basecase-independent-validation.json').write_text(json.dumps(rows,indent=2))
