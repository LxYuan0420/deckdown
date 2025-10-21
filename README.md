DeckDown — PPTX ⇆ Markdown (AST)

Quick start
- Extract: `uv run deckdown extract deck.pptx -o deck.md`
- Validate: `uv run deckdown validate deck.md`
- Preview: `uv run deckdown preview deck.md -o preview.html`
- Assemble: `uv run deckdown assemble deck.md -o out.pptx`
- Schema: `uv run deckdown schema -o schema.json`

What it does
- Produces a single Markdown file with per-slide fenced JSON blocks (AST) that preserve:
  - Positions (x/y/w/h in EMU + normalized), z-order, grouping
  - Text (paragraphs/runs, basic styles), images (as data URLs), tables (grid + merges)
  - Charts (type, categories/series, colors; axes metadata; per-point colors; scatter/bubble assembly)
- Reassembles a PPTX from that AST (text, images, tables, basic/line shapes, charts).
- Renders an absolute-position HTML preview for quick visual checks.

Dev tips
- Run tests: `uv run pytest -q`
- Lint/format: `make fix`
- Type check: `make typecheck`
