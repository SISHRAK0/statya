#!/usr/bin/env python3
"""Прототип: турнир стратегий маркет-мейкинга по Аксельроду (тема 10).

Среда (один период = стадия повторяющейся игры):
  * бинарный контракт, справедливая середина 0.5, исход V ~ Bernoulli(0.5) скрыт;
  * шумовые трейдеры: Poisson(LAM_N/2) покупок и столько же продаж за период;
  * информированный: Poisson(lam_i) единиц на «правильной» стороне (покупает при V=1);
  * мейкеры котируют симметрично 0.5 ± h, h на сетке тика, Q единиц на сторону;
  * исполнение: цена, затем время (кто раньше встал на эту цену); одновременный
    приход на цену = усреднение по всем порядкам очереди;
  * пул наград по формуле Polymarket: score = ((v-h)/v)^2 * Q, доля от пула.
Ожидаемые выплаты стадии считаются точно (пуассоновские хвосты), случайность —
только в стратегиях (GTFT, ZD, Q-learning, дрожание EPS). Всё детерминировано seed'ом.
"""
import argparse, itertools, math
import numpy as np

W = 0.04       # «кооперативный» (широкий) полуспред
V_MAX = 0.045  # max spread от середины (v в формуле наград)
Q = 6          # размер котировки на сторону
LAM_N = 20.0   # шумовых заявок за период (обе стороны)
EPS = 0.02     # дрожание: намерение C<->D переворачивается с этой вероятностью
KMAX = 120


def pois(mu):
    k = np.arange(KMAX)
    return np.exp(k * math.log(mu) - mu - np.array([math.lgamma(x + 1) for x in k]))


class Env:
    def __init__(self, tick, pool, alpha, step=0.0):
        self.tick, self.pool, self.alpha = tick, pool, alpha
        self.step = max(tick, step)                   # на сколько подрезает 'D'
        self.lam_i = alpha * LAM_N / (1 - alpha)
        self.sstar = 0.5 * alpha                      # безубыточный полуспред без наград
        self.floor = round(max(tick, math.ceil(self.sstar / tick - 1e-9) * tick), 6)
        self.k = np.arange(KMAX)
        self.p_hi = pois(LAM_N / 2 + self.lam_i)      # поток на «проигрышной» стороне
        self.p_lo = pois(LAM_N / 2)
        self.nf = (LAM_N / 2) / (LAM_N / 2 + self.lam_i)
        self.cache = {}

    def efill(self, p, ahead):
        return float(np.sum(p * np.clip(self.k - ahead, 0, Q)))

    def _ordered(self, hs, order):
        """Выплаты при фиксированной очереди order (индексы мейкеров)."""
        n = len(hs); pnl = np.zeros(n); noise_cost = 0.0; ahead = 0
        for i in order:
            h = hs[i]
            f_hi, f_lo = self.efill(self.p_hi, ahead), self.efill(self.p_lo, ahead)
            # одна сторона; x2 за симметрию bid/ask
            pnl[i] = 2 * 0.5 * (f_hi * (h - 0.5) + f_lo * (0.5 + h))
            noise_cost += 2 * 0.5 * (f_hi * self.nf + f_lo) * h
            ahead += Q
        return pnl, noise_cost

    def stage(self, hs, since):
        """Ожидаемые (выплаты мейкеров, издержки шумовых). since — период прихода на цену."""
        key = (tuple(hs), tuple(since))
        if key in self.cache:
            return self.cache[key]
        n = len(hs)
        groups = {}
        for i in range(n):
            groups.setdefault((hs[i], since[i]), []).append(i)
        glist = [groups[g] for g in sorted(groups)]
        perms = list(itertools.product(*[itertools.permutations(g) for g in glist]))
        pnl = np.zeros(n); nc = 0.0
        for pr in perms:
            p, c = self._ordered(hs, [i for g in pr for i in g])
            pnl += p / len(perms); nc += c / len(perms)
        sc = np.array([((V_MAX - h) / V_MAX) ** 2 * Q if h < V_MAX else 0.0 for h in hs])
        if sc.sum() > 0:
            pnl = pnl + self.pool * sc / sc.sum()
        self.cache[key] = (pnl, nc)
        return pnl, nc

    def benchmark(self, h, n=2):
        return self.stage([h] * n, [0] * n)[0][0]


