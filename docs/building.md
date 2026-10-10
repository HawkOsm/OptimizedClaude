# Building Guide

You build, Claude explains and reviews. This doc gives you the picture of what each piece
looks like, what to learn before building it (search keywords), what actually matters,
and when it's done. Work top to bottom; don't skip milestones.

## Rules of engagement

- Osm writes every line of `src/` and `tests/`. Claude never writes modules.
- Allowed asks: "explain X before I build it", "review this diff", "why does this error
  happen" (Claude points at the cause, doesn't paste the fix).
- **Stuck protocol:** timebox 45 minutes of your own attempts. Then ask, including what
  you tried and what you observed. This is where the learning actually happens.
- Every milestone ends with a review: bring the diff, Claude tears it apart, you fix.

## The picture — what the finished tool looks like

One terminal. You run `ocl` inside a repo and it feels like Claude Code, except a local
model quietly filters what reaches Claude:

```
$ ocl
[ocl] resuming session 4f2a… · local: qwen2.5:7b · /help for commands

> fix the udp issue
[local] two quick questions:
  1. what's the symptom — drops, timeout, or wrong data?
  2. which side, jetson script or yki?
> drops when ftp upload runs, jetson side
[local] compiled spec ↓                                    (y=send / e=edit / n=cancel)
  # Task
  Fix UDP packet drops on the jetson side occurring during FTP uploads. …
> y
[claude] ⚙ Read jetson/sihaTamOtonomV3.py
[claude] The drops happen because the telemetry thread and MAVFTP share…

> now add a log line when it recovers          ← short follow-up: passes straight through
[claude] Added. ⚙ Edit jetson/sihaTamOtonomV3.py

> btw what does setsockopt SO_RCVBUF do
[local] Sets the kernel receive buffer size for the socket…            (cost: 0 tokens)
```

Three behaviors, one loop: clarify-and-compile new tasks, pass follow-ups through
untouched, answer trivia locally. Everything logged to `.ocl/ledger.jsonl`.

## Ground rules (apply from day one)

- **uv + Python 3.12**, src layout (`src/ocl/`). Never install into system python.
- **TDD rhythm** where the code is pure (ledger, config, router heuristics, rendering):
  write the failing test, make it pass, clean up. Async/UI code gets tests after, but
  gets them.
- **Dependency direction law:** `core/` never imports `ui/`. Enforced by a lint rule,
  not by good intentions.
- **Small commits**, one idea each, imperative messages ("add ledger event models").
  Commit when tests are green, not at end of day.
- **ADR habit:** every time reality forces a deviation from design.md, add a 5-line
  record to `docs/adr/NNN-title.md` (template at the bottom). Then fix design.md.
- Tools: `ruff` (lint+format), `pytest`, `mypy` later. Wire them before writing code.

---

## M0 — Skeleton & tooling (half a day)

**Picture:** empty package that installs, lints, and runs one dummy test.

- Build: `pyproject.toml` via uv, `src/ocl/__init__.py`, `tests/test_smoke.py`,
  ruff config, a `Makefile` or `justfile` with `test`, `lint`, `goldens` targets.
- Search: `uv python project src layout` · `pyproject.toml scripts entry point` ·
  `ruff configuration pyproject` · `pytest getting started`
- Focus: get the feedback loop fast — `make test` under 2 seconds. You'll run it
  hundreds of times.
- Done when: `uv run ocl --version` prints something; `make test` and `make lint` pass.

## M1 — Ledger + Config (the data-management milestone)

**Picture:** no UI yet. A module you can drive from a Python REPL:

```python
>>> led = Ledger(Path(".ocl/ledger.jsonl"))
>>> led.emit(UserInput(text="fix the udp issue"))
>>> stats(led.read())
LedgerStats(claude_turns=0, input_tokens=0, …)
```

- Build: pydantic models for every event in `docs/schemas.md` §1 (tagged union on
  `event`), append-only writer (crash-safe: one line = one atomic append), reader,
  and a `stats()` function that folds events into the benchmark metrics. Then config:
  load TOML with precedence per-repo > global > defaults, unknown keys warn.
