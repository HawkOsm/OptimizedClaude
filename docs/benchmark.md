# Benchmark Protocol (Phase 0)

The published claim of this project is measured, not asserted. This protocol defines the
measurement before any optimization exists, so the numbers can't be quietly bent later.

## Metrics

Per task, from the ledger (`claude_result` events) and Claude Code's own `/cost`:

- **claude_turns** — number of `claude_send` events (the primary metric)
- **total_input_tokens**, **total_output_tokens**
- **cache_read_tokens**, **cache_creation_tokens**
- **wall_clock_s** — first user input to accepted result
- **local_calls / local_answered** — layer overhead and triage wins (tool runs only)
- **outcome** — `success` | `partial` | `fail` (defined per task below, judged before
  looking at any numbers)

## Tasks

Three fixed tasks, chosen to represent real work. Each defines its own success check.
(Fill in the concrete repo/commit before the first run; once filled, frozen.)

| id | type | task | success check |
|---|---|---|---|
| T1 | bug fix | a real, reproducible bug in the UAV repo (pick one from the issue backlog; document repro) | repro no longer triggers; existing tests pass |
| T2 | refactor | extract/restructure one module (defined scope) without behavior change | tests pass; diff reviewed as behavior-neutral |
| T3 | explain | "explain how <chosen subsystem> works end to end" | written answer judged correct against the code |

## Procedure

1. **Fixed start state:** each run starts from the same commit, in a fresh `git worktree`,
   with a fresh Claude session (`/new`). No leftover context.
2. **Arm A (baseline):** perform the task in plain Claude Code, typing as you normally
   would. No special effort to write good prompts — the baseline is honest habits.
3. **Arm B (tool):** same task through OptimizedClaude, fresh worktree, fresh session.
4. Run each (task, arm) pair **3 times** (LLM variance is real); report median and range,
   not best-of.
5. Record outcome before reading token numbers, to avoid grading drift.
6. **Order control:** alternate which arm goes first per repetition (doing the same task
   twice teaches the human; alternation spreads that bias across both arms).

## Rules

- No cherry-picking: every attempted run is reported, including failures and aborts.
- If the tool's clarification questions are useless in a run, that run still counts —
  annoyance is data.
- Baseline runs may not be sandbagged: type the way you actually type (the golden sets
  exist precisely because that's terse and vague).
- Any protocol deviation is written down in the report.

## Report format (`docs/results/<date>.md`)

| task | arm | run | outcome | claude_turns | input_tok | output_tok | cache_read | wall_s |
|---|---|---|---|---|---|---|---|---|

Followed by: median comparison table per task, and a short honest paragraph per task on
*why* the numbers differ (fewer clarification round-trips? triage wins? or no difference).

Negative results get published with the same prominence as positive ones. If the tool
doesn't beat baseline, that's the finding.
