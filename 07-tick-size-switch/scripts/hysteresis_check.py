"""Проверка гистерезиса/«рождённых мелкими» по истории цен CLOB (/prices-history, шаг 60 мин).
Для выборки рынков с текущим тиком 0.001 и mid в [0.1,0.9] и с тиком 0.01:
был ли когда-либо YES-цена <0.04 или >0.96 (по почасовой истории (startTs — interval=max при fidelity=60 обрезает до 30 дней!) — оценка снизу касаний).
Запуск: python3 -I hysteresis_check.py OUT_DIR [N]   (читает OUT_DIR/markets.json от scan_ticks.py)
"""
import json, sys, random, urllib.request, time, collections
out = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 150
rows = json.load(open(f"{out}/markets.json"))
act = [x for x in rows if (x["vol24"] or 0) > 0 and x["tokens"]]
random.seed(7)
def hist(tok):
    u = f"https://clob.polymarket.com/prices-history?market={tok}&startTs=1600000000&fidelity=60"
    for i in range(3):
        try:
            return [h["p"] for h in json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "r"}), timeout=30))["history"]]
        except Exception:
            time.sleep(1 + i)
    return []
res = {}
for name, pool in [("tick0.001_mid", [x for x in act if x["tick"] == 0.001 and .1 <= x["p"] <= .9]),
                   ("tick0.01_any", [x for x in act if x["tick"] == 0.01])]:
    c = collections.Counter(); ex = []
    for x in random.sample(pool, min(N, len(pool))):
        h = hist(json.loads(x["tokens"])[0])
        if not h: c["no_history"] += 1; continue
        touched = min(h) < 0.04 or max(h) > 0.96
        c["touched" if touched else "never"] += 1
        if (name.startswith("tick0.01") and touched) or (name.startswith("tick0.001") and not touched):
            ex.append((x["slug"][:60], round(min(h), 4), round(max(h), 4), x["created"][:10], x["feeType"]))
    res[name] = dict(counts=c, examples=ex[:15])
    print(name, dict(c)); [print("   ", e) for e in ex[:15]]
json.dump(res, open(f"{out}/hysteresis.json", "w"), default=str)
