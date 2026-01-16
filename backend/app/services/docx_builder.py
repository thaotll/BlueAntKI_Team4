"""
Builds DocxDocumentModel from PortfolioAnalysis.
Responsible for content decisions and document composition.
"""

import logging
from datetime import datetime
from typing import List

from app.models.scoring import PortfolioAnalysis, ProjectScore
from app.models.pptx import RgbColor, ChartType, ChartShape, ChartDataPoint
from app.models.docx import (
    DocxDocumentModel,
    DocxSection,
    DocxHeading,
    DocxParagraph,
    DocxTextRun,
    DocxTextStyle,
    DocxList,
    DocxListItem,
    DocxImage,
    HeadingLevel,
    ListStyle,
)
from app.services.chart_generator import ChartGenerator, create_project_radar_chart

logger = logging.getLogger(__name__)


class DesignTokens:
    """Centralized design tokens - single source of truth for styling."""

    # Brand colors
    PRIMARY = RgbColor(r=1, g=107, b=213)  # BlueAnt blue #016bd5
    ACCENT = RgbColor(r=0, g=141, b=202)  # Light blue #008dca
    TEXT_DARK = RgbColor(r=51, g=51, b=51)  # Dark gray #333333
    TEXT_LIGHT = RgbColor(r=128, g=128, b=128)  # Gray #808080
    WHITE = RgbColor(r=255, g=255, b=255)

    # Status colors
    STATUS_GREEN = RgbColor(r=0, g=170, b=68)  # #00AA44
    STATUS_YELLOW = RgbColor(r=255, g=170, b=0)  # #FFAA00
    STATUS_RED = RgbColor(r=204, g=0, b=0)  # #CC0000
    STATUS_GRAY = RgbColor(r=128, g=128, b=128)  # #808080

    # Score colors (1-5 scale: green to red)
    SCORE_COLORS = {
        1: RgbColor(r=34, g=197, b=94),   # Green - sehr niedrig
        2: RgbColor(r=132, g=204, b=22),  # Light green - niedrig
        3: RgbColor(r=234, g=179, b=8),   # Yellow - mittel
        4: RgbColor(r=249, g=115, b=22),  # Orange - hoch
        5: RgbColor(r=239, g=68, b=68),   # Red - sehr hoch
    }

    # Typography
    FONT_FAMILY = "Calibri"
    TITLE_SIZE = 24
    HEADING1_SIZE = 18
    HEADING2_SIZE = 14
    HEADING3_SIZE = 12
    BODY_SIZE = 11
    CAPTION_SIZE = 9


