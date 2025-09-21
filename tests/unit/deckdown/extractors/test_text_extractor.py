from __future__ import annotations

from pathlib import Path

from deckdown.extractors.text import extract_deck_text
from deckdown.renderers.markdown import MarkdownRenderer


def _make_text_basic(tmp: Path) -> Path:
    # Generate a tiny deck similar to data/samples/text_basic
    from pptx import Presentation

    out = tmp / "t.pptx"
    prs = Presentation()
    layout = prs.slide_layouts[1]

    # Slide 1
    s1 = prs.slides.add_slide(layout)
    s1.shapes.title.text = "Intro"
    tf = s1.placeholders[1].text_frame
    tf.clear()
    tf.paragraphs[0].text = "Welcome to DeckDown"
    p = tf.add_paragraph()
    p.text = "Goals: Clean Markdown from PPTX"
    p = tf.add_paragraph()
    p.text = "Item 1"
    p.level = 0
    p = tf.add_paragraph()
    p.text = "Sub 1"
    p.level = 1

    # Slide 2
    s2 = prs.slides.add_slide(layout)
    s2.shapes.title.text = "Details"
    tf2 = s2.placeholders[1].text_frame
    tf2.clear()
    tf2.paragraphs[0].text = "Alpha"
    p = tf2.add_paragraph()
    p.text = "Beta"

    # Slide 3
    s3 = prs.slides.add_slide(layout)
    tf3 = s3.placeholders[1].text_frame
    tf3.clear()
    tf3.paragraphs[0].text = "Closing"

    prs.save(str(out))
    return out


def test_extract_deck_text_basic(tmp_path: Path) -> None:
    pptx = _make_text_basic(tmp_path)
    deck = extract_deck_text(str(pptx))
    md = MarkdownRenderer().render(deck)
    expected = (
        "# Intro\n\n"
        "## Slide 1 — Intro\n\n"
        "### Text\n"
        "Welcome to DeckDown\n"
        "Goals: Clean Markdown from PPTX\n\n"
        "### Bullets\n"
        "- Item 1\n"
        "  - Sub 1\n\n"
        "## Slide 2 — Details\n\n"
        "### Text\n"
        "Alpha\n"
        "Beta\n\n"
        "## Slide 3 — Untitled\n\n"
        "### Text\n"
        "Closing\n"
    )
    assert md == expected

