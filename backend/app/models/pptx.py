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


# =============================================================================
# Chart Models
# =============================================================================


class ChartType(str, Enum):
    """Supported chart types for visualization."""

    BAR = "bar"  # Vertical bar chart
    HORIZONTAL_BAR = "horizontal_bar"  # Horizontal bar chart
    PIE = "pie"  # Pie chart
    DONUT = "donut"  # Donut chart (pie with hole)
    SCATTER = "scatter"  # Scatter plot (e.g., Risk-Urgency matrix)
    RADAR = "radar"  # Radar/Spider chart for U/I/C/R/DQ profiles
    LINE = "line"  # Line chart
    STACKED_BAR = "stacked_bar"  # Stacked bar chart


class ChartDataPoint(BaseModel):
    """A single data point for charts."""

    label: str = Field(..., description="Label for this data point")
    value: float = Field(..., description="Numeric value")
    color: Optional[RgbColor] = None  # Optional custom color for this point


class ChartDataSeries(BaseModel):
    """A data series for multi-series charts."""

    name: str = Field(..., description="Series name for legend")
    values: List[float] = Field(default_factory=list, description="Numeric values")
    color: Optional[RgbColor] = None  # Optional custom color for this series


class ChartShape(BaseModel):
    """A chart shape for data visualization."""

    shape_type: Literal["chart"] = "chart"
    position: Optional[Position] = None  # Can be set later by builder
    chart_type: ChartType = Field(..., description="Type of chart to render")
    title: Optional[str] = None  # Chart title
    
    # For simple charts (bar, pie, etc.)
    data_points: List[ChartDataPoint] = Field(
        default_factory=list, description="Data points for simple charts"
    )
    
    # For multi-series charts (stacked bar, line, etc.)
    categories: List[str] = Field(
        default_factory=list, description="Category labels for x-axis"
    )
    series: List[ChartDataSeries] = Field(
        default_factory=list, description="Data series for multi-series charts"
    )
    
    # For scatter plots
    x_values: List[float] = Field(default_factory=list, description="X-axis values for scatter")
    y_values: List[float] = Field(default_factory=list, description="Y-axis values for scatter")
    point_labels: List[str] = Field(default_factory=list, description="Labels for scatter points")
    
    # Styling options
    show_legend: bool = True
    show_values: bool = True  # Show value labels on chart
    show_grid: bool = False
    
    # Axis labels (for bar/scatter charts)
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    
    # Pre-rendered chart (generated by chart_generator)
    rendered_image_bytes: Optional[bytes] = None


class TableCell(BaseModel):
    """A single cell in a table."""

    text: str = Field(..., description="Cell text content")
    style: Optional[TextStyle] = None
    background_color: Optional[RgbColor] = None
    colspan: int = 1
    rowspan: int = 1


class TableRow(BaseModel):
    """A row in a table."""

    cells: List[TableCell] = Field(default_factory=list)
    is_header: bool = False


class TableShape(BaseModel):
    """A table shape for structured data display."""

    shape_type: Literal["table"] = "table"
    position: Position
    rows: List[TableRow] = Field(default_factory=list)
    header_style: Optional[TextStyle] = None
    cell_style: Optional[TextStyle] = None
    header_background: Optional[RgbColor] = None
    alternating_row_color: Optional[RgbColor] = None


# Union type for all shapes
ShapeModel = Union[TextBoxShape, ImageShape, RectangleShape, ChartShape, TableShape]


# =============================================================================
# Slide Models
# =============================================================================


class SlideLayout(str, Enum):
    """Available slide layouts."""

    BLANK = "blank"  # Layout index 6 - full control
    TITLE = "title"  # Layout index 0 - title slide
    TITLE_CONTENT = "title_content"  # Layout index 1


class SlideType(str, Enum):
    """Semantic slide types for AI-generated structure."""

    TITLE = "title"  # Title slide
    EXECUTIVE_SUMMARY = "executive_summary"  # Key insights summary
    STATISTICS = "statistics"  # Portfolio statistics with charts
    CRITICAL_PROJECTS = "critical_projects"  # Critical projects overview
    PRIORITY_RANKING = "priority_ranking"  # Project priority ranking
    RISK_MATRIX = "risk_matrix"  # Risk-Urgency scatter plot
    SCORE_OVERVIEW = "score_overview"  # U/I/C/R/DQ score overview
    PROJECT_DETAIL = "project_detail"  # Single project details
    RISK_CLUSTERS = "risk_clusters"  # Risk cluster visualization
    RECOMMENDATIONS = "recommendations"  # Recommendations slide
    STATUS_DISTRIBUTION = "status_distribution"  # Status distribution pie chart


class VisualizationType(str, Enum):
    """Types of visualizations recommended by AI."""

    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    RADAR_CHART = "radar_chart"
    SCATTER_PLOT = "scatter_plot"
    TABLE = "table"
    METRIC_CARDS = "metric_cards"
    BULLET_POINTS = "bullet_points"


class SlideVisualization(BaseModel):
    """A visualization element recommended by AI for a slide."""

    visualization_type: VisualizationType
    data_source: str = Field(..., description="What data to visualize (e.g., 'avg_scores', 'critical_projects')")
    description: str = Field(..., description="Description of what this visualization shows")
    position_hint: Literal["full", "left", "right", "top", "bottom"] = "full"


class AISlideSpec(BaseModel):
    """AI-generated specification for a single slide."""

    slide_type: SlideType
    title: str
    subtitle: Optional[str] = None
    visualizations: List[SlideVisualization] = Field(default_factory=list)
    key_message: Optional[str] = None  # Main takeaway for this slide
    speaker_notes: Optional[str] = None


class AIPresentationStructure(BaseModel):
    """AI-generated presentation structure."""

    slides: List[AISlideSpec] = Field(default_factory=list)
    theme_suggestion: Optional[str] = None
    total_estimated_slides: int = 0


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
