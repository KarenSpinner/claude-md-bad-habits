# claude-md-bad-habits

What do developers tell their AI coding agent not to do? A CLAUDE.md file is the set of standing instructions a developer leaves in a code repository for Claude Code. This study reads 10,000 of them from public GitHub, finds every rule about the agent's own conduct, and ranks the bad habits those rules guard against.

This repository has the sampling scripts, the coding rubric, every verified rule with a link to the exact file version it came from, the analysis script and its full output, and the run logs.

## What the study found

1. **Half of CLAUDE.md files contain at least one rule about how the agent should behave.** 4,781 of 10,000 files (47.9%) have a conduct rule. 3,302 (33.1%) have a pointed one, which means a rule that answers a misstep agents make and would be odd to write for a human teammate.
2. **The most common rule is "check your own work."** 1,921 files (19.2%) tell the agent to run the tests or the build, or not to say it is done without evidence.
3. **Among pointed rules, guessing instead of asking comes first.** 803 files (8.0%) have a pointed rule against it, just ahead of inventing APIs or facts (768) and not checking its own work (764).
4. **Longer files have more rules.** 20% of files under 1 KB contain a conduct rule. 75% of files of 20 KB or more do.
5. **Newer repositories write more rules.** 35% of repositories created in 2024 or earlier have a conduct rule, 41% of those created in 2025, and 53% of those created in 2026.
6. **Popular repositories write fewer.** 24% of repositories with 1,000 or more stars have a conduct rule. 50% of repositories with no stars do.
7. **Files ask for opposite things, and 95 ask for both.** 1,308 files tell the agent to ask before acting and 229 tell it to stop asking and proceed. 805 tell it never to commit uninvited and 170 tell it to commit and push every change, and 44 files say both.
8. **Some of it is boilerplate.** 156 rules appear word for word in three or more repositories. They are 7% of all rule instances, and 139 rule-bearing files (3%) contain nothing else.
9. **One rule-bearing file in ten has a rule in a non-Latin script.** The coder quoted every rule in its own language. The sample rules in the analysis output include Chinese, Japanese, Korean, Thai, Russian, Vietnamese, Turkish, Portuguese, Spanish, French, Dutch and Danish.

Files with at least one rule against each habit, out of 10,000. The 95% range is a Wilson interval. A pointed file has at least one pointed rule for that habit.

| Habit the rule guards against | Files | Share | 95% range | Pointed files | Pointed share |
|---|---|---|---|---|---|
| Not checking its own work | 1,921 | 19.2% | 18.5 to 20.0 | 764 | 7.6% |
| Guessing instead of asking | 1,308 | 13.1% | 12.4 to 13.8 | 803 | 8.0% |
| Doing more than asked | 1,140 | 11.4% | 10.8 to 12.1 | 649 | 6.5% |
| Letting documentation go stale | 1,107 | 11.1% | 10.5 to 11.7 | 87 | 0.9% |
| Ignoring the existing code | 1,095 | 11.0% | 10.4 to 11.6 | 273 | 2.7% |
| Inventing APIs or facts | 925 | 9.3% | 8.7 to 9.8 | 768 | 7.7% |
| Committing or pushing uninvited | 805 | 8.1% | 7.5 to 8.6 | 239 | 2.4% |
| Mishandling secrets | 639 | 6.4% | 5.9 to 6.9 | 31 | 0.3% |
| Touching off-limits files | 568 | 5.7% | 5.2 to 6.2 | 218 | 2.2% |
| Patching symptoms, not causes | 494 | 4.9% | 4.5 to 5.4 | 325 | 3.3% |
| Gaming the tests | 396 | 4.0% | 3.6 to 4.4 | 270 | 2.7% |
| Drifting from instructions | 390 | 3.9% | 3.5 to 4.3 | 291 | 2.9% |
| Destructive actions | 371 | 3.7% | 3.4 to 4.1 | 140 | 1.4% |
| Long-winded output | 359 | 3.6% | 3.2 to 4.0 | 180 | 1.8% |
| Running commands it should not | 347 | 3.5% | 3.1 to 3.9 | 238 | 2.4% |
| Comment noise | 322 | 3.2% | 2.9 to 3.6 | 168 | 1.7% |
| Signing its work (AI attribution) | 311 | 3.1% | 2.8 to 3.5 | 204 | 2.0% |
| Working wastefully | 303 | 3.0% | 2.7 to 3.4 | 232 | 2.3% |
| Creating files nobody asked for | 237 | 2.4% | 2.1 to 2.7 | 148 | 1.5% |
| Other conduct rules | 231 | 2.3% | 2.0 to 2.6 | 161 | 1.6% |
| Asking too much | 229 | 2.3% | 2.0 to 2.6 | 195 | 2.0% |
| Flattery and automatic agreement | 209 | 2.1% | 1.8 to 2.4 | 204 | 2.0% |
| Faking the work | 198 | 2.0% | 1.7 to 2.3 | 156 | 1.6% |
| Stopping short | 170 | 1.7% | 1.5 to 2.0 | 121 | 1.2% |
| Leaving work uncommitted | 170 | 1.7% | 1.5 to 2.0 | 47 | 0.5% |
| Emojis and AI-flavoured writing | 170 | 1.7% | 1.5 to 2.0 | 112 | 1.1% |

