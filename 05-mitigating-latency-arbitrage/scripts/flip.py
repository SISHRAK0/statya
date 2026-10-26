import numpy as np
rng=np.random.default_rng(3); dt=0.5
for T in (300,900):
  for N in (30,60,120):
    M=40000; Nn=int(N/dt); n=int(T/dt)
    W=np.cumsum(rng.normal(0,np.sqrt(dt),(M,n+Nn)),1)  # time -N..T
    X0=W[:,Nn-1]; XT=W[:,-1]
    Aopen=W[:,:Nn].mean(1); Aend=W[:,-Nn:].mean(1)
    spot=XT>X0; tw=Aend>Aopen; tw_spotK=Aend>X0
    print(f"T={T} N={N}: flip vs spot (TWAP open+close)={np.mean(spot!=tw)*100:.2f}%  (TWAP close only, spot strike)={np.mean(spot!=tw_spotK)*100:.2f}%")
