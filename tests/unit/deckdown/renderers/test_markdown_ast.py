from __future__ import annotations

from deckdown.ast import (
    BBox,
    Paragraph,
    SlideDoc,
    SlideModel,
    SlideSize,
    TextPayload,
    TextRun,
    TextShape,
    ShapeKind,
)
from deckdown.models import Deck, Slide, TextBlock
from deckdown.renderers.markdown import MarkdownRenderer


def _make_slide_doc() -> SlideDoc:
    bbox = BBox(
        x_emu=100,
        y_emu=200,
        w_emu=300,
        h_emu=400,
        x_norm=0.1,
        y_norm=0.2,
        w_norm=0.3,
        h_norm=0.4,
    )
    text_shape = TextShape(
        id="shape-1",
        kind=ShapeKind.TEXT,
        bbox=bbox,
        z=0,
        text=TextPayload(
            paras=(
                Paragraph(
                    runs=(TextRun(text="Hello"),),
                ),
            ),
        ),
    )
    slide_model = SlideModel(
        index=1,
        size=SlideSize(width_emu=9144000, height_emu=5143500),
        shapes=(text_shape,),
    )
    return SlideDoc(slide=slide_model)


def test_renderer_emits_slide_doc_json_block() -> None:
    slide = Slide(index=1, title="T", text_blocks=(TextBlock(text="A"),))
    deck = Deck(file="s.pptx", title=None, slides=(slide,))
    doc = _make_slide_doc()

    md = MarkdownRenderer().render(deck, ast_per_slide={1: doc})

    assert "```json" in md and md.strip().endswith("```")
    json_payload = md.split("```json\n", 1)[1].split("\n```", 1)[0]
    assert json_payload == doc.model_dump_json(indent=2, ensure_ascii=False)


def test_slide_doc_json_block_includes_normalized_bbox() -> None:
    slide = Slide(index=1, title="T", text_blocks=(TextBlock(text="A"),))
    deck = Deck(file="deck.pptx", title=None, slides=(slide,))
    doc = _make_slide_doc()

    md = MarkdownRenderer().render(deck, ast_per_slide={1: doc})
    json_payload = md.split("```json\n", 1)[1].split("\n```", 1)[0]

    assert '"x_norm": 0.1' in json_payload
    assert '"y_norm": 0.2' in json_payload
    assert '"w_norm": 0.3' in json_payload
    assert '"h_norm": 0.4' in json_payload


def test_slide_doc_json_block_is_deterministic() -> None:
    slide = Slide(index=1, title="T", text_blocks=(TextBlock(text="A"),))
    deck = Deck(file="s.pptx", title=None, slides=(slide,))
    doc = _make_slide_doc()
    renderer = MarkdownRenderer()

    first = renderer.render(deck, ast_per_slide={1: doc})
    second = renderer.render(deck, ast_per_slide={1: doc})

    assert first == second


def test_renderer_accepts_plain_dict_ast_for_compatibility() -> None:
    slide = Slide(index=1, title="T", text_blocks=(TextBlock(text="A"),))
    deck = Deck(file="s.pptx", title=None, slides=(slide,))
    ast = {
        1: {
            "version": "deckdown-1",
            "slide": {"index": 1, "size": {"width_emu": 1, "height_emu": 1}, "shapes": []},
        }
    }

    md = MarkdownRenderer().render(deck, ast_per_slide=ast)

    assert '"version": "deckdown-1"' in md
