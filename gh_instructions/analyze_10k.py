"""Rank the bad habits that CLAUDE.md files write rules against (10,000-file sample).

Reads data/c10k_files.jsonl, data/c10k_meta.json and data/c10k_coded.jsonl. Every quote is
checked against its source file and dropped if it is not there. Counts are per repository:
when several repositories hold the same text, each one counts.

Writes data/c10k_rules.csv (every verified rule with its repository and link).
"""
import csv, json, math, os, random, re
from collections import Counter, defaultdict

from code_habits import CHECK_MODEL, CODE_BLOCK, MODEL, sample_repos

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CAPS = re.compile(r"\b(NEVER|ALWAYS|MUST|DO NOT|DON'T|IMPORTANT|CRITICAL|MANDATORY|FORBIDDEN|STOP|ABSOLUTELY|STRICTLY)\b")
NAMES = {
    "UNVERIFIED": "Not checking its own work", "FAKE": "Faking the work", "TEST_GAMING": "Gaming the tests",
    "LAZY": "Stopping short", "WORKAROUND": "Patching symptoms, not causes", "HALLUCINATE": "Inventing APIs or facts",
    "SCOPE": "Doing more than asked", "EXTRA_FILES": "Creating files nobody asked for",
    "IGNORES_CODE": "Ignoring the existing code", "OFF_LIMITS": "Touching off-limits files",
    "NO_ASK": "Guessing instead of asking", "OVER_ASKS": "Asking too much", "GIT": "Committing or pushing uninvited",
    "UNCOMMITTED": "Leaving work uncommitted", "ATTRIBUTION": "Signing its work (AI attribution)",
    "DESTRUCTIVE": "Destructive actions", "RUNS_THINGS": "Running commands it should not",
    "SECRETS": "Mishandling secrets", "STALE_DOCS": "Letting documentation go stale",
    "DRIFT": "Drifting from instructions", "WASTEFUL": "Working wastefully", "VERBOSE": "Long-winded output",
    "FLATTERY": "Flattery and automatic agreement", "COMMENTS": "Comment noise",
    "AI_STYLE": "Emojis and AI-flavoured writing", "OTHER": "Other conduct rules",
}


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def ci(k, n):
    """95% Wilson interval, in percentage points."""
    if not n:
        return (0, 0)
    p, z = k / n, 1.96
    mid = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (100 * (mid - half), 100 * (mid + half))


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None
    agree = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (agree - pe) / (1 - pe) if pe < 1 else None


