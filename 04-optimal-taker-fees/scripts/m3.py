# TWAP resolution over last L sec: Up iff mean(X on [T-L,T]) >= X_open (log-price, BM sigma=1, small-move approx)
import numpy as np
from scipy.stats import norm
L=60.; d=0.5
def teff(tau): return tau-2*L/3 if tau>=L else tau**3/(3*L**2)
def w(tau): return 1.0 if tau>=L else tau/L
# conditional on current p: p = Phi(m/ sqrt(teff)), m = expected avg - open given info; spot shock sqrt(d)Z shifts m by w*sqrt(d)Z
rng=np.random.default_rng(1)
for tau in [840,300,60,30,10,5]:
  for p in [.5,.9]:
    m=norm.ppf(p)*np.sqrt(teff(tau)); Z=rng.standard_normal(400000)
    # after delta: m' = m + w(tau)*sqrt(d)Z ; teff shrinks
    pn=norm.cdf((m+w(tau)*np.sqrt(d)*Z)/np.sqrt(teff(tau-d)))
    e=np.mean(np.abs(pn-p)); pt=norm.pdf(norm.ppf(p))*np.sqrt(d/tau)*np.sqrt(2/np.pi)
    print(tau,p,"TWAP E|dp|=%.4f point=%.4f ratio=%.2f"%(e,pt,e/pt))
