"""Liquidity-rewards contest with adverse-selection costs (topic 06).

Stylised model (RESEARCH.md, section 2):
  N symmetric makers; maker i posts a symmetric two-sided quote at half-spread
  s_i ($ from the size-cutoff-adjusted midpoint) with q_i shares per side.
  Polymarket score:  w_i = q_i * S(s_i),  S(s) = ((v - s)/v)^2 for s < v, else 0.
  Reward: R * w_i / sum_j w_j  (Tullock contest, r = 1, in score units).
  Trading P&L per share of resting depth per day (each maker faces its own
  flow -- no price-priority competition for flow, so the model isolates the
  rewards contest):
      pi(s) = lamU * s * exp(-s/kap)      uninformed, elastic in the spread
            - lamI * sig * exp(-s/sig)    informed: exp. jumps of mean sig,
                                          trade iff jump > s, loss = jump - s
            - k                           capital cost
      c(s) = -pi(s)   (net cost per share)
  Inventory risk gamma/2 * q^2.
      U_i = R * w_i / W - q_i * c(s_i) - gamma/2 * q_i^2

Symmetric interior NE (K = R (N-1) / N^2):
      q = 2K / ((v - s) * (-c'(s)))        (FOC in s)
      K / q = c(s) + gamma * q             (FOC in q)
Solved on a fine s-grid, then verified by a global grid best response.
Benchmarks: no-reward optimum (= cooperative quoting: with a lump-sum pool the
makers' joint surplus is maximised by ignoring the score), 2x2 Wide/Tight game.

Run:  python3 rewards_contest.py
"""
import numpy as np

BASE = dict(v=0.045, sig=0.02, kap=0.03, lamU=0.6, alpha=0.3, k=0.0003,
            gamma=2e-6, m=20.0)


def lamI(p):
    return p["lamU"] * p["alpha"] / (1.0 - p["alpha"])


def c(s, p):
    return (p["k"] + lamI(p) * p["sig"] * np.exp(-s / p["sig"])
            - p["lamU"] * s * np.exp(-s / p["kap"]))


def dc(s, p, h=1e-7):
    return (c(s + h, p) - c(s - h, p)) / (2 * h)


def S(s, p):
    s = np.asarray(s, float)
    return np.where(s < p["v"], ((p["v"] - s) / p["v"]) ** 2, 0.0)


def payoff(si, qi, s_o, q_o, R, N, p):
    wi = qi * S(si, p)
    W = wi + (N - 1) * q_o * S(s_o, p)
    share = np.where(W > 0, wi / np.where(W > 0, W, 1.0), 0.0)
    return R * share - qi * c(si, p) - 0.5 * p["gamma"] * qi ** 2


def best_q_given_s(s, Wo, R, p):
    """argmax_q R qS/(qS+Wo) - q c - g q^2/2, q in {0} U [m, inf)."""
    Ss, cs, g = float(S(s, p)), float(c(s, p)), p["gamma"]
    if Ss <= 0 or Wo <= 0:
        # no contest (or no score): pure trading optimum, or min size if alone
        q = max(0.0, -cs / g)
        if Ss > 0 and Wo <= 0:  # alone -> any positive score wins whole pool
            q = max(q, p["m"])
        return q
    f = lambda q: R * Ss * Wo / (q * Ss + Wo) ** 2 - cs - g * q
    lo, hi = 0.0, 1e9
    if f(lo) <= 0:
        return 0.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    q = lo
    if q < p["m"]:  # compare q=m vs abstaining
        q = p["m"] if payoff(s, p["m"], 0, 0, 0, 1, p) + R * p["m"] * Ss / (p["m"] * Ss + Wo) > 0 else 0.0
    return q


def best_response(s_o, q_o, R, N, p, ns=1500):
    Wo = (N - 1) * q_o * float(S(s_o, p))
    grid = np.concatenate([np.linspace(0, p["v"] * 0.999, ns), np.linspace(p["v"], 0.2, 300)])
    best = (-np.inf, None, None)
    for s in grid:
        q = best_q_given_s(s, Wo, R, p)
        u = float(payoff(s, q, s_o, q_o, R, N, p))
        if u > best[0]:
            best = (u, s, q)
    return best


def nash(R, N, p, ns=20000):
    K = R * (N - 1) / N ** 2
    s = np.linspace(0, p["v"] * 0.9999, ns)
    cp = dc(s, p)
    with np.errstate(divide="ignore", invalid="ignore"):
        q = 2 * K / ((p["v"] - s) * (-cp))
        resid = K / q - c(s, p) - p["gamma"] * q
    ok = (cp < 0) & np.isfinite(resid)
    cand = []
    idx = np.where(ok[:-1] & ok[1:] & (np.sign(resid[:-1]) != np.sign(resid[1:])))[0]
    for i in idx:
        cand.append((s[i], q[i]))
    # corner s = 0: q from q-FOC alone
    c0, g = float(c(0.0, p)), p["gamma"]
    q0 = (-c0 + np.sqrt(c0 ** 2 + 4 * g * K)) / (2 * g)
    cand.append((0.0, q0))
    # pick candidate that survives deviation check best
    best = None
    for sc, qc in cand:
        u = float(payoff(sc, qc, sc, qc, R, N, p))
        ub, _, _ = best_response(sc, qc, R, N, p, ns=600)
        gap = ub - u
        if best is None or gap < best[2]:
            best = (sc, qc, gap)
    return best


