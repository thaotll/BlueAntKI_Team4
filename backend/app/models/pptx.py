"""
Pydantic models for PowerPoint presentation structure.
Data-driven approach: models define WHAT to render, not HOW.
"""

from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


# =============================================================================
# Color & Typography Models
# =============================================================================


class RgbColor(BaseModel):
    """RGB color specification."""

    r: int = Field(..., ge=0, le=255)
    g: int = Field(..., ge=0, le=255)
    b: int = Field(..., ge=0, le=255)

    @classmethod
    def from_hex(cls, hex_color: str) -> "RgbColor":
        """Create from hex string like '#016bd5' or '016bd5'."""
        hex_color = hex_color.lstrip("#")
        return cls(
            r=int(hex_color[0:2], 16),
            g=int(hex_color[2:4], 16),
            b=int(hex_color[4:6], 16),
        )


class TextStyle(BaseModel):
    """Text styling configuration."""

    font_name: str = "Calibri"
    font_size_pt: int = 12
    bold: bool = False
    italic: bool = False
    color: Optional[RgbColor] = None


class Position(BaseModel):
    """Position and size in inches."""

    x: float = Field(..., description="X position in inches")
    y: float = Field(..., description="Y position in inches")
    width: float = Field(..., description="Width in inches")
    height: float = Field(..., description="Height in inches")


# =============================================================================
# Text Models
# =============================================================================


class TextRun(BaseModel):
    """A run of text with consistent styling."""

    text: str
    style: Optional[TextStyle] = None  # None = inherit from paragraph


class TextParagraph(BaseModel):
    """A paragraph containing one or more text runs."""

    runs: List[TextRun] = Field(default_factory=list)
    alignment: Literal["left", "center", "right"] = "left"
    space_after_pt: int = 0

    @classmethod
    def simple(cls, text: str, alignment: Literal["left", "center", "right"] = "left") -> "TextParagraph":
        """Create simple single-run paragraph."""
        return cls(runs=[TextRun(text=text)], alignment=alignment)


# =============================================================================
# Shape Models
# =============================================================================


class TextBoxShape(BaseModel):
    """A text box shape."""

    shape_type: Literal["textbox"] = "textbox"
    position: Position
    paragraphs: List[TextParagraph] = Field(default_factory=list)
    default_style: Optional[TextStyle] = None  # Applied to runs without explicit style


class ImageShape(BaseModel):
    """An image shape."""

    shape_type: Literal["image"] = "image"
    position: Position
    image_path: Optional[str] = None
    image_bytes: Optional[bytes] = None


class RectangleShape(BaseModel):
    """A rectangle shape for decorative elements."""

    shape_type: Literal["rectangle"] = "rectangle"
    position: Position
    fill_color: Optional[RgbColor] = None
    line_color: Optional[RgbColor] = None
    line_width_pt: float = 0


# Union type for all shapes
ShapeModel = Union[TextBoxShape, ImageShape, RectangleShape]


# =============================================================================
# Slide Models
# =============================================================================


class SlideLayout(str, Enum):
    """Available slide layouts."""

    BLANK = "blank"  # Layout index 6 - full control
    TITLE = "title"  # Layout index 0 - title slide
    TITLE_CONTENT = "title_content"  # Layout index 1


class PptxSlideModel(BaseModel):
    """A single slide in the presentation."""

    layout: SlideLayout = SlideLayout.BLANK
    shapes: List[ShapeModel] = Field(default_factory=list)
    notes: Optional[str] = None  # Speaker notes


# =============================================================================
# Presentation Model
# =============================================================================


class PptxPresentationModel(BaseModel):
    """Complete presentation model."""

    title: str = Field(..., description="Presentation title (for metadata)")
    slides: List[PptxSlideModel] = Field(default_factory=list)

    # Presentation settings (16:9 widescreen default)
    width_inches: float = 13.333
    height_inches: float = 7.5

    # Theme/branding (for consistent styling)
    primary_color: RgbColor = Field(
        default_factory=lambda: RgbColor(r=1, g=107, b=213)
    )
    accent_color: RgbColor = Field(
        default_factory=lambda: RgbColor(r=0, g=141, b=202)
    )
    text_color: RgbColor = Field(
        default_factory=lambda: RgbColor(r=51, g=51, b=51)
    )
