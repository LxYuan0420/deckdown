# tables_basic — Input Spec

Create a small deck with 2 slides to exercise tables:

- Slide 1 (Title: "Tables")
  - One table with header row [H1, H2]
  - Body rows: ["A|A", "B"], ["C", "D"] — includes a cell with a pipe to test escaping

- Slide 2 (Title: "Ragged")
  - One table with header [H1, H2, H3]
  - Body row: ["A"] — shorter than header to test padding

Save as `tables_basic.pptx` in this folder.

See `expected.md` for the Markdown shape DeckDown should produce.
