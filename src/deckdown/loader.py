from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pptx import Presentation


@dataclass(frozen=True)
class Loader:
    path: str

    def presentation(self) -> Any:  # noqa: ANN401 - external lib type
        return Presentation(self.path)

    # No extra helpers; callers can use prs.slides directly.
