.PHONY: test lint lint-fix format goldens

test:
	uv run pytest

lint:
	uv run ruff check .


lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

goldens:
	echo "no golden harness yet (M3)"