class DocxBuilder:
    """
    Builds Word document models from portfolio analysis data.

    Usage:
        builder = DocxBuilder(analysis)
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
        self.chart_generator = ChartGenerator(dpi=120)  # Slightly lower DPI for Word

    def build(self) -> DocxDocumentModel:
        """Build complete document model."""
        logger.info(f"Building Word document for portfolio: {self.analysis.portfolio_name}")

        document = DocxDocumentModel(
            title=f"{self.analysis.portfolio_name} - Portfolio Analysis",
            author="BlueAnt AI Analysis",
            primary_color=self.tokens.PRIMARY,
            accent_color=self.tokens.ACCENT,
            text_color=self.tokens.TEXT_DARK,
        )

        # Build all sections (streamlined: no overview tables, no separate critical section)
        document.sections.append(self._build_title_section())
        document.sections.append(self._build_executive_summary_section())
        document.sections.append(self._build_project_details_section())

        if self.analysis.recommendations:
            document.sections.append(self._build_recommendations_section())

        logger.info(f"Built document with {len(document.sections)} sections")
        return document

    # =========================================================================
    # Section Builders
    # =========================================================================

    def _build_title_section(self) -> DocxSection:
        """Build the title section."""
        section = DocxSection()

        # Main title
        title_style = DocxTextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.TITLE_SIZE,
            bold=True,
            color=self.tokens.PRIMARY,
        )
        section.paragraphs.append(
            DocxParagraph(
                runs=[DocxTextRun(text=self.analysis.portfolio_name or "Portfolio Analysis", style=title_style)],
                alignment="center",
                space_after_pt=12,
            )
        )
        section.content_order.append(("paragraph", 0))

        # Subtitle
        subtitle_style = DocxTextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.HEADING2_SIZE,
            color=self.tokens.TEXT_DARK,
        )
        section.paragraphs.append(
            DocxParagraph(
                runs=[DocxTextRun(text=self._get_label("title_subtitle"), style=subtitle_style)],
                alignment="center",
                space_after_pt=24,
            )
        )
        section.content_order.append(("paragraph", 1))

        # Timestamp
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        timestamp_text = f"{self._get_label('generated')}: {timestamp}"
        timestamp_style = DocxTextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.CAPTION_SIZE,
            color=self.tokens.TEXT_LIGHT,
        )
        section.paragraphs.append(
            DocxParagraph(
                runs=[DocxTextRun(text=timestamp_text, style=timestamp_style)],
                alignment="center",
                space_after_pt=36,
            )
        )
        section.content_order.append(("paragraph", 2))

        return section

    def _build_executive_summary_section(self) -> DocxSection:
        """Build the executive summary section - text only, no tables."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("executive_summary"),
                level=HeadingLevel.H1,
                color=self.tokens.PRIMARY,
            )
        )

        # Executive summary text only
        summary_text = self.analysis.executive_summary or self._get_label("no_summary")
        section.paragraphs.append(DocxParagraph.simple(summary_text))
        section.content_order.append(("paragraph", 0))

        return section

    def _build_project_details_section(self) -> DocxSection:
        """Build detailed project assessments section with radar charts and flowing text."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("project_details"),
                level=HeadingLevel.H1,
                color=self.tokens.PRIMARY,
            )
        )

        para_idx = 0
        image_idx = 0

        # Sort projects by status color: red first, then yellow, then green
        def get_status_sort_key(status: str) -> int:
            """Return sort key for status: red=0, yellow=1, green=2, gray=3"""
            order = {"red": 0, "yellow": 1, "green": 2, "gray": 3}
            return order.get(status or "gray", 4)

        sorted_projects = sorted(
            self.analysis.project_scores,
            key=lambda p: (
                get_status_sort_key(p.status_color),
                -p.priority_score,  # Within same status, sort by priority descending
            ),
        )

        for project in sorted_projects:
            # Get ampel style (icon and color) based on project status
            ampel_icon, ampel_color, ampel_type = self._get_project_ampel_style(project)

            # Project heading with ampel icon only - no label suffixes (icon shows status)
            project_title = f"{ampel_icon} {project.project_name}"

            section.paragraphs.append(
                DocxParagraph.simple(
                    f"\n{project_title}",
                    bold=True,
                    color=ampel_color,
                )
            )
            section.content_order.append(("paragraph", para_idx))
            para_idx += 1

            # Project key facts as inline text
            info_parts = []
            if project.owner_name:
                info_parts.append(f"{self._get_label('owner')}: {project.owner_name}")
            info_parts.append(f"{self._get_label('progress')}: {project.progress_percent:.0f}%")
            if project.milestones_total > 0:
                milestone_text = f"{self._get_label('milestones')}: {project.milestones_completed}/{project.milestones_total}"
                if project.milestones_delayed > 0:
                    milestone_text += f" ({project.milestones_delayed} {self._get_label('delayed')})"
                info_parts.append(milestone_text)

            section.paragraphs.append(
                DocxParagraph.simple(" | ".join(info_parts), color=self.tokens.TEXT_LIGHT)
            )
            section.content_order.append(("paragraph", para_idx))
            para_idx += 1

            # Generate and add Radar Chart for U/I/C/R/DQ scores
            radar_chart = self._generate_project_radar_chart(project)
            if radar_chart:
                section.images.append(radar_chart)
                section.content_order.append(("image", image_idx))
                image_idx += 1

            # Detailed analysis as flowing text (primary content)
            if project.detailed_analysis:
                section.paragraphs.append(
                    DocxParagraph.simple(project.detailed_analysis)
                )
                section.content_order.append(("paragraph", para_idx))
                para_idx += 1
            elif project.summary:
                # Fallback to summary if no detailed analysis
                section.paragraphs.append(
                    DocxParagraph.simple(project.summary)
                )
                section.content_order.append(("paragraph", para_idx))
                para_idx += 1

        return section

    def _generate_project_radar_chart(self, project: ProjectScore) -> DocxImage:
        """Generate radar chart for project U/I/C/R/DQ scores."""
        try:
            # Get score values (default to 0 if not available)
            urgency = project.urgency.value if project.urgency else 0
            importance = project.importance.value if project.importance else 0
            complexity = project.complexity.value if project.complexity else 0
            risk = project.risk.value if project.risk else 0
            data_quality = project.data_quality.value if project.data_quality else 0
            
            # Skip if all scores are 0
            if urgency == 0 and importance == 0 and complexity == 0 and risk == 0 and data_quality == 0:
                return None
            
            # Create chart model
            chart_shape = create_project_radar_chart(
                project_name=project.project_name,
                urgency=urgency,
                importance=importance,
                complexity=complexity,
                risk=risk,
                data_quality=data_quality,
            )
            
            # Generate PNG bytes
            chart_bytes = self.chart_generator.generate(chart_shape)
            
            return DocxImage(
                image_bytes=chart_bytes,
                width_cm=8.0,  # Reasonable size for Word document
                alignment="center",
            )
        except Exception as e:
            logger.warning(f"Failed to generate radar chart for {project.project_name}: {e}")
            return None

    def _build_recommendations_section(self) -> DocxSection:
        """Build recommendations section with all recommendations."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("recommendations"),
                level=HeadingLevel.H1,
                color=self.tokens.PRIMARY,
            )
        )

        # Show all recommendations
        rec_items = [
            DocxListItem(text=rec, bold=False)
            for rec in self.analysis.recommendations
        ]

        if rec_items:
            section.lists.append(DocxList(items=rec_items, style=ListStyle.NUMBER))
            section.content_order.append(("list", 0))

        return section

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_status_color(self, status: str) -> RgbColor:
        """Get color for status."""
        status_colors = {
            "green": self.tokens.STATUS_GREEN,
            "yellow": self.tokens.STATUS_YELLOW,
            "red": self.tokens.STATUS_RED,
            "gray": self.tokens.STATUS_GRAY,
        }
        return status_colors.get(status.lower(), self.tokens.STATUS_GRAY)

    def _get_project_ampel_style(self, project: ProjectScore) -> tuple:
        """
        Get traffic light style for project header.
        Returns: (icon, color, status_type)
        - Positive (green): ✅
        - Warning (yellow): ⚠️
        - Critical (red): ❌
        """
        # Critical projects: RED
        if project.is_critical:
            return ("❌", self.tokens.STATUS_RED, "critical")

        # Check for status mismatch (yellow warning)
        if getattr(project, 'has_status_mismatch', False):
            return ("⚠️", self.tokens.STATUS_YELLOW, "warning")

        # Check status color
        status_color = getattr(project, 'status_color', 'gray')
        if status_color == "red":
            return ("❌", self.tokens.STATUS_RED, "critical")
        elif status_color == "yellow":
            return ("⚠️", self.tokens.STATUS_YELLOW, "warning")

        # High risk projects: YELLOW
        if project.risk.value >= 4:
            return ("⚠️", self.tokens.STATUS_YELLOW, "warning")

        # High urgency projects: YELLOW
        if project.urgency.value >= 4:
            return ("⚠️", self.tokens.STATUS_YELLOW, "warning")

        # Default positive (green)
        return ("✅", self.tokens.STATUS_GREEN, "positive")

    def _get_status_symbol(self, status: str) -> str:
        """Get symbol for status."""
        symbols = {
            "green": "●",
            "yellow": "●",
            "red": "●",
            "gray": "○",
        }
        return symbols.get(status.lower(), "○")

    def _get_label(self, key: str) -> str:
        """Get localized label."""
        labels = {
            "de": {
                "title_subtitle": "KI-gestützte Portfolioanalyse",
                "generated": "Generiert",
                "executive_summary": "Executive Summary",
                "portfolio_overview": "Portfolio-Übersicht",
                "project_details": "Projektanalysen im Detail",
                "critical_projects": "Kritische Projekte",
                "recommendations": "Handlungsempfehlungen",
                "key_metrics": "Kennzahlen",
                "metric": "Kennzahl",
                "value": "Wert",
                "total_projects": "Projekte gesamt",
                "project": "Projekt",
                "status": "Status",
                "no_projects": "Keine Projekte zur Analyse vorhanden.",
                "no_summary": "Keine Zusammenfassung verfügbar.",
                "owner": "Verantwortlich",
                "progress": "Fortschritt",
                "milestones": "Meilensteine",
                "delayed": "verzögert",
                "critical_projects_intro": "Die folgenden {count} Projekte wurden als kritisch eingestuft und erfordern besondere Aufmerksamkeit:",
                "critical_label": "Kritisch",
                "yes": "Ja",
                "no": "Nein",
            },
            "en": {
                "title_subtitle": "AI-Powered Portfolio Analysis",
                "generated": "Generated",
                "executive_summary": "Executive Summary",
                "portfolio_overview": "Portfolio Overview",
                "project_details": "Detailed Project Assessments",
                "critical_projects": "Critical Projects",
                "recommendations": "Recommendations",
                "key_metrics": "Key Metrics",
                "metric": "Metric",
                "value": "Value",
                "total_projects": "Total Projects",
                "project": "Project",
                "status": "Status",
                "no_projects": "No projects available for analysis.",
                "no_summary": "No summary available.",
                "owner": "Owner",
                "progress": "Progress",
                "milestones": "Milestones",
                "delayed": "delayed",
                "critical_projects_intro": "The following {count} projects have been identified as critical and require special attention:",
                "critical_label": "Critical",
                "yes": "Yes",
                "no": "No",
            },
        }
        return labels.get(self.language, labels["de"]).get(key, key)
