.PHONY: test lint goldens

test:
	uv run pytest

lint:
	uv run ruff check .

goldens:
	echo "no golden harness yet (M3)"