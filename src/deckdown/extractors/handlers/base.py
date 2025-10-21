from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from deckdown.ast import Shape
from deckdown.extractors.context import ExtractContext


class ShapeHandler(ABC):
    @abstractmethod
    def supports(self, shape: Any) -> bool:  # noqa: ANN401
        ...

    @abstractmethod
    def build(self, shape: Any, *, z: int, ctx: ExtractContext) -> Optional[Shape]:  # noqa: ANN401
        ...

