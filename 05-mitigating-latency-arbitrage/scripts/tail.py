import numpy as np, importlib.util, sys
spec=importlib.util.spec_from_file_location('m','twap_arb.py')
src=open('twap_arb.py').read().split('for delta in (1.0,2.0):')[0]
m={}; exec(src,m)
np_=np; rng=np.random.default_rng(7)
T,dt,n,t,sig=m['T'],m['dt'],m['n'],m['t'],m['sig']
for delta in (1.0,2.0):
  step=int(round(delta/dt)); grid=np.arange(0,n+1,step)
  acc={}
  for c in range(5):
    chunk=2000
    X=np.concatenate([np.zeros((chunk,1)),np.cumsum(rng.normal(0,sig*np.sqrt(dt),(chunk,n)),1)],1)
    P={'spot':np.stack([m['p_spot'](X[:,g],t[g]) for g in grid],1)}
    for N in (30,60,120):
      i0=int(round((T-N)/dt)); seg=X[:,i0:]
      ci=np.concatenate([np.zeros((chunk,1)),np.cumsum((seg[:,1:]+seg[:,:-1])/2*dt,1)],1)
      P[f'avg{N}']=np.stack([m['p_avg'](X[:,g],ci[:,g-i0] if g>=i0 else 0.0,t[g],N) for g in grid],1)
    tau=T-t[grid[1:]]
    for r,p in P.items():
      dp=np.abs(np.diff(p,1)); pm=p[:,:-1]
      a=acc.setdefault(r,{'big5':0,'big10':0,'rent_big':0,'tot':0,'cond':[],'maxjump':[]})
      a['big5']+=(dp>0.05).sum(); a['big10']+=(dp>0.10).sum()
      rent=np.maximum(dp-0.07*pm*(1-pm),0); a['tot']+=rent.sum(); a['rent_big']+=rent[dp>0.05].sum()
      mask=(tau[None,:]<=10)&(pm>0.3)&(pm<0.7); a['cond'].append(dp[mask])
      a['maxjump'].append(dp.max(1))
  print(f'\n=== delta={delta}s, 10000 paths ===')
  print(f"{'rule':7} {'#|dp|>5c':>9} {'#|dp|>10c':>9} {'rent share from >5c':>19} {'E|dp| | tau<=10,p in(.3,.7)':>27} {'E max jump':>10}")
  for r,a in acc.items():
    cc=np.concatenate(a['cond'])
    print(f"{r:7} {a['big5']/10000:9.3f} {a['big10']/10000:9.3f} {100*a['rent_big']/a['tot']:18.1f}% {cc.mean() if cc.size else float('nan'):20.4f} (n={cc.size:6d}) {np.concatenate(a['maxjump']).mean():8.4f}")
