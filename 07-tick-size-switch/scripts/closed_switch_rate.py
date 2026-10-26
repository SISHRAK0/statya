"""Оценка частоты переключений тика по закрытым рынкам за окно (Gamma /markets/keyset?closed=true).
Тик на момент закрытия = 0.001 и цена в истории когда-то касалась порога => переключение произошло
(одностороннее). Группируем по типу рынка (крипто up/down 5m/15m/1h/4h, спорт, прочее).
Запуск: python3 -I closed_switch_rate.py OUT_DIR END_MIN END_MAX
"""
import json, sys, urllib.request, urllib.parse, collections, time, re
out, emin, emax = sys.argv[1], sys.argv[2], sys.argv[3]
def get(u):
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "r"}), timeout=60))
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError(u)
rows, cur = [], None
while True:
    u = f"https://gamma-api.polymarket.com/markets/keyset?closed=true&limit=500&end_date_min={emin}&end_date_max={emax}"
    if cur: u += "&after_cursor=" + urllib.parse.quote(cur)
    d = get(u)
    for m in d.get("markets", []):
        rows.append(dict(slug=m.get("slug"), tick=m.get("orderPriceMinTickSize"), vol=m.get("volumeNum") or 0,
                         end=m.get("endDate"), created=m.get("createdAt"), feeType=m.get("feeType"),
                         tokens=m.get("clobTokenIds"), closedTime=m.get("closedTime")))
    cur = d.get("next_cursor")
    if not cur or not d.get("markets"): break
json.dump(rows, open(f"{out}/closed.json", "w"))
def kind(s):
    m = re.search(r"updown-(\w+)-\d+$", s or "")
    if m: return "crypto-updown-" + m.group(1)
    if (s or "").startswith(("nfl-", "nba-", "mlb-", "nhl-", "epl-", "ucl-", "atp-", "wta-", "cbb-", "cfb-", "lal-", "sea-")): return "sports-game"
    return "other"
g = collections.defaultdict(collections.Counter)
for r in rows:
    if r["vol"] > 0: g[kind(r["slug"])][r["tick"]] += 1
print("closed with volume, window", emin, emax, "total rows", len(rows))
for k, c in sorted(g.items(), key=lambda kv: -sum(kv[1].values())):
    n = sum(c.values()); print(f"{k:24s} n={n:6d} share_tick0.001={c.get(0.001,0)/n:.2f}  {dict(c)}")