- Search: `pydantic v2 discriminated union` · `python jsonl append` · `event sourcing basics` · `tomllib python` · `pytest tmp_path fixture` · `dataclass vs pydantic when`
- Focus: **schema first, code second.** The interesting design question: how do you
  version events so a v2 field addition doesn't break reading old files? Decide, write
  an ADR.
- Traps: reading the whole file into memory (stream it); letting a ledger write failure
  raise (design.md §11 says never).
- Done when: schemas.md §1 fully implemented; tests cover round-trip, corrupt-line
  tolerance, stats on a hand-written fixture file; config precedence tested.
- Review checkpoint: bring the models + tests. Expected fight: your first union design.

## M2 — Passthrough wrapper (the architecture milestone, hardest)

**Picture:** a usable Claude Code frontend with zero local intelligence:

```
$ ocl
[ocl] new session · /help
> explain the repo structure
[claude] This repo contains… ⚙ Read README.md
> ^C                                  ← interrupts the stream, doesn't kill the session
```

- Build: async REPL (prompt_toolkit), `ClaudeSession` wrapper around `ClaudeSDKClient`
  (connect, send, stream events, interrupt, session_id persistence to
  `.ocl/session.json`, resume on restart), permission callback rendered as a REPL
  prompt, every event → ledger.
- Search: `python asyncio tasks tutorial` · `asyncio cancellation CancelledError` ·
  `claude agent sdk python quickstart` · `ClaudeSDKClient receive_response` ·
  `claude agent sdk can_use_tool permission` · `prompt_toolkit PromptSession async` ·
  `asyncio handle SIGINT gracefully`
- Focus: **two concurrent loops** (stdin reader, SDK event consumer) and what happens
  at every boundary: Ctrl+C mid-stream, layer crash mid-stream, claude exiting. Draw
  the task lifecycle on paper before coding — this drawing IS the architecture practice.
- Traps: blocking `input()` inside async (freezes the stream); killing the subprocess
  instead of `interrupt()`; forgetting that resume needs the CLI/SDK versions pinned.
- Done when: you use it instead of `claude` for one real day and don't hate it;
  `kill -9` the wrapper mid-task → restart → resume works.
- Review checkpoint: the ClaudeSession class + your lifecycle drawing.

### M2 front-end decision (open — decide before building M2)

The text above is **option A**. There is a second option, found later, that may fit
the original idea ("steer the chat from inside Claude Code") better. Choose one and
record it as an ADR; the Python core (ledger, events, stats, router, clarifier,
compiler, goldens) is the same under both.

- **A. Wrapper REPL (above).** `ocl` is its own terminal program. It drives Claude Code
  headlessly through `claude-agent-sdk` and you type into `ocl`, not into Claude Code.
  Open risk: whether a Pro/Max subscription login may be used through the Agent SDK is
  unverified (see `docs/design.md` D1 and the roadmap's "verify early" item; Anthropic's
  legal page says Pro/Max limits assume ordinary individual use of Claude Code and the
  Agent SDK, but also that developers building products should use API keys).
- **B. Claude Code mod.** The UI stays the real Claude Code. A mod (a plugin written in
  JS/TS, needs Claude Code v2.1.287+) adds a hotkey or button that opens the local
  layer, so Enter stays a plain send and the hotkey means "refine this first".
  What the docs say a mod can do: draw panes, buttons and text fields, rewrite a prompt,
  add `/commands`, start processes. Keybindings alone and prompt hooks alone cannot do
  this (a hook can only add context or block, not rewrite or ask the user).
  - Layout: a `mod/` folder in this repo (`.claude-plugin/plugin.json`,
    `hooks/hooks.json`, `hooks/register.js`) that is a thin UI. It calls the Python core
    as a process (for example an `ocl` command that takes the message and prints JSON).
    That bridge is the intended design but is **untested**.
  - Benefits: no separate REPL, no async stream plumbing, and no SDK auth question,
    because it runs inside the Claude Code you are already signed into.
  - Costs and unknowns: mods are JS/TS (the UI part is not Python), they run with your
    full permissions, the feature is new, and the router becomes manual-trigger (the
    `PASSTHROUGH` goldens, 24 of 46, would need to be rethought).
