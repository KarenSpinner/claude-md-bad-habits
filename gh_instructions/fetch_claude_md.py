"""Sample about 1,000 CLAUDE.md files from public GitHub, one per repository.

Files are split into 22 size bands and drawn in proportion to GitHub's own search counts.
Within a band, results come from randomly chosen search pages. Safe to rerun: the search
step is saved to data/claude_candidates.json and downloads resume where they stopped.

Writes data/claude_md.jsonl (one file per line, with its text and repository facts).
"""
import concurrent.futures as cf, json, math, os, random

from fetch_sample import DATA, fetch, log, search

SEED = 20261005
TARGET = 1000
SPARE = 1.12
EDGES = [150, 300, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000, 8000,
         10000, 12000, 15000, 20000, 30000, 50000]
BANDS = [f"<{EDGES[0]}"] + [f"{a}..{b - 1}" for a, b in zip(EDGES, EDGES[1:])] + [f">={EDGES[-1]}"]
CAND = os.path.join(DATA, "claude_candidates.json")
OUT = os.path.join(DATA, "claude_md.jsonl")


def pool_from(items, seen):
    out = []
    for it in items:
        repo = it["repository"]["full_name"]
        if it["name"].lower() == "claude.md" and repo not in seen:
            seen.add(repo)
            out.append({"type": "CLAUDE.md", "repo": repo, "path": it["path"],
                        "html_url": it["html_url"], "api_url": it["url"]})
    return out


def find_candidates(rng):
    first, seen = {}, set()
    for band in BANDS:
        d = search(f"filename:CLAUDE.md size:{band}", 1)
        first[band] = (d.get("total_count", 0), d.get("items", []))
    grand = sum(t for t, _ in first.values()) or 1
    picks, counts = [], {}
    for band, (total, items) in first.items():
        want = math.ceil(TARGET * total / grand * SPARE)
        pool = pool_from(items, seen)
        pages = list(range(2, min(10, math.ceil(total / 100)) + 1))
        rng.shuffle(pages)
        while len(pool) < want * 2 and pages:      # draw from more than one page, so not just the top hits
            pool += pool_from(search(f"filename:CLAUDE.md size:{band}", pages.pop()).get("items", []), seen)
        chosen = rng.sample(pool, min(want, len(pool)))
        for c in chosen:
            c["band"] = band
        picks += chosen
        counts[band] = total
        log(f"  size {band:<14} github_count={total:<8} wanted={want:<4} drawn={len(chosen)}")
    json.dump({"counts": counts, "picks": picks}, open(CAND, "w"))
    return picks


def main():
    rng = random.Random(SEED)
    os.makedirs(DATA, exist_ok=True)
    picks = json.load(open(CAND))["picks"] if os.path.exists(CAND) else find_candidates(rng)
    done = set()
    if os.path.exists(OUT):
        done = {json.loads(l)["repo"] for l in open(OUT)}
    todo = [p for p in picks if p["repo"] not in done]
    log(f"candidates={len(picks)} already downloaded={len(done)} to download={len(todo)}")
    n = 0
    with open(OUT, "a") as f, cf.ThreadPoolExecutor(max_workers=4) as ex:
        for g in ex.map(fetch, todo):
            if g:
                g.pop("api_url", None)
                f.write(json.dumps(g) + "\n")
                f.flush()
                n += 1
                if n % 200 == 0:
                    log(f"  downloaded {n}")
    log(f"DONE files={len(done) + n} of {len(picks)} candidates")


if __name__ == "__main__":
    main()
