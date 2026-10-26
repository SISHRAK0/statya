"""Агрегация по рынкам: мощность, кластеры по событию, влияние FLB / премии за риск,
калибровка шума, который «объяснил бы» Betfair-результат Augenblick–Rabin."""
import numpy as np
from scipy.stats import norm
from common import latent_paths

rng = np.random.default_rng(5)

print("(1) Точная нулевая дисперсия полного потока для непрерывного мартингала:")
print("    M = [p]_T =d время выхода BM из (0,1) из p0 => E M = u, Var M = u(1-2u)/3, u=p0(1-p0)")
for p0 in [0.5, 0.3, 0.1, 0.03]:
    u = p0 * (1 - p0); cv = np.sqrt(u * (1 - 2 * u) / 3) / u
    print(f"    p0={p0:.2f}: CV(M)={cv:.2f};  N для |Xnorm-1|=0.05 при 2σ: {int((2*cv/0.05)**2)}")
pm = rng.uniform(0.05, 0.95, 10 ** 6); u = pm * (1 - pm)
se1 = np.sqrt(np.mean(u * (1 - 2 * u) / 3)) / np.mean(u)
print(f"    смесь p0~U(0.05,0.95): SE(Xnorm) ≈ {se1:.2f}/sqrt(N) -> N=1000: {se1/np.sqrt(1000):.3f}, "
      f"N=10000: {se1/np.sqrt(10000):.4f}, N=100000: {se1/np.sqrt(1e5):.4f}")

print("\n(2) Кластеры: событие = 5 пороговых рынков на одном X (как «BTC выше K»),")
print("    p_k = Phi((X_t - c_k)/sqrt(T-t)); сравниваем SE Xnorm по рынкам и по событиям")
E, K, n = 1500, 5, 1000
cs = np.linspace(-0.8, 0.8, K)
X0 = rng.normal(0, 0.3, E)
dW = rng.standard_normal((E, n)) * np.sqrt(1 / n)
X = X0[:, None] + np.concatenate([np.zeros((E, 1)), np.cumsum(dW, 1)], 1)
tau = 1 - np.arange(n) / n
Ms, U = [], []
for c in cs:
    p = norm.cdf((X[:, :n] - c) / np.sqrt(tau)); Y = (X[:, n] > c).astype(float)
    path = np.concatenate([p, Y[:, None]], 1)
    Ms.append(np.sum(np.diff(path, 1) ** 2, 1)); U.append(p[:, 0] * (1 - p[:, 0]))
M = np.array(Ms).T; U = np.array(U).T            # (E, K)
xn = M.sum() / U.sum()
r = (M - U) / U.mean()                             # вклад в Xnorm-1
se_naive = r.std() / np.sqrt(r.size)
se_cl = r.sum(1).std() / r.size * np.sqrt(E)
print(f"    Xnorm={xn:.3f}; SE наивная={se_naive:.4f}, кластерная по событию={se_cl:.4f} "
      f"(отношение {se_cl/se_naive:.2f}); средняя межрыночная корр. M: "
      f"{np.mean(np.corrcoef(M.T)[np.triu_indices(K,1)]):.2f}")

print("\n(3) Neg-risk: событие из K исходов, сумма вероятностей 1, разрешение one-hot.")
print("    Событийная статистика S = sum_i sum_t (dp_i)^2, E S = 1 - sum p_i0^2  (проверено в 01, п.(f)).")

print("\n(4) Статические искажения цены (FLB / сжатие к 0.5): цена p = Phi(Phi^{-1}(pi)/beta),")
print("    pi — P-мартингал (истинная вероятность), исход разыгрывается по P. Xnorm по полному потоку:")
N, n = 6000, 1000
for beta in [0.8, 0.9, 1.0, 1.1, 1.25]:
    pi0 = rng.uniform(0.1, 0.9, N)
    pi, Y = latent_paths(N, n, pi0, rng=rng)
    p = norm.cdf(norm.ppf(np.clip(pi, 1e-12, 1 - 1e-12)) / beta)
    path = np.concatenate([p, Y[:, None]], 1)
    Mx = np.sum(np.diff(path, 1) ** 2, 1); u0 = p[:, 0] * (1 - p[:, 0])
    # окно без исхода: X = sum dp^2 - (u(p_0) - u(p_tau)), tau=0.9T
    m = int(0.9 * n); Mw = np.sum(np.diff(p[:, :m + 1], 1) ** 2, 1)
    rw = u0 - p[:, m] * (1 - p[:, m])
    tag = {0.8: "экстремизация", 0.9: "экстремизация", 1.0: "мартингал", 1.1: "FLB/сжатие", 1.25: "FLB/сжатие"}[beta]
    print(f"    beta={beta:4.2f} ({tag:13s}): Xnorm полный={Mx.sum()/u0.sum():.3f}±{Mx.std()/np.sqrt(N)/u0.mean():.3f}"
          f"   Xnorm окно[0,0.9T]={Mw.sum()/rw.sum():.3f}")

print("\n(5) Калибровка: какой iid-шум цены объяснил бы Betfair-результат A–R (2020/21)?")
print("    E[X_naive] - E[X] = 2 σ_ε^2 на шаг (A–R, сноска 21). Betfair: 7.42 млн набл./286 тыс. событий")
m_per = 7_422_530 / 286_257; mov_per = 61_382 / 286_257
for target in [0.046, 0.012]:
    s2 = target * mov_per / (2 * m_per)
    print(f"    Xnorm-1={target}: σ_ε ≈ {np.sqrt(s2)*100:.2f} п.п. (шагов на событие ≈{m_per:.0f}, движение ≈{mov_per:.3f})")
