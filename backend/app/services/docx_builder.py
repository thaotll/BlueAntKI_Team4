"""
Builds DocxDocumentModel from PortfolioAnalysis.
Responsible for content decisions and document composition.
"""

import logging
from datetime import datetime
from typing import List, Optional

from app.models.scoring import PortfolioAnalysis, ProjectScore
from app.models.pptx import RgbColor
from app.models.docx import (
    DocxDocumentModel,
    DocxSection,
    DocxHeading,
    DocxParagraph,
    DocxTextRun,
    DocxTextStyle,
    DocxTable,
    DocxTableRow,
    DocxTableCell,
    DocxList,
    DocxListItem,
    HeadingLevel,
    ListStyle,
    TableCellAlignment,
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

        # Build all sections
        document.sections.append(self._build_title_section())
        document.sections.append(self._build_executive_summary_section())
        document.sections.append(self._build_portfolio_overview_section())
        document.sections.append(self._build_project_details_section())

        if self.analysis.critical_projects:
            document.sections.append(self._build_critical_projects_section())

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
        """Build the executive summary section."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("executive_summary"),
                level=HeadingLevel.H1,
                color=self.tokens.PRIMARY,
            )
        )

        # Executive summary text
        summary_text = self.analysis.executive_summary or self._get_label("no_summary")
        section.paragraphs.append(DocxParagraph.simple(summary_text))
        section.content_order.append(("paragraph", 0))

        # Key metrics box
        section.paragraphs.append(
            DocxParagraph.simple(
                f"\n{self._get_label('key_metrics')}:",
                bold=True,
            )
        )
        section.content_order.append(("paragraph", 1))

        metrics_table = self._build_key_metrics_table()
        section.tables.append(metrics_table)
        section.content_order.append(("table", 0))

        return section

    def _build_key_metrics_table(self) -> DocxTable:
        """Build key metrics table."""
        rows = [
            DocxTableRow(
                cells=[
                    DocxTableCell(
                        content=self._get_label("metric"),
                        bold=True,
                        background_color=self.tokens.PRIMARY,
                        text_color=self.tokens.WHITE,
                    ),
                    DocxTableCell(
                        content=self._get_label("value"),
                        bold=True,
                        background_color=self.tokens.PRIMARY,
                        text_color=self.tokens.WHITE,
                        alignment=TableCellAlignment.CENTER,
                    ),
                ],
                is_header=True,
            ),
            DocxTableRow(
                cells=[
                    DocxTableCell(content=self._get_label("total_projects")),
                    DocxTableCell(
                        content=str(len(self.analysis.project_scores)),
                        alignment=TableCellAlignment.CENTER,
                    ),
                ]
            ),
            DocxTableRow(
                cells=[
                    DocxTableCell(content=self._get_label("critical_projects")),
                    DocxTableCell(
                        content=str(len(self.analysis.critical_projects)),
                        alignment=TableCellAlignment.CENTER,
                    ),
                ]
            ),
            DocxTableRow(
                cells=[
                    DocxTableCell(content=f"{self._get_label('avg_urgency')} (U)"),
                    DocxTableCell(
                        content=f"{self.analysis.avg_urgency:.1f}",
                        alignment=TableCellAlignment.CENTER,
                    ),
                ]
            ),
            DocxTableRow(
                cells=[
                    DocxTableCell(content=f"{self._get_label('avg_importance')} (I)"),
                    DocxTableCell(
                        content=f"{self.analysis.avg_importance:.1f}",
                        alignment=TableCellAlignment.CENTER,
                    ),
                ]
            ),
            DocxTableRow(
                cells=[
                    DocxTableCell(content=f"{self._get_label('avg_complexity')} (C)"),
                    DocxTableCell(
                        content=f"{self.analysis.avg_complexity:.1f}",
                        alignment=TableCellAlignment.CENTER,
                    ),
                ]
            ),
            DocxTableRow(
                cells=[
                    DocxTableCell(content=f"{self._get_label('avg_risk')} (R)"),
                    DocxTableCell(
                        content=f"{self.analysis.avg_risk:.1f}",
                        alignment=TableCellAlignment.CENTER,
                    ),
                ]
            ),
            DocxTableRow(
                cells=[
                    DocxTableCell(content=f"{self._get_label('avg_data_quality')} (DQ)"),
                    DocxTableCell(
                        content=f"{self.analysis.avg_data_quality:.1f}",
                        alignment=TableCellAlignment.CENTER,
                    ),
                ]
            ),
        ]

        return DocxTable(rows=rows, col_widths_cm=[8.0, 3.0])

    def _build_portfolio_overview_section(self) -> DocxSection:
        """Build the portfolio overview section."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("portfolio_overview"),
                level=HeadingLevel.H1,
                color=self.tokens.PRIMARY,
            )
        )

        # Projects overview table
        if self.analysis.project_scores:
            overview_table = self._build_projects_overview_table()
            section.tables.append(overview_table)
            section.content_order.append(("table", 0))

            # Add legend
            section.paragraphs.append(
                DocxParagraph.simple(
                    f"\n{self._get_label('score_legend')}: 1={self._get_label('very_low')}, "
                    f"2={self._get_label('low')}, 3={self._get_label('medium')}, "
                    f"4={self._get_label('high')}, 5={self._get_label('very_high')}",
                    color=self.tokens.TEXT_LIGHT,
                )
            )
            section.content_order.append(("paragraph", 0))
        else:
            section.paragraphs.append(
                DocxParagraph.simple(self._get_label("no_projects"))
            )
            section.content_order.append(("paragraph", 0))

        return section

    def _build_projects_overview_table(self) -> DocxTable:
        """Build projects overview table with scores."""
        header_row = DocxTableRow(
            cells=[
                DocxTableCell(
                    content=self._get_label("project"),
                    bold=True,
                    background_color=self.tokens.PRIMARY,
                    text_color=self.tokens.WHITE,
                ),
                DocxTableCell(
                    content="U",
                    bold=True,
                    background_color=self.tokens.PRIMARY,
                    text_color=self.tokens.WHITE,
                    alignment=TableCellAlignment.CENTER,
                ),
                DocxTableCell(
                    content="I",
                    bold=True,
                    background_color=self.tokens.PRIMARY,
                    text_color=self.tokens.WHITE,
                    alignment=TableCellAlignment.CENTER,
                ),
                DocxTableCell(
                    content="C",
                    bold=True,
                    background_color=self.tokens.PRIMARY,
                    text_color=self.tokens.WHITE,
                    alignment=TableCellAlignment.CENTER,
                ),
                DocxTableCell(
                    content="R",
                    bold=True,
                    background_color=self.tokens.PRIMARY,
                    text_color=self.tokens.WHITE,
                    alignment=TableCellAlignment.CENTER,
                ),
                DocxTableCell(
                    content="DQ",
                    bold=True,
                    background_color=self.tokens.PRIMARY,
                    text_color=self.tokens.WHITE,
                    alignment=TableCellAlignment.CENTER,
                ),
                DocxTableCell(
                    content=self._get_label("status"),
                    bold=True,
                    background_color=self.tokens.PRIMARY,
                    text_color=self.tokens.WHITE,
                    alignment=TableCellAlignment.CENTER,
                ),
            ],
            is_header=True,
        )

        rows = [header_row]

        for project in self.analysis.project_scores:
            status_color = self._get_status_color(project.status_color)
            status_symbol = self._get_status_symbol(project.status_color)

            row = DocxTableRow(
                cells=[
                    DocxTableCell(content=project.project_name),
                    DocxTableCell(
                        content=str(project.urgency.value),
                        alignment=TableCellAlignment.CENTER,
                    ),
                    DocxTableCell(
                        content=str(project.importance.value),
                        alignment=TableCellAlignment.CENTER,
                    ),
                    DocxTableCell(
                        content=str(project.complexity.value),
                        alignment=TableCellAlignment.CENTER,
                    ),
                    DocxTableCell(
                        content=str(project.risk.value),
                        alignment=TableCellAlignment.CENTER,
                    ),
                    DocxTableCell(
                        content=str(project.data_quality.value),
                        alignment=TableCellAlignment.CENTER,
                    ),
                    DocxTableCell(
                        content=status_symbol,
                        alignment=TableCellAlignment.CENTER,
                        text_color=status_color,
                        bold=True,
                    ),
                ]
            )
            rows.append(row)

        return DocxTable(rows=rows, col_widths_cm=[6.0, 1.5, 1.5, 1.5, 1.5, 1.5, 2.0])

    def _build_project_details_section(self) -> DocxSection:
        """Build detailed project assessments section."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("project_details"),
                level=HeadingLevel.H1,
                color=self.tokens.PRIMARY,
            )
        )

        para_idx = 0
        table_idx = 0

        for project in self.analysis.project_scores:
            # Project heading
            section.paragraphs.append(
                DocxParagraph.simple(
                    f"\n{project.project_name}",
                    bold=True,
                    color=self.tokens.ACCENT,
                )
            )
            section.content_order.append(("paragraph", para_idx))
            para_idx += 1

            # Project info
            info_parts = []
            if project.owner_name:
                info_parts.append(f"{self._get_label('owner')}: {project.owner_name}")
            info_parts.append(f"{self._get_label('progress')}: {project.progress_percent:.0f}%")
            if project.milestones_total > 0:
                info_parts.append(
                    f"{self._get_label('milestones')}: {project.milestones_completed}/{project.milestones_total}"
                )
                if project.milestones_delayed > 0:
                    info_parts.append(f"({project.milestones_delayed} {self._get_label('delayed')})")

            section.paragraphs.append(
                DocxParagraph.simple(" | ".join(info_parts), color=self.tokens.TEXT_LIGHT)
            )
            section.content_order.append(("paragraph", para_idx))
            para_idx += 1

            # Scores table
            scores_table = self._build_project_scores_table(project)
            section.tables.append(scores_table)
            section.content_order.append(("table", table_idx))
            table_idx += 1

            # Project summary
            if project.summary:
                section.paragraphs.append(
                    DocxParagraph.simple(f"{self._get_label('assessment')}: {project.summary}")
                )
                section.content_order.append(("paragraph", para_idx))
                para_idx += 1

        return section

    def _build_project_scores_table(self, project: ProjectScore) -> DocxTable:
        """Build scores table for a single project."""
        rows = [
            DocxTableRow(
                cells=[
                    DocxTableCell(
                        content=self._get_label("dimension"),
                        bold=True,
                        background_color=self.tokens.ACCENT,
                        text_color=self.tokens.WHITE,
                    ),
                    DocxTableCell(
                        content=self._get_label("score"),
                        bold=True,
                        background_color=self.tokens.ACCENT,
                        text_color=self.tokens.WHITE,
                        alignment=TableCellAlignment.CENTER,
                    ),
                    DocxTableCell(
                        content=self._get_label("reasoning"),
                        bold=True,
                        background_color=self.tokens.ACCENT,
                        text_color=self.tokens.WHITE,
                    ),
                ],
                is_header=True,
            ),
        ]

        score_data = [
            (f"U ({self._get_label('urgency')})", project.urgency),
            (f"I ({self._get_label('importance')})", project.importance),
            (f"C ({self._get_label('complexity')})", project.complexity),
            (f"R ({self._get_label('risk')})", project.risk),
            (f"DQ ({self._get_label('data_quality')})", project.data_quality),
        ]

        for label, score in score_data:
            score_color = self.tokens.SCORE_COLORS.get(score.value, self.tokens.TEXT_DARK)
            rows.append(
                DocxTableRow(
                    cells=[
                        DocxTableCell(content=label),
                        DocxTableCell(
                            content=self._score_to_stars(score.value),
                            alignment=TableCellAlignment.CENTER,
                            text_color=score_color,
                        ),
                        DocxTableCell(content=score.reasoning),
                    ]
                )
            )

        return DocxTable(rows=rows, col_widths_cm=[4.0, 2.5, 9.0])

    def _build_critical_projects_section(self) -> DocxSection:
        """Build critical projects section."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("critical_projects"),
                level=HeadingLevel.H1,
                color=self.tokens.STATUS_RED,
            )
        )

        # Intro text
        section.paragraphs.append(
            DocxParagraph.simple(
                self._get_label("critical_projects_intro").format(
                    count=len(self.analysis.critical_projects)
                )
            )
        )
        section.content_order.append(("paragraph", 0))

        # Critical projects list
        critical_items = []
        for project_id in self.analysis.critical_projects:
            project = self._find_project_by_id(project_id)
            if project:
                critical_items.append(
                    DocxListItem(text=f"{project.project_name}: {project.summary}", bold=False)
                )

        if critical_items:
            section.lists.append(DocxList(items=critical_items, style=ListStyle.BULLET))
            section.content_order.append(("list", 0))

        return section

    def _build_recommendations_section(self) -> DocxSection:
        """Build recommendations section."""
        section = DocxSection(
            heading=DocxHeading(
                text=self._get_label("recommendations"),
                level=HeadingLevel.H1,
                color=self.tokens.PRIMARY,
            )
        )

        # Recommendations list
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

    def _score_to_stars(self, score: int) -> str:
        """Convert numeric score to star representation."""
        return "●" * score + "○" * (5 - score)

    def _get_status_color(self, status: str) -> RgbColor:
        """Get color for status."""
        status_colors = {
            "green": self.tokens.STATUS_GREEN,
            "yellow": self.tokens.STATUS_YELLOW,
            "red": self.tokens.STATUS_RED,
            "gray": self.tokens.STATUS_GRAY,
        }
        return status_colors.get(status.lower(), self.tokens.STATUS_GRAY)

    def _get_status_symbol(self, status: str) -> str:
        """Get symbol for status."""
        symbols = {
            "green": "●",
            "yellow": "●",
            "red": "●",
            "gray": "○",
        }
        return symbols.get(status.lower(), "○")

    def _find_project_by_id(self, project_id: str) -> Optional[ProjectScore]:
        """Find project by ID."""
        for project in self.analysis.project_scores:
            if project.project_id == project_id:
                return project
        return None

    def _get_label(self, key: str) -> str:
        """Get localized label."""
        labels = {
            "de": {
                "title_subtitle": "KI-gestützte Portfolioanalyse (U/I/C/R/DQ)",
                "generated": "Generiert",
                "executive_summary": "Executive Summary",
                "portfolio_overview": "Portfolio-Übersicht",
                "project_details": "Projektbewertungen im Detail",
                "critical_projects": "Kritische Projekte",
                "recommendations": "Handlungsempfehlungen",
                "key_metrics": "Kennzahlen",
                "metric": "Kennzahl",
                "value": "Wert",
                "total_projects": "Projekte gesamt",
                "avg_urgency": "Ø Dringlichkeit",
                "avg_importance": "Ø Wichtigkeit",
                "avg_complexity": "Ø Komplexität",
                "avg_risk": "Ø Risiko",
                "avg_data_quality": "Ø Datenqualität",
                "project": "Projekt",
                "status": "Status",
                "score_legend": "Skala",
                "very_low": "sehr niedrig",
                "low": "niedrig",
                "medium": "mittel",
                "high": "hoch",
                "very_high": "sehr hoch",
                "no_projects": "Keine Projekte zur Analyse vorhanden.",
                "no_summary": "Keine Zusammenfassung verfügbar.",
                "dimension": "Dimension",
                "score": "Score",
                "reasoning": "Begründung",
                "urgency": "Dringlichkeit",
                "importance": "Wichtigkeit",
                "complexity": "Komplexität",
                "risk": "Risiko",
                "data_quality": "Datenqualität",
                "owner": "Verantwortlich",
                "progress": "Fortschritt",
                "milestones": "Meilensteine",
                "delayed": "verzögert",
                "assessment": "Einschätzung",
                "critical_projects_intro": "Die folgenden {count} Projekte wurden als kritisch eingestuft und erfordern besondere Aufmerksamkeit:",
            },
            "en": {
                "title_subtitle": "AI-Powered Portfolio Analysis (U/I/C/R/DQ)",
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
                "avg_urgency": "Avg. Urgency",
                "avg_importance": "Avg. Importance",
                "avg_complexity": "Avg. Complexity",
                "avg_risk": "Avg. Risk",
                "avg_data_quality": "Avg. Data Quality",
                "project": "Project",
                "status": "Status",
                "score_legend": "Scale",
                "very_low": "very low",
                "low": "low",
                "medium": "medium",
                "high": "high",
                "very_high": "very high",
                "no_projects": "No projects available for analysis.",
                "no_summary": "No summary available.",
                "dimension": "Dimension",
                "score": "Score",
                "reasoning": "Reasoning",
                "urgency": "Urgency",
                "importance": "Importance",
                "complexity": "Complexity",
                "risk": "Risk",
                "data_quality": "Data Quality",
                "owner": "Owner",
                "progress": "Progress",
                "milestones": "Milestones",
                "delayed": "delayed",
                "assessment": "Assessment",
                "critical_projects_intro": "The following {count} projects have been identified as critical and require special attention:",
            },
        }
        return labels.get(self.language, labels["de"]).get(key, key)