def main():
    meta = json.load(open(os.path.join(DATA, "c10k_meta.json")))
    texts, raw, repos = {}, {}, defaultdict(list)
    keep = sample_repos()
    for line in open(os.path.join(DATA, "c10k_files.jsonl")):
        f = json.loads(line)
        if f["repo"] not in keep:
            continue
        texts.setdefault(f["sha"], norm(f["text"]))
        raw.setdefault(f["sha"], f["text"])
        repos[f["sha"]].append({"repo": f["repo"], "url": f["html_url"], "bytes": f["bytes"], **(meta.get(f["repo"]) or {})})
    coded = {MODEL: {}, CHECK_MODEL: {}}
    dropped = total = 0
    for line in open(os.path.join(DATA, "c10k_coded.jsonl")):
        e = json.loads(line)
        good = []
        for r in e["rules"]:
            total += e["coder"] == MODEL
            q = norm(r["quote"])
            if len(q) >= 10 and q in texts[e["file"]]:
                good.append(r)
            else:
                dropped += e["coder"] == MODEL
        coded[e["coder"]][e["file"]] = good
    main_coded = coded[MODEL]
    # the same rule the coding step used: under 80 characters once code samples are left out
    tiny = [s for s in texts if s not in main_coded and len(CODE_BLOCK.sub("[code block omitted]", raw[s]).strip()) < 80]
    for s in tiny:
        main_coded[s] = []
    w = lambda shas: sum(len(repos[s]) for s in shas)
    n = w(main_coded)
    print(f"repositories downloaded={w(texts)} distinct texts={len(texts)} coded={n} "
          f"(of which too short to hold a rule={w(tiny)}) not coded={w(texts) - n}")
    print(f"rules returned={total} dropped (quote not in file)={dropped} ({100 * dropped / max(1, total):.1f}%)")

    has = lambda pred: {s for s, rs in main_coded.items() if any(pred(r) for r in rs)}
    any_rule, any_pointed = has(lambda r: True), has(lambda r: r["kind"] == "pointed")
    print(f"files with any conduct rule: {w(any_rule)} ({100 * w(any_rule) / n:.1f}%) | "
          f"with a pointed rule: {w(any_pointed)} ({100 * w(any_pointed) / n:.1f}%)")
    per = sorted(len({r["habit"] for r in rs}) for rs in main_coded.values() if rs)
    print(f"habits covered per file, among those: median {per[len(per) // 2]}, 90th percentile {per[int(.9 * len(per))]}, max {per[-1]}")

    print(f"\n{'rank':<5}{'habit':<36}{'files':>6}{'share':>8}{'95% range':>15}{'pointed files':>15}{'pointed':>9}{'shouted':>9}")
    rows = []
    for h in NAMES:
        files = has(lambda r, h=h: r["habit"] == h)
        pointed = has(lambda r, h=h: r["habit"] == h and r["kind"] == "pointed")
        quotes = [r["quote"] for rs in main_coded.values() for r in rs if r["habit"] == h]
        rows.append((h, w(files), w(pointed), sum(bool(CAPS.search(q)) for q in quotes) / max(1, len(quotes))))
    rows.sort(key=lambda r: -r[1])
    for i, (h, k, kp, shout) in enumerate(rows, 1):
        lo, hi = ci(k, n)
        print(f"{i:<5}{NAMES[h]:<36}{k:>6}{100 * k / n:>7.1f}%{f'{lo:.1f}-{hi:.1f}%':>15}{kp:>15}{100 * kp / n:>8.1f}%{100 * shout:>8.0f}%")

    print(f"\nPOINTED RULES ONLY\n{'rank':<5}{'habit':<36}{'files':>6}{'share':>8}{'95% range':>15}")
    for i, (h, k, kp, _) in enumerate(sorted(rows, key=lambda r: -r[2]), 1):
        lo, hi = ci(kp, n)
        print(f"{i:<5}{NAMES[h]:<36}{kp:>6}{100 * kp / n:>7.1f}%{f'{lo:.1f}-{hi:.1f}%':>15}")

    recs = [(s, r) for s in main_coded for r in repos[s]]       # one record per repository

    def cut(title, groups):
        print(f"\n{title}")
        for name, keep in groups:
            g = [(s, r) for s, r in recs if keep(s, r)]
            if g:
                top = Counter(h for s, _ in g for h in {x["habit"] for x in main_coded[s]})
                print(f"  {name:<22} n={len(g):<6} any rule {100 * sum(s in any_rule for s, _ in g) / len(g):5.1f}%  pointed "
                      f"{100 * sum(s in any_pointed for s, _ in g) / len(g):5.1f}%  top: "
                      + ", ".join(f"{h} {100 * c / len(g):.0f}%" for h, c in top.most_common(4)))

    stars = lambda r: r.get("stars") or 0
    year = lambda r: (r.get("repo_created") or "0000")[:4]
    cut("BY STARS", [("1,000+ stars", lambda s, r: stars(r) >= 1000), ("100-999 stars", lambda s, r: 100 <= stars(r) < 1000),
                     ("10-99 stars", lambda s, r: 10 <= stars(r) < 100), ("1-9 stars", lambda s, r: 1 <= stars(r) < 10),
                     ("no stars", lambda s, r: stars(r) == 0)])
    cut("BY YEAR THE REPOSITORY WAS CREATED", [("2024 or earlier", lambda s, r: "0000" < year(r) <= "2024"),
                                               ("2025", lambda s, r: year(r) == "2025"), ("2026", lambda s, r: year(r) == "2026")])
    cut("BY OWNER", [("individual", lambda s, r: r.get("owner_type") == "User"),
                     ("organisation", lambda s, r: r.get("owner_type") == "Organization")])
    cut("BY FILE SIZE", [("under 1 KB", lambda s, r: r["bytes"] < 1000), ("1-5 KB", lambda s, r: 1000 <= r["bytes"] < 5000),
                         ("5-20 KB", lambda s, r: 5000 <= r["bytes"] < 20000), ("20 KB and over", lambda s, r: r["bytes"] >= 20000)])
    first = {s: repos[s][0] for s in main_coded}

    pair = lambda a, b: (w(has(lambda r: r["habit"] == a)), w(has(lambda r: r["habit"] == b)),
                         w(has(lambda r: r["habit"] == a) & has(lambda r: r["habit"] == b)))
    print("\nOPPOSITE DEMANDS (files with A, files with B, files with both)")
    print("  ask first vs asks too much:", pair("NO_ASK", "OVER_ASKS"))
    print("  commits uninvited vs leaves work uncommitted:", pair("GIT", "UNCOMMITTED"))

    by_quote = defaultdict(set)
    for s, rs in main_coded.items():
        for r in rs:
            by_quote[norm(r["quote"])].add(s)
    repeated = {q: ss for q, ss in by_quote.items() if w(ss) >= 3}
    inst = [(s, r) for s, rs in main_coded.items() for r in rs]
    is_rep = lambda r: norm(r["quote"]) in repeated
    all_rep = {s for s in any_rule if all(is_rep(r) for r in main_coded[s])}
    print(f"\nBOILERPLATE: {len(repeated)} quotes appear word for word in 3 or more repositories; they are "
          f"{100 * sum(len(repos[s]) for s, r in inst if is_rep(r)) / sum(len(repos[s]) for s, r in inst):.0f}% of all rule instances; "
          f"{w(all_rep)} rule-bearing files ({100 * w(all_rep) / w(any_rule):.0f}%) contain nothing but such lines")
    other_script = re.compile(r"[\u0400-\u04FF\u0E00-\u0E7F\u3040-\u30FF\u3400-\u9FFF\uAC00-\uD7AF\u0600-\u06FF\u0590-\u05FF]")
    non_latin = has(lambda r: bool(other_script.search(r["quote"])))
    print(f"files with a rule written in a non-Latin script: {w(non_latin)} ({100 * w(non_latin) / w(any_rule):.0f}% of rule-bearing files)")
    for q, ss in sorted(repeated.items(), key=lambda kv: -w(kv[1]))[:12]:
        print(f"  x{w(ss):<4} {q[:150]}")

    rng = random.Random(7)
    print("\nSAMPLE POINTED RULES")
    for h, k, kp, _ in rows:
        qs = sorted({r["quote"] for rs in main_coded.values() for r in rs if r["habit"] == h and r["kind"] == "pointed"})
        rng.shuffle(qs)
        print(f"\n## {NAMES[h]} ({len(qs)} distinct pointed rules)")
        for q in qs[:7]:
            print("   - " + re.sub(r"\s+", " ", q)[:220])
    labels = Counter(r["label"].lower() for rs in main_coded.values() for r in rs if r["habit"] == "OTHER" and r["label"])
    print("\nOTHER labels:", labels.most_common(45))

    check = coded[CHECK_MODEL]
    both = [s for s in check if s in main_coded]
    if both:
        hs = lambda d, s: {r["habit"] for r in d[s]}
        a_pairs = {(s, h) for s in both for h in hs(main_coded, s)}
        b_pairs = {(s, h) for s in both for h in hs(check, s)}
        print(f"\nTWO-CODER CHECK on {len(both)} files ({MODEL} vs {CHECK_MODEL})")
        print(f"  file has any rule: agree {100 * sum(bool(main_coded[s]) == bool(check[s]) for s in both) / len(both):.0f}%, "
              f"kappa {kappa([(bool(main_coded[s]), bool(check[s])) for s in both]):.2f} "
              f"({MODEL} {sum(bool(main_coded[s]) for s in both)}, {CHECK_MODEL} {sum(bool(check[s]) for s in both)})")
        print(f"  file-habit pairs: {MODEL} {len(a_pairs)}, {CHECK_MODEL} {len(b_pairs)}, both {len(a_pairs & b_pairs)} "
              f"(overlap {100 * len(a_pairs & b_pairs) / max(1, len(a_pairs | b_pairs)):.0f}%)")
        pt = lambda d, s, h: any(r["kind"] == "pointed" for r in d[s] if r["habit"] == h)
        shared = a_pairs & b_pairs
        print(f"  pointed or routine, on the {len(shared)} shared pairs: agree "
              f"{100 * sum(pt(main_coded, s, h) == pt(check, s, h) for s, h in shared) / max(1, len(shared)):.0f}%, "
              f"kappa {kappa([(pt(main_coded, s, h), pt(check, s, h)) for s, h in shared]):.2f}")
        print(f"  file has any pointed rule: kappa "
              f"{kappa([(any(r['kind'] == 'pointed' for r in main_coded[s]), any(r['kind'] == 'pointed' for r in check[s])) for s in both]):.2f}")
        for h in [r[0] for r in rows[:12]]:
            k = kappa([(h in hs(main_coded, s), h in hs(check, s)) for s in both])
            print(f"    {NAMES[h]:<36} kappa {k:.2f}  ({sum(h in hs(main_coded, s) for s in both)} vs {sum(h in hs(check, s) for s in both)})"
                  if k is not None else f"    {NAMES[h]:<36} not present")

    with open(os.path.join(DATA, "c10k_rules.csv"), "w", newline="") as fh:
        out = csv.writer(fh)
        out.writerow(["file_id", "repo", "url", "stars", "repo_created", "copies", "habit", "kind", "label", "quote"])
        for s, rs in sorted(main_coded.items()):
            for r in rs:
                f = first[s]
                out.writerow([s, f["repo"], f["url"], f.get("stars"), f.get("repo_created"), len(repos[s]),
                              r["habit"], r["kind"], r["label"], r["quote"]])
    print("\nwrote data/c10k_rules.csv")


if __name__ == "__main__":
    main()
