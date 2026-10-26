"""Snapshot Polymarket reward configs + order books (topic 06, forward data collection).

One run = one snapshot:
  1) /rewards/markets/multi (public, sorted by rate_per_day) -> condition_id,
     tokens, rewards_max_spread (cents), rewards_min_size, rate_per_day,
     market_competitiveness;
  2) /book for the first outcome token of each market;
  3) writes <out>/snap_<UTCts>.jsonl (raw-ish) and prints a bunching summary:
     where resting depth with size >= min_size sits relative to max_spread v.

Run every N minutes from cron to build the panel the paper needs (parameter
history + book state). Usage:
  python3 snapshot_rewards_books.py --out DIR [--pages 2] [--workers 8]
Approximations: the "size-cutoff-adjusted midpoint" is approximated by the best
bid/ask levels whose level size >= rewards_min_size; only the first token's book
is read (complement-side orders may be missing).
"""
import argparse, json, os, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

CLOB = "https://clob.polymarket.com"


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research"}), timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(1.5 * (i + 1))
    return None


def reward_markets(pages):
    out, cur = [], ""
    for _ in range(pages):
        q = urllib.parse.urlencode(dict(order_by="rate_per_day", position="DESC", page_size=500, next_cursor=cur))
        d = get(f"{CLOB}/rewards/markets/multi?{q}")
        if not d:
            break
        out += d["data"]
        cur = d.get("next_cursor", "LTE=")
        if cur == "LTE=":
            break
    return out


def adj_mid(book, mins):
    bids = sorted(((float(x["price"]), float(x["size"])) for x in book.get("bids", [])), reverse=True)
    asks = sorted((float(x["price"]), float(x["size"])) for x in book.get("asks", []))
    bb = next((p for p, s in bids if s >= mins), None)
    ba = next((p for p, s in asks if s >= mins), None)
    if bb is None or ba is None:
        return None, bids, asks
    return (bb + ba) / 2, bids, asks


def one(m):
    tok = m["tokens"][0]["token_id"]
    b = get(f"{CLOB}/book?token_id={tok}")
    return m, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    mk = [m for m in reward_markets(a.pages) if m.get("rewards_config") and m.get("tokens")]
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(one, mk))
    bins = [0.0] * 21  # depth share by d/v in 0.1 bins, last bin = beyond 2.0
    nmk, inside_any, lvl_at_edge = 0, 0, 0
    with open(os.path.join(a.out, f"snap_{ts}.jsonl"), "w") as f:
        for m, b in res:
            f.write(json.dumps(dict(ts=ts, market=m, book=b)) + "\n")
            if not b:
                continue
            v, mins = float(m["rewards_max_spread"]), float(m["rewards_min_size"])
            mid, bids, asks = adj_mid(b, mins)
            if mid is None or not (0.10 <= mid <= 0.90) or v <= 0:
                continue
            nmk += 1
            tot = 0.0
            loc = [0.0] * 21
            for p, s in bids + asks:
                if s < mins:
                    continue
                d = abs(p - mid) * 100 / v
                j = min(int(d / 0.1), 20)
                loc[j] += s
                tot += s
            if tot > 0:
                for j in range(21):
                    bins[j] += loc[j] / tot  # equal weight per market
                inside_any += sum(loc[:10]) > 0
    print(f"snapshot {ts}: {len(mk)} reward markets, {nmk} with adjusted mid in [0.10,0.90]")
    print(f"markets with any qualifying depth inside v: {inside_any}/{nmk}")
    print("avg share of qualifying depth by distance d/v (equal-weighted markets):")
    for j in range(21):
        lab = f"{j/10:.1f}-{(j+1)/10:.1f}" if j < 20 else ">=2.0"
        print(f"  {lab:>8}: {bins[j]/max(nmk,1):6.3f} " + "#" * int(60 * bins[j] / max(nmk, 1)))


if __name__ == "__main__":
    main()