- **Before choosing:** read the mods pages (overview, create a mod, draw in the
  interface, react to events) and try one sample mod from Anthropic's
  `claude-code-playground` repository with `--plugin-dir`. Then write the ADR.
- Sources: https://code.claude.com/docs/en/plugins/mods/overview ·
  https://code.claude.com/docs/en/hooks · https://code.claude.com/docs/en/keybindings

## M3 — Heuristic router + golden harness (the SQA milestone)

**Picture:** still no Ollama. `route(msg, session_active)` returns a decision from pure
rules (`/` → META, active+short → PASSTHROUGH, else → PASSTHROUGH with source
`fallback`), and:

```
$ make goldens
router: 31/46 correct · must_pass: 20/20 ✓  (LLM cases fail — expected, no LLM yet)
```

- Build: `core/router.py` heuristic tier; a harness that loads
  `tests/golden/router_cases.jsonl`, runs any router callable, prints per-class
  accuracy and the must_pass verdict.
- Search: `pytest parametrize from file` · `python structural pattern matching` ·
  `confusion matrix by hand`
- Focus: harness design — it must accept *any* router implementation, because M4 swaps
  in the LLM tier and you compare both with the same command.
- Done when: harness runs; heuristic tier passes 100% of the cases it claims to handle.

## M4 — LocalLLM + LLM router (the working-with-nondeterminism milestone)

**Picture:** Ollama installed, and:

```
$ make goldens
router[heuristic+llm/qwen2.5:7b]: 44/46 · must_pass: 20/20 ✓ · p95 latency 380ms
```

- Build: install Ollama, pull 2–3 candidate models; `core/localllm.py` (async httpx
  client, `format=json`, timeout, retry-once ladder, degrade signal); LLM router tier
  behind the heuristics; G1 bake-off = goldens run per model, results table committed.
- Search: `ollama api chat format json schema` · `ollama keep_alive` · `httpx async client timeout` · `small llm structured output reliability` · `ollama gpu vram check`
- Focus: the failure ladder (schemas.md → design.md §8). Every LLM call site follows
  the same pattern; extract it once, reuse.
- Traps: cold-start latency counted as model quality; trusting `confidence` blindly
  (calibrate the threshold against the goldens).
- Done when: G1 table committed, default model chosen, accuracy ≥90% + must_pass 100%,
  p95 within budget on your machine.

## M5 — Clarifier + Compiler + review step

**Picture:** the full flow from "The picture" section works end to end.

- Build: clarify state (pending questions, collected answers) in the REPL flow;
  compiler → TaskSpec (pydantic) → deterministic render (schemas.md §3) → y/e/n review
  → send; `/quick`, `/task`, `/pass`, `/spec` commands; clarifier goldens harness.
- Search: `python state machine enum` · `pydantic model_validate_json` · `prompt_toolkit multiline edit` (for `e`)
- Focus: the session state machine (design.md §9) — implement it as explicit states,
  not nested ifs. This is the second big architecture rep.
- Done when: clarifier goldens pass (incl. the two zero-question cases); render
  property test holds (no content in output absent from spec).

## M6 — Triage + `/escalate`

- Build: TRIVIAL path → triage prompt → `[local]`-tagged answer or ESCALATE → forward;
  ledger records the split.
- Focus: small. Enjoy an easy one.
- Done when: golden trivial cases answer locally; a repo question sneaks past the
  router → triage says ESCALATE (defense in depth).

## M7 — Benchmark + honest README

- Run `docs/benchmark.md` exactly as written. Commit results. Rewrite README's claims
  to match the numbers, whatever they are.
- Focus: resist the urge to fix the tool mid-benchmark. Finish the runs, then iterate.

---

## ADR template (`docs/adr/NNN-short-title.md`)

```
# NNN — <decision, one line>
Date: YYYY-MM-DD
Status: accepted
Context: <what forced a decision, 1–2 lines>
Decision: <what you chose>
Consequences: <what this costs / enables, 1–2 lines>
```

## Definition of done, every milestone

tests green · lint clean · ledger events emitted where schemas.md says · design.md and
schemas.md updated if reality diverged (with ADR) · committed in small pieces · reviewed.
