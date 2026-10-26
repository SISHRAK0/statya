import numpy as np
from scipy.stats import norm
rng=np.random.default_rng(0)
T=900.; d=0.5  # window, latency (s)
# 1) linearized vs exact E|dp| at fixed p
def exact(p,tau,delta,n=400000):
    D=norm.ppf(p); Z=rng.standard_normal(n)
    # d = x/(sig*sqrt(tau)); after delta: x'=x+sig sqrt(delta) Z, tau'=tau-delta
    x=D*np.sqrt(tau); xn=x+np.sqrt(delta)*Z
    return np.mean(np.abs(norm.cdf(xn/np.sqrt(tau-delta))-p))
def lin(p,tau,delta): return norm.pdf(norm.ppf(p))*np.sqrt(delta/tau)*np.sqrt(2/np.pi)
print("p tau exact lin")
for p in [0.5,0.7,0.9,0.97,0.99]:
  for tau in [840,120,30,5,2]:
    print(p,tau,round(exact(p,tau,d),5),round(lin(p,tau,d),5))
print("ratio 30 vs 840 at p=.5:",exact(.5,30,d)/exact(.5,840,d), np.sqrt(840/30))
# 2) unconditional over the path: E|dp| as function of tau (BTC-free units, sigma cancels)
n=400000
for tau in [840,600,300,120,30,5]:
    x=np.sqrt(T-tau)*rng.standard_normal(n)  # log-move since open, sigma=1
    p=norm.cdf(x/np.sqrt(tau)); pn=norm.cdf((x+np.sqrt(d)*rng.standard_normal(n))/np.sqrt(tau-d))
    print("tau",tau,"uncond E|dp|",round(np.mean(np.abs(pn-p)),5),"theory sqrt(d/T)/pi",round(np.sqrt(d/T)/np.pi,5),
          "share p in[.4,.6]",round(np.mean((p>.4)&(p<.6)),3))
# 3) g(p) vs p(1-p)
for p in [.5,.3,.1,.03,.01]:
    g=norm.pdf(norm.ppf(p)); print("p",p,"g",round(g,4),"g/(p(1-p))",round(g/(p*(1-p)),3),"g/(p(1-p))^2",round(g/(p*(1-p))**2,2))
