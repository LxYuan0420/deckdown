DeckDown Planning (Markdown‑only, M1–M3)

Scope and Constraints (agreed)
- Output: Markdown only (no JSON for now).
- Features order: 1) Text, 2) Redaction, 3) Tables, 4) Charts, 5) Diff.
- Bullets: part of Text extraction.
- Notes: good‑to‑have later (after the above features).
- Images: out of scope for now.
- Slide range: not a priority (skip for now).
- Ordering heuristic: top‑to‑bottom, then left‑to‑right for shapes.
- Style: OOFP, SOLID, immutable dataclasses, stdlib‑first; strict and deterministic.
- Avoid generic utils: move redaction to a first‑class module (not under utils/).
- Data folder: yes, for development and testing samples.

Repo Structure (proposed)
- src/deckdown/
  - __init__.py (version)
  - cli.py (argparse CLI)
  - loader.py (open PPTX, enumerate slides/shapes)
  - models.py (frozen dataclasses: Deck, Slide, TextBlock, Bullet, Table, Chart[stub])
  - redact.py (immutable redactor; moved from utils/)
  - extractors/
    - text.py (text frames + bullet levels; top→bottom, left→right)
    - tables.py (normalize tables to list‑of‑lists)
    - charts.py (OOXML parser – later; requires lxml)
    - notes.py (later)
  - renderers/
    - markdown.py (deterministic writer; sections per slide)
    - diff.py (later; slide‑level change report)
- tests/
  - unit/ (module‑level unit tests)
  - fixtures/pptx/ (tiny decks for tests; versioned)
  - golden/<fixture_name>/ (expected .md outputs for goldens)
- data/
  - samples/ (larger decks for manual dev; git‑ignored)

Mermaid: Module Flow
```mermaid
flowchart TD
  CLI[deckdown.cli] --> LOADER[deckdown.loader]
  LOADER --> XTEXT[extractors.text]
  LOADER --> XTABLES[extractors.tables]
  LOADER --> XCHARTS[extractors.charts (later)]
  XTEXT --> RMD[renderers.markdown]
  XTABLES --> RMD
  XCHARTS --> RMD
  REDACT[deckdown.redact] --> XTEXT
  REDACT --> RMD
  DIFF[renderers.diff (later)] --> RMD
```

Mermaid: Core Models
```mermaid
classDiagram
  class Deck {
    +file: str
    +title: str?
    +slides: list[Slide]
  }
  class Slide {
    +index: int
    +title: str?
    +text_blocks: list[TextBlock]
    +bullets: list[Bullet]
    +tables: list[Table]
    +charts: list[Chart]  // later
    +notes: str?          // later
  }
  class TextBlock { +text: str }
  class Bullet { +level: int; +text: str }
  class Table { +rows: list[list[str]] }
  class Chart { +type: str; +series: ... }  // later

  Deck "1" o-- "*" Slide
  Slide "1" o-- "*" TextBlock
  Slide "1" o-- "*" Bullet
  Slide "1" o-- "*" Table
  Slide "1" o-- "*" Chart
```

Task Plan (tackle top‑to‑bottom)

0) Housekeeping and Conventions
- Confirm strict quality gates via `ruff`, `mypy`, `pytest` (already configured).
- Adopt deterministic formatting rules in markdown writer (no trailing spaces, stable blank lines).
- Define data folders:
  - `tests/fixtures/pptx/` (versioned tiny decks for unit/golden tests)
  - `tests/golden/<fixture_name>/` for expected `.md`
  - `data/samples/` for manual experiments (add to `.gitignore`)

1) Core Models Scaffold (no deps)
- Add `src/deckdown/models.py` with frozen dataclasses:
  - `Deck(file: str, title: str|None, slides: list[Slide])`
  - `Slide(index: int, title: str|None, text_blocks: list[TextBlock], bullets: list[Bullet], tables: list[Table], charts: list[Chart])`
  - `TextBlock(text: str)`
  - `Bullet(level: int, text: str)`
  - `Table(rows: list[list[str]])`
  - `Chart` (stub for later: `type: str`, `series`, `categories`)
- Acceptance:
  - `uv run mypy .` clean; `uv run ruff check .` clean.
  - Unit test constructs a minimal Deck and asserts shapes/types.

2) Markdown Renderer v0 (Markdown‑only)
- Add `src/deckdown/renderers/markdown.py` deterministic writer:
  - `# <deck title or filename>`
  - For each slide: `## Slide <N> — <Title or Untitled>`
  - Sections: Text, Bullets (indented per level), Tables (Markdown tables)
- No layout metadata for now; rely on stable shape ordering.
- Acceptance:
  - Golden test: construct a Deck in memory and compare `.md` output.

