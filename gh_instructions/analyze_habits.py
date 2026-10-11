"""Rank the bad habits that CLAUDE.md files write rules against.

Reads data/claude_md.jsonl and rules_out/*.json, checks every quote against its source
file, and prints how many files carry a rule against each habit. Also compares the
line-filter pipeline with full reads of the same files.

Writes data/habit_rules.csv (every verified rule with its repository and link).
"""
import csv, glob, json, os, random, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CAPS = re.compile(r"\b(NEVER|ALWAYS|MUST|DO NOT|DON'T|IMPORTANT|CRITICAL|MANDATORY|FORBIDDEN|STOP|ABSOLUTELY|STRICTLY)\b")
NAMES = {
    "FAKE": "Faking the work (mocks, placeholders, hardcoding)",
    "UNVERIFIED": "Claiming it works without checking",
    "SCOPE": "Doing more than asked",
    "EXTRA_FILES": "Creating files nobody asked for",
    "TEST_GAMING": "Gaming the tests",
    "GIT": "Committing or pushing uninvited",
    "DESTRUCTIVE": "Destructive actions",
    "NO_ASK": "Guessing instead of asking",
    "VERBOSE": "Long-winded output",
    "FLATTERY": "Flattery and automatic agreement",
    "COMMENTS": "Comment noise",
    "IGNORES_CODE": "Ignoring the existing code",
    "SECRETS": "Mishandling secrets",
    "WORKAROUND": "Patching symptoms, not causes",
    "AI_STYLE": "Emojis and AI-flavoured writing",
    "HALLUCINATE": "Inventing APIs or facts",
    "OFF_LIMITS": "Editing off-limits files",
    "RUNS_THINGS": "Running commands it should not",
    "FORGETS": "Losing track of instructions",
    "LAZY": "Stopping short",
    "OTHER": "Other conduct rules",
}


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", re.sub(r"[*_`]", "", s)).strip().lower()


def load_rules(paths, files, stats):
    """(file id, habit) -> list of verified (quote, label)."""
    out = defaultdict(list)
    for path in paths:
        for entry in json.load(open(path)):
            f = files.get(entry.get("file"))
            if not f:
                stats["unknown_file"] += 1
                continue
            for r in entry.get("rules") or []:
                stats["rules"] += 1
                q = norm(r.get("quote") or "")
                if r.get("habit") not in NAMES or len(q) < 10 or q not in f["_norm"]:
                    stats["dropped"] += 1
                    continue
                out[(f["id"], r["habit"])].append((r["quote"], r.get("label") or ""))
    return out


def main():
    files = {}
    for line in open(os.path.join(HERE, "data", "claude_md.jsonl")):
        f = json.loads(line)
        f["id"] = f["sha"]                      # identical texts share one id; "copies" counts the repositories
        if f["id"] in files:
            files[f["id"]]["copies"] += 1
            continue
        f["copies"] = 1
        f["_norm"] = norm(f["text"])
        files[f["id"]] = f
    n = sum(f["copies"] for f in files.values())
    weight = lambda ids: sum(files[i]["copies"] for i in ids)
    stats = Counter()
    rules = load_rules(sorted(glob.glob(os.path.join(HERE, "rules_out", "b*.json"))), files, stats)
    print(f"files={n} distinct texts={len(files)} rules returned={stats['rules']} "
          f"dropped (quote not found or bad code)={stats['dropped']} unknown file ids={stats['unknown_file']}")
    with_rule = {fid for fid, _ in rules}
    print(f"files with at least one conduct rule: {weight(with_rule)} ({100 * weight(with_rule) / n:.0f}%)")
    per_file = Counter(fid for fid, _ in rules)
    print(f"habits covered per file, among those: median {sorted(per_file.values())[len(per_file) // 2]}, "
          f"max {max(per_file.values())}")

    by_habit = defaultdict(set)
    for (fid, habit) in rules:
        by_habit[habit].add(fid)
    rng = random.Random(11)
    print(f"\n{'rank':<5}{'habit':<52}{'files':>6}{'% of all':>10}{'% shouted':>11}")
    ranked = sorted(by_habit, key=lambda h: -weight(by_habit[h]))
    for i, h in enumerate(ranked, 1):
        quotes = [q for (fid, hh), qs in rules.items() if hh == h for q, _ in qs]
        shout = sum(bool(CAPS.search(q)) for q in quotes) / len(quotes)
        print(f"{i:<5}{NAMES[h]:<52}{weight(by_habit[h]):>6}{100 * weight(by_habit[h]) / n:>9.1f}%{100 * shout:>10.0f}%")
    print("\nSAMPLE RULES")
    for h in ranked:
        quotes = sorted({q for (fid, hh), qs in rules.items() if hh == h for q, _ in qs})
        rng.shuffle(quotes)
        print(f"\n## {NAMES[h]}")
        for q in quotes[:5]:
            print("   - " + re.sub(r"\s+", " ", q)[:210])
    labels = Counter(l.lower() for (fid, hh), qs in rules.items() if hh == "OTHER" for _, l in qs if l)
    print("\nOTHER labels:", labels.most_common(40))

    full_path = os.path.join(HERE, "rules_out", "full.json")
    if os.path.exists(full_path):
        ids = set(json.load(open(os.path.join(HERE, "data", "full_read.json")))["full_read_ids"])
        full = set(load_rules([full_path], files, Counter()))
        pipe = {k for k in rules if k[0] in ids}
        full = {k for k in full if k[0] in ids}
        print(f"\nFILTER CHECK on {len(ids)} files read in full: full read found {len(full)} file-habit pairs, "
              f"pipeline found {len(pipe)}, both {len(full & pipe)}")
        if full:
            print(f"  share of full-read findings the pipeline also caught: {100 * len(full & pipe) / len(full):.0f}%")
        print(f"  files with any rule: full read {len({k[0] for k in full})}, pipeline {len({k[0] for k in pipe})}")
        missed = Counter(h for _, h in full - pipe)
        print("  habits missed by the pipeline:", dict(missed.most_common()))

    with open(os.path.join(HERE, "data", "habit_rules.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file_id", "repo", "url", "stars", "repo_created", "habit", "label", "quote"])
        for (fid, habit), qs in sorted(rules.items()):
            f = files[fid]
            for q, label in qs:
                w.writerow([fid, f["repo"], f["html_url"], f["stars"], f["repo_created"], habit, label, q])
    print("\nwrote data/habit_rules.csv")


if __name__ == "__main__":
    main()
