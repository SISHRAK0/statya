"""Когда происходит переключение относительно разрешения: по почасовой истории YES-цены
закрытых рынков (выход closed_switch_rate.py) находим первое касание mid<0.04 или >0.96
и считаем часы до конца торгов. Почасовая история = mid/last с шагом 60 мин => оценка грубая.
Запуск: python3 -I switch_timing.py OUT_DIR [N]
"""
import json, sys, random, urllib.request, time, statistics, collections
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 200
rows = [r for r in json.load(open(f"{out}/closed.json")) if r["vol"] > 1000 and r.get("tokens") and "updown" not in r["slug"]]
random.seed(3); smp = random.sample(rows, min(N, len(rows)))
def hist(tok):
    u = f"https://clob.polymarket.com/prices-history?market={tok}&startTs=1600000000&fidelity=60"
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "r"}), timeout=30))["history"]
        except Exception:
            time.sleep(1 + i)
    return []
lead = []; c = collections.Counter()
for r in smp:
    h = hist(json.loads(r["tokens"])[0])
    if len(h) < 2: c["nohist"] += 1; continue
    tend = h[-1]["t"]
    hit = next((x["t"] for x in h if x["p"] < 0.04 or x["p"] > 0.96), None)
    if hit is None: c["no_touch_hourly"] += 1; continue
    c["touch"] += 1; lead.append((tend - hit) / 3600)
lead.sort()
q = lambda a, f: a[int(f * (len(a) - 1))]
print(dict(c))
if lead:
    print("hours from first touch to last history point: p10 %.1f p25 %.1f median %.1f p75 %.1f p90 %.1f" % tuple(q(lead, f) for f in (.1, .25, .5, .75, .9)))
    for th in (1, 24, 24 * 7, 24 * 30):
        print(f"  share with >= {th} h before end: {sum(l >= th for l in lead)/len(lead):.2f}")
