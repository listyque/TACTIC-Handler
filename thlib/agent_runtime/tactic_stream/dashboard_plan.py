"""Portable dashboard bricks shared by agent schemas and native server commands."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DashboardFilter(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    column: str = Field(min_length=1, max_length=128)
    relation: Literal['=', '!=', '<', '<=', '>', '>=', 'like'] = '='
    value: str | int | float | bool | None


class DashboardPageFilter(DashboardFilter):
    name: str = Field(pattern=r'^[a-z][a-z0-9_]{0,47}$')
    title: str = Field(min_length=1, max_length=256)
    search_type: str = Field(min_length=1, max_length=256)
    enabled: bool = False


class DashboardFilterValue(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    enabled: bool
    value: str | int | float | bool | None


class DashboardGrouping(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    column: str = Field(min_length=1, max_length=128)
    title: str = Field(default='', max_length=256)
    period: Literal['value', 'year', 'month', 'day'] = 'value'


class DashboardAggregate(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: str = Field(pattern=r'^[a-z][a-z0-9_]{0,47}$')
    title: str = Field(min_length=1, max_length=256)
    function: Literal['count', 'sum', 'avg', 'min', 'max'] = 'count'
    column: str = Field(default='', max_length=128)


class DashboardAppearance(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    fill: str = Field(default='transparent', pattern=r'^(transparent|panel|workspace|surfaceContainerLow|#[0-9a-fA-F]{6})$')
    stroke: str = Field(default='outlineVariant', pattern=r'^(outlineVariant|contentAccent|transparent|#[0-9a-fA-F]{6})$')
    stroke_width: int = Field(default=0, ge=0, le=8)
    radius: int = Field(default=0, ge=0, le=48)
    shadow: bool = False
    animate: bool = False


class DashboardSizing(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    width_mode: Literal['auto', 'fixed', 'fill', 'content'] = 'auto'
    height_mode: Literal['auto', 'fixed', 'fill', 'content'] = 'auto'
    min_width: int = Field(default=0, ge=0, le=2400)
    max_width: int | None = Field(default=None, ge=40, le=2400)
    min_height: int = Field(default=0, ge=0, le=1600)
    max_height: int | None = Field(default=None, ge=24, le=1600)

    @model_validator(mode='after')
    def check_ranges(self):
        for axis in ('width', 'height'):
            maximum = getattr(self, 'max_' + axis)
            if maximum is not None and maximum < getattr(self, 'min_' + axis):
                raise ValueError('Maximum size must not be smaller than minimum size')
        return self


class DashboardBlock(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    region: Literal['header', 'content', 'footer'] = 'content'
    kind: Literal['row', 'column', 'text', 'markdown', 'metric', 'table', 'items', 'details', 'link', 'chart', 'summary', 'grid', 'heading', 'icon', 'image', 'button', 'divider', 'spacer', 'field', 'form', 'action']
    title: str = Field(default='', max_length=256)
    text: str = Field(default='', max_length=65536)
    source_key: str = Field(default='', max_length=2048)
    field: str = Field(default='', max_length=128)
    binding: Literal['auto', 'static', 'project', 'selection', 'record'] = 'auto'
    search_type: str = Field(default='', max_length=256)
    view: str = Field(default='table', pattern=r'^[A-Za-z_][\w.@-]{0,127}$')
    filters: list[DashboardFilter] = Field(default_factory=list, max_length=32)
    page_filters: dict[str, str] | None = Field(default=None, max_length=8)
    group_by: list[DashboardGrouping] = Field(default_factory=list, max_length=3)
    aggregates: list[DashboardAggregate] = Field(default_factory=list, max_length=8)
    measure: str = Field(default='', max_length=48)
    group_limit: int = Field(default=50, ge=1, le=100)
    group_order: Literal['group', 'value_asc', 'value_desc'] = 'group'
    href: str = Field(default='', max_length=2048)
    weight: int = Field(default=1, ge=1, le=12)
    width: int | None = Field(default=None, ge=40, le=2400)
    height: int | None = Field(default=None, ge=24, le=1600)
    padding: list[Annotated[int, Field(ge=0, le=256)]] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)
    margin: list[Annotated[int, Field(ge=0, le=256)]] = Field(default_factory=lambda: [0, 0, 0, 0], min_length=4, max_length=4)
    gap: int = Field(default=8, ge=0, le=128)
    offset_x: int = Field(default=0, ge=-2400, le=2400)
    offset_y: int = Field(default=0, ge=-1600, le=1600)
    appearance: DashboardAppearance = Field(default_factory=DashboardAppearance)
    sizing: DashboardSizing = Field(default_factory=DashboardSizing)
    columns: int = Field(default=3, ge=1, le=12)
    min_cell_width: int = Field(default=200, ge=80, le=1200)
    row_height: int = Field(default=120, ge=40, le=800)
    column_span: int = Field(default=1, ge=1, le=12)
    row_span: int = Field(default=1, ge=1, le=12)
    collapse_width: int = Field(default=600, ge=0, le=2400)
    text_role: Literal['auto', 'caption', 'body', 'bodyLarge', 'title', 'heading', 'display', 'statistic', 'hero'] = 'auto'
    text_align: Literal['left', 'center', 'right'] = 'left'
    text_color: str = Field(default='auto', pattern=r'^(auto|primaryText|secondaryText|contentAccent|error|#[0-9a-fA-F]{6})$')
    text_weight: Literal[400, 600, 700] = 400
    icon: str = Field(default='', max_length=128, pattern=r'^[A-Za-z0-9_./:-]*$')
    icon_size: int = Field(default=32, ge=16, le=128)
    image_fit: Literal['cover', 'contain'] = 'contain'
    button_style: Literal['normal', 'primary', 'tonal'] = 'normal'
    fields: list[str] = Field(default_factory=list, max_length=16)
    edit_view: str = Field(default='edit', pattern=r'^[A-Za-z_][\w.@-]{0,127}$')
    format: Literal['plain', 'badge', 'progress', 'date', 'datetime', 'number'] = 'plain'
    suffix: str = Field(default='', max_length=32)
    native_action: Literal['details', 'edit', 'notes', 'copy_link', 'refresh'] = 'details'
    controls: list[Literal['search', 'searchLimit', 'shelf', 'selection', 'gear', 'insert']] | None = Field(default=None, max_length=6)
    children: list['DashboardBlock'] = Field(default_factory=list, max_length=32)


class DashboardDocument(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    name: str = Field(pattern=r'^[a-z][a-z0-9_]{0,47}$')
    title: str = Field(min_length=1, max_length=256)
    filters: list[DashboardPageFilter] = Field(default_factory=list, max_length=8)
    blocks: list[DashboardBlock] = Field(min_length=0, max_length=32)
