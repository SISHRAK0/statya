import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
# per latency interval: one potential snipe with dp~N(0,sp^2); noise takers arrive Lam*exp(-c/c0)
# maker receives s' per fill (spread+rebate); taker pays c=s'+t (t=retained fee wedge)
# arb snipes iff |dp|>c ; maker loss on snipe = |dp|-s'
def tailE(a,b,sp):  # E[(|dp|-a) 1{|dp|>b}], b>=a
    z=b/sp; return 2*(sp*norm.pdf(z)-a*(1-norm.cdf(z)))
def eq(t,sp,Lam,c0,hmin):
    f=lambda s: Lam*np.exp(-(s+t)/c0)*s - tailE(s,s+t,sp)
    s=0.0 if f(1e-12)>=0 else brentq(f,1e-12,1.0)
    bind = s<hmin
    s=max(s,hmin)
    c=s+t; Vn=Lam*np.exp(-c/c0); Pa=2*(1-norm.cdf(c/sp))
    CS=Lam*c0*np.exp(-c/c0)
    makerprofit=Vn*s - tailE(s,c,sp)
    W=CS+t*(Vn+Pa)+makerprofit   # arb rents treated as dissipated (BCS)
    return dict(s=s,c=c,W=W,Vn=Vn,Pa=Pa,bind=bind,CS=CS)
def best(sp,Lam,c0,hmin):
    ts=np.linspace(0,0.2,2001); Ws=[eq(t,sp,Lam,c0,hmin)['W'] for t in ts]
    i=int(np.argmax(Ws)); return ts[i],eq(ts[i],sp,Lam,c0,hmin)
g=norm.pdf(0); delta=0.5
for hmin in [0.0,0.005]:
  for Lam,c0 in [(1.0,0.05),(3.0,0.05),(1.0,0.02)]:
    print(f"--- half-tick floor={hmin} Lam={Lam} c0={c0}  (p=0.5)")
    for tau in [840,300,120,60,30,10]:
        sp=g*np.sqrt(delta/tau)
        t,r=best(sp,Lam,c0,hmin); r0=eq(0,sp,Lam,c0,hmin)
        print(f"tau={tau:4d} sp={sp:.4f} t*={t:.4f} t*/sp={t/sp if sp else 0:.2f} fee*=t/(1-0.2)={t/0.8:.4f} | at t=0: s={r0['s']:.4f} bind={r0['bind']}  W(t*)/W(0)={r['W']/r0['W']:.3f}")
