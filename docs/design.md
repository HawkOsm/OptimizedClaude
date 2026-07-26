# OptimizedClaude — Engineering Design v1

Companion to `roadmap.md`. This document is the contract for implementation:
no code exists yet; when code and this doc disagree, one of them is wrong and must be fixed.

## 0. Locked decisions

| # | Decision | Choice | Why |
|---|----------|--------|-----|
| D1 | Claude transport | Wrap Claude Code CLI via **claude-agent-sdk (Python)** | Subscription auth works (SDK spawns the `claude` CLI as subprocess); no API billing needed |
| D2 | Scope | **Stay in loop** — the tool is the terminal frontend for the whole session | Osm's choice; enables routing/triage on every message |
| D3 | Language | Python | — |
| D4 | Local model class | 7–8B Q4 on GPU, single model | 8GB VRAM fits one 7–8B fully resident; two models would thrash |
| D5 | Runtime env | **uv-managed venv, Python 3.12 pinned** | System python is 3.14 (too new for some wheels); and no repeat of the numpy `--user` site-packages disaster |
| D6 | Cache stance | Never touch Claude session history; only shape new outgoing messages | Cache-safe by construction |

## 1. Verified environment (live-checked 2026-07-26)

- GPU: NVIDIA RTX 4070 Laptop, 8188 MiB VRAM
- RAM: 30 GiB (22 available)
- Python (system): 3.14.4 — do NOT use for the project (D5)
- Claude Code CLI: 2.1.220, on PATH
- Ollama: **not installed** (install step in build order)

Model VRAM budget: 7–8B at Q4_K_M ≈ 4.5–5.2 GiB weights + ~1–2 GiB KV at 8k ctx → fits with headroom. 14B does not (spills to RAM, latency dies).

## 2. Product definition

A terminal REPL that replaces typing directly into `claude`. The user talks to it; a local
Ollama model routes, clarifies, and compiles; a headless Claude Code session runs underneath.
Claude never sees a vague prompt; the user never pays Claude tokens for clarification or
trivia. Everything degrades gracefully to "thin claude wrapper" if the local side breaks.

## 3. Requirements

### Functional

- FR1: Interactive REPL; user messages and streamed Claude output in one scrollback.
- FR2: Every user message is classified by the **Router** into exactly one of:
  `PASSTHROUGH | TASK_NEW | TRIVIAL | META`.
- FR3: `TASK_NEW` → **Clarifier** may ask ≤ N questions (config, default 3), skipping any
  whose answer already appears in the dialogue.
- FR4: **Compiler** produces a schema-valid TaskSpec; user reviews (`y` / `e`dit / `n`)
  before send. A trust mode (`/trust on`) skips review.
- FR5: One persistent Claude Code session per repo: start, resume after crash/restart,
  interrupt (Ctrl+C → SDK interrupt, not process kill), `/new` for fresh session.
- FR6: Claude output streams live; tool activity rendered as one-liners (`⚙ Read src/x.py`).
- FR7: Claude Code permission requests surface in the REPL (allow / deny / always-allow).
- FR8: `TRIVIAL` → answered by the local model, visibly tagged `[local]`, with `/escalate`
  to forward the same question to Claude.
- FR9: Ledger: every event (local turns, Claude turns, usage, routing decisions) appended
  to a JSONL file per repo.
- FR10: Meta commands (§10).
- FR11: If Ollama is unreachable or slow, the tool silently becomes a pure passthrough
  wrapper with a status banner. The user's work is never blocked by the local side.

### Non-functional

- NFR1 latency: Router ≤ 500 ms p95; Clarifier turn ≤ 2.5 s; passthrough added overhead
  ≤ 50 ms; heuristic-only passthrough (no LLM call) for messages < 40 chars.
- NFR2 robustness: layer crash must not lose the Claude session (session_id persisted;
  restart offers resume).
- NFR3 privacy: nothing leaves the machine except the `claude` CLI's own traffic. No
  telemetry. Ledger stays in the repo (`.ocl/`, gitignored by default).
- NFR4 quality: pydantic schemas everywhere the local model outputs JSON; typed code;
  pytest; prompt files are versioned artifacts with their own tests.

## 4. Architecture

