"""Механический FLB от сетки цен: истинная вероятность v, тик d, минимальный спред в 1 тик
(bid = floor(v/d)*d, ask = bid + d; цена ограничена [d, 1-d]). Тейкер, покупающий YES, платит ask
(+ комиссия f*p*(1-p) на акцию); покупатель NO платит 1-bid. Доходность = E[payoff]/цена - 1.
Усредняем по v равномерно внутри ценовой корзины (положение v внутри клетки сетки случайно).
Запуск: python3 -I mech_flb.py
"""
import math
def ret(v, d, fee):
    bid = max(d, math.floor(v / d + 1e-12) * d)
    ask = min(1 - d, bid + d) if v >= d else d          # v < d: лучший ask не ниже d (пол сетки)
    bid = min(bid, 1 - 2 * d)
    py, pn = ask, 1 - bid
    ry = v / (py + fee * py * (1 - py)) - 1
    rn = (1 - v) / (pn + fee * pn * (1 - pn)) - 1
    return ry, rn, (ask + bid) / 2 - v
bins = [(0.001, 0.005), (0.005, 0.01), (0.01, 0.02), (0.02, 0.04), (0.04, 0.06), (0.06, 0.10), (0.10, 0.20), (0.20, 0.50)]
for fee in (0.0, 0.05):
    print(f"\nfee rate {fee}:  bin | tick | E[ret buy YES] | E[ret buy NO] | E[mid - v]")
    for lo, hi in bins:
        for d in (0.01, 0.001):
            vs = [lo + (hi - lo) * (i + .5) / 2000 for i in range(2000)]
            r = [ret(v, d, fee) for v in vs]
            ay = sum(x[0] for x in r) / len(r); an = sum(x[1] for x in r) / len(r); mb = sum(x[2] for x in r) / len(r)
            print(f"  [{lo:.3f},{hi:.3f}) d={d:<5} {ay:+8.1%} {an:+8.2%} {mb:+.4f}")
