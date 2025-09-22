from __future__ import annotations

from re import Pattern

from deckdown.utils.redact import Redactor, redact_text


class TestRedact:
    def test_apply_default(self) -> None:
        # Arrange
        r = Redactor.from_strings([r"secret", r"token\d+"])
        # Act
        out = r.apply("This secret is token123.")
        # Assert
        assert out == "This [REDACTED] is [REDACTED]."

    def test_mixed_patterns(self) -> None:
        # Arrange
        import re

        compiled: Pattern[str] = re.compile(r"email: \S+")
        # Act
        out = redact_text(
            "email: a@b.com and SECRET",
            patterns=[compiled, r"SECRET"],
            replacement="█",
        )
        # Assert
        assert out == "█ and █"