```
┌────────────────────────── REPL (prompt_toolkit) ──────────────────────────┐
│ user input                                            streamed output     │
└─────┬─────────────────────────────────────────────────────▲──────────────┘
      ▼                                                     │
  Router ──META──▶ command dispatch                         │
   │ │ │                                                    │
   │ │ └─TRIVIAL─▶ Triage (local answer, tagged) ───────────┤
   │ └───TASK_NEW─▶ Clarifier ⇄ user ─▶ Compiler ─▶ Review ─┤
   │                                        │ approve       │
   └───PASSTHROUGH──────────────────────────┴──▶ ClaudeSession (agent-sdk)
                                                    │  ClaudeSDKClient
                                                    ▼
                                             claude CLI subprocess
      Ledger (JSONL) ◀── every component logs events
      LocalLLM (ollama HTTP) ◀── Router / Clarifier / Compiler / Triage
```

Modules: `ui/repl.py`, `core/router.py`, `core/clarifier.py`, `core/compiler.py`,
`core/triage.py`, `core/claude_session.py`, `core/localllm.py`, `core/ledger.py`,
`config.py`, `prompts/{router,clarifier,compiler,triage}.md`.

## 5. Routing policy — the make-or-break rule

**The compiler engages at task boundaries, not on every message.** Mid-session follow-ups
("yes", "now fix the test", "no, the other file") must fly through untouched, or the tool
gets uninstalled in a day.

| Condition | Class | LLM call? |
|---|---|---|
| Message starts with `/` | META | no |
| Session active AND len < 40 chars | PASSTHROUGH | no (pure heuristic) |
| Session active AND anaphoric/contextual (pronouns, "it", "that", imperative continuations) | PASSTHROUGH | router LLM confirms |
| No active session AND message is task-shaped | TASK_NEW | yes |
| Session active AND message states a NEW goal (no anaphora, new nouns) | TASK_NEW (ask: `[c]ompile or [p]ass?`) | yes |
| Question-shaped, answerable without repo knowledge (syntax, flags, concepts) | TRIVIAL | yes |
| **Router unsure (confidence < threshold) or errors** | **PASSTHROUGH** | — |

Failsafe direction is always PASSTHROUGH: wrongly passing a compilable prompt costs a
little; wrongly interrogating the user costs trust.

Router output schema: `{"class": str, "confidence": float, "reason": str}` — `format=json`
enforced, pydantic-validated, 1 retry on parse failure, then PASSTHROUGH.

## 6. TaskSpec schema & rendering

```python
class ContextRef(BaseModel):
    path: str
    lines: str | None      # "120-180"
    why: str

class TaskSpec(BaseModel):
    goal: str
    constraints: list[str] = []
    context_refs: list[ContextRef] = []
    acceptance: list[str] = []
    non_goals: list[str] = []
    raw_user_words: str     # verbatim original request, always included
```

Rendering to the outgoing prompt is **deterministic Python string templating** from the
validated model — the local LLM fills slots; it never freeforms the final prompt text.

**No-invention invariant:** every claim in the spec must trace to the user's words or the
user's clarification answers. Enforced by (a) the compiler system prompt, (b) mandatory
review step until `/trust on`, (c) `raw_user_words` always shipped so Claude can detect
compiler drift, (d) v2: a local verifier pass diffing spec content against dialogue.

## 7. Claude Code integration

- Library: `claude-agent-sdk` (PyPI). `ClaudeSDKClient` gives a persistent multi-turn
  session with streaming, interruption, and dynamic permission handling; it spawns the
  `claude` CLI subprocess, so the Pro/Max subscription login is used as-is.
