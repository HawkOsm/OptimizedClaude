# OptimizedClaude (`ocl`)

A local-model layer in front of Claude Code: a small local LLM routes, clarifies and
compiles requests, and only a clean prompt reaches Claude. Python 3.12, `uv`, `src/ocl/`.
Plan and design: `docs/building.md` (milestones), `docs/design.md`, `docs/schemas.md`.

## Working contract (this is a learning project)
- **The owner writes every line of `src/` and `tests/`.** Claude explains, plans and
  reviews. Do not write or paste fixed code for them, even if asked or if they are tired.
  Describe the shape in plain steps instead.
- **When stuck:** find the real cause by reproducing it, point at the file and line, name
  the concept, and link a good source (check it exists and is beginner-friendly). Do not
  explain the whole mechanism or hand over the fix.
- **Review by running:** run `make test` and `make lint`, reproduce suspected bugs with
  scratch scripts (never inside the project), report findings by severity, and say what
  the green tests do not cover. Correct your own earlier mistakes plainly.
- **Before coding:** work a tiny example by hand and write the steps in plain words, then
  the test, then the code.
- Use plain words and a small picture (text diagram) when explaining. Prefer one next
  step over a long list.
- Docs, schedules and notes may be written by Claude when asked.

## Commands
- `make test`, `make lint`, `make lint-fix`, `make format`, `make goldens`
- Run `make format` then `make lint-fix` before committing.

## Conventions
- Follow `docs/building.md` milestone order. A deviation from `docs/design.md` gets a
  short ADR in `docs/adr/` and an update to the design doc.
- Dependency direction: `core/` never imports `ui/`.
- pydantic v2 (`from pydantic import ...`, never `pydantic.v1`). Timestamps are
  timezone-aware UTC. Use `Literal` for fixed sets of values.
- Tests use `tmp_path` for files and explicit timestamps; avoid global state (a started
  freezegun clock must be stopped, so prefer its decorator or context manager).
- Router contract: a function `(message: str, session_active: bool) -> str` returning one
  of `PASSTHROUGH`, `TASK_NEW`, `TRIVIAL` (`META` for `/` commands).

## Git
- Small commits, one idea each, made when tests and lint are green. Formatting-only
  changes get their own commit.
- Stage files by name; never `git add .` or `-A` on a messy tree.
- Run `git status` before any command that could discard work. Stash or commit first.
- Do not commit `src/ocl/.config` (local placeholder) or `.claude/skills/` (ignored).
