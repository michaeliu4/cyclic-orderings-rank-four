/* Forward DRUP checker: verifies every lemma in a DRUP proof by reverse unit propagation (RUP)
   against the current clause database (original clauses + verified lemmas - deletions), and that
   the empty clause is derived. Two-watched-literal propagation; deletions handled lazily.
   v2: literals outside 1..nv and over-long proof lines are rejected (NOT VERIFIED), literal buffer grows. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct { int *lits; int n; int deleted; } Clause;
static Clause *cl; static int ncl=0, capcl=0;
static int nv;
static int **w; static int *wn, *wc; /* watch lists indexed by literal code */
static signed char *val; /* per var: 0 unassigned, 1 true, -1 false */
static int *trail; static int tn;
static int code(int lit){ return lit>0 ? 2*lit : 2*(-lit)+1; }
static int litval(int lit){ int v=val[abs(lit)]; return lit>0? v : -v; }
static void addwatch(int lit,int ci){ int c=code(lit); if(wn[c]==wc[c]){ wc[c]=wc[c]?2*wc[c]:4; w[c]=realloc(w[c],sizeof(int)*wc[c]); } w[c][wn[c]++]=ci; }
static int addclause(int *lits,int n){
  if(ncl==capcl){ capcl=capcl?2*capcl:1024; cl=realloc(cl,sizeof(Clause)*capcl); }
  cl[ncl].lits=malloc(sizeof(int)*(n>0?n:1)); memcpy(cl[ncl].lits,lits,sizeof(int)*n); cl[ncl].n=n; cl[ncl].deleted=0;
  if(n>=2){ addwatch(lits[0],ncl); addwatch(lits[1],ncl); }
  return ncl++;
}
/* hash of sorted clause for deletion lookup */
#define HB 1048576
typedef struct Node { int ci; struct Node *next; } Node;
static Node *ht[HB];
static unsigned hsh(int *l,int n){ unsigned h=2166136261u; for(int i=0;i<n;i++){ h^=(unsigned)l[i]; h*=16777619u; } return h%HB; }
static int cmp(const void*a,const void*b){ return (*(int*)a)-(*(int*)b); }
static void hins(int ci){ int n=cl[ci].n; int *s=malloc(sizeof(int)*(n?n:1)); memcpy(s,cl[ci].lits,sizeof(int)*n); qsort(s,n,sizeof(int),cmp); unsigned h=hsh(s,n); free(s); Node*x=malloc(sizeof(Node)); x->ci=ci; x->next=ht[h]; ht[h]=x; }
static int hdel(int *l,int n){ int *s=malloc(sizeof(int)*(n?n:1)); memcpy(s,l,sizeof(int)*n); qsort(s,n,sizeof(int),cmp); unsigned h=hsh(s,n);
  for(Node**p=&ht[h];*p;p=&(*p)->next){ int ci=(*p)->ci; if(cl[ci].deleted||cl[ci].n!=n) continue; int *t=malloc(sizeof(int)*(n?n:1)); memcpy(t,cl[ci].lits,sizeof(int)*n); qsort(t,n,sizeof(int),cmp); int eq=memcmp(s,t,sizeof(int)*n)==0; free(t); if(eq){ cl[ci].deleted=1; Node*d=*p; *p=d->next; free(d); free(s); return 1; } }
  free(s); return 0; }
