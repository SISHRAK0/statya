"""Шум микроструктуры: probit-мартингал + bid-ask bounce + округление к шагу Polymarket.
Сравнение наивной RV, разреженной RV, TSRV, pre-averaging, realized kernel.

Окно [0, tau], tau = 0.9T (до финального «взрыва» волатильности); статистика
  Xnorm = sum_j QVhat_j / sum_j (u(p0_j) - u(p_tau_j)),  u(p) = p(1-p),
под нулём = 1 (латентная цена — мартингал). Концевые u — по наблюдаемым ценам
(среднее последних/первых 10 сделок), как сделал бы эмпирик.
Отдельно: полный поток до разрешения (с финальной точкой = исход Y)."""
import numpy as np
from common import latent_paths, observe, rv, rv_sparse, tsrv, preavg, rkernel

rng = np.random.default_rng(7)
N = 1500

def endpoint(b, i, side):
    return b[:, i:i + 10].mean(1) if side == 0 else b[:, i - 9:i + 1].mean(1)

def run(n, h, tick, iid_sd=0.0, frac=0.9, label=""):
    p0 = rng.uniform(0.15, 0.85, N)
    p, Y = latent_paths(N, n, p0, rng=rng)
    b = observe(p, rng, half_spread=h, tick=tick, iid_sd=iid_sd)
    m = int(frac * n)
    lat, ob = p[:, :m + 1], b[:, :m + 1]
    u = lambda x: x * (1 - x)
    den_lat = np.sum(u(lat[:, 0]) - u(lat[:, -1]))
    den_obs = np.sum(u(endpoint(ob, 0, 0)) - u(endpoint(ob, m, 1)))
    res = {"латентная RV": rv(lat).sum() / den_lat}
    est = {"наивная RV": rv(ob), "разреж. RV k=20": rv_sparse(ob, 20),
           "TSRV": tsrv(ob), "pre-avg": preavg(ob), "RK Parzen": rkernel(ob)}
    for k, v in est.items():
        res[k] = v.sum() / den_obs
    # кросс-секционная ст.ошибка Xnorm (через дельта-метод грубо: sd(QV)/mean(den)/sqrt(N))
    se = np.std(est["pre-avg"] - (u(endpoint(ob, 0, 0)) - u(endpoint(ob, m, 1)))) / (den_obs / N) / np.sqrt(N)
    print(f"{label:34s} " + "  ".join(f"{k}={v:6.3f}" for k, v in res.items()) + f"   (SE≈{se:.3f})")
    return p, b, Y

print("Xnorm на окне [0, 0.9T] (под нулём = 1). N =", N, "рынков, p0 ~ U(0.15,0.85)\n")
for n in [1000, 5000, 20000]:
    run(n, 0.01, True, label=f"n={n:5d} bounce h=0.01 + tick")
for n in [5000]:
    run(n, 0.005, True, label=f"n={n:5d} bounce h=0.005 + tick")
    run(n, 0.0, True, label=f"n={n:5d} только округление")
    run(n, 0.0, False, iid_sd=0.01, label=f"n={n:5d} iid N(0,0.01^2), без шага")

print("\nПолный поток до разрешения (последняя точка = исход Y, без шума):")
for n in [5000]:
    p0 = rng.uniform(0.15, 0.85, N)
    p, Y = latent_paths(N, n, p0, rng=rng)
    b = observe(p, rng, half_spread=0.01, tick=True)
    u0 = np.sum(p0 * (1 - p0))
    lat = np.concatenate([p, Y[:, None]], 1); ob = np.concatenate([b, Y[:, None]], 1)
    out = {"латентная": rv(lat).sum() / u0, "наивная RV": rv(ob).sum() / u0, "TSRV": tsrv(ob).sum() / u0,
           "pre-avg": preavg(ob).sum() / u0, "RK": rkernel(ob).sum() / u0}
    # гибрид: робастная QV до 0.9T + наивная сумма квадратов по редким точкам хвоста + финальный скачок
    m = int(0.9 * n)
    tail = ob[:, m:]
    hyb = preavg(ob[:, :m + 1]) + rv_sparse(tail, 25) + 0  # rv_sparse включает последнюю точку только если попала
    tail_s = np.concatenate([tail[:, ::25], Y[:, None]], 1)
    hyb = preavg(ob[:, :m + 1]) + rv(tail_s)
    out["гибрид PA+разреж.хвост"] = hyb.sum() / u0
    print("  " + "  ".join(f"{k}={v:.3f}" for k, v in out.items()))
