## Convenience tasks (no global installs; uses uv)

.PHONY: help lint fmt fmt-check typecheck test all

help:
	@echo "Available targets:"
	@echo "  lint       - Run ruff checks"
	@echo "  fmt        - Apply ruff formatting"
	@echo "  typecheck  - Run mypy on the repo"
	@echo "  test       - Run pytest"
	@echo "  all        - lint, typecheck, test"

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format --check .

typecheck:
	uv run mypy .

test:
	uv run pytest

all: fmt lint typecheck test
