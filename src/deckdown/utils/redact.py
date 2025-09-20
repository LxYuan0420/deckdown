from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from re import Pattern

DEFAULT_REPLACEMENT = "[REDACTED]"


@dataclass(frozen=True)
class Redactor:
    patterns: tuple[Pattern[str], ...]
    replacement: str = DEFAULT_REPLACEMENT

    def apply(self, text: str) -> str:
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
        compiled = tuple(re.compile(p, flags=flags) for p in patterns)
        return cls(patterns=compiled, replacement=replacement)


def redact_text(
    text: str,
    patterns: Iterable[str | Pattern[str]],
    *,
    replacement: str = DEFAULT_REPLACEMENT,
    flags: int | re.RegexFlag = re.MULTILINE,
) -> str:
    compiled: list[Pattern[str]] = []
    for p in patterns:
        if isinstance(p, str):
            compiled.append(re.compile(p, flags=flags))
        else:
            compiled.append(p)
    return Redactor(patterns=tuple(compiled), replacement=replacement).apply(text)
