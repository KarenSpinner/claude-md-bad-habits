"""Code CLAUDE.md files against the habits codebook (v2) with the Anthropic API.

Run with the project environment, which holds a current SDK:

  ../.venv/bin/python code_habits.py pilot      a few packs, run directly, to measure token use
  ../.venv/bin/python code_habits.py submit     pack the 10,000-file sample and submit batches
  ../.venv/bin/python code_habits.py collect    wait for the batches, then save the results
  ../.venv/bin/python code_habits.py retry      re-run files that failed, one per request

Several files go in each request. Every answer is tied back to a file id, and the analysis
later drops any rule whose quote is not in that file, so a rule filed under the wrong id
cannot survive.
"""
import json, os, random, re, sys, time

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MODEL = "claude-sonnet-5-5"
CHECK_MODEL = "claude-opus-5-5"              # second coder for the agreement check
EFFORT = {MODEL: "medium", CHECK_MODEL: "medium"}
PRICE = {MODEL: (2.0, 10.0), CHECK_MODEL: (4.0, 20.0)}   # dollars per million tokens; batches cost half
SPEND_CAP = 40.0
PACK_CHARS, PACK_MAX_FILES = 60000, 12
BATCH_REQUESTS = 250
CHECK_N, CHECK_MAX_BYTES = 200, 30000
SEED = 20261006
RUBRIC = open(os.path.join(HERE, "habits_rubric_v2.txt")).read()
CODES = re.findall(r"^  ([A-Z_]{3,})\s", RUBRIC, re.M)
SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["files"],
    "properties": {"files": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["file", "rules"],
        "properties": {"file": {"type": "string"}, "rules": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["habit", "quote", "kind", "label"],
            "properties": {"habit": {"type": "string", "enum": CODES}, "quote": {"type": "string"},
                           "kind": {"type": "string", "enum": ["pointed", "routine"]},
                           "label": {"type": "string"}}}}}}}},
}