static int assign(int lit){ int v=litval(lit); if(v==1) return 1; if(v==-1) return 0; val[abs(lit)]= lit>0?1:-1; trail[tn++]=lit; return 1; }
static void undo(int to){ while(tn>to){ val[abs(trail[--tn])]=0; } }
/* unit clauses (n==1) kept in a list; propagate them first each time */
static int *units; static int nunits=0, capunits=0;
static int propagate(int start){ /* returns 0 on conflict */
  int qi=start;
  while(qi<tn){ int lit=trail[qi++]; int fl=-lit; int c=code(fl);
    int i=0,j=0;
    while(i<wn[c]){ int ci=w[c][i++]; Clause*C=&cl[ci]; if(C->deleted) continue; /* drop */
      int *L=C->lits; if(L[0]==fl){ L[0]=L[1]; L[1]=fl; }
      if(litval(L[0])==1){ w[c][j++]=ci; continue; }
      int found=0; for(int k=2;k<C->n;k++){ if(litval(L[k])!=-1){ int t=L[1]; L[1]=L[k]; L[k]=t; addwatch(L[1],ci); found=1; break; } }
      if(found) continue;
      w[c][j++]=ci;
      if(litval(L[0])==-1){ while(i<wn[c]) w[c][j++]=w[c][i++]; wn[c]=j; return 0; }
      assign(L[0]);
    }
    wn[c]=j;
  }
  return 1;
}
static int rup(int *lits,int n){ /* 1 if lemma is RUP */
  int base=tn; int ok=1;
  for(int u=0;u<nunits;u++){ int ci=units[u]; if(cl[ci].deleted) continue; if(!assign(cl[ci].lits[0])){ ok=0; break; } }
  if(ok) for(int i=0;i<n;i++){ if(!assign(-lits[i])){ ok=0; break; } }
  if(ok) ok=propagate(base); else ok=0; /* ok==0 means conflict */
  int conflict=!ok; undo(base); return conflict;
}
int main(int argc,char**argv){
  int ignoredel = (argc>3 && strcmp(argv[3],"--ignore-deletions")==0);
  FILE*f=fopen(argv[1],"r"); int nc; if(!f){ fprintf(stderr,"cannot open %s\n",argv[1]); return 2; }
  if(fscanf(f," p cnf %d %d",&nv,&nc)!=2){ fprintf(stderr,"bad header\n"); return 2; }
  w=calloc(2*nv+2,sizeof(int*)); wn=calloc(2*nv+2,sizeof(int)); wc=calloc(2*nv+2,sizeof(int)); val=calloc(nv+1,1); trail=malloc(sizeof(int)*(nv+1));
  int captmp=1024; int *tmp=malloc(sizeof(int)*captmp); int tl=0,x;
#define PUSHLIT(v) do{ if(abs(v)>nv){ fprintf(stderr,"literal %d out of range (nv=%d)\n",(int)(v),nv); printf("NOT VERIFIED: malformed input\n"); return 2; } \
    if(tl==captmp){ captmp*=2; tmp=realloc(tmp,sizeof(int)*captmp); } tmp[tl++]=(int)(v); }while(0)
  int read=0;
  while(fscanf(f,"%d",&x)==1){ if(x==0){ int ci=addclause(tmp,tl); hins(ci); if(tl==1){ if(nunits==capunits){capunits=capunits?2*capunits:64; units=realloc(units,sizeof(int)*capunits);} units[nunits++]=ci; } if(tl==0){ printf("original formula contains empty clause\n"); } tl=0; read++; } else PUSHLIT(x); }
  fclose(f); printf("read %d original clauses\n",read);
  FILE*p=fopen(argv[2],"r"); if(!p){ fprintf(stderr,"cannot open %s\n",argv[2]); return 2; } long lemmas=0, dels=0, faildel=0; int gotempty=0;
  char line[1<<20];
  while(fgets(line,sizeof line,p)){
    if(strlen(line)==sizeof(line)-1 && line[sizeof(line)-2]!='\n'){ printf("NOT VERIFIED: proof line too long\n"); return 2; }
    char*s=line; while(*s==' ') s++; if(*s=='\n'||*s==0) continue;
    int isdel=0; if(*s=='d'){ isdel=1; s++; }
    tl=0; char*e; while(1){ long v=strtol(s,&e,10); if(e==s) break; s=e; if(v==0) break; PUSHLIT(v); }
    if(isdel){ dels++; if(!ignoredel){ if(!hdel(tmp,tl)) faildel++; } continue; }
    lemmas++;
    if(!rup(tmp,tl)){ printf("FAIL: lemma %ld is not RUP\n",lemmas); return 1; }
    if(tl==0){ gotempty=1; break; }
    int ci=addclause(tmp,tl); hins(ci); if(tl==1){ if(nunits==capunits){capunits=capunits?2*capunits:64; units=realloc(units,sizeof(int)*capunits);} units[nunits++]=ci; }
  }
  printf("lemmas checked %ld, deletions %ld (unmatched %ld)%s\n",lemmas,dels,faildel, ignoredel?" [deletions ignored: sound, database only grows]":"");
  if(gotempty){ printf("VERIFIED: empty clause derived by RUP\n"); return 0; }
  printf("NOT VERIFIED: no empty clause\n"); return 1;
}
