from pathlib import Path
import gzip,lzma,hashlib,json,shutil
here=Path(__file__).resolve().parent
work=here/'.replay-work';work.mkdir(exist_ok=True)
for e in json.loads((here/'PLAIN-BYTE-MANIFEST.json').read_text()):
 src=here/e['compressed_file'];out=work/e['file'];h=hashlib.sha256();n=0
 with (lzma.open if e['compression']=='xz' else gzip.open)(src,'rb') as f,out.open('wb') as g:
  while b:=f.read(1024*1024):g.write(b);h.update(b);n+=len(b)
 if h.hexdigest()!=e['sha256'] or n!=e['bytes']:raise SystemExit('Plain-byte verification failed: '+e['file'])
 print('EXACT decompressed bytes:',e['file'],n,h.hexdigest())
shutil.copyfile(here/'validate_old14_cnf.py',work/'validate_old14_cnf.py')
