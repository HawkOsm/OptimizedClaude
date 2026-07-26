# Local Prompt Compiler for Claude — Roadmap

Core idea (Osm's original): an **Ollama-based local layer that sits in front of Claude**.
You talk to a free local model first — it clarifies, organizes, and assembles your request —
and only a clean, well-structured prompt ever reaches Claude. One target model (Claude),
deeply optimized. No multi-provider routing.

Name: **OptimizedClaude** — repo: github.com/HawkOsm/OptimizedClaude. CLI command: `ocl`.

---

## Why this beats blind compression (the real economics)

The expensive thing in Claude usage is not prompt *length* — it's **wasted turns**:
- vague prompt → Claude asks back or guesses wrong → 2–4 extra round trips
- each Claude Code turn re-sends the growing context, so a wasted turn late in a session
  costs 10–50x a wasted turn early
- missing context → Claude re-reads half the repo to find it

A local layer attacks exactly this: clarification round-trips happen locally (free),
context selection happens locally (free), and Claude gets one shot set up to succeed.
Metric that matters: **tokens and turns per COMPLETED task**, not per prompt.

### Cache-safety comes for free in this design

Anthropic caching is prefix-based and byte-exact (tools -> system -> messages); rewriting
history busts the cache and can make usage worse. This layer never touches history — it only
shapes the **new tail message before it is ever sent**. Cache-safe by construction. Keep it
that way: never add a feature that rewrites past turns.

### Design law for the local model

The local model **asks and structures — it never invents**. A 3–8B model that "improves"
your prompt by adding requirements you didn't state is worse than no layer. Its outputs:
questions to you, and a structured compilation of *your* answers. Final compiled prompt is
shown for approval (fast y/n) before sending, at least until trust is earned.

---

## Architecture

```
you ⇄ local model (Ollama)          [free back-and-forth]
        │  1. intake: understand the ask
        │  2. clarify: ≤3 targeted questions if ambiguous
        │  3. context: pick relevant files/snippets (ripgrep first, embeddings later)
        │  4. compile: structured task spec (goal / constraints / context / acceptance)
        ▼
   [you approve]
        ▼
     Claude (API or Claude Code)     [one well-armed shot]
        ▼
   local post-check (optional): does the answer satisfy the spec? draft follow-up locally
```

## Phase 0 — Baseline & measurement (1 weekend)

- [ ] Pick 3 representative real tasks (UAV repo bug fix, a refactor, a "explain this" ask).
- [ ] Run them raw through Claude Code today; record turns used + token totals
      (`/context`, `/cost`, `ccusage`).
- [ ] Write the benchmark harness: same tasks, later run through the layer, compare
      turns-per-task and tokens-per-task. This harness is the credibility of the whole project.

## Phase 1 — CLI MVP (2 weekends)

- [ ] Python CLI/TUI: chat loop with an Ollama model (start: `qwen2.5:7b-instruct` or
      `llama3.2:3b` for speed; make it a config knob).
- [ ] System prompt for the local model = the compiler persona: intake → clarify → compile.
      Hard rule in the prompt: no invented requirements, ask instead.
- [ ] `/send` command: compiles the conversation into the structured spec, shows it, on
      approval fires it to the Anthropic API (`httpx`, streaming) and prints the reply.
- [ ] Spec template v1: Goal / Constraints / Relevant context / What done looks like /
      Explicit non-goals.
- [ ] Log every exchange (local + Claude) to disk for the benchmark harness.

Deliverable: `v0.1` — usable daily by you, even if rough.

## Phase 2 — Clarification engine (1–2 weekends)

- [ ] Ambiguity detection: local model scores the request; if unclear, asks up to N questions
      (configurable, default 3) before compiling. Skips questions whose answers are already
      in the conversation.
- [ ] Question quality is THE product here — iterate the local system prompt hard, keep a
      test set of vague prompts + expected good questions (SQA instincts: this is a test
      suite for a prompt).
- [ ] `/quick` escape hatch: skip clarification entirely, compile as-is.

## Phase 3 — Context curation (2–3 weekends)

- [ ] Repo-aware mode: given a project dir, layer runs ripgrep/ctags to find candidate files
      for the task; local model ranks and selects; selected snippets go into the spec's
      context section with file:line references.
- [ ] Token budget: hard cap on attached context (e.g. 8k tokens), local model must
      prioritize within it.
- [ ] Later: local embeddings (`nomic-embed-text` via Ollama) for semantic file search when
      grep isn't enough.
- [ ] Benchmark: does curated context beat "let Claude Code read whatever it wants"? Measure
      turns + tokens on the Phase 0 tasks.

## Phase 4 — Local triage gate (1 weekend)

- [ ] Before compiling, local model classifies: trivial question it can answer itself
      (syntax, "what does this flag do", regex explanation) vs. Claude-worthy work.
- [ ] Trivial → answer locally, tag the answer clearly as local-model output, offer
      `/escalate` to send to Claude anyway.
- [ ] Track the split: % of asks that never cost a Claude token.

## Phase 5 — Claude Code integration (2–3 weekends)

Options, in order of increasing depth — decide after living with the CLI:
- [ ] a) Launcher: `ocl "fix the udp bug"` → clarify/compile locally → spawns
      `claude -p "<compiled spec>"` in the repo. Simplest, zero interference with caching.
