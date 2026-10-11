.PHONY: test lint lint-fix format goldens build \
        py-test py-lint py-lint-fix py-format

# Rust is the main implementation (see docs/adr). Python is the reference version.
RUST = --manifest-path rust/Cargo.toml

test:
	cargo test $(RUST)

lint:
	cargo clippy $(RUST) --all-targets -- -D warnings

lint-fix:
	cargo clippy $(RUST) --fix --allow-dirty --all-targets

format:
	cargo fmt $(RUST)

build:
	cargo build $(RUST)

goldens:
	echo "no golden harness yet (M3)"

# Python reference version (tag: python-reference)
py-test:
	uv run pytest

py-lint:
	uv run ruff check .

py-lint-fix:
	uv run ruff check --fix .

py-format:
	uv run ruff format .
