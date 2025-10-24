from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _DictLikeFrozenModel(_FrozenModel):
    def get(self, key: str, default: Any = None) -> Any:
        return self.model_dump().get(key, default)

    def items(self):
        return self.model_dump().items()

    def keys(self):
        return self.model_dump().keys()

    def __contains__(self, key: str) -> bool:
        return key in self.model_dump()

    def __getitem__(self, key: str) -> Any:
        return self.model_dump()[key]


class ThemeRef(_FrozenModel):
    key: str
    tint: Optional[float] = Field(default=None, ge=-1.0, le=1.0)


class Color(_FrozenModel):
    resolved_rgb: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    model: Literal["srgb"] = "srgb"
    alpha: Optional[float] = None
    theme_ref: Optional[ThemeRef] = None


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


class FontSpec(_FrozenModel):
    family: Optional[str] = None
    size_pt: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    color: Optional[Color] = None


class TextRun(_FrozenModel):
    text: str
    font: Optional[FontSpec] = None


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


class CropSpec(_FrozenModel):
    left: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    right: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    top: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    bottom: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class PicturePayload(_FrozenModel):
    media: Media
    crop: Optional[CropSpec] = None
    opacity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    alt: Optional[str] = None


class PictureShape(ShapeBase):
    kind: Literal[ShapeKind.PICTURE]
    image: PicturePayload


class StrokeSpec(_FrozenModel):
    color: Optional[Color] = None
    width_pt: Optional[float] = None
    dash: Optional[str] = None


class FillSpec(_FrozenModel):
    color: Optional[Color] = None


class BasicStyle(_FrozenModel):
    fill: Optional[FillSpec] = None
    stroke: Optional[StrokeSpec] = None


class CellBorders(_DictLikeFrozenModel):
    left: Optional[StrokeSpec] = None
    right: Optional[StrokeSpec] = None
    top: Optional[StrokeSpec] = None
    bottom: Optional[StrokeSpec] = None


class TableCell(_FrozenModel):
    r: int
    c: int
    rowspan: int = 1
    colspan: int = 1
    text: TextPayload = Field(default_factory=TextPayload)
    fill: Optional[Color] = None
    borders: Optional[CellBorders] = None


class TablePayload(_FrozenModel):
    rows: int
    cols: int
    cells: tuple[TableCell, ...] = ()
    header_row: Optional[bool] = None


class TableShape(ShapeBase):
    kind: Literal[ShapeKind.TABLE]
    table: TablePayload


class ChartDataPoint(_DictLikeFrozenModel):
    idx: int
    color: Optional[Color] = None
    label: Optional[str] = None


class ChartDataLabelOptions(_DictLikeFrozenModel):
    show_value: Optional[bool] = None
    show_category_name: Optional[bool] = None
    show_series_name: Optional[bool] = None
    show_percentage: Optional[bool] = None
    position: Optional[str] = None
    number_format: Optional[str] = None


class ChartSeriesModel(_FrozenModel):
    name: Optional[str] = None
    values: tuple[float | None, ...] = ()
    color: Optional[Color] = None
    points: Optional[tuple[ChartDataPoint, ...]] = None
    x_values: Optional[tuple[float | None, ...]] = None
    sizes: Optional[tuple[float | None, ...]] = None
    labels: Optional[ChartDataLabelOptions] = None


class PlotAreaSpec(_DictLikeFrozenModel):
    has_data_labels: Optional[bool] = None
    has_legend: Optional[bool] = None
    legend_pos: Optional[Literal["right", "left", "top", "bottom"]] = None


class CategoryAxis(_DictLikeFrozenModel):
    title: Optional[str] = None


class ValueAxis(_DictLikeFrozenModel):
    title: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    major_unit: Optional[float] = None
    format_code: Optional[str] = None


class ChartAxes(_DictLikeFrozenModel):
    category: Optional[CategoryAxis] = None
    value: Optional[ValueAxis] = None


class ChartPayload(_FrozenModel):
    type: str
    subtype: Optional[str] = None
    categories: tuple[str | float, ...] = ()
    series: tuple[ChartSeriesModel, ...] = ()
    plot_area: Optional[PlotAreaSpec] = None
    axes: Optional[ChartAxes] = None
    style: Optional[int] = None
    snapshot: Optional[Media] = None


class ChartShape(ShapeBase):
    kind: Literal[ShapeKind.CHART]
    chart: ChartPayload


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


class SlideBackground(_DictLikeFrozenModel):
    color: Optional[Color] = None
    image: Optional[Media] = None


class SlideModel(_FrozenModel):
    index: int
    size: SlideSize
    shapes: tuple[Shape, ...] = ()
    background: Optional[SlideBackground] = None


class SlideDoc(_FrozenModel):
    version: Literal["deckdown-1"] = "deckdown-1"
    slide: SlideModel
