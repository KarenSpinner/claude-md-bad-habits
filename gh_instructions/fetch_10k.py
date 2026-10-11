"""Sample about 10,000 CLAUDE.md files from public GitHub, one per repository.

GitHub's search returns at most 1,000 results per query, so files are split into about
150 size bands (cut at the size quantiles of the 1,000-file sample) and each band is drawn
from randomly chosen result pages, in proportion to GitHub's own count for that band.

Safe to rerun: the search step is saved, and downloads resume where they stopped.

  python3 fetch_10k.py --smoke    3 bands, 30 files, to check the plumbing
  python3 fetch_10k.py            the full sample

Writes data/c10k_files.jsonl (text per file) and data/c10k_meta.json (repository facts).
"""
import concurrent.futures as cf, hashlib, json, math, os, random, re, subprocess, sys, time
import urllib.error, urllib.request

from fetch_sample import DATA, gh, log, search

SEED = 20261006
SMOKE = "--smoke" in sys.argv
TARGET = 30 if SMOKE else 10000
SPARE = 1.15
N_BANDS = 150
TAG = "smoke" if SMOKE else "c10k"
CAND = os.path.join(DATA, f"{TAG}_candidates.json")
OUT = os.path.join(DATA, f"{TAG}_files.jsonl")
META = os.path.join(DATA, f"{TAG}_meta.json")
TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()


def bands():
    sizes = sorted(json.loads(l)["bytes"] for l in open(os.path.join(DATA, "claude_md.jsonl")))
    edges = sorted({sizes[int(len(sizes) * i / N_BANDS)] for i in range(1, N_BANDS)} - {0})
    out = [f"<{edges[0]}"] + [f"{a}..{b - 1}" for a, b in zip(edges, edges[1:])] + [f">={edges[-1]}"]
    return out[40:43] if SMOKE else out


def pool_from(items, seen):
    out = []
    for it in items:
        repo = it["repository"]["full_name"]
        if it["name"].lower() == "claude.md" and repo not in seen:
            seen.add(repo)
            out.append({"repo": repo, "path": it["path"], "html_url": it["html_url"]})
    return out


def find_candidates(rng):
    seen, state = set(), {}
    for band in bands():
        q = f"filename:CLAUDE.md size:{band}"
        page = rng.randint(1, 10)
        d = search(q, page)
        if not d.get("items") and d.get("total_count"):
            page = 1
            d = search(q, 1)
        state[band] = {"total": d.get("total_count", 0), "pool": pool_from(d.get("items", []), seen), "used": {page}}
    grand = sum(s["total"] for s in state.values()) or 1
    picks = []
    for band, s in state.items():
        want = math.ceil(TARGET * s["total"] / grand * SPARE)
        pages = [p for p in range(1, min(10, math.ceil(s["total"] / 100)) + 1) if p not in s["used"]]
        rng.shuffle(pages)
        while len(s["pool"]) < want and pages:
            s["pool"] += pool_from(search(f"filename:CLAUDE.md size:{band}", pages.pop()).get("items", []), seen)
        chosen = rng.sample(s["pool"], min(want, len(s["pool"])))
        for c in chosen:
            c["band"] = band
        picks += chosen
        log(f"  size {band:<14} github_count={s['total']:<7} wanted={want:<4} drawn={len(chosen)}")
    json.dump({"counts": {b: s["total"] for b, s in state.items()}, "picks": picks}, open(CAND, "w"))
    return picks


def download(c):
    url = c["html_url"].replace("https://github.com/", "https://raw.githubusercontent.com/", 1).replace("/blob/", "/", 1)
    req = urllib.request.Request(url, headers={"Authorization": f"token {TOKEN}", "User-Agent": "claude-md-study"})
    for wait in (0, 10, 40, 120):
        time.sleep(wait)
        try:
            text = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")
            norm = re.sub(r"\s+", " ", text).strip().lower()
            return {**c, "text": text, "bytes": len(text.encode()), "sha": hashlib.sha1(norm.encode()).hexdigest()[:12]}
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503):
                return None
        except Exception:
            continue
    return None


def repo_facts(repos):
    """Stars, age and owner for many repositories per request, through GitHub's GraphQL API."""
    facts = json.load(open(META)) if os.path.exists(META) else {}
    todo = [r for r in repos if r not in facts]
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        parts = []
        for j, full in enumerate(chunk):
            owner, name = full.split("/", 1)
            parts.append(f'r{j}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) '
                         "{ stargazerCount createdAt pushedAt isFork diskUsage primaryLanguage { name } owner { __typename } }")
        r = subprocess.run(["gh", "api", "graphql", "-f", "query=query { " + " ".join(parts) + " }"],
                           capture_output=True, text=True)
        try:
            data = json.loads(r.stdout).get("data") or {}
        except Exception:
            data = {}
        for j, full in enumerate(chunk):
            d = data.get(f"r{j}")
            facts[full] = None if not d else {
                "stars": d["stargazerCount"], "repo_created": d["createdAt"][:10], "repo_pushed": (d["pushedAt"] or "")[:10],
                "fork": d["isFork"], "repo_size_kb": d["diskUsage"],
                "language": (d["primaryLanguage"] or {}).get("name"), "owner_type": d["owner"]["__typename"]}
        json.dump(facts, open(META, "w"))
        if (i // 50) % 40 == 0:
            log(f"  repository facts {min(i + 50, len(todo))}/{len(todo)}")
        time.sleep(0.4)
    return facts


def main():
    rng = random.Random(SEED)
    picks = json.load(open(CAND))["picks"] if os.path.exists(CAND) else find_candidates(rng)
    done = {json.loads(l)["repo"] for l in open(OUT)} if os.path.exists(OUT) else set()
    todo = [p for p in picks if p["repo"] not in done]
    log(f"candidates={len(picks)} already downloaded={len(done)} to download={len(todo)}")
    n = 0
    with open(OUT, "a") as f, cf.ThreadPoolExecutor(max_workers=8) as ex:
        for g in ex.map(download, todo):
            if g:
                f.write(json.dumps(g) + "\n")
                f.flush()
                n += 1
                if n % 1000 == 0:
                    log(f"  downloaded {n}")
    repos = [json.loads(l)["repo"] for l in open(OUT)]
    facts = repo_facts(repos)
    log(f"DONE files={len(repos)} of {len(picks)} candidates; repository facts for "
        f"{sum(1 for r in repos if facts.get(r))}")


if __name__ == "__main__":
    main()