def client():
    """The API key comes from the ANTHROPIC_API_KEY environment variable, which the SDK reads itself.

    Set it before running:  export ANTHROPIC_API_KEY=your-key-here
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Run: export ANTHROPIC_API_KEY=your-key-here")
    return anthropic.Anthropic(max_retries=4)


# Fenced blocks tagged with a programming, shell or config language are samples, not conduct
# rules. They are left out of what the coder reads; quotes are still checked against the full file.
CODE_BLOCK = re.compile(
    r"^```[ \t]*(bash|sh|shell|zsh|console|powershell|ps1|cmd|bat|js|javascript|jsx|ts|typescript|tsx|py|python|"
    r"json|jsonc|yaml|yml|toml|ini|env|dotenv|sql|go|rust|rs|java|kotlin|swift|c|cpp|c\+\+|csharp|cs|php|ruby|rb|"
    r"html|css|scss|xml|graphql|proto|dockerfile|docker|makefile|make|hcl|terraform|tf|nginx|diff|lua|r|dart|"
    r"elixir|scala|vue|svelte|mermaid|tree|plaintext)\b[^\n]*\n.*?^```[ \t]*$", re.S | re.M | re.I)


def without_code(texts):
    return {i: CODE_BLOCK.sub("[code block omitted]", t) for i, t in texts.items()}


SAMPLE_N = 10000


def sample_repos():
    """The study sample: 10,000 repositories drawn at random from everything downloaded.

    The download drew 15% extra to cover failures, and almost none failed.
    """
    path = os.path.join(DATA, "c10k_sample.json")
    if os.path.exists(path):
        return set(json.load(open(path)))
    repos = sorted(json.loads(l)["repo"] for l in open(os.path.join(DATA, "c10k_files.jsonl")))
    chosen = sorted(random.Random(SEED).sample(repos, SAMPLE_N))
    json.dump(chosen, open(path, "w"))
    return set(chosen)


def load_texts(name):
    """Distinct texts from a sample file: id (content hash) -> text."""
    keep = sample_repos() if name == "c10k_files.jsonl" else None
    texts = {}
    for line in open(os.path.join(DATA, name)):
        f = json.loads(line)
        if keep is None or f["repo"] in keep:
            texts.setdefault(f["sha"], f["text"])
    return texts


def make_packs(ids, texts):
    packs, cur, size = [], [], 0
    for i in ids:
        n = len(texts[i])
        if cur and (size + n > PACK_CHARS or len(cur) >= PACK_MAX_FILES):
            packs.append(cur)
            cur, size = [], 0
        cur.append(i)
        size += n
    if cur:
        packs.append(cur)
    return packs


def params(model, pack, texts):
    body = "\n\n".join(f"<<<FILE id={i}>>>\n{texts[i]}\n<<<END FILE {i}>>>" for i in pack)
    return dict(
        model=model, max_tokens=16000,
        system=[{"type": "text", "text": RUBRIC, "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": EFFORT[model], "format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content":
                   f"Code each of the following {len(pack)} files. Return one entry per file.\n\n{body}"}])


def read_message(msg, pack):
    """Returns ({file id: rules}, failure reason or None)."""
    if msg.stop_reason == "refusal":
        cat = getattr(getattr(msg, "stop_details", None), "category", None)
        return {}, f"refusal:{cat}"
    if msg.stop_reason == "max_tokens":
        return {}, "max_tokens"
    try:
        data = json.loads(next(b.text for b in msg.content if b.type == "text"))
    except Exception:
        return {}, "unreadable_json"
    got = {e["file"]: e["rules"] for e in data["files"] if e["file"] in pack}
    return got, None


def usage_cost(model, usage, batch):
    inp = usage.input_tokens + (getattr(usage, "cache_creation_input_tokens", 0) or 0) * 1.25 \
        + (getattr(usage, "cache_read_input_tokens", 0) or 0) * 0.1
    return (inp * PRICE[model][0] + usage.output_tokens * PRICE[model][1]) / 1e6 * (0.5 if batch else 1)


def pilot():
    texts = load_texts("claude_md.jsonl")
    ids = json.load(open(os.path.join(DATA, "full_read.json")))["full_read_ids"]
    packs = make_packs(ids, texts)
    c, out = client(), {}
    for effort in ("low", "medium"):
        EFFORT[MODEL] = effort
        tok_in = tok_out = cost = 0
        coded = {}
        for pack in packs:
            msg = c.messages.create(**params(MODEL, pack, texts))
            got, why = read_message(msg, pack)
            if why:
                print(f"  pack failed: {why}")
            coded.update(got)
            u = msg.usage
            tok_in += u.input_tokens + (u.cache_creation_input_tokens or 0) + (u.cache_read_input_tokens or 0)
            tok_out += u.output_tokens
            cost += usage_cost(MODEL, u, batch=False)
        chars = sum(len(texts[i]) for i in ids)
        rules = [(i, r) for i, rs in coded.items() for r in rs]
        found = sum(re.sub(r"\s+", " ", r["quote"]).strip().lower() in re.sub(r"\s+", " ", texts[i]).lower()
                    for i, r in rules)
        out[effort] = {"tokens_in_per_char": (tok_in - len(packs) * 1500) / chars, "tokens_out_per_file": tok_out / len(ids)}
        print(f"effort={effort}: files={len(coded)}/{len(ids)} with rules={sum(1 for v in coded.values() if v)} "
              f"rules={len(rules)} quotes found={found} pointed={sum(r['kind'] == 'pointed' for _, r in rules)} "
              f"| tokens in={tok_in} out={tok_out} | chars per input token={chars / tok_in:.2f} | cost=${cost:.3f}")
        json.dump({i: rs for i, rs in coded.items()}, open(os.path.join(DATA, f"pilot_{effort}.json"), "w"))
    json.dump(out, open(os.path.join(DATA, "pilot_usage.json"), "w"), indent=1)


def submit():
    force = "--force" in sys.argv
    rng = random.Random(SEED)
    texts = without_code(load_texts("c10k_files.jsonl"))
    ids = [i for i in texts if len(texts[i].strip()) >= 80]      # shorter files cannot hold a rule
    rng.shuffle(ids)
    packs = make_packs(ids, texts)
    check_ids = rng.sample([i for i in ids if len(texts[i].encode()) <= CHECK_MAX_BYTES], CHECK_N)
    check_packs = make_packs(check_ids, texts)
    use = json.load(open(os.path.join(DATA, "pilot_usage.json")))[EFFORT[MODEL]]
    print(f"code samples left out: {100 * (1 - sum(map(len, texts.values())) / sum(map(len, load_texts('c10k_files.jsonl').values()))):.0f}% of the text")
    rubric_tokens = 1500

    def project(model, pk, out_per_file):
        chars = sum(len(texts[i]) for p in pk for i in p)
        tin = chars * use["tokens_in_per_char"] + len(pk) * rubric_tokens
        tout = out_per_file * sum(len(p) for p in pk)
        return (tin * PRICE[model][0] + tout * PRICE[model][1]) / 1e6 * 0.5, tin, tout

    main_cost, tin, tout = project(MODEL, packs, use["tokens_out_per_file"])
    check_cost, _, _ = project(CHECK_MODEL, check_packs, use["tokens_out_per_file"] * 2)
    print(f"distinct texts={len(texts)} to code={len(ids)} requests={len(packs)} "
          f"projected tokens in={tin / 1e6:.1f}M out={tout / 1e6:.2f}M")
    print(f"projected cost: main ${main_cost:.2f} + agreement check ${check_cost:.2f} = ${main_cost + check_cost:.2f} "
          f"(cap ${SPEND_CAP:.0f})")
    if main_cost + check_cost > SPEND_CAP and not force:
        print("over the cap: nothing submitted")
        return
    c = client()
    manifest = {"batches": []}
    jobs = [(MODEL, "s", packs[i:i + BATCH_REQUESTS], i) for i in range(0, len(packs), BATCH_REQUESTS)]
    jobs.append((CHECK_MODEL, "o", check_packs, 0))
    for model, prefix, group, base in jobs:
        reqs, index = [], {}
        for k, pack in enumerate(group):
            cid = f"{prefix}-{base + k:05d}"
            index[cid] = pack
            reqs.append(Request(custom_id=cid, params=MessageCreateParamsNonStreaming(**params(model, pack, texts))))
        b = c.messages.batches.create(requests=reqs)
        manifest["batches"].append({"id": b.id, "model": model, "packs": index})
        json.dump(manifest, open(os.path.join(DATA, "c10k_batches.json"), "w"))
        print(f"submitted {b.id} model={model} requests={len(reqs)}", flush=True)


def collect():
    c = client()
    manifest = json.load(open(os.path.join(DATA, "c10k_batches.json")))
    coded, failed, cost = [], [], 0.0
    for b in manifest["batches"]:
        while True:
            st = c.messages.batches.retrieve(b["id"])
            if st.processing_status == "ended":
                break
            print(f"  {b['id']} {st.processing_status} processing={st.request_counts.processing} "
                  f"done={st.request_counts.succeeded}", flush=True)
            time.sleep(90)
        for res in c.messages.batches.results(b["id"]):
            pack = b["packs"][res.custom_id]
            if res.result.type != "succeeded":
                failed += [{"file": i, "coder": b["model"], "why": res.result.type} for i in pack]
                continue
            msg = res.result.message
            cost += usage_cost(b["model"], msg.usage, batch=True)
            got, why = read_message(msg, pack)
            for i in pack:
                if i in got:
                    coded.append({"file": i, "coder": b["model"], "rules": got[i]})
                else:
                    failed.append({"file": i, "coder": b["model"], "why": why or "missing_from_answer"})
        print(f"collected {b['id']} model={b['model']}", flush=True)
    with open(os.path.join(DATA, "c10k_coded.jsonl"), "w") as f:
        for r in coded:
            f.write(json.dumps(r) + "\n")
    json.dump(failed, open(os.path.join(DATA, "c10k_failed.json"), "w"), indent=1)
    why = {}
    for x in failed:
        why[x["why"]] = why.get(x["why"], 0) + 1
    print(f"DONE coded={len(coded)} failed={len(failed)} {why} actual cost=${cost:.2f}")


def retry():
    c = client()
    texts = without_code(load_texts("c10k_files.jsonl"))
    failed = json.load(open(os.path.join(DATA, "c10k_failed.json")))
    still, cost = [], 0.0
    with open(os.path.join(DATA, "c10k_coded.jsonl"), "a") as f:
        for x in failed:
            msg = c.messages.create(**params(x["coder"], [x["file"]], texts))
            cost += usage_cost(x["coder"], msg.usage, batch=False)
            got, why = read_message(msg, [x["file"]])
            if x["file"] in got:
                f.write(json.dumps({"file": x["file"], "coder": x["coder"], "rules": got[x["file"]]}) + "\n")
            else:
                still.append({**x, "why": why or "missing_from_answer"})
    json.dump(still, open(os.path.join(DATA, "c10k_failed.json"), "w"), indent=1)
    print(f"retried={len(failed)} recovered={len(failed) - len(still)} still failed={len(still)} cost=${cost:.2f}")


if __name__ == "__main__":
    {"pilot": pilot, "submit": submit, "collect": collect, "retry": retry}[sys.argv[1]]()
