"""
Builds PptxPresentationModel from PortfolioAnalysis.
Responsible for content decisions and layout composition.
"""

import logging
from datetime import datetime

from app.models.scoring import PortfolioAnalysis
from app.models.pptx import (
    PptxPresentationModel,
    PptxSlideModel,
    TextBoxShape,
    TextParagraph,
    TextRun,
    TextStyle,
    Position,
    RgbColor,
    SlideLayout,
)

logger = logging.getLogger(__name__)


class DesignTokens:
    """Centralized design tokens - single source of truth for styling."""

    # Brand colors
    PRIMARY = RgbColor(r=1, g=107, b=213)  # BlueAnt blue #016bd5
    ACCENT = RgbColor(r=0, g=141, b=202)  # Light blue #008dca
    TEXT_DARK = RgbColor(r=51, g=51, b=51)  # Dark gray #333333
    TEXT_LIGHT = RgbColor(r=128, g=128, b=128)  # Gray #808080
    WHITE = RgbColor(r=255, g=255, b=255)

    # Typography
    FONT_FAMILY = "Calibri"
    TITLE_SIZE = 40
    SUBTITLE_SIZE = 20
    BODY_SIZE = 14
    CAPTION_SIZE = 12

    # Layout (16:9 slide = 13.333 x 7.5 inches)
    SLIDE_WIDTH = 13.333
    SLIDE_HEIGHT = 7.5
    MARGIN = 0.5
    CONTENT_WIDTH = 12.333  # SLIDE_WIDTH - 2 * MARGIN


class PptxBuilder:
    """
    Builds presentation models from portfolio analysis data.

    Usage:
        builder = PptxBuilder(analysis)
        model = builder.build()
    """

    def __init__(
        self,
        analysis: PortfolioAnalysis,
        language: str = "de",
    ):
        self.analysis = analysis
        self.language = language
        self.tokens = DesignTokens()

    def build(self) -> PptxPresentationModel:
        """Build complete presentation model."""
        logger.info(f"Building presentation for portfolio: {self.analysis.portfolio_name}")

        presentation = PptxPresentationModel(
            title=f"{self.analysis.portfolio_name} - Portfolio Analysis",
            primary_color=self.tokens.PRIMARY,
            accent_color=self.tokens.ACCENT,
            text_color=self.tokens.TEXT_DARK,
        )

        # Phase 1: Title slide only
        presentation.slides.append(self._build_title_slide())

        # Future phases will add more slides here:
        # presentation.slides.append(self._build_executive_summary_slide())
        # presentation.slides.append(self._build_statistics_slide())
        # etc.

        logger.info(f"Built presentation with {len(presentation.slides)} slides")
        return presentation

    def _build_title_slide(self) -> PptxSlideModel:
        """Build the title slide."""
        shapes = []

        # Main title
        title_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.TITLE_SIZE,
            bold=True,
            color=self.tokens.PRIMARY,
        )

        title_box = TextBoxShape(
            position=Position(x=0.5, y=2.5, width=12.333, height=1.2),
            paragraphs=[
                TextParagraph(
                    runs=[TextRun(text=self.analysis.portfolio_name or "Portfolio Analysis")],
                    alignment="center",
                )
            ],
            default_style=title_style,
        )
        shapes.append(title_box)

        # Subtitle
        subtitle_text = self._get_label("title_subtitle")
        subtitle_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.SUBTITLE_SIZE,
            bold=False,
            color=self.tokens.TEXT_DARK,
        )

        subtitle_box = TextBoxShape(
            position=Position(x=0.5, y=3.8, width=12.333, height=0.8),
            paragraphs=[
                TextParagraph(
                    runs=[TextRun(text=subtitle_text)],
                    alignment="center",
                )
            ],
            default_style=subtitle_style,
        )
        shapes.append(subtitle_box)

        # Timestamp
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        timestamp_text = f"{self._get_label('generated')}: {timestamp}"

        timestamp_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.CAPTION_SIZE,
            bold=False,
            color=self.tokens.TEXT_LIGHT,
        )

        timestamp_box = TextBoxShape(
            position=Position(x=0.5, y=6.5, width=12.333, height=0.5),
            paragraphs=[
                TextParagraph(
                    runs=[TextRun(text=timestamp_text)],
                    alignment="center",
                )
            ],
            default_style=timestamp_style,
        )
        shapes.append(timestamp_box)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
        )

    def _get_label(self, key: str) -> str:
        """Get localized label."""
        labels = {
            "de": {
                "title_subtitle": "KI-gestutzte Portfolioanalyse (U/I/C/R/DQ)",
                "generated": "Generiert",
                "executive_summary": "Executive Summary",
                "portfolio_overview": "Portfolio-Ubersicht",
                "critical_projects": "Kritische Projekte",
                "recommendations": "Empfehlungen",
                "projects": "Projekte",
                "average": "Durchschnitt",
            },
            "en": {
                "title_subtitle": "AI-Powered Portfolio Analysis (U/I/C/R/DQ)",
                "generated": "Generated",
                "executive_summary": "Executive Summary",
                "portfolio_overview": "Portfolio Overview",
                "critical_projects": "Critical Projects",
                "recommendations": "Recommendations",
                "projects": "Projects",
                "average": "Average",
            },
        }
        return labels.get(self.language, labels["de"]).get(key, key)
