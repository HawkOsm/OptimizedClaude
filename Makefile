.PHONY: test lint lint-fix goldens

test:
	uv run pytest

lint:
	uv run ruff check .


lint-fix:
	uv run ruff check --fix .

goldens:
	echo "no golden harness yet (M3)"