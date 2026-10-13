.PHONY: test lint lint-fix format goldens \
        rs-test rs-lint rs-format

# Python is the main implementation. A Rust skeleton is parked in rust/ (see the
# parking lot in the schedule); its commands are prefixed with rs-.

test:
	uv run pytest

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .

goldens:
	echo "no golden harness runner yet (M3)"

# Parked Rust skeleton
RUST = --manifest-path rust/Cargo.toml

rs-test:
	cargo test $(RUST)

rs-lint:
	cargo clippy $(RUST) --all-targets -- -D warnings

rs-format:
	cargo fmt $(RUST)
