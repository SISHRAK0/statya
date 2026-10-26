import numpy as np
from scipy.stats import norm
rng=np.random.default_rng(1)
sig=0.5/np.sqrt(365*24*3600)   # per sqrt(sec)
T=900.0; dt=0.1; n=int(T/dt)
t=np.arange(n+1)*dt
def p_spot(X,ti):
    tau=T-ti
    return np.where(tau>0, norm.cdf(X/(sig*np.sqrt(np.maximum(tau,1e-12)))), (X>0).astype(float))
def p_avg(X,cumI,ti,N):
    # cumI: integral of X from T-N to ti (0 if ti<T-N)
    tau=T-ti
    if tau>N:
        m=X; v=sig**2*(tau-2*N/3)
    elif tau>0:
        m=cumI/N+(tau/N)*X; v=sig**2*tau**3/(3*N**2)
    else:
        return (cumI/N>0).astype(float)
    return norm.cdf(m/np.sqrt(v))
def run(delta,Ns,paths=20000,chunk=2000,fees=(0.0,0.07),hs=0.0):
    step=int(round(delta/dt)); grid=np.arange(0,n+1,step)
    rules=['spot']+[f'avg{N}' for N in Ns]
    res={r:{'abs':0,'sq':0,'late_abs':0,**{f'rent{f}':0 for f in fees},**{f'late_rent{f}':0 for f in fees}} for r in rules}
    tau_bins=[1,2,5,10,30,60,120,300]
    bucket={r:{b:[] for b in tau_bins} for r in rules}
    for c in range(paths//chunk):
        dX=rng.normal(0,sig*np.sqrt(dt),(chunk,n)); X=np.concatenate([np.zeros((chunk,1)),np.cumsum(dX,1)],1)
        P={}
        P['spot']=np.stack([p_spot(X[:,g],t[g]) for g in grid],1)
        for N in Ns:
            i0=int(round((T-N)/dt))
            # trapezoid cumulative integral from i0
            seg=X[:,i0:]; ci=np.concatenate([np.zeros((chunk,1)),np.cumsum((seg[:,1:]+seg[:,:-1])/2*dt,1)],1)
            cols=[]
            for g in grid:
                cI=ci[:,g-i0] if g>=i0 else 0.0
                cols.append(p_avg(X[:,g],cI,t[g],N))
            P[f'avg{N}']=np.stack(cols,1)
        for r in rules:
            p=P[r]; dp=np.diff(p,1); pm=p[:,:-1]  # stale quote at p_{t-d}, arb sees p_t
            tau_end=T-t[grid[1:]]
            res[r]['abs']+=np.abs(dp).sum(); res[r]['sq']+=(dp**2).sum()
            late=tau_end<60
            res[r]['late_abs']+=np.abs(dp[:,late]).sum()
            for f in fees:
                cost=f*pm*(1-pm)+hs  # fee per share at quote price (pm), plus half-spread
                rent=np.maximum(np.abs(dp)-cost,0)
                res[r][f'rent{f}']+=rent.sum(); res[r][f'late_rent{f}']+=rent[:,late].sum()
            for b in tau_bins:
                j=np.argmin(np.abs(tau_end-b)); bucket[r][b].append(np.abs(dp[:,j]))
    out={}
    for r in rules:
        d={k:v/paths for k,v in res[r].items()}
        d['by_tau']={b:float(np.mean(np.concatenate(bucket[r][b]))) for b in tau_bins}
        out[r]=d
    return out
for delta in (1.0,2.0):
    for hs in (0.0,0.005):
        o=run(delta,[30,60,120],hs=hs)
        print(f'\n=== delta={delta}s half-spread={hs} === (per share, per 15-min market; sum over non-overlapping delta-intervals)')
        print(f"{'rule':8} {'sum|dp|':>8} {'sum dp^2':>8} {'late60%':>7} {'rent f=0':>9} {'rent f=.07':>10} {'late%f.07':>9}")
        for r,d in o.items():
            print(f"{r:8} {d['abs']:8.4f} {d['sq']:8.4f} {100*d['late_abs']/d['abs']:7.1f} {d['rent0.0']:9.4f} {d['rent0.07']:10.4f} {100*d['late_rent0.07']/max(d['rent0.07'],1e-12):9.1f}")
        if hs==0.0:
            print('E|dp| per opportunity by time-to-expiry tau (s):')
            for r,d in o.items(): print(f"  {r:8}", ' '.join(f"{b}:{v:.4f}" for b,v in d['by_tau'].items()))
