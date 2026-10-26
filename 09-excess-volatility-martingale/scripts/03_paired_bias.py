"""Точное смещение оценщиков относительно латентной QV на тех же путях (парные разности),
в т.ч. режимы: краевые p0 (шаг 0.001), нерегулярные сделки (интенсивность растёт к разрешению),
шум, зависящий от p (спред шире в середине)."""
import numpy as np
from scipy.stats import norm
from common import observe, rv, rv_sparse, tsrv, preavg, rkernel, polymarket_tick

rng = np.random.default_rng(11)

def paths_at_times(N, times, p0, T=1.0):
    """probit-мартингал на заданной (общей) сетке времён < T."""
    X0 = norm.ppf(p0) * np.sqrt(T)
    dt = np.diff(np.concatenate([[0.0], times]))
    X = X0[:, None] + np.cumsum(rng.standard_normal((N, len(times))) * np.sqrt(dt), 1)
    X = np.concatenate([X0[:, None], X], 1)
    tt = np.concatenate([[0.0], times])
    return norm.cdf(X / np.sqrt(T - tt))

def table(label, p, b, frac=0.9):
    m = int(frac * (p.shape[1] - 1))
    lat, ob = p[:, :m + 1], b[:, :m + 1]
    den = np.sum(lat[:, 0] * (1 - lat[:, 0]) - lat[:, -1] * (1 - lat[:, -1]))
    L = rv(lat)
    row = []
    for name, f in [("RV", rv), ("RV k=20", lambda y: rv_sparse(y, 20)), ("TSRV", tsrv),
                    ("PA", preavg), ("RK", rkernel)]:
        d = f(ob) - L
        row.append(f"{name}: {d.sum()/den:+.3f}±{d.std()*np.sqrt(len(d))/den:.3f}")
    print(f"{label:38s} " + "  ".join(row))

N, n = 1500, 5000
print("Смещение Xnorm (оценщик − латентная RV) / уменьшение неопределённости; окно [0,0.9T]\n")
# 1. базовый
p0 = rng.uniform(0.15, 0.85, N); t = np.arange(1, n + 1) / (n + 1)
p = paths_at_times(N, t, p0); table("база: h=0.01, шаг 0.01, регулярно", p, observe(p, rng, 0.01))
# 2. краевые
p0 = rng.uniform(0.02, 0.10, N); p = paths_at_times(N, t, p0)
table("краевые p0∈[0.02,0.10], h=0.01", p, observe(p, rng, 0.01))
b = observe(p, rng, 0.0); table("краевые, только округление", p, b)
# 3. нерегулярные сделки: плотность ~ 1/sqrt(T-t) (торговля ускоряется к разрешению)
u = np.sort(rng.uniform(0, 1, n)); t_irr = 1 - (1 - u) ** 2 * 0.999
p0 = rng.uniform(0.15, 0.85, N); p = paths_at_times(N, t_irr, p0)
table("нерегулярные сделки (ускорение к T)", p, observe(p, rng, 0.01))
# 4. шум зависит от p: h(p) = 0.02 * 4p(1-p) (шире в середине), плюс шаг
p0 = rng.uniform(0.15, 0.85, N); p = paths_at_times(N, t, p0)
q = rng.choice([-1.0, 1.0], p.shape); tk = polymarket_tick(p)
b = np.clip(np.round((p + q * 0.02 * 4 * p * (1 - p)) / tk) * tk, tk, 1 - tk)
table("гетероскед. h(p)=0.08p(1-p) + шаг", p, b)
# 5. «вялый» рынок: та же QV размазана по 20000 сделкам, шаг доминирует
p0 = rng.uniform(0.15, 0.85, 800); t2 = np.arange(1, 20001) / 20001
p = paths_at_times(800, t2, p0); table("n=20000, только округление", p, observe(p, rng, 0.0))
table("n=20000, h=0.01 + шаг", p, observe(p, rng, 0.01))
# 6. «мусорные» сделки: с вероятностью 0.002 сделка по краевой цене 0.01/0.99 (тонкая книга, fat finger)
p0 = rng.uniform(0.15, 0.85, N); p = paths_at_times(N, t, p0)
b = observe(p, rng, 0.01)
junk = rng.uniform(size=b.shape) < 0.002; junk[:, 0] = False; junk[:, -1] = False
b2 = np.where(junk, np.where(rng.uniform(size=b.shape) < 0.5, 0.01, 0.99), b)
table("+0.2% мусорных сделок по 0.01/0.99", p, b2)
# простой фильтр: выкинуть сделку, если она отклоняется от медианы соседних 20 больше чем на 0.15
from scipy.ndimage import median_filter
med = median_filter(b2, size=(1, 21), mode="nearest")
b3 = np.where(np.abs(b2 - med) > 0.15, med, b2)
table("  то же после медианного фильтра", p, b3)