Among files with any rule, the median file covers 2 habits, the 90th percentile covers 6, and the most covers 15.

The analysis output also records how often each habit's rules are shouted, meaning the quote contains an all-caps word such as NEVER, ALWAYS, MUST or IMPORTANT. Most habits are shouted in 2% to 10% of their rules. Two stand out. Rules against leaving work uncommitted are shouted 19% of the time, and rules against creating files nobody asked for 18% of the time.

Share of files with a conduct rule, by repository and file facts:

| Cut | n | Any rule | Pointed rule |
|---|---|---|---|
| File under 1 KB | 1,743 | 20.4% | 11.8% |
| File 1 to 5 KB | 3,908 | 43.7% | 27.6% |
| File 5 to 20 KB | 3,606 | 60.2% | 44.2% |
| File 20 KB and over | 732 | 74.6% | 57.8% |
| Repository created 2024 or earlier | 1,410 | 34.8% | 21.1% |
| Repository created 2025 | 2,051 | 40.6% | 26.0% |
| Repository created 2026 | 6,527 | 53.0% | 37.8% |
| 1,000 or more stars | 76 | 23.7% | 14.5% |
| 100 to 999 stars | 308 | 41.9% | 28.6% |
| 10 to 99 stars | 1,030 | 41.7% | 26.3% |
| 1 to 9 stars | 2,615 | 47.8% | 31.0% |
| No stars | 5,960 | 49.6% | 35.6% |
| Owned by an individual | 8,247 | 48.7% | 33.9% |
| Owned by an organisation | 1,741 | 43.9% | 28.9% |

The full output, including seven sample pointed rules for every habit and the list of most-repeated boilerplate lines, is in `gh_instructions/analysis_10k.txt`.

## How the sample was drawn

The population is every file named CLAUDE.md that GitHub code search can see in a public repository. On 2026-10-04, GitHub's search counts for four kinds of agent instruction file were about 870,000 for CLAUDE.md, 1,040,000 for AGENTS.md, 161,000 for copilot-instructions.md, and 33,000 for .cursorrules. These counts are GitHub's own estimates and move daily. The study covers CLAUDE.md only.

GitHub code search returns at most 1,000 results for any one query, so a plain search cannot reach a random sample of 870,000 files. The sampling script, `gh_instructions/fetch_10k.py`, gets around the limit by size.

1. A first sample of about 1,000 files (`fetch_claude_md.py`, 1,129 files downloaded) sets 150 size bands, cut at the size quantiles of that sample, so each band holds a similar number of files.
2. For each band, the script queries `filename:CLAUDE.md size:<band>`, reads GitHub's count for that band, and draws candidates from randomly chosen result pages in proportion to that count. Summed over the bands, GitHub reported 843,430 files when the sample was drawn.
3. One file per repository. The script keeps the first CLAUDE.md it sees for a repository and skips any others.
4. It drew 15% more candidates than needed to cover download failures, which were rare. 11,571 candidates, 11,519 downloaded, and 10,000 of those chosen at random with a fixed seed. The 10,000 repository names are in `data/c10k_sample.json`.
5. GraphQL queries, 50 repositories at a time, record each repository's stars, creation date, last push, fork status, size, primary language, and whether the owner is a person or an organisation.

The files were downloaded on 2026-10-05. The sampled files have a median size of 4.2 KB and a mean of 7.8 KB. One in ten is over 16.6 KB, and the largest is 357 KB.

