"""Проверка тождеств: E[sum dp^2] = p0(1-p0), условная версия, дисперсия (время выхода BM),
многомерный случай (neg-risk): E[sum dp dp'] = diag(p0) - p0 p0'."""
import numpy as np
from common import latent_paths

rng = np.random.default_rng(1)
n = 2000

def full_M(p, Y):
    path = np.concatenate([p, Y[:, None]], 1)
    return np.sum(np.diff(path, axis=1) ** 2, 1)

print("(a,b) полная сумма с финальным скачком к исходу; n =", n)
print(" p0   E[M]     u0      sd(M)   sqrt(u(1-2u)/3)  A-R bound sqrt(u(1.5-u))")
for p0 in [0.05, 0.1, 0.3, 0.5]:
    Ms = []
    for _ in range(4):
        p, Y = latent_paths(5000, n, p0, rng=rng)
        Ms.append(full_M(p, Y))
    M = np.concatenate(Ms); u = p0 * (1 - p0)
    print(f" {p0:.2f} {M.mean():.4f}±{M.std()/np.sqrt(M.size):.4f} {u:.4f}  {M.std():.4f}  {np.sqrt(u*(1-2*u)/3):.4f}"
          f"          {np.sqrt(u*(1.5-u)):.4f}")

print("\n(c) условная версия: E[sum_{s>t} dp^2 | p_t] vs p_t(1-p_t), t = T/2")
p, Y = latent_paths(20000, n, 0.5, rng=rng)
h = n // 2
fut = np.sum(np.diff(np.concatenate([p[:, h:], Y[:, None]], 1), axis=1) ** 2, 1)
pt = p[:, h]
bins = np.linspace(0, 1, 11)
for a, b in zip(bins[:-1], bins[1:]):
    m = (pt >= a) & (pt < b)
    if m.sum() > 200:
        print(f"  p_t in [{a:.1f},{b:.1f}): E[fut]={fut[m].mean():.4f}  E[p(1-p)]={(pt[m]*(1-pt[m])).mean():.4f}  n={m.sum()}")

print("\n(d) со скачками новостей (lam=3, sj=0.5): среднее сохраняется, дисперсия растёт")
p, Y = latent_paths(8000, 1000, 0.5, rng=rng, lam=3.0, sj=0.5)
M = full_M(p, Y)
print(f"  E[M]={M.mean():.4f}±{M.std()/np.sqrt(M.size):.4f} (u0=0.25), sd={M.std():.4f} vs непрерывный 0.2041")

print("\n(e) инкрементная форма: m - r = (1 - 2 p_{s-1}) dp_s  (алгебраическая проверка)")
path = np.concatenate([p, Y[:, None]], 1)[:3]
d = np.diff(path, axis=1); u = path * (1 - path)
lhs = d ** 2 - (u[:, :-1] - u[:, 1:]); rhs = (1 - 2 * path[:, :-1]) * d
print("  max|lhs-rhs| =", np.abs(lhs - rhs).max())

print("\n(f) многомерный случай: K=4 исхода, байесовское обновление по гауссовым сигналам")
K, steps, N = 4, 400, 20000
p0 = np.array([0.5, 0.25, 0.15, 0.10])
state = rng.choice(K, size=N, p=p0)
mu = np.eye(K) * 1.0
logp = np.tile(np.log(p0), (N, 1))
S = np.zeros((N, K, K)); prev = np.tile(p0, (N, 1))
for t in range(steps):
    s = mu[state] * 0.15 + rng.standard_normal((N, K))      # слабый сигнал
    logp += -0.5 * ((s[:, None, :] - mu[None] * 0.15) ** 2).sum(-1)
    logp -= logp.max(1, keepdims=True)
    cur = np.exp(logp); cur /= cur.sum(1, keepdims=True)
    d = cur - prev; S += d[:, :, None] * d[:, None, :]; prev = cur
d = np.eye(K)[state] - prev; S += d[:, :, None] * d[:, None, :]   # разрешение в one-hot
emp = S.mean(0); th = np.diag(p0) - np.outer(p0, p0)
np.set_printoptions(precision=4, suppress=True)
print("  эмпирика E[sum dp dp']:\n", emp)
print("  теория diag(p0)-p0p0':\n", th)
print("  след: emp", emp.trace().round(4), " теория 1-sum p^2 =", (1 - (p0**2).sum()).round(4))
print("  max abs dev =", np.abs(emp - th).max().round(4), "; ст.ошибка следа ~",
      (np.trace(S, axis1=1, axis2=2).std() / np.sqrt(N)).round(4))
