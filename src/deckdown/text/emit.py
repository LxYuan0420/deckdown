from __future__ import annotations

from typing import Any

from deckdown.ast import TextPayload


def write_text_frame(tf: Any, text: TextPayload) -> None:  # noqa: ANN401
    tf.clear()
    first = True
    for p in text.paras:
        par = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        par.level = p.lvl
        par.text = "".join(run.text for run in p.runs)

