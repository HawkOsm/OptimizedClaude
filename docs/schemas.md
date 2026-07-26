# Data Formats & Schemas

Everything design.md references but doesn't spell out. Code must match this file.

## 1. Ledger — `.ocl/ledger.jsonl`

One JSON object per line. Common envelope on every event:

```json
{"ts": "2026-07-26T14:03:22.114Z", "v": 1, "session_id": "<claude session uuid or null>", "event": "<type>", ...}
```

Event types and their extra fields:

| event | fields | when |
|---|---|---|
| `user_input` | `text` | every message the user types |
| `route_decision` | `class`, `confidence`, `source` (`heuristic`\|`llm`\|`fallback`), `latency_ms` | after routing |
| `local_call` | `component` (`router`\|`clarifier`\|`compiler`\|`triage`), `model`, `latency_ms`, `ok`, `retries` | every Ollama call |
| `clarify_q` | `questions` (list) | clarifier asked |
| `clarify_a` | `answers` (list) | user answered |
| `spec_compiled` | `spec` (full TaskSpec object) | compiler output validated |
| `spec_review` | `verdict` (`approved`\|`edited`\|`rejected`), `edited_spec` (if edited) | review step |
| `claude_send` | `mode` (`passthrough`\|`compiled`\|`escalated`), `chars` | message sent to Claude |
| `tool_activity` | `tool`, `summary` | Claude used a tool |
| `claude_result` | `usage` (see below), `duration_ms`, `num_turns`, `is_error` | Claude turn finished |
| `local_answer` | `text` | triage answered locally |
| `escalate` | — | user forwarded a local answer's question to Claude |
| `degrade` | `reason` (`ollama_down`\|`ollama_timeout`\|`parse_fail`) | fell back to passthrough |
| `error` | `where`, `message` | any caught exception |
| `session` | `action` (`start`\|`resume`\|`new`\|`interrupt`), `cli_version`, `sdk_version` | lifecycle |

`usage` object (copied verbatim from the SDK result message where available):
`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`,
`cost_usd` (null on subscription).

Rules: append-only; write failures never crash the app (§11 design.md); `.ocl/` is
gitignored in target repos.

## 2. Config — `~/.config/ocl/config.toml` (global) + `.ocl.toml` (per-repo overrides)

Full example with every knob and its default:

```toml
[local]
host = "http://127.0.0.1:11434"
model = "qwen2.5:7b-instruct"     # overridden by G1 bake-off result
keep_alive = "30m"
num_ctx = 8192
timeout_s = 4.0                    # per call; exceeded -> degrade to passthrough
temperature_router = 0.1
temperature_clarifier = 0.4
temperature_compiler = 0.1
temperature_triage = 0.2

[router]
confidence_threshold = 0.7         # below -> PASSTHROUGH
heuristic_max_chars = 40           # active session + shorter than this -> no LLM call

[clarifier]
max_questions = 3

[compiler]
trust = false                      # true = skip review step (gate G2 first)

[claude]
cli_path = "claude"                # resolved on PATH
permission_mode = "default"        # default | acceptEdits | plan
model = ""                         # empty = Claude Code's own default

[ledger]
enabled = true
path = ".ocl/ledger.jsonl"
```

Precedence: per-repo `.ocl.toml` > global config > built-in defaults. Unknown keys → warn,
don't crash.

## 3. TaskSpec render template (deterministic)

The compiler fills the TaskSpec model (design.md §6); this exact template renders it.
Sections with empty lists are omitted entirely — no "None" placeholders.

```
# Task
{goal}

## Constraints
- {constraints[0]}
- ...

## Relevant context
- {path} ({lines}) — {why}
- ...

## Done when
- {acceptance[0]}
- ...

## Out of scope
- {non_goals[0]}
- ...

## Original request (verbatim)
> {raw_user_words}
```

Rendering is pure Python string assembly from the validated pydantic model. The local LLM
never produces this text. Property test: render(spec) contains no content absent from spec.

## 4. Golden-set file formats

- `tests/golden/router_cases.jsonl` — fields: `id`, `session_active`, `message`,
  `expected` (`PASSTHROUGH`|`TASK_NEW`|`TRIVIAL`), optional `must_pass` (bool, the 100%
  subset), optional `note`. Harness: overall accuracy ≥ 90%, must_pass subset = 100%.
- `tests/golden/clarifier_cases.jsonl` — fields: `id`, `message`, `context`,
  `expect_questions_about` (topics, judged by rubric not string match; empty list means
  `needs_clarification` must be false), `must_not_ask` (auto-fail topics).
