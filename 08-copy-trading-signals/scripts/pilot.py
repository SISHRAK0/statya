import json, urllib.request, time, sys, collections
B="https://data-api.polymarket.com"
def get(u):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"research"}),timeout=30) as r: return json.load(r)
        except Exception as e: time.sleep(1)
    return []
lead=get(B+"/v1/leaderboard?timePeriod=MONTH&orderBy=PNL&limit=40")
W=60; bins=10
same=collections.Counter(); opp=collections.Counter(); nev=0; per_wallet=collections.Counter()
quiet_same=collections.Counter(); nq=0
for L in lead:
    w=L["proxyWallet"].lower()
    acts=get(B+f"/activity?user={w}&type=TRADE&limit=500")
    acts=[a for a in acts if isinstance(a,dict) and a.get("usdcSize",0)>=500]
    seen=set(); k=0
    for a in acts:
        key=(a["asset"],a["timestamp"]//600)
        if key in seen: continue
        seen.add(key); t=a["timestamp"]
        tr=get(B+f"/trades?market={a['conditionId']}&start={t-W*bins}&end={t+W*bins}&limit=10000&takerOnly=true")
        if not isinstance(tr,list): continue
        pre=sum(1 for x in tr if x["timestamp"]<t-60)
        q = pre<=3
        nev+=1; nq+=q
        for x in tr:
            if x["proxyWallet"].lower()==w: continue
            b=(x["timestamp"]-t)//W
            if b< -bins or b>=bins: continue
            v=x["size"]*x["price"]
            s = (x["asset"]==a["asset"] and x["side"]==a["side"]) or (x["asset"]!=a["asset"] and x["side"]!=a["side"])
            (same if s else opp)[b]+=v
            if q and s: quiet_same[b]+=v
        k+=1
        if k>=6: break
    per_wallet[w]=k
print("events",nev,"quiet",nq,"wallets",sum(1 for v in per_wallet.values() if v))
print("bin(min) same_usd opp_usd quiet_same_usd")
for b in range(-bins,bins):
    print(b, round(same[b]), round(opp[b]), round(quiet_same[b]))