# ---------- стратегии: act(...) -> намерение 'C' (широко), 'D' (подрезать), 'M' (сравняться)
class Strat:
    name = "?"
    def reset(self, rng, T): self.rng = rng; self.T = T
    def act(self, t, me_c, oth_c, payoff): raise NotImplementedError
    def learn(self, payoff, me_c, oth_c): pass


class Wide(Strat):
    name = "WIDE"
    def act(self, *a): return "C"

class Undercut(Strat):
    name = "UNDERCUT"
    def act(self, *a): return "D"

class TFT(Strat):
    name = "TFT"
    def act(self, t, me_c, oth_c, p): return "C" if t == 0 or oth_c else "M"

class GTFT(Strat):
    name = "GTFT"
    def act(self, t, me_c, oth_c, p):
        if t == 0 or oth_c: return "C"
        return "C" if self.rng.random() < 1 / 3 else "M"

class Grim(Strat):
    name = "GRIM"
    def reset(self, rng, T): super().reset(rng, T); self.trig = False
    def act(self, t, me_c, oth_c, p):
        if t > 0 and not oth_c: self.trig = True
        return "D" if self.trig else "C"

class WSLS(Strat):
    name = "WSLS"
    def act(self, t, me_c, oth_c, p): return "C" if t == 0 or me_c == oth_c else "D"

class ZDExtort(Strat):
    """Вероятности Press–Dyson (chi=3) на классификации C/D — лишь аналог ZD."""
    name = "ZD-EXT"
    P = {(True, True): 11 / 13, (True, False): 1 / 2, (False, True): 7 / 26, (False, False): 0.0}
    def act(self, t, me_c, oth_c, p):
        if t == 0: return "C"
        return "C" if self.rng.random() < self.P[(me_c, oth_c)] else "D"

class QL(Strat):
    """Табличный Q-learning: состояние (я C?, соперники C?), действия C/D; учится внутри матча."""
    name = "Q-LEARN"
    def reset(self, rng, T):
        super().reset(rng, T); self.q = np.zeros((5, 2)); self.s = 4; self.a = 0
        self.beta = 5.0 / T
    def act(self, t, me_c, oth_c, p):
        self.s = 4 if t == 0 else 2 * int(me_c) + int(oth_c)
        eps = math.exp(-self.beta * t)
        self.a = int(self.rng.integers(2)) if self.rng.random() < eps else int(np.argmax(self.q[self.s]))
        return "C" if self.a == 0 else "D"
    def learn(self, payoff, me_c, oth_c):
        s2 = 2 * int(me_c) + int(oth_c)
        self.q[self.s, self.a] += 0.1 * (payoff + 0.95 * self.q[s2].max() - self.q[self.s, self.a])


ALL = [Wide, Undercut, TFT, GTFT, Grim, WSLS, ZDExtort, QL]


def price(intent, others, env):
    lo = min(others)
    if intent == "C": return W
    if intent == "M": return round(max(env.floor, min(lo, W)), 6)
    return round(max(env.floor, min(lo, W) - env.step), 6)


def match(env, classes, T, rng):
    n = len(classes)
    ss = [c() for c in classes]
    for s in ss: s.reset(rng, T)
    hs = [W] * n; since = [0] * n; pay = np.zeros(n); spread = 0.0; ncost = 0.0
    last = [0.0] * n
    for t in range(T):
        new = []
        for i, s in enumerate(ss):
            others = [hs[j] for j in range(n) if j != i]
            me_c = hs[i] >= W - 1e-9
            oth_c = min(others) >= W - 1e-9
            it = s.act(t, me_c, oth_c, last[i])
            if rng.random() < EPS: it = "C" if it != "C" else "D"
            new.append(price(it, others, env))
        since = [since[i] if new[i] == hs[i] else t for i in range(n)]
        hs = new
        p, c = env.stage(hs, since)
        for i, s in enumerate(ss):
            others = [hs[j] for j in range(n) if j != i]
            s.learn(p[i], hs[i] >= W - 1e-9, min(others) >= W - 1e-9)
        last = list(p); pay += p; spread += min(hs); ncost += c
    return pay / T, spread / T, ncost / T


def replicator(M, steps=20000, dt=0.05):
    k = len(M); x = np.full(k, 1 / k)
    scale = max(np.ptp(M), 1e-9)
    for _ in range(steps):
        f = M @ x
        x = np.clip(x + dt * x * (f - x @ f) / scale, 0, None); x /= x.sum()
    return x


