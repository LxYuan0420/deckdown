# Scripts

This folder contains helper scripts for local development. Outputs are written under `data/` and are git‑ignored unless otherwise noted.

| Script | Purpose | Requirements | Example | Outputs |
|---|---|---|---|---|
| `generate_samples.py` | Generate sample PPTX decks for scenarios under `data/samples/` | Install `python-pptx` in your uv env | 1) `uv pip install python-pptx`  2) `make generate-samples`  3) Or: `uv run python scripts/generate_samples.py --only text_basic tables_basic` | `.pptx` files in `data/samples/<scenario>/`. Compare CLI output with `expected.md` in each scenario folder. |

Notes
- Generated `.pptx` files are ignored by git (see `data/.gitignore`).
- Regenerate safely; files are overwritten in place.
- For details of each scenario and expected Markdown, see `data/README.md` and the `expected.md` files in each scenario directory.