def no_reward(p):
    ss = np.linspace(0, 0.2, 40001)
    cc = c(ss, p)
    i = int(np.argmin(cc))
    return ss[i], max(0.0, -cc[i] / p["gamma"])


def summary(R, N, p):
    s, q, gap = nash(R, N, p)
    s0, q0 = no_reward(p)
    u = float(payoff(s, q, s, q, R, N, p))
    tr = lambda s_, q_: -q_ * c(s_, p) - 0.5 * p["gamma"] * q_ ** 2
    dissip = N * (tr(s0, q0) - tr(s, q)) / R
    # depth inside v: baseline quotes at s0 >= v contribute nothing
    D0v = N * q0 if s0 < p["v"] else 0.0
    return dict(s=s, q=q, D=N * q, s0=s0, q0=q0, u=u, dissip=dissip, gap=gap,
                depth_per_usd=(N * q - D0v) / R)


def fmt(d):
    return (f"s*={d['s']*100:5.2f}c q*={d['q']:8.0f} D={d['D']:8.0f} | "
            f"U_i={d['u']:8.2f} dissip={d['dissip']:5.2f} "
            f"depthInV/$={d['depth_per_usd']:6.1f} NEgap={d['gap']:.1e}")


def pd_matrix(R, p, N=2):
    s, q, _ = nash(R, N, p)
    s0, q0 = no_reward(p)
    if s0 >= p["v"]:  # 'wide' must still be in the band to stay eligible
        s0 = p["v"] * 0.95
        q0 = max(p["m"], -float(c(s0, p)) / p["gamma"])
    Wd, Td = (s0, q0), (s, q)
    out = {}
    for a, xa in (("W", Wd), ("T", Td)):
        for b, xb in (("W", Wd), ("T", Td)):
            out[a + b] = float(payoff(xa[0], xa[1], xb[0], xb[1], R, N, p))
    T_, R_, P_, S_ = out["TW"], out["WW"], out["TT"], out["WT"]
    return out, (s0, q0, s, q), (T_ > R_ > P_ > S_)


if __name__ == "__main__":
    p = dict(BASE)
    s0, q0 = no_reward(p)
    print("base", p, f"| lamI={lamI(p):.3f}")
    print(f"no-reward optimum: s0={s0*100:.2f}c q0={q0:.0f} (s0 vs v={p['v']*100:.1f}c)")
    print("\n-- R ($/day), N=5")
    for R in [5, 20, 100, 500, 2000]:
        print(f"R={R:5d}", fmt(summary(R, 5, p)))
    print("\n-- N, R=200")
    for N in [2, 3, 5, 10, 30]:
        print(f"N={N:3d}", fmt(summary(200, N, p)))
    print("\n-- v (max spread), R=200, N=5")
    for v in [0.015, 0.025, 0.035, 0.045, 0.065, 0.085]:
        print(f"v={v*100:4.1f}c", fmt(summary(200, 5, dict(p, v=v))))
    print("\n-- alpha (informed share), R=200, N=5")
    for a in [0.1, 0.2, 0.3, 0.4, 0.5]:
        print(f"a={a:.1f}", fmt(summary(200, 5, dict(p, alpha=a))))
    print("\n-- gamma (inventory convexity), R=20 vs 2000, N=5")
    for g in [1e-8, 2e-7, 2e-6, 2e-5]:
        a, b = summary(20, 5, dict(p, gamma=g)), summary(2000, 5, dict(p, gamma=g))
        print(f"g={g:.0e}  s*(R=20)={a['s']*100:5.2f}c  s*(R=2000)={b['s']*100:5.2f}c  "
              f"D(R=20)={a['D']:9.0f} D(R=2000)={b['D']:9.0f}")
    print("\n-- 2x2 Wide/Tight, N=2 (Wide = no-reward quote kept inside band)")
    for R in [20, 200, 2000]:
        m, (sw, qw, st, qt), isPD = pd_matrix(R, p)
        print(f"R={R:5d} W=({sw*100:.2f}c,{qw:.0f}) T=({st*100:.2f}c,{qt:.0f}) "
              + " ".join(f"{k}={v:8.2f}" for k, v in m.items()), "-> PD" if isPD else "-> not PD")
