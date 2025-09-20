## Convenience tasks (no global installs; uses uv)

.PHONY: help lint fmt fmt-check lint-fix fix typecheck test coverage coverage-xml coverage-html clean dev-symlink dev-symlink-clean all

help:
	@echo "Available targets:"
	@echo "  fmt            - Apply ruff formatting"
	@echo "  fmt-check      - Check formatting only (no changes)"
	@echo "  lint           - Run ruff checks"
	@echo "  lint-fix       - Run ruff with --fix (auto-fixable rules)"
	@echo "  fix            - Auto-fix (lint-fix) then format"
	@echo "  typecheck      - Run mypy on the repo"
	@echo "  test           - Run pytest"
	@echo "  coverage       - Run pytest with coverage (term-missing)"
	@echo "  coverage-xml   - Generate coverage.xml (CI integrations)"
	@echo "  coverage-html  - Generate HTML coverage report in htmlcov/"
	@echo "  clean          - Remove caches and coverage artifacts"
	@echo "  dev-symlink    - Create deckdown -> src/deckdown symlink for editor jumps"
	@echo "  dev-symlink-clean - Remove the symlink if present"
	@echo "  all            - fmt, lint, typecheck, test"

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix

fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format --check .

fix: lint-fix fmt

typecheck:
	uv run mypy .

test:
	uv run pytest

# Coverage requires pytest-cov to be installed in the env.
coverage:
	uv run pytest --cov=deckdown --cov-report=term-missing:skip-covered

coverage-xml:
	uv run pytest --cov=deckdown --cov-report=xml

coverage-html:
	uv run pytest --cov=deckdown --cov-report=html

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage* htmlcov coverage.xml

dev-symlink:
	@if [ -L deckdown ]; then \
		echo "Symlink 'deckdown' already exists"; \
	elif [ -e deckdown ]; then \
		echo "Path 'deckdown' exists and is not a symlink. Refusing."; exit 1; \
	else \
		ln -s src/deckdown deckdown && echo "Created symlink deckdown -> src/deckdown"; \
	fi

dev-symlink-clean:
	@if [ -L deckdown ]; then rm deckdown && echo "Removed symlink 'deckdown'"; else echo "No 'deckdown' symlink to remove"; fi

all: fmt lint typecheck test
