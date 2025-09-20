# Data and Sample Decks

This folder contains sample scenarios and guidance for creating small PPTX decks to exercise DeckDown features. Binary assets (e.g., `.pptx`) are git-ignored here to keep the repo lean; only documentation and expectations are tracked.

Usage
- Auto-generate sample decks (requires python-pptx):
  - Install: `uv pip install python-pptx`
  - Generate all: `make generate-samples`
  - Or subset: `uv run python scripts/generate_samples.py --only text_basic tables_basic`
- Run the CLI on a sample, writing output alongside the input:
  - `uv run python -m deckdown.cli extract data/samples/text_basic/text_basic.pptx`
- Compare the produced `<basename>.md` with the `expected.md` sketch for that scenario.

Scenarios
- `samples/text_basic/` — Paragraphs and bullets with indentation levels.
- `samples/tables_basic/` — Tables, header rows, ragged rows, and cell escaping.
- `samples/charts_basic/` — Pie/column/line examples (for chart extraction milestone).
- `samples/diff_pair/v1` and `samples/diff_pair/v2` — Two versions of a deck to test diff output.
- `samples/notes/` — Slides with speaker notes (optional feature, later).
- `samples/edge_cases/` — Untitled slides, empty slides, deep bullets, special characters, and tricky table cells.

Notes
- Charts and diff are future milestones; their expectations document the intended Markdown, even if not implemented yet.
- Keep each deck small (1–3 slides per focused case) for fast iteration.
