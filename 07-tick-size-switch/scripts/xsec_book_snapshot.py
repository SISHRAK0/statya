"""Пилотный кросс-секционный снимок: рынки с mid в [LO,HI] и тиком 0.01 vs 0.001
(тик 0.001 там почти всегда — след прошлого касания порога, т.е. гистерезис).
Метрики по живому стакану CLOB /book: котируемый спред (в вероятности), глубина на лучшей цене ($),
глубина в пределах ±1 цента от mid ($), число ценовых уровней в ±1 цент.
Запуск: python3 -I xsec_book_snapshot.py OUT_DIR LO HI [N] [MINVOL24]   (читает OUT_DIR/markets.json)
"""
import json, sys, random, urllib.request, time, statistics as st
out, lo, hi = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); N = int(sys.argv[4]) if len(sys.argv) > 4 else 80
MINVOL = float(sys.argv[5]) if len(sys.argv) > 5 else 500
rows = json.load(open(f"{out}/markets.json"))
def book(tok):
    u = f"https://clob.polymarket.com/book?token_id={tok}"
    for i in range(3):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "r"}), timeout=30))
        except Exception: time.sleep(1 + i)
random.seed(5)
for tick in (0.01, 0.001):
    pool = [x for x in rows if x["tick"] == tick and lo <= x["p"] <= hi and (x["vol24"] or 0) > MINVOL and x["tokens"]]
    M = {"spread": [], "best_depth_usd": [], "depth1c_usd": [], "levels1c": [], "spread_ticks": []}
    for x in random.sample(pool, min(N, len(pool))):
        b = book(json.loads(x["tokens"])[0])
        if not b or not b.get("bids") or not b.get("asks"): continue
        bids = sorted(((float(l["price"]), float(l["size"])) for l in b["bids"]), reverse=True)
        asks = sorted((float(l["price"]), float(l["size"])) for l in b["asks"])
        bb, ba = bids[0][0], asks[0][0]; mid = (bb + ba) / 2; t = float(b["tick_size"])
        if ba - bb > 0.1: continue
        M["spread"].append(ba - bb); M["spread_ticks"].append(round((ba - bb) / t))
        M["best_depth_usd"].append(bids[0][0] * bids[0][1] + asks[0][0] * asks[0][1])
        near = [(p, s) for p, s in bids + asks if abs(p - mid) <= 0.01 + 1e-9]
        M["depth1c_usd"].append(sum(p * s for p, s in near)); M["levels1c"].append(len(near))
    n = len(M["spread"])
    print(f"tick {tick}: pool {len(pool)}, books {n}")
    for k, v in M.items():
        if v: print(f"   {k:15s} median {st.median(v):10.4f}  mean {st.mean(v):10.4f}")
