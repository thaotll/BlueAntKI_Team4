"""
Pydantic models for Word document structure.
Data-driven approach: models define WHAT to render, not HOW.
"""

from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field

from app.models.pptx import RgbColor


# =============================================================================
# Enums
# =============================================================================


class HeadingLevel(int, Enum):
    """Heading levels for Word document."""

    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4


class ListStyle(str, Enum):
    """List styles for Word document."""

    BULLET = "bullet"
    NUMBER = "number"


class TableCellAlignment(str, Enum):
    """Cell alignment options."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


# =============================================================================
# Text Models
# =============================================================================


class DocxTextStyle(BaseModel):
    """Text styling configuration for Word documents."""

    font_name: str = "Calibri"
    font_size_pt: int = 11
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[RgbColor] = None
    highlight_color: Optional[str] = None  # e.g., "yellow", "green"


class DocxTextRun(BaseModel):
    """A run of text with consistent styling."""

    text: str
    style: Optional[DocxTextStyle] = None  # None = inherit from paragraph


class DocxParagraph(BaseModel):
    """A paragraph containing one or more text runs."""

    runs: List[DocxTextRun] = Field(default_factory=list)
    alignment: Literal["left", "center", "right", "justify"] = "left"
    space_before_pt: int = 0
    space_after_pt: int = 6
    first_line_indent_cm: float = 0.0

    @classmethod
    def simple(
        cls,
        text: str,
        alignment: Literal["left", "center", "right", "justify"] = "left",
        bold: bool = False,
        color: Optional[RgbColor] = None,
    ) -> "DocxParagraph":
        """Create simple single-run paragraph."""
        style = None
        if bold or color:
            style = DocxTextStyle(bold=bold, color=color)
        return cls(runs=[DocxTextRun(text=text, style=style)], alignment=alignment)


# =============================================================================
# Table Models
# =============================================================================


class DocxTableCell(BaseModel):
    """A single table cell."""

    content: str = ""
    bold: bool = False
    alignment: TableCellAlignment = TableCellAlignment.LEFT
    background_color: Optional[RgbColor] = None
    text_color: Optional[RgbColor] = None
    colspan: int = 1


class DocxTableRow(BaseModel):
    """A table row."""

    cells: List[DocxTableCell] = Field(default_factory=list)
    is_header: bool = False


class DocxTable(BaseModel):
    """A table in the document."""

    rows: List[DocxTableRow] = Field(default_factory=list)
    col_widths_cm: Optional[List[float]] = None  # Column widths in cm
    style_name: str = "Table Grid"  # Word table style


# =============================================================================
# List Models
# =============================================================================


class DocxListItem(BaseModel):
    """A single list item."""

    text: str
    bold: bool = False
    level: int = 0  # Nesting level (0 = top level)


class DocxList(BaseModel):
    """A list (bulleted or numbered)."""

    items: List[DocxListItem] = Field(default_factory=list)
    style: ListStyle = ListStyle.BULLET


# =============================================================================
# Section Models
# =============================================================================


class DocxHeading(BaseModel):
    """A heading in the document."""

    text: str
    level: HeadingLevel = HeadingLevel.H1
    color: Optional[RgbColor] = None


class DocxSection(BaseModel):
    """A logical section of the document."""

    heading: Optional[DocxHeading] = None
    paragraphs: List[DocxParagraph] = Field(default_factory=list)
    tables: List[DocxTable] = Field(default_factory=list)
    lists: List[DocxList] = Field(default_factory=list)

    # Content order tracking (for mixed content)
    # Format: [("paragraph", 0), ("table", 0), ("paragraph", 1), ...]
    content_order: List[tuple] = Field(default_factory=list)


# =============================================================================
# Document Model
# =============================================================================


class DocxDocumentModel(BaseModel):
    """Complete Word document model."""

    title: str = Field(..., description="Document title (for metadata)")
    author: str = Field(default="BlueAnt AI Analysis", description="Document author")

    # Document sections
    sections: List[DocxSection] = Field(default_factory=list)

    # Theme/branding (for consistent styling)
    primary_color: RgbColor = Field(
        default_factory=lambda: RgbColor(r=1, g=107, b=213)  # BlueAnt blue
    )
    accent_color: RgbColor = Field(
        default_factory=lambda: RgbColor(r=0, g=141, b=202)  # Light blue
    )
    text_color: RgbColor = Field(
        default_factory=lambda: RgbColor(r=51, g=51, b=51)  # Dark gray
    )

    # Status colors for traffic lights
    status_green: RgbColor = Field(
        default_factory=lambda: RgbColor(r=0, g=170, b=68)  # #00AA44
    )
    status_yellow: RgbColor = Field(
        default_factory=lambda: RgbColor(r=255, g=170, b=0)  # #FFAA00
    )
    status_red: RgbColor = Field(
        default_factory=lambda: RgbColor(r=204, g=0, b=0)  # #CC0000
    )
    status_gray: RgbColor = Field(
        default_factory=lambda: RgbColor(r=128, g=128, b=128)  # #808080
    )

