"""Поток переключений «вдали от разрешения»: выборка активных торгуемых рынков с тиком 0.001
и endDate > CUTOFF; по почасовой истории (startTs — interval=max при fidelity=60 обрезает до 30 дней!) находим первое касание (<0.04 или >0.96) и считаем,
сколько первых касаний пришлось на последние 30 дней -> экстраполяция на генеральную совокупность.
Запуск: python3 -I switch_flow_longdated.py OUT_DIR CUTOFF_ISO NOW_UNIX [N]
"""
import json, sys, random, urllib.request, time, collections
out, cutoff, now = sys.argv[1], sys.argv[2], int(sys.argv[3]); N = int(sys.argv[4]) if len(sys.argv) > 4 else 300
rows = json.load(open(f"{out}/markets.json"))
pop = [x for x in rows if (x["vol24"] or 0) > 0 and x["tick"] == 0.001 and (x["end"] or "") > cutoff and x["tokens"]]
random.seed(11); smp = random.sample(pop, min(N, len(pop)))
def hist(tok):
    u = f"https://clob.polymarket.com/prices-history?market={tok}&startTs=1600000000&fidelity=60"
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "r"}), timeout=30))["history"]
        except Exception:
            time.sleep(1 + i)
    return []
c = collections.Counter(); ages = []
for x in smp:
    h = hist(json.loads(x["tokens"])[0])
    if not h: c["nohist"] += 1; continue
    t0 = h[0]["t"]
    hit = next((p["t"] for p in h if p["p"] < 0.04 or p["p"] > 0.96), None)
    if hit is None: c["never_touched(born_fine_or_intrahour)"] += 1; continue
    if hit - t0 < 3600 * 2: c["touched_at_birth(<2h)"] += 1; continue
    c["switched_later"] += 1; ages.append((now - hit) / 86400)
print("population:", len(pop), "sample:", len(smp), dict(c))
if ages:
    last30 = sum(a <= 30 for a in ages)
    share = last30 / len(smp)
    print(f"first touch within last 30 days: {last30}/{len(smp)} -> ~{share*len(pop)/30:.1f} switches/day among surviving long-dated markets")