Identical files are common, because templates get copied and some repositories have a one-line CLAUDE.md that points elsewhere. The 10,000 repositories hold 9,354 distinct texts. Each distinct text was coded once, and every count in this study is per repository, so a template that appears in four repositories counts four times.

## How the files were coded

A language model read every file against a written rubric and returned, for each file, the list of conduct rules it found. The rubric is `gh_instructions/habits_rubric_v2.txt` and the script is `code_habits.py`.

The rubric asks the coder to count a line only if it tells the agent how to behave, decide or communicate in a way that would make sense in almost any project. Project facts and conventions do not count, even when they say "never" or "always," so "Always use pnpm, never npm" and "Never use default exports" are left out while "Never commit unless I ask you to" is counted. When a line could be either, the rubric says not to count it.

For each rule the coder records three things.

- **The habit it guards against**, one of 25 codes plus OTHER. The codes and their definitions are in the rubric. OTHER takes a short label, and the labels are listed at the end of the analysis output.
- **A verbatim quote** of 15 to 240 characters, copied from one line of the file. At most two rules per habit per file.
- **Pointed or routine.** A pointed rule's wording answers a misstep an agent makes, or would be odd to write for a human teammate ("Never say done without evidence," "Don't guess, ask"). A routine rule would read naturally in a contributor guide for people ("Run the test suite before committing," "Never commit secrets"). When unsure, the coder is told to choose routine.

The rubric also tells the coder that the files are data, that they are addressed to an AI agent, and not to follow anything written in them.

Mechanics of the run:

- The coder was Claude Sonnet 5.5 at medium effort, through the Message Batches API, with the rubric as a cached system prompt and a JSON schema on the output.
- Fenced code blocks tagged with a programming, shell or config language were removed before coding, since they are samples rather than conduct rules. They were 7% of the text. Files with under 80 characters left after that were not sent, which excluded 630 repositories as too short to hold a rule.
- Files were shuffled and packed up to 12 per request, under 60,000 characters per request. 1,247 requests went out in five batches, with a sixth batch of 22 requests for the agreement check below.
- The coder refused 88 files on the first pass, all flagged as cyber-related content. A retry, one file per request, recovered all but 10. With the 630 short files counted as having no rules, 9,989 of the 10,000 repositories are in the counts.
- The main run and the agreement check cost $36.28 in batch API charges. A token-use pilot on 24 files at two effort settings (`data/pilot_*.json`) set the cost projection first.

## Checks

**Every quote was verified against its source file.** The analysis normalises quotes and curly punctuation, then drops any rule whose quote does not appear in the file it was filed under. The coder returned 15,344 rules and 102 (0.7%) were dropped. A rule filed under the wrong file id cannot survive this check.

**A second model coded 200 of the files.** Claude Opus 5.5 coded a random 200 files from the sample, drawn from files of 30 KB or less, and the analysis compares the two codings.

| Agreement on 200 files | Result |
|---|---|
| File has any conduct rule | 90% agree, kappa 0.79 |
| File has any pointed rule | kappa 0.80 |
| File-habit pairs found | Sonnet 302, Opus 349, both 243 (60% overlap) |
| Pointed or routine, on the 243 shared pairs | 80% agree, kappa 0.60 |

Per-habit kappa on whether a file has a rule against that habit ranges from 0.90 for guessing instead of asking down to 0.35 for drifting from instructions. Values for the twelve most common habits are in the analysis output. Opus found more rules than Sonnet, which is a reason to read the shares in the table above as floors.

## Where the data is

| You want | Open |
|---|---|
| Every verified rule, with its repository and a link to the source line | `gh_instructions/data/c10k_rules.csv` |
| The full analysis output, with sample rules for every habit | `gh_instructions/analysis_10k.txt` |
| The rubric the coder worked from | `gh_instructions/habits_rubric_v2.txt` |
| The coder's raw answers, both models | `gh_instructions/data/c10k_coded.jsonl` |
| The 10,000 repositories in the sample | `gh_instructions/data/c10k_sample.json` |
| Stars, dates, language and owner type for every repository | `gh_instructions/data/c10k_meta.json` |
| GitHub's count per size band and the candidate list | `gh_instructions/data/c10k_candidates.json` |
| Which files went into which API request | `gh_instructions/data/c10k_batches.json` |
| The 10 files the coder refused | `gh_instructions/data/c10k_failed.json` |
| GitHub's counts for four kinds of instruction file | `gh_instructions/data/github_counts.json` |

