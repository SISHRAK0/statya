"""Снимок всех активных рынков Polymarket (Gamma /markets/keyset): цена vs orderPriceMinTickSize.
Печатает: распределение тиков по бинам цены (mid из outcomePrices), рынки с тиком 0.01 у краёв,
число рынков в «зоне подхода» к порогу (0.04..0.06 и 0.94..0.96) с тиком 0.01 — кандидаты на переключение.
Запуск: python3 -I scan_ticks.py OUT_DIR   (пишет OUT_DIR/markets.json)
"""
import json, sys, urllib.request, urllib.parse, collections, time
out = sys.argv[1] if len(sys.argv) > 1 else "."

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research"})
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError(url)

rows, cur = [], None
while True:
    url = "https://gamma-api.polymarket.com/markets/keyset?active=true&closed=false&limit=500"
    if cur: url += "&after_cursor=" + urllib.parse.quote(cur)
    d = get(url)
    for m in d.get("markets", []):
        try:
            p = float(json.loads(m.get("outcomePrices") or "[]")[0])
        except Exception:
            continue
        rows.append(dict(id=m["id"], slug=m.get("slug"), p=p, tick=m.get("orderPriceMinTickSize"),
                         bid=m.get("bestBid"), ask=m.get("bestAsk"), spread=m.get("spread"),
                         last=m.get("lastTradePrice"), end=m.get("endDate"), created=m.get("createdAt"),
                         ob=m.get("enableOrderBook"), acc=m.get("acceptingOrders"),
                         tokens=m.get("clobTokenIds"), vol24=m.get("volume24hr"), negRisk=m.get("negRisk"),
                         feeType=m.get("feeType")))
    cur = d.get("next_cursor")
    if not cur or not d.get("markets"): break
json.dump(rows, open(f"{out}/markets.json", "w"))
live = [r for r in rows if r["ob"] and r["acc"]]
print("rows:", len(rows), "accepting orders:", len(live))
print("tick counts:", collections.Counter(r["tick"] for r in live))
bins = [0, .005, .01, .02, .03, .035, .04, .045, .05, .06, .1, .5, .9, .94, .95, .955, .96, .965, .97, .98, .99, .995, 1.0001]
for lo, hi in zip(bins, bins[1:]):
    sub = [r for r in live if lo <= r["p"] < hi]
    print(f"[{lo:.3f},{hi:.3f}) n={len(sub):5d}", dict(collections.Counter(r["tick"] for r in sub)))
# по лучшим котировкам (bestBid/bestAsk) — проверка правила «цена стакана <0.04 / >0.96»
viol = [r for r in live if r["tick"] == 0.01 and r["bid"] is not None and r["ask"] is not None
        and (float(r["ask"]) < 0.04 or float(r["bid"]) > 0.96)]
print("tick 0.01 but whole top-of-book beyond threshold:", len(viol))
for r in viol[:10]: print("  ", r["bid"], r["ask"], r["slug"])
near = [r for r in live if r["tick"] == 0.01 and (0.04 <= r["p"] <= 0.06 or 0.94 <= r["p"] <= 0.96)]
print("tick 0.01, mid in [0.04,0.06]∪[0.94,0.96] (candidates):", len(near),
      " vol24>1000:", sum(1 for r in near if (r["vol24"] or 0) > 1000))
mid01 = [r for r in live if r["tick"] == 0.001 and 0.1 <= r["p"] <= 0.9]
print("tick 0.001 with mid in [0.1,0.9] (hysteresis / born-fine):", len(mid01))