3) CLI Skeleton (argparse; no deps yet)
- Add `src/deckdown/cli.py` with command:
  - `deckdown extract <input.pptx> --md-out <file>`
  - Flags stubbed for `--with-notes` (ignored for now)
- Wire to renderer with a placeholder empty Deck (until extractors land).
- Acceptance:
  - Running CLI produces a minimal `.md` with deck header.

4) Loader + Text Extraction (Feature 1)
- Implement `src/deckdown/loader.py` using `python-pptx` to open and enumerate slides.
- Implement `src/deckdown/extractors/text.py`:
  - Extract text frames; normalize whitespace; capture bullet levels.
  - Order shapes by (top, then left) to approximate reading order.
  - Populate `Slide.text_blocks` and `Slide.bullets` accordingly.
- Integrate into CLI `extract` command; render markdown.
- Dependency request (host‑installed): `python-pptx`.
- Acceptance:
  - Fixture `tests/fixtures/pptx/text_basic.pptx` → stable `tests/golden/text_basic/deck.md`.
  - Unit tests cover bullet levels and ordering.

5) Redaction Refactor + Integration (Feature 2)
- Move redactor from `src/deckdown/utils/redact.py` to `src/deckdown/redact.py` (first‑class module).
- Update imports and unit tests accordingly (relocate tests to `tests/unit/test_redact.py`).
- Add CLI flags:
  - `--redact PATTERN` (repeatable)
  - `--redact-file FILE` (one pattern per line; `#` comments)
- Apply redaction to: slide titles, text blocks, bullets. (Notes later.)
- Acceptance:
  - Unit tests: deterministic ordered replacement; mixed compiled/raw patterns.
  - Fixture with secrets shows redacted `.md` golden.

6) Tables Extraction (Feature 3)
- Implement `src/deckdown/extractors/tables.py`:
  - Extract table shapes into `Table(rows: list[list[str]])` with normalized cell text.
  - Stable ordering aligned with shape order.
- Render as Markdown tables with consistent alignment and escaping.
- Acceptance:
  - Fixture `tests/fixtures/pptx/tables_basic.pptx` → golden `.md` with tables.
  - Unit tests for escaping, empty cells, and deterministic formatting.

7) Charts Extraction (Feature 4)
- Implement `src/deckdown/extractors/charts.py` parsing OOXML under `ppt/charts/*.xml`.
- Support common types: pie, column/bar, line (start simple; extend incrementally).
- Emit concise Markdown summaries per chart (type, series names, categories, values snapshot).
- Dependency request (host‑installed): `lxml`.
- Acceptance:
  - Fixtures for pie/column/line with known data → golden `.md` sections.
  - Unit tests validate parsed series/categories/values.

8) Diff Markdown (Feature 5)
- Implement `src/deckdown/renderers/diff.py`:
  - CLI: `deckdown diff <old.pptx> <new.pptx> --out diff.md`
  - Reuse extraction pipeline for both decks.
  - Report per‑slide changes: added/removed/modified for titles, text, bullets, tables, charts summary.
- Acceptance:
  - Two small fixtures produce stable `diff.md` highlighting changes.

9) Notes (Good‑to‑have, later)
- Implement `src/deckdown/extractors/notes.py` gated by `--with-notes`.
- Apply redaction to notes; render a Notes section per slide.
- Acceptance:
  - Fixture with notes shows correctly redacted Notes in `.md`.

10) Quality Gates & Polish
- Ensure deterministic whitespace and ordering; add tests where needed.
- Make targets (if not present): `fmt`, `lint`, `typecheck`, `test`, `all`.
- `uv run ruff check .`, `uv run mypy .`, `uv run pytest -q` all green.

Dependencies (host‑installed; no global installs)
- Text/Tables: `python-pptx`
- Charts: `lxml`
- No `Pillow`, no `mdformat` for now.

Out‑of‑Scope (current phase)
- Images and OCR.
- Slide range selection.
- JSON outputs.

Open Questions
- Redaction file format: allow inline comments and blank lines? (proposed yes)
- Markdown table formatting preference: left alignment vs. auto? (proposed left)
- Any need to preserve approximate layout metadata in Markdown (e.g., a fenced block)? (proposed skip for now; revisit later)

Commit Message Formatting (local convention)
- Avoid literal `\n` in commit bodies and avoid extra blank lines between bullets.
- Use a single `-m` with real newlines (preferred) or `-F <file>`:
  - Single `-m` with newlines (no extra spacing):
    - `git commit -m "$(printf '%s\n\n- Why: ...\n- What: ...\n- How to verify: ...\n' 'Add <concise change>')"`
  - Or write a small message file and run: `git commit -F /path/to/message.txt`
- Do not chain multiple `-m` flags per bullet — Git inserts a blank line between each, leading to double-spaced bodies.