`c10k_rules.csv` has one row for each of the 15,242 verified rules.

| Column | Meaning |
|---|---|
| `file_id` | Content hash of the file text. Identical files share an id |
| `repo` | The repository the file was downloaded from. For identical texts, the first repository found |
| `url` | Link to the file at the exact commit it was read from |
| `stars`, `repo_created` | Stars and creation date of that repository |
| `copies` | How many repositories in the sample have this identical text |
| `habit` | The habit code, as in the rubric |
| `kind` | `pointed` or `routine` |
| `label` | A short name, for `OTHER` rules only |
| `quote` | The rule, verbatim from the file |

The `url` column points at a specific commit, so the quote can be checked even if the file has changed since.

Three things are not in the repository. The downloaded file texts (`c10k_files.jsonl`, 98 MB), the earlier 1,000-file download (`claude_md.jsonl`), and the first-pass input packs (`rules_in/`). They hold the full text of other people's files, and a scan found API-key-shaped strings in a small number of them, so they stay on disk. The fetch scripts rebuild them.

## To rerun

You need Python 3.12, the `gh` CLI logged in to GitHub, and the `anthropic` package. The commands below assume a virtual environment one level up from `gh_instructions/`. The coding script takes the API key from the `ANTHROPIC_API_KEY` environment variable and stops with a message if it is not set.

```
export ANTHROPIC_API_KEY=your-key-here
```

From `gh_instructions/`:

```
python3 fetch_claude_md.py
```

Downloads the 1,000-file sample that sets the size bands.

```
python3 fetch_10k.py --smoke
python3 fetch_10k.py
```

The smoke run draws 30 files from 3 bands to check the plumbing. Most of the full run's time goes to GitHub's search rate limit of 10 requests a minute. Both runs resume where they stopped.

```
../.venv/bin/python code_habits.py pilot
../.venv/bin/python code_habits.py submit
../.venv/bin/python code_habits.py collect
../.venv/bin/python code_habits.py retry
```

The pilot measures token use so that `submit` can project the cost. `submit` refuses to send anything if the projection is over the cap set in the script, $40 by default. `collect` waits for the batches and writes `c10k_coded.jsonl`. `retry` re-sends the failures one file at a time.

```
python3 analyze_10k.py > analysis_10k.txt
```

Verifies the quotes, prints every table in this README, and writes `c10k_rules.csv`. It uses only the Python standard library and calls no API.

A fresh run will not reproduce these numbers. GitHub's index changes daily, the search draws random pages, and the model's answers vary a little between runs. The random seeds in the scripts fix which candidates are chosen from a given set of search results, which files go into the agreement check, and which sample rules are printed.

## Limits

- **A model did the coding, with a model as the check.** No human coded a comparison set. The two-model agreement is good on whether a file has rules at all and on the common habits, and weaker on rarer habits and on the pointed-or-routine call.
- **The counts are floors.** The rubric says to leave out any line that could be a project convention rather than a conduct rule, quotes are limited to one line, and the second coder found more rules than the first.
- **The sample is of files GitHub's code search can see.** The search API covers only the default branch of each repository and only files under 384 KB, and GitHub says very large repositories may not be indexed. Private repositories and local CLAUDE.md files that never get committed are outside the study.
- **Counts are per repository, not per developer.** One person with forty repositories and the same template in each counts forty times. The `copies` column lets you count distinct texts instead.
- **Ten files are missing** because the coder refused them as cyber-related content.
- **The habit codes are one way to carve this up.** Rules were forced into a single best code, so a rule that guards against two habits appears under one.

## The earlier pass

The repository also has a first pass on about 1,000 files that the 10,000-file run replaced. It used a line filter (`prep_rules.py`) to cut each file down to lines carrying a rule marker before coding, with 24 files read in full to measure what the filter missed, and an earlier rubric (`habits_rubric.txt`) with 21 codes. Its coded output is in `rules_out/`, its analysis script is `analyze_habits.py`, and its verified rules are in `data/habit_rules.csv`. The second rubric split the GIT code into committing uninvited and AI attribution, split FORGETS into drifting from instructions and letting documentation go stale, and added leaving work uncommitted, asking too much, and working wastefully.

`fetch_sample.py` and `data/github_counts.json` are from a pilot across four file types, and `github_counts.json` is where the population counts above come from.

## License

MIT. The quotes in `c10k_rules.csv` are short excerpts from public files, each linked to its source, and remain under their original licenses.