def tournament(env, T, reps, seed, cid):
    k = len(ALL); M = np.zeros((k, k)); S = np.zeros((k, k)); C = np.zeros((k, k))
    for i in range(k):
        for j in range(i, k):
            for r in range(reps):
                rng = np.random.default_rng([seed, cid, i, j, r])
                p, sp, nc = match(env, [ALL[i], ALL[j]], T, rng)
                if i == j:
                    M[i, i] += p.mean() / reps
                else:
                    M[i, j] += p[0] / reps; M[j, i] += p[1] / reps
                S[i, j] += sp / reps; S[j, i] = S[i, j]; C[i, j] += nc / reps; C[j, i] = C[i, j]
    return M, S, C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--T", type=int, default=600)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--step", type=float, default=0.0, help="шаг подрезания (0 = один тик)")
    a = ap.parse_args()
    names = [c.name for c in ALL]
    ticks, alphas = [0.01, 0.001], [0.0, 0.03, 0.06]
    pools = {"0": 0.0, "мал": 0.1, "бол": 1.0}
    print("## Стадия-игра 2×2 (C = полуспред W, D = W − шаг; R,S,T,P — выплата строчного игрока)\n")
    print("| тик | α | пул | R (C,C) | S (C,D) | T (D,C) | P (D,D) | PD? |")
    print("|---|---|---|---|---|---|---|---|")
    for tick in ticks:
        for al in alphas:
            for pn, pool in pools.items():
                e = Env(tick, pool, al, a.step); d = round(max(e.floor, W - e.step), 6)
                R = e.stage([W, W], [0, 0])[0][0]; P = e.stage([d, d], [0, 0])[0][0]
                Tm, Sm = e.stage([d, W], [0, 0])[0]
                pd = "да" if Tm > R > P > Sm else "нет"
                print(f"| {tick} | {al} | {pn} | {R:.3f} | {Sm:.3f} | {Tm:.3f} | {P:.3f} | {pd} |")
    print()
    print("## Круговой турнир (2 мейкера) + репликаторная динамика\n")
    print("| тик | α | пул | s* | пол | π_comp | π_coll | топ-3 турнира | выжившие (репликатор, доля) | полуспред (реплик.) | Δ (реплик.) | издержки шумовых |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    cid = 0
    for tick in ticks:
        for al in alphas:
            for pn, pool in pools.items():
                env = Env(tick, pool, al, a.step); cid += 1
                M, S, C = tournament(env, a.T, a.reps, a.seed, cid)
                score = M.mean(axis=1); top = np.argsort(-score)[:3]
                x = replicator(M)
                pc, pk = env.benchmark(env.floor), env.benchmark(W)
                pay = x @ M @ x
                d = (pay - pc) / (pk - pc) if abs(pk - pc) > 1e-12 else float("nan")
                surv = ", ".join(f"{names[i]} {x[i]:.2f}" for i in np.argsort(-x) if x[i] > 0.02)
                print(f"| {tick} | {al} | {pn} | {env.sstar:.3f} | {env.floor:.3f} | {pc:.3f} | {pk:.3f} | "
                      + ", ".join(names[i] for i in top)
                      + f" | {surv} | {x @ S @ x:.4f} | {d:.2f} | {x @ C @ x:.3f} |", flush=True)
    print("\n## Самоигра и вторжение, N мейкеров (α=0.03): средний лучший полуспред / Δ\n")
    groups = {"TFT×N": lambda n: [TFT] * n, "GRIM×N": lambda n: [Grim] * n,
              "WSLS×N": lambda n: [WSLS] * n, "QL×N": lambda n: [QL] * n,
              "TFT×(N−1)+UNDERCUT": lambda n: [TFT] * (n - 1) + [Undercut]}
    print("| тик | пул | группа | N=2 | N=3 | N=4 |")
    print("|---|---|---|---|---|---|")
    for tick in ticks:
        for pn, pool in pools.items():
            env = Env(tick, pool, 0.03, a.step)
            for gname, g in groups.items():
                cells = []
                for n in (2, 3, 4):
                    rng = np.random.default_rng([a.seed, 999, n, int(tick * 1000), int(pool * 10)])
                    p, sp, _ = match(env, g(n), a.T, rng)
                    pc, pk = env.benchmark(env.floor, n), env.benchmark(W, n)
                    cells.append(f"{sp:.4f} / {(p.mean() - pc) / (pk - pc):.2f}")
                print(f"| {tick} | {pn} | {gname} | " + " | ".join(cells) + " |", flush=True)


if __name__ == "__main__":
    main()
