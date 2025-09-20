# edge_cases — Input Spec

Create a small deck to cover edge cases:

- Slide 1 (no title)
  - Empty slide (no shapes) — should render a slide header with no sections.

- Slide 2 (Title: "Special Chars")
  - Text: include characters like: `|`, `*`, `_`, backticks, and multi-line paragraphs.

- Slide 3 (Title: "Deep Bullets")
  - Bullets at levels 0, 1, 2, 3.

- Slide 4 (Title: "Table Weird")
  - A table with a newline in a cell (e.g., "B\nB") and a pipe (e.g., "A|A").

Save as `edge_cases.pptx` in this folder.

Expected Markdown behavior (sketch):
- Special characters in table cells are escaped (e.g., `|` becomes `\|`).
- Multi-line text appears as separate lines in the Text section.
- Bullets are indented by two spaces per level.
- Ragged rows are padded with empty cells.
