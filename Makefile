## Convenience tasks (uv-managed env; no global installs)

.PHONY: all help \
		fmt fmt-check lint lint-fix fix \
		typecheck test coverage coverage-xml coverage-html \
		generate-samples \
		install-cli \
		clean

# === Install & CLI ===
install-cli:
	uv pip install -e .

# === Dev: Format & Lint ===
fmt:
	uv run ruff format .

fmt-check:
	uv run ruff format --check .

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix

fix: lint-fix fmt

# === Dev: Type & Test ===
typecheck:
	uv run mypy .

test:
	uv run pytest

coverage:
	uv run pytest --cov=deckdown --cov-report=term-missing:skip-covered

coverage-xml:
	uv run pytest --cov=deckdown --cov-report=xml

coverage-html:
	uv run pytest --cov=deckdown --cov-report=html

# === Dev: Data & Samples ===
generate-samples:
	uv run python scripts/generate_samples.py --out data/samples

# === Clean ===
clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache .coverage* htmlcov coverage.xml

# === Meta ===
all: fmt lint typecheck test

help:
	@echo "Install & CLI:"
	@echo "  install-cli     - Install this project in editable mode"
	@echo
	@echo "Dev: Format & Lint:"
	@echo "  fmt             - Apply ruff formatting"
	@echo "  fmt-check       - Check formatting only"
	@echo "  lint            - Run ruff checks"
	@echo "  lint-fix        - Auto-fix fixable lint issues"
	@echo "  fix             - lint-fix then fmt"
	@echo
	@echo "Dev: Type & Test:"
	@echo "  typecheck       - Run mypy"
	@echo "  test            - Run pytest"
	@echo "  coverage        - Run pytest with coverage (term-missing)"
	@echo "  coverage-xml    - Generate coverage.xml"
	@echo "  coverage-html   - Generate HTML coverage report"
	@echo
	@echo "Dev: Data & Samples:"
	@echo "  generate-samples - Generate PPTX samples into data/samples"
	@echo
	@echo "Clean & Meta:"
	@echo "  clean           - Remove caches and coverage artifacts"
	@echo "  all             - fmt, lint, typecheck, test"

install-cli:
	uv pip install -e .
