from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from re import Pattern

DEFAULT_REPLACEMENT = "[REDACTED]"


@dataclass(frozen=True)
class Redactor:
    """Immutable redactor that applies regex replacements in order.

    OOFP style: small immutable object encapsulating compiled patterns; methods are pure.
    """

    patterns: tuple[Pattern[str], ...]
    replacement: str = DEFAULT_REPLACEMENT

    def apply(self, text: str) -> str:
        """Return `text` with all patterns replaced by `replacement`, deterministically.

        - Applies patterns sequentially as provided.
        - Does not mutate input; returns a new string.
        """
        result = text
        for pat in self.patterns:
            result = pat.sub(self.replacement, result)
        return result

    @classmethod
    def from_strings(
        cls,
        patterns: Iterable[str],
        *,
        replacement: str = DEFAULT_REPLACEMENT,
        flags: int | re.RegexFlag = re.MULTILINE,
    ) -> Redactor:
        """Construct a Redactor from raw pattern strings.

        - Compiles patterns with provided flags (default MULTILINE).
        - Patterns are kept in given order.
        """
        compiled = tuple(re.compile(p, flags=flags) for p in patterns)
        return cls(patterns=compiled, replacement=replacement)


def redact_text(
    text: str,
    patterns: Iterable[str | Pattern[str]],
    *,
    replacement: str = DEFAULT_REPLACEMENT,
    flags: int | re.RegexFlag = re.MULTILINE,
) -> str:
    """Functional convenience: redact `text` using patterns.

    Accepts a mix of raw pattern strings and compiled regex patterns.
    """
    compiled: list[Pattern[str]] = []
    for p in patterns:
        if isinstance(p, str):
            compiled.append(re.compile(p, flags=flags))
        else:
            compiled.append(p)
    return Redactor(patterns=tuple(compiled), replacement=replacement).apply(text)

