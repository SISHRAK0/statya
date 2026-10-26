"""Общие генераторы и оценщики для проверок темы 09.

Латентная вероятность: p_t = P(X_T > 0 | F_t), X_t = x0 + W_t (+ гауссовы скачки),
т.е. probit-модель p_t = Phi(X_t / sqrt(T - t)) — ограниченный мартингал, разрешается в {0,1}.
"""
import numpy as np
from scipy.stats import norm, poisson


def latent_paths(N, n, p0, T=1.0, rng=None, lam=0.0, sj=0.0, kmax=30):
    """N путей на сетке t_i = i T / n, i = 0..n-1, плюс исход Y в {0,1}.

    lam, sj: интенсивность и ст.откл. гауссовых скачков X (новости).
    Возвращает p (N, n) и Y (N,).
    """
    rng = rng or np.random.default_rng(0)
    p0 = np.broadcast_to(np.asarray(p0, float), (N,))
    dt = T / n
    # начальное X0 подбираем так, чтобы p_0 = p0
    def prob(X, tau):
        if lam == 0.0:
            return norm.cdf(X / np.sqrt(tau))
        ks = np.arange(kmax)
        w = poisson.pmf(ks, lam * tau)                    # (kmax,) или (..,kmax)
        v = tau + ks * sj ** 2
        return np.sum(w * norm.cdf(X[..., None] / np.sqrt(v)), axis=-1)
    if lam == 0.0:
        X0 = norm.ppf(p0) * np.sqrt(T)
    else:
        from scipy.optimize import brentq
        X0 = np.array([brentq(lambda z: prob(np.array(z), T) - q, -20, 20) for q in p0])
    dW = rng.standard_normal((N, n)) * np.sqrt(dt)
    if lam > 0:
        cnt = rng.poisson(lam * dt, (N, n))
        J = rng.standard_normal((N, n)) * sj * np.sqrt(cnt)
        dW = dW + J
    X = X0[:, None] + np.concatenate([np.zeros((N, 1)), np.cumsum(dW, 1)], 1)  # n+1 точек, X[:, n] = X_T
    tau = T - np.arange(n) * dt                           # оставшееся время в t_0..t_{n-1}
    if lam == 0.0:
        p = norm.cdf(X[:, :n] / np.sqrt(tau))
    else:
        p = np.empty((N, n))
        for i in range(n):
            p[:, i] = prob(X[:, i], tau[i])
    Y = (X[:, n] > 0).astype(float)
    return p, Y


def polymarket_tick(q):
    """Шаг цены: 0.01, у краёв (q<0.04 или q>0.96) — 0.001."""
    return np.where((q < 0.04) | (q > 0.96), 0.001, 0.01)


def observe(p, rng, half_spread=0.01, tick=True, iid_sd=0.0):
    """Наблюдаемая цена сделки: p + q*h (+ iid шум), округление к шагу, обрезка в [tick, 1-tick]."""
    q = rng.choice([-1.0, 1.0], size=p.shape)
    b = p + q * half_spread + (rng.standard_normal(p.shape) * iid_sd if iid_sd else 0.0)
    if tick:
        tk = polymarket_tick(p)
        b = np.round(b / tk) * tk
        b = np.clip(b, tk, 1 - tk)
    else:
        b = np.clip(b, 1e-4, 1 - 1e-4)
    return b


# ---------- оценщики квадратичной вариации по строкам матрицы Y (N, n) ----------

def rv(Y):
    return np.sum(np.diff(Y, axis=1) ** 2, axis=1)


def rv_sparse(Y, k):
    return rv(Y[:, ::k])


def tsrv(Y, K=None):
    """Zhang–Mykland–Aït-Sahalia (2005), со small-sample поправкой."""
    n = Y.shape[1] - 1
    K = K or max(2, int(round(0.5 * n ** (2 / 3))))
    # RV^{(K)}: среднее K разреженных RV = (1/K) sum_i (Y_{i+K}-Y_i)^2
    d = Y[:, K:] - Y[:, :-K]
    avg = np.sum(d ** 2, 1) / K
    nbar = (n - K + 1) / K
    return (avg - nbar / n * rv(Y)) / (1 - nbar / n)


def preavg(Y, theta=0.5):
    """Pre-averaging (Jacod, Li, Mykland, Podolskij, Vetter 2009), g(x)=min(x,1-x),
    дискретные константы как у Christensen–Kinnebrock–Podolskij (2010)."""
    n = Y.shape[1] - 1
    k = max(2, int(np.ceil(theta * np.sqrt(n))))
    j = np.arange(1, k)
    g = np.minimum(j / k, 1 - j / k)
    gg = np.minimum(np.arange(0, k + 1) / k, 1 - np.arange(0, k + 1) / k)
    psi1 = k * np.sum(np.diff(gg) ** 2)
    psi2 = np.sum(g ** 2) / k
    dY = np.diff(Y, axis=1)
    # Ybar_i = sum_{j=1}^{k-1} g(j/k) dY_{i+j-1}, i = 0..n-k+1 (накопление без материализации окон)
    m = n - k + 2
    Ybar = np.zeros((Y.shape[0], m))
    for jj in range(1, k):
        Ybar += g[jj - 1] * dY[:, jj - 1:jj - 1 + m]
    term = n / (n - k + 2) * np.sum(Ybar ** 2, 1) / (k * psi2)
    return term - psi1 / (2 * k ** 2 * psi2) * rv(Y)


def parzen(x):
    x = np.abs(x)
    return np.where(x <= 0.5, 1 - 6 * x ** 2 + 6 * x ** 3, np.where(x <= 1, 2 * (1 - x) ** 3, 0.0))


def rkernel(Y, c=1.0):
    """Реализованное ядро Barndorff-Nielsen–Hansen–Lunde–Shephard (2008), flat-top Parzen,
    H ~ c n^{1/2} (несмещённая версия; не гарантирует положительность)."""
    n = Y.shape[1] - 1
    H = max(1, int(round(c * np.sqrt(n))))
    x = np.diff(Y, axis=1)
    out = np.sum(x * x, 1)
    for h in range(1, H + 1):
        gh = np.sum(x[:, h:] * x[:, :-h], 1)
        out = out + parzen((h - 1) / H) * 2 * gh
    return out
