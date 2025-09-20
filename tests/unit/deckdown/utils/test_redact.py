from __future__ import annotations

from re import Pattern

from deckdown.utils.redact import Redactor, redact_text


def test_redactor_apply_default() -> None:
    r = Redactor.from_strings([r"secret", r"token\d+"])
    out = r.apply("This secret is token123.")
    assert out == "This [REDACTED] is [REDACTED]."


def test_redact_text_mixed_patterns() -> None:
    import re

    compiled: Pattern[str] = re.compile(r"email: \S+")
    out = redact_text("email: a@b.com and SECRET", patterns=[compiled, r"SECRET"], replacement="█")
    assert out == "█ and █"