- [ ] b) MCP server: expose the compiler as a tool inside Claude Code ("refine this with the
      user locally before proceeding"). Inverts control; interesting but weirder UX.
- [ ] c) Thin proxy that only shapes the outgoing new user message (tail-only, cache-safe)
      so the layer works transparently inside long Claude Code sessions.
- [ ] Verify early: does a `ANTHROPIC_BASE_URL` proxy even see subscription (Pro/Max)
      traffic, or API-key billing only? Determines whether (c) is broadly usable.

## Phase 6 — Polish & release (ongoing)

- [ ] `pipx install`-able; one command to start; config file for models/budgets.
- [ ] README led by the honest benchmark table: turns-per-task and tokens-per-task,
      before/after, per task type. No "90% savings, same output" reel-math — real curves.
- [ ] Short demo clip: vague one-liner goes in → 2 local questions → compiled spec → Claude
      one-shots it. That's the shareable moment.
- [ ] Write-up: "Stop paying Claude to ask you what you meant." Post to r/ClaudeAI, HN.

---

## Stack

- Python 3.12; `ollama` python client (or raw HTTP to localhost:11434); `httpx` for
  Anthropic API with SSE streaming; Textual (TUI) or plain readline loop first.
- ripgrep + ctags for Phase 3; `nomic-embed-text` later.
- pytest + recorded exchanges for regression; the vague-prompt test set as fixtures.

## Risks / open questions

- Local model quality ceiling: if 3–8B clarification questions are dumb, the layer is
  friction, not help. Mitigation: question test set, model knob, aggressive prompt iteration.
- Latency budget: local round-trip must feel < ~2s to not annoy. Measure on your hardware;
  pick model size accordingly.
- Overhead trap: for already-clear prompts the layer must get out of the way (`/quick`,
  ambiguity threshold). A tool that interrogates you about "rename this variable" dies fast.
- Approval fatigue: y/n on every compile may get old → add auto-send trust mode once the
  compiler proves itself.

## Deferred (explicitly out of scope for now)

- Multi-provider fallback/routing — not needed; Claude-only by design.
- History rewriting / lossy compression of past turns — cache-hostile, skip.
- Cache observability dashboard — nice-to-have later; the compiler is the product.

## Sources worth keeping open

- Prompt caching mechanics: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Cost management (Claude Code): https://code.claude.com/docs/en/costs
- Why third-party layers break caching: https://www.mindstudio.ai/blog/anthropic-prompt-caching-claude-subscription-limits
- Token efficiency deep-dive: https://www.firecrawl.dev/blog/claude-code-token-efficiency
- LLMLingua family (only if lossy compression ever returns): https://github.com/microsoft/LLMLingua
