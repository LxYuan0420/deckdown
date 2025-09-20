from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from deckdown.models import Bullet, Deck, Slide, Table, TextBlock


def test_construct_minimal_deck() -> None:
    tb = TextBlock(text="Hello world")
    b = Bullet(level=0, text="Item 1")
    t = Table(
        rows=(
            ("H1", "H2"),
            ("A", "B"),
        )
    )
    slide = Slide(index=1, title="Intro", text_blocks=(tb,), bullets=(b,), tables=(t,))
    deck = Deck(file="sample.pptx", title="Sample", slides=(slide,))

    assert deck.title == "Sample"
    assert len(deck.slides) == 1
    s0 = deck.slides[0]
    assert s0.index == 1
    assert s0.title == "Intro"
    assert s0.text_blocks[0].text == "Hello world"
    assert s0.bullets[0].level == 0
    assert s0.tables[0].rows[1][1] == "B"


def test_slide_and_bullet_validations() -> None:
    with pytest.raises(ValueError):
        _ = Slide(index=0)
    with pytest.raises(ValueError):
        _ = Bullet(level=-1, text="bad")


def test_immutability() -> None:
    s = Slide(index=1)
    with pytest.raises(FrozenInstanceError):
        s.index = 2  # type: ignore[misc]


def test_table_invalid_rows_type_raises() -> None:
    # Top-level rows container must be a tuple
    with pytest.raises(TypeError):
        _ = Table(rows=[("x",)])  # type: ignore[arg-type]
