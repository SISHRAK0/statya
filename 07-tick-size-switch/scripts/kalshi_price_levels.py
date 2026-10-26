"""Kalshi: распределение price_level_structure / price_ranges у открытых рынков (публичный API).
Запуск: python3 -I kalshi_price_levels.py [MAX_PAGES]
"""
import json, sys, urllib.request, urllib.parse, collections, time
P = int(sys.argv[1]) if len(sys.argv) > 1 else 30
c = collections.Counter(); ex = {}; cur = None; n = 0; mve = collections.Counter()
for _ in range(P):
    u = "https://api.elections.kalshi.com/trade-api/v2/markets?limit=1000&status=open&mve_filter=exclude"
    if cur: u += "&cursor=" + urllib.parse.quote(cur)
    d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "r"}), timeout=60))
    for m in d.get("markets", []):
        k = m.get("price_level_structure"); c[k] += 1; n += 1
        ex.setdefault(k, (m["ticker"], m.get("price_ranges")))
    cur = d.get("cursor")
    if not cur: break
    time.sleep(0.3)
print("markets:", n); print(c)
for k, v in ex.items(): print(k, v)
