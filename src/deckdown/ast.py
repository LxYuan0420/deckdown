from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Color(_FrozenModel):
    resolved_rgb: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    model: Literal["srgb"] = "srgb"
    alpha: Optional[float] = None
    theme_ref: Optional[dict] = None  # { key: "accent1|...", tint?: float }


class Media(_FrozenModel):
    data_url: Optional[str] = None
    ref: Optional[str] = None


class BBox(_FrozenModel):
    x_emu: int
    y_emu: int
    w_emu: int
    h_emu: int
    x_norm: float
    y_norm: float
    w_norm: float
    h_norm: float


class TextRun(_FrozenModel):
    text: str
    font: Optional[dict] = None  # { family?, size_pt?, bold?, italic?, underline?, color? }


class Paragraph(_FrozenModel):
    lvl: int = 0
    align: Optional[Literal["left", "center", "right", "justify"]] = None
    bullet: Optional[bool] = None
    num: Optional[bool] = None
    runs: tuple[TextRun, ...] = ()


class TextPayload(_FrozenModel):
    paras: tuple[Paragraph, ...] = ()
    autofit: Optional[Literal["none", "shrink", "resize"]] = None
    vertical_align: Optional[Literal["top", "mid", "bottom"]] = None


class ShapeKind(str, Enum):
    TEXT = "text_box"
    PICTURE = "picture"
    TABLE = "table"
    CHART = "chart"
    GROUP = "group"
    LINE = "line"
    BASIC = "shape_basic"


class ShapeBase(_FrozenModel):
    id: str
    kind: ShapeKind
    name: Optional[str] = None
    bbox: BBox
    z: int
    rotation: Optional[float] = None
    group: Optional[str] = None
    visible: bool = True


class TextShape(ShapeBase):
    kind: Literal[ShapeKind.TEXT]
    text: TextPayload


class PicturePayload(_FrozenModel):
    media: Media
    crop: Optional[dict] = None  # { left,right,top,bottom } (0–1)
    opacity: Optional[float] = None
    alt: Optional[str] = None


class PictureShape(ShapeBase):
    kind: Literal[ShapeKind.PICTURE]
    image: PicturePayload


class TableCell(_FrozenModel):
    r: int
    c: int
    rowspan: int = 1
    colspan: int = 1
    text: TextPayload = Field(default_factory=TextPayload)
    fill: Optional[Color] = None
    borders: Optional[dict] = None  # future: left/right/top/bottom


class TablePayload(_FrozenModel):
    rows: int
    cols: int
    cells: tuple[TableCell, ...] = ()
    header_row: Optional[bool] = None


class TableShape(ShapeBase):
    kind: Literal[ShapeKind.TABLE]
    table: TablePayload


Shape = TextShape | PictureShape | TableShape


class ChartSeriesModel(_FrozenModel):
    name: Optional[str] = None
    values: tuple[float | None, ...] = ()
    color: Optional[Color] = None
    points: Optional[tuple[dict, ...]] = None
    x_values: Optional[tuple[float | None, ...]] = None
    sizes: Optional[tuple[float | None, ...]] = None


class ChartPayload(_FrozenModel):
    type: str
    subtype: Optional[str] = None
    categories: tuple[str | float, ...] = ()
    series: tuple[ChartSeriesModel, ...] = ()
    plot_area: Optional[dict] = None  # { has_data_labels?, has_legend?, legend_pos? }
    axes: Optional[dict] = None
    style: Optional[int] = None
    snapshot: Optional[Media] = None


class ChartShape(ShapeBase):
    kind: Literal[ShapeKind.CHART]
    chart: ChartPayload

class StrokeSpec(_FrozenModel):
    color: Optional[Color] = None
    width_pt: Optional[float] = None
    dash: Optional[str] = None


class FillSpec(_FrozenModel):
    color: Optional[Color] = None


class BasicStyle(_FrozenModel):
    fill: Optional[FillSpec] = None
    stroke: Optional[StrokeSpec] = None


class BasicShape(ShapeBase):
    kind: Literal[ShapeKind.BASIC]
    geom: Optional[str] = None
    style: Optional[BasicStyle] = None
    text: Optional[TextPayload] = None


class LineShape(ShapeBase):
    kind: Literal[ShapeKind.LINE]
    style: Optional[BasicStyle] = None


class GroupShape(ShapeBase):
    kind: Literal[ShapeKind.GROUP]
    children: tuple[str, ...]


Shape = TextShape | PictureShape | TableShape | ChartShape | BasicShape | LineShape | GroupShape


class SlideSize(_FrozenModel):
    width_emu: int
    height_emu: int
    width_px: Optional[int] = None
    height_px: Optional[int] = None


class SlideModel(_FrozenModel):
    index: int
    size: SlideSize
    shapes: tuple[Shape, ...] = ()
    background: Optional[dict] = None


class SlideDoc(_FrozenModel):
    version: Literal["deckdown-1"] = "deckdown-1"
    slide: SlideModel
