# OptimizedClaude

A local-first frontend for Claude Code. You talk to a small Ollama model running on your
own GPU; it routes, clarifies, and compiles your requests — and only clean, well-structured
prompts ever reach Claude. Fewer wasted turns, fewer wasted tokens, same subscription.

**Status: design phase.** No code yet — the engineering contract comes first.

## How it works

```
you ⇄ local 7–8B model (free)        route / clarify / compile
        ▼
   compiled task spec (you approve)
        ▼
   Claude Code session (headless, via claude-agent-sdk)
```

- Trivial questions are answered locally and never cost a Claude token.
- Vague requests get up to 3 clarifying questions — locally, for free — before Claude
  sees anything.
- Short mid-session follow-ups ("yes", "fix the test") pass straight through untouched.
- If the local layer is down, the tool degrades to a plain Claude Code wrapper. Your
  work is never blocked.
- Claude session history is never rewritten — prompt caching stays intact by design.

## Why not just compress prompts?

Anthropic's prompt caching is prefix-based and byte-exact: tools that rewrite conversation
history bust the cache and can make token usage *worse*. The expensive thing isn't prompt
length — it's wasted turns. This project attacks turns.

The metric that will be published here: **tokens and turns per completed task**,
before/after, on real work. No reel-math.

## Docs

- [`docs/design.md`](docs/design.md) — engineering design: requirements, architecture,
  routing policy, schemas, degradation matrix, test strategy.
- [`docs/roadmap.md`](docs/roadmap.md) — phases and milestones.

## Planned stack

Python 3.12 (uv), `claude-agent-sdk`, Ollama (qwen2.5:7b class on an 8GB GPU),
prompt_toolkit, pydantic, pytest.

## License

MIT — see [LICENSE](LICENSE).