- Options: `cwd` = repo root; permission mode `default` + `can_use_tool` callback that
  renders an allow/deny/always prompt in the REPL; user's own CLAUDE.md / settings load
  normally (slimming Claude's context is explicitly out of scope in v1).
- Events consumed: assistant text deltas → stream to REPL; tool-use start → one-liner;
  result message → extract usage/cost/session_id → ledger.
- Session lifecycle: session_id persisted to `.ocl/session.json`; on start, if present,
  offer resume; `/new` clears it. Ctrl+C during a stream calls `interrupt()`.
- **Version pinning:** pin the SDK and CLI versions together (`.ocl/versions`) — session
  resume has broken across mismatched CLI versions in the wild. Record both in the ledger.

## 8. Local model spec

- Candidates: `qwen2.5:7b-instruct` (default) vs `llama3.1:8b` vs `qwen3:8b` — decided by
  gate G1 (golden-set eval, §13) before any tuning work.
- Ollama settings: `keep_alive=30m` (no reload latency), `num_ctx=8192`,
  temperature 0.1 for Router/Compiler, 0.4 for Clarifier phrasing, `format=json` on all
  structured calls.
- Three system prompts (`prompts/*.md`) are versioned, tested artifacts. Common clauses:
  output schema, "ask, never invent," "prefer PASSTHROUGH when unsure" (router).
- Failure ladder per call: parse fail → 1 retry with error echoed → give up →
  PASSTHROUGH (router) / abort compile with message (compiler).

## 9. State machine (session level)

```
            ┌────────────── /abort from any state ──────────────┐
            ▼                                                    │
IDLE ──TASK_NEW──▶ CLARIFYING ──answers done | /quick──▶ REVIEW ─┤
 │  │                                                     │ y    │
 │  ├─TRIVIAL──▶ LOCAL_ANSWER ──▶ IDLE                    ▼      │
 │  └─PASSTHROUGH────────────────────────────▶ CLAUDE_STREAM ──▶ IDLE
 └─META─▶ dispatch ─▶ IDLE                    (Ctrl+C → interrupt → IDLE)
```

Only one Claude stream at a time; input during streaming is queued (or Ctrl+C to interrupt).

## 10. Meta commands

`/quick` (skip clarification, compile as-is) · `/pass` (force passthrough this message) ·
`/task` (force compile path) · `/new` · `/resume` · `/escalate` · `/spec` (show last spec) ·
`/usage` (session token/turn stats from ledger) · `/trust on|off` · `/model <name>` ·
`/help` · `/quit`

## 11. Degradation matrix

| Failure | Behavior |
|---|---|
| Ollama not running / unreachable | Banner `local layer offline — passthrough mode`; everything routes straight to Claude |
| Local call > 4 s | Abandon call, PASSTHROUGH, log warning |
| Local JSON invalid twice | PASSTHROUGH (router) / abort with message (compiler) |
| `claude` spawn fails | Show CLI stderr verbatim, exit nonzero |
| Session resume rejected (version mismatch) | Offer `/new`, print pinning hint |
| Ledger write fails | Warn once, keep running |
| Layer crashes mid-stream | Claude session survives on disk; restart offers resume |

## 12. Test strategy

- **Unit:** schema validation, heuristic router rules, deterministic spec rendering,
  ledger format.
- **Prompt goldens (run locally, GPU):**
  - `tests/golden/router_cases.jsonl` — ≥ 40 labeled messages across all classes,
    including the nasty ones (short new tasks, long follow-ups). Accuracy gate ≥ 90%,
    and 100% on the "must-pass-through" subset.
  - Clarifier set: vague prompts + rubric (questions answerable? non-redundant? ≤ N?).
  - Compiler no-invention check: spec content vocabulary ⊆ dialogue vocabulary
    (heuristic diff, flags hallucinated constraints).
- **Integration:** a fake `claude` executable on PATH (`tests/bin/claude`) that replays
  recorded stream-json fixtures → full loop tests without touching the subscription.
- **E2E protocol:** the 3 benchmark tasks from roadmap Phase 0, run raw vs through the
  tool; report turns-per-task, tokens-per-task (from result usage), wall clock.
- CI (GitHub Actions): unit + integration. Prompt goldens are a local `make goldens`
  target (needs GPU).

## 13. Gates before/at implementation

- **G0 (before code):** this doc reviewed by Osm; open items below resolved or defaulted.
- **G1 (after Phase 1 skeleton):** model bake-off on router+clarifier goldens picks the
  default model. No prompt micro-tuning before G1.
- **G2 (before `/trust` ships):** compiler passes no-invention golden set 20/20.

## 14. Open items (defaults apply if no objection)

| Item | Default |
|---|---|
| Project name | **OptimizedClaude** (repo); python package + CLI command: `ocl` |
| REPL lib | `prompt_toolkit` v1; Textual only if scrollback/stream rendering hurts |
| Where triage answers come from | Same 7–8B model, no web access, tagged `[local]` |
| Trivial-answer risk appetite | Conservative: router requires high confidence for TRIVIAL, else PASSTHROUGH |
| Repo layout | `src/ocl/` + `prompts/` + `tests/`; `pyproject.toml` via uv |

## 15. Build order (maps to roadmap phases)

1. uv project skeleton, config, ledger, REPL shell that is a **pure passthrough** to
   ClaudeSDKClient (FR5–FR7, FR9, FR11 path). Ship: usable claude wrapper.
2. Install Ollama, pull candidates, LocalLLM wrapper + heuristic router (no LLM yet).
3. LLM router + goldens (G1 bake-off).
4. Clarifier + Compiler + Review + TaskSpec.
5. Triage + `/escalate`.
6. Benchmarks, polish, README with honest numbers.

Note the inversion vs. the roadmap draft: **passthrough wrapper first**, local intelligence
second. The wrapper is the load-bearing wall; the compiler is furniture.
