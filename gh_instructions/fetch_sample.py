"""Pilot sample of AI instruction files on public GitHub.

Four file types, each split into six size bands. The sample follows GitHub's own search
counts, so a band holding 30% of the files gets about 30% of that type's sample. Within a
band, files come from the first search page plus one random later page.

Uses the logged-in gh CLI. Writes data/files.jsonl: one file per line, with its text and
basic facts about the repository.
"""
import concurrent.futures as cf, hashlib, json, math, os, random, re, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SEED = 20261004
TARGET = {"CLAUDE.md": 70, "AGENTS.md": 70, "copilot-instructions.md": 30, ".cursorrules": 30}
SIZES = ["<300", "300..1000", "1000..3000", "3000..8000", "8000..20000", ">20000"]
SPARE = 1.15                      # draw a few extra per band to cover failed downloads


def log(*a):
    print(*a, flush=True)


def gh(args, raw=False):
    for wait in (0, 20, 60):
        time.sleep(wait)
        r = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout if raw else json.loads(r.stdout)
        if "rate limit" not in (r.stderr + r.stdout).lower():
            return None
    return None


def search(q, page):
    time.sleep(6.5)               # code search allows 10 requests a minute
    return gh(["-X", "GET", "search/code", "-f", f"q={q}", "-f", "per_page=100", "-f", f"page={page}"]) or {}


def fetch(c):
    text = gh([c["api_url"], "-H", "Accept: application/vnd.github.raw"], raw=True)
    repo = gh([f"repos/{c['repo']}"])
    if text is None or repo is None:
        return None
    norm = re.sub(r"\s+", " ", text).strip().lower()
    c.update({"text": text, "bytes": len(text.encode()), "sha": hashlib.sha1(norm.encode()).hexdigest()[:12],
              "stars": repo.get("stargazers_count"), "fork": repo.get("fork"),
              "repo_created": (repo.get("created_at") or "")[:10], "repo_pushed": (repo.get("pushed_at") or "")[:10],
              "language": repo.get("language"), "owner_type": (repo.get("owner") or {}).get("type"),
              "repo_size_kb": repo.get("size")})
    return c


def main():
    rng = random.Random(SEED)
    os.makedirs(DATA, exist_ok=True)
    picks, counts = [], {}
    for ftype, target in TARGET.items():
        bands = {}
        for size in SIZES:
            q = f"filename:{ftype} size:{size}"
            first = search(q, 1)
            total = first.get("total_count", 0)
            items = first.get("items", [])
            pages = min(10, math.ceil(total / 100))
            if pages > 1:
                items += search(q, rng.randint(2, pages)).get("items", [])
            seen, pool = set(), []
            for it in items:
                repo = it["repository"]["full_name"]
                if it["name"].lower() == ftype.lower() and repo not in seen:
                    seen.add(repo)
                    pool.append({"type": ftype, "band": size, "repo": repo, "path": it["path"],
                                 "html_url": it["html_url"], "api_url": it["url"]})
            bands[size] = (total, pool)
            counts[f"{ftype} {size}"] = total
            log(f"  {ftype:<24} size {size:<12} github_count={total:<8} candidates={len(pool)}")
        grand = sum(t for t, _ in bands.values()) or 1
        for size, (total, pool) in bands.items():
            n = math.ceil(target * total / grand * SPARE)
            for c in rng.sample(pool, min(n, len(pool))):
                c["band_quota"] = round(target * total / grand, 2)
                picks.append(c)
    log(f"candidates drawn: {len(picks)}")
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        got = [g for g in ex.map(fetch, picks) if g]
    with open(os.path.join(DATA, "files.jsonl"), "w") as f:
        for g in got:
            g.pop("api_url", None)
            f.write(json.dumps(g) + "\n")
    with open(os.path.join(DATA, "github_counts.json"), "w") as f:
        json.dump(counts, f, indent=1)
    by = {}
    for g in got:
        by[g["type"]] = by.get(g["type"], 0) + 1
    log(f"DONE fetched={len(got)}/{len(picks)} by type={by}")


if __name__ == "__main__":
    main()
