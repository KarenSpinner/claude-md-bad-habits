"""Cut each CLAUDE.md down to the lines that could be rules, and pack them for the coders.

Most of a CLAUDE.md is project description. This keeps a line when it carries a rule
marker (never, always, must, ask, verify ...) or is a list item under a rule-like heading.
Code blocks are skipped. Each kept line is written with its heading in brackets.

Writes rules_in/bNN/cNN.txt (batches of chunks) and rules_in/full/<id>.txt (full text of a
few files, read separately to measure what the line filter misses).
"""
import json, os, random, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data", "claude_md.jsonl")
OUT = os.path.join(HERE, "rules_in")
SEED = 20261005
CHUNK_CHARS = 55000          # about 14k tokens, under the reader's per-file limit
CHUNKS_PER_BATCH = 5
MAX_LINES_PER_FILE = 80
FULL_READ_N = 24
FULL_READ_MAX_BYTES = 15000

MARK = re.compile(
    r"\b(never|always|must|do not|don'?t|avoid|should|ensure|make sure|prefer|instead of|unless|"
    r"without (asking|permission|approval|being)|ask |confirm|verify|stop |wait for|important|critical|"
    r"mandatory|forbidden|prohibit|required|rule|not allowed|"
    r"no (need|more|new|unnecessary|emoji|comment|mock|placeholder)|remember|careful|assum|guess|claim|"
    r"pretend|mock|placeholder|hack|workaround|shortcut|minimal|concise|brief|verbose|emoji|apolog|honest|"
    r"push back|disagree|only (when|if|after|what)|before (you|commit|push|start|writing|making|claiming|any)|"
    r"after (every|each|any|making))\b", re.I)
HEAD = re.compile(
    r"(rule|guideline|principle|behavio|important|critical|do not|don'?t|never|always|constraint|workflow|"
    r"working|process|communicat|instruction|safety|guardrail|boundar|anti-?pattern|avoid|git|commit|testing|"
    r"expectation|reminder|notes? for|how to work|collaborat|style|convention|practice)", re.I)


def candidate_lines(text):
    head, fence, under, out = "", False, False, []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or len(s) < 12:
            continue
        if s.startswith("#"):
            head = s.lstrip("# ").strip()[:60]
            under = bool(HEAD.search(head))
            continue
        if MARK.search(s) or (under and re.match(r"([-*+]|\d+[.)])\s", s)):
            out.append(f"[{head}] {s[:320]}")
    return out


def main():
    rng = random.Random(SEED)
    # Some repositories hold byte-identical files (shared templates, one-line pointers).
    # Each distinct text is coded once; the analysis counts every repository that carries it.
    everything = [json.loads(l) for l in open(SRC)]
    files = list({f["sha"]: f for f in everything}.values())
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "full"))
    chunks, cur, cur_len, empty, truncated = [], [], 0, 0, 0
    for f in files:
        f["id"] = f["sha"]
        lines = candidate_lines(f["text"])
        if not lines:
            empty += 1
            continue
        if len(lines) > MAX_LINES_PER_FILE:
            truncated += 1
            lines = lines[:MAX_LINES_PER_FILE]
        block = f"=== FILE {f['id']}\n" + "\n".join(lines) + "\n\n"
        if cur_len + len(block) > CHUNK_CHARS and cur:
            chunks.append("".join(cur))
            cur, cur_len = [], 0
        cur.append(block)
        cur_len += len(block)
    if cur:
        chunks.append("".join(cur))
    for i, chunk in enumerate(chunks):
        d = os.path.join(OUT, f"b{i // CHUNKS_PER_BATCH + 1:02d}")
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, f"c{i + 1:02d}.txt"), "w").write(chunk)
    small = [f for f in files if 600 <= f["bytes"] <= FULL_READ_MAX_BYTES]
    full = rng.sample(small, min(FULL_READ_N, len(small)))
    for f in full:
        open(os.path.join(OUT, "full", f"{f['id']}.txt"), "w").write(f"=== FILE {f['id']}\n{f['text']}\n")
    json.dump({"full_read_ids": [f["id"] for f in full]}, open(os.path.join(HERE, "data", "full_read.json"), "w"))
    print(f"repositories={len(everything)} distinct texts={len(files)} "
          f"with candidate lines={len(files) - empty} none={empty} capped={truncated} "
          f"chunks={len(chunks)} batches={-(-len(chunks) // CHUNKS_PER_BATCH)} "
          f"chars={sum(len(c) for c in chunks)} full_read={len(full)}")


if __name__ == "__main__":
    main()
