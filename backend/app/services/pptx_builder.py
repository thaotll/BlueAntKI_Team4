"""
Builds PptxPresentationModel from PortfolioAnalysis.
Responsible for content decisions and layout composition.
Now supports AI-generated presentation structures with chart visualizations.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

from app.models.scoring import PortfolioAnalysis, ProjectScore
from app.models.pptx import (
    PptxPresentationModel,
    PptxSlideModel,
    TextBoxShape,
    ImageShape,
    TableShape,
    TableRow,
    TableCell,
    ChartShape,
    ChartType,
    ChartDataPoint,
    TextParagraph,
    TextRun,
    TextStyle,
    Position,
    RgbColor,
    SlideLayout,
    AIPresentationStructure,
    AISlideSpec,
    SlideType,
    VisualizationType,
)
from app.services.chart_generator import (
    ChartGenerator,
    create_score_bar_chart,
    create_status_pie_chart,
    create_risk_urgency_scatter,
    create_project_radar_chart,
)
from app.services.sanity_validator import SanityValidator

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
    GREEN = RgbColor(r=52, g=168, b=83)
    YELLOW = RgbColor(r=251, g=188, b=4)
    RED = RgbColor(r=234, g=67, b=53)
    GRAY = RgbColor(r=128, g=128, b=128)

    # Typography
    FONT_FAMILY = "Calibri"
    TITLE_SIZE = 40
    SUBTITLE_SIZE = 20
    HEADING_SIZE = 28
    BODY_SIZE = 14
    CAPTION_SIZE = 12
    METRIC_SIZE = 48

    # Layout (16:9 slide = 13.333 x 7.5 inches)
    SLIDE_WIDTH = 13.333
    SLIDE_HEIGHT = 7.5
    MARGIN = 0.5
    CONTENT_WIDTH = 12.333  # SLIDE_WIDTH - 2 * MARGIN
    CONTENT_HEIGHT = 5.5  # Available height for content


class PptxBuilder:
    """
    Builds presentation models from portfolio analysis data.
    
    Now supports AI-generated presentation structures with dynamic
    slide generation and chart visualizations.

    Usage:
        builder = PptxBuilder(analysis)
        model = builder.build()
        
        # Or with AI structure:
        model = builder.build_from_ai_structure(ai_structure)
    """

    def __init__(
        self,
        analysis: PortfolioAnalysis,
        language: str = "de",
        detail_level: str = "compact",
    ):
        self.analysis = analysis
        self.language = language
        self.detail_level = detail_level  # "compact" or "detailed"
        self.tokens = DesignTokens()
        self.chart_generator = ChartGenerator()

    def build(self) -> PptxPresentationModel:
        """
        Build complete presentation model with fixed structure:
        1. Title Slide
        2. Executive Summary
        3. Project Radar Charts (one per project with key insights)
        4. Risk Clusters
        5. Recommendations
        """
        logger.info(f"Building presentation for portfolio: {self.analysis.portfolio_name}")

        presentation = PptxPresentationModel(
            title=f"{self.analysis.portfolio_name} - Portfolio Analysis",
            primary_color=self.tokens.PRIMARY,
            accent_color=self.tokens.ACCENT,
            text_color=self.tokens.TEXT_DARK,
        )

        # 1. Title Slide
        presentation.slides.append(self._build_title_slide())

        # 2. Executive Summary
        presentation.slides.append(self._build_executive_summary_slide())
        
        # 3. One Radar Chart Slide per Project (with key insights)
        for project_score in self.analysis.project_scores:
            presentation.slides.append(self._build_project_radar_slide(project_score))
        
        # 4. Risk Clusters
        presentation.slides.append(self._build_risk_clusters_slide())
        
        # 5. Recommendations
        presentation.slides.append(self._build_recommendations_slide())

        logger.info(f"Built presentation with {len(presentation.slides)} slides")
        return presentation

    def build_from_ai_structure(
        self,
        ai_structure: AIPresentationStructure,
    ) -> PptxPresentationModel:
        """
        Build presentation from AI-generated structure.
        
        Args:
            ai_structure: AI-generated presentation specification
            
        Returns:
            Complete presentation model
        """
        logger.info(
            f"Building AI-structured presentation for portfolio: {self.analysis.portfolio_name} "
            f"({len(ai_structure.slides)} slides)"
        )

        presentation = PptxPresentationModel(
            title=f"{self.analysis.portfolio_name} - Portfolio Analysis",
            primary_color=self.tokens.PRIMARY,
            accent_color=self.tokens.ACCENT,
            text_color=self.tokens.TEXT_DARK,
        )

        # Map slide types to builder methods
        slide_builders = {
            SlideType.TITLE: self._build_title_slide,
            SlideType.EXECUTIVE_SUMMARY: self._build_executive_summary_slide,
            SlideType.STATISTICS: self._build_statistics_slide,
            SlideType.CRITICAL_PROJECTS: self._build_critical_projects_slide,
            SlideType.PRIORITY_RANKING: self._build_priority_ranking_slide,
            SlideType.RISK_MATRIX: self._build_risk_matrix_slide,
            SlideType.SCORE_OVERVIEW: self._build_score_overview_slide,
            SlideType.RISK_CLUSTERS: self._build_risk_clusters_slide,
            SlideType.RECOMMENDATIONS: self._build_recommendations_slide,
            SlideType.STATUS_DISTRIBUTION: self._build_status_distribution_slide,
            SlideType.PROJECT_DETAIL: self._build_project_detail_slide,
        }

        for slide_spec in ai_structure.slides:
            builder_func = slide_builders.get(slide_spec.slide_type)
            if builder_func:
                try:
                    slide = builder_func(slide_spec=slide_spec)
                    presentation.slides.append(slide)
                except Exception as e:
                    logger.warning(f"Failed to build slide {slide_spec.slide_type}: {e}")
            else:
                logger.warning(f"Unknown slide type: {slide_spec.slide_type}")

        logger.info(f"Built AI-structured presentation with {len(presentation.slides)} slides")
        return presentation

    # =========================================================================
    # Slide Builder Methods
    # =========================================================================

    def _build_title_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build the title slide."""
        shapes = []

        # Main title
        title_text = slide_spec.title if slide_spec else (self.analysis.portfolio_name or "Portfolio Analysis")
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
                    runs=[TextRun(text=title_text)],
                    alignment="center",
                )
            ],
            default_style=title_style,
        )
        shapes.append(title_box)

        # Subtitle
        subtitle_text = slide_spec.subtitle if slide_spec and slide_spec.subtitle else self._get_label("title_subtitle")
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
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_executive_summary_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build executive summary slide with key metrics."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Executive Summary"
        shapes.append(self._create_slide_title(title_text))

        # Key metrics cards
        metrics = [
            (str(len(self.analysis.project_scores)), "Projekte", self.tokens.PRIMARY),
            (str(len(self.analysis.critical_projects)), "Kritisch", self.tokens.RED),
            (f"{self.analysis.avg_risk:.1f}", "Ø Risiko", self.tokens.YELLOW),
            (f"{self.analysis.avg_urgency:.1f}", "Ø Dringlichkeit", self.tokens.ACCENT),
        ]

        card_width = 2.5
        card_height = 1.5
        start_x = 0.75
        y_pos = 1.8

        for i, (value, label, color) in enumerate(metrics):
            x_pos = start_x + i * (card_width + 0.3)
            shapes.extend(self._create_metric_card(x_pos, y_pos, card_width, card_height, value, label, color))

        # Executive summary text (preserve full content with smart wrapping)
        if self.analysis.executive_summary:
            summary_paragraphs = self._prepare_summary_paragraphs(
                self.analysis.executive_summary
            )

            summary_style = TextStyle(
                font_name=self.tokens.FONT_FAMILY,
                font_size_pt=self.tokens.BODY_SIZE,
                color=self.tokens.TEXT_DARK,
            )

            summary_box = TextBoxShape(
                position=Position(x=0.5, y=3.8, width=12.333, height=3.4),
                paragraphs=summary_paragraphs,
                default_style=summary_style,
            )
            shapes.append(summary_box)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _prepare_summary_paragraphs(self, text: str) -> List[TextParagraph]:
        """Split long executive summaries into readable paragraphs."""
        if not text:
            return []

        raw_blocks = [
            block.strip()
            for block in re.split(r"\n{2,}", text.strip())
            if block.strip()
        ]
        if not raw_blocks:
            raw_blocks = [text.strip()]

        paragraphs: List[TextParagraph] = []
        for block in raw_blocks:
            for chunk in self._chunk_sentences(block):
                paragraphs.append(
                    TextParagraph(
                        runs=[TextRun(text=chunk)],
                        alignment="left",
                        space_after_pt=6,
                    )
                )
        return paragraphs

    def _chunk_sentences(self, text: str, max_length: int = 350) -> List[str]:
        """Group sentences so paragraphs stay readable without truncation."""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not sentences:
            return [text.strip()] if text.strip() else []

        chunks: List[str] = []
        current = ""
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) > max_length and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = candidate

        if current:
            chunks.append(current.strip())

        return chunks

    def _build_statistics_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build statistics slide with charts."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Portfolio-Scores im Überblick"
        shapes.append(self._create_slide_title(title_text))

        # Score bar chart (left side)
        score_chart = create_score_bar_chart(
            labels=["Dringlichkeit", "Wichtigkeit", "Komplexität", "Risiko", "Datenqualität"],
            values=[
                self.analysis.avg_urgency,
                self.analysis.avg_importance,
                self.analysis.avg_complexity,
                self.analysis.avg_risk,
                self.analysis.avg_data_quality,
            ],
            title="Durchschnittliche Scores (U/I/C/R/DQ)",
        )
        score_chart.position = Position(x=0.5, y=1.6, width=6.0, height=4.5)
        
        # Generate chart image
        chart_bytes = self.chart_generator.generate(score_chart)
        score_chart_image = ImageShape(
            position=Position(x=0.5, y=1.6, width=6.0, height=4.5),
            image_bytes=chart_bytes,
        )
        shapes.append(score_chart_image)

        # Status distribution pie chart (right side)
        status_counts = self._get_status_counts()
        if status_counts:
            status_chart = create_status_pie_chart(
                status_counts=status_counts,
                title="Projektstatus-Verteilung",
            )
            status_chart.position = Position(x=6.8, y=1.6, width=6.0, height=4.5)
            
            chart_bytes = self.chart_generator.generate(status_chart)
            status_chart_image = ImageShape(
                position=Position(x=6.8, y=1.6, width=6.0, height=4.5),
                image_bytes=chart_bytes,
            )
            shapes.append(status_chart_image)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_risk_matrix_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build risk-urgency matrix scatter plot slide."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Risiko-Dringlichkeits-Matrix"
        shapes.append(self._create_slide_title(title_text))

        # Create scatter chart
        projects_data = [
            {
                'name': score.project_name,
                'risk': score.risk.value,
                'urgency': score.urgency.value,
            }
            for score in self.analysis.project_scores
        ]

        scatter_chart = create_risk_urgency_scatter(
            projects=projects_data,
            title="Projekte nach Risiko und Dringlichkeit",
        )
        scatter_chart.position = Position(x=1.0, y=1.6, width=11.333, height=5.0)
        
        chart_bytes = self.chart_generator.generate(scatter_chart)
        scatter_image = ImageShape(
            position=Position(x=1.0, y=1.6, width=11.333, height=5.0),
            image_bytes=chart_bytes,
        )
        shapes.append(scatter_image)

        # Add quadrant labels
        quadrant_labels = [
            ("Beobachten", Position(x=2.0, y=5.5, width=2.0, height=0.5)),
            ("Sofort handeln", Position(x=9.0, y=5.5, width=2.0, height=0.5)),
        ]

        for label, pos in quadrant_labels:
            label_style = TextStyle(
                font_name=self.tokens.FONT_FAMILY,
                font_size_pt=self.tokens.CAPTION_SIZE,
                italic=True,
                color=self.tokens.TEXT_LIGHT,
            )
            label_box = TextBoxShape(
                position=pos,
                paragraphs=[TextParagraph(runs=[TextRun(text=label)], alignment="center")],
                default_style=label_style,
            )
            shapes.append(label_box)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_critical_projects_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build critical projects overview slide with table."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Kritische Projekte"
        shapes.append(self._create_slide_title(title_text))

        # Get critical projects
        critical_scores = [s for s in self.analysis.project_scores if s.is_critical]

        if not critical_scores:
            # No critical projects message
            no_critical_style = TextStyle(
                font_name=self.tokens.FONT_FAMILY,
                font_size_pt=self.tokens.SUBTITLE_SIZE,
                color=self.tokens.GREEN,
            )
            no_critical_box = TextBoxShape(
                position=Position(x=0.5, y=3.0, width=12.333, height=1.0),
                paragraphs=[
                    TextParagraph(
                        runs=[TextRun(text="Keine kritischen Projekte identifiziert")],
                        alignment="center",
                    )
                ],
                default_style=no_critical_style,
            )
            shapes.append(no_critical_box)
        else:
            # Build table for critical projects (max 6)
            table_rows = [
                TableRow(
                    is_header=True,
                    cells=[
                        TableCell(text="Projekt"),
                        TableCell(text="U"),
                        TableCell(text="I"),
                        TableCell(text="R"),
                        TableCell(text="Status"),
                    ]
                )
            ]

            for score in critical_scores[:6]:
                status_color = self._get_status_color(score.status_color)
                table_rows.append(
                    TableRow(
                        cells=[
                            TableCell(text=score.project_name[:30]),
                            TableCell(text=str(score.urgency.value)),
                            TableCell(text=str(score.importance.value)),
                            TableCell(text=str(score.risk.value)),
                            TableCell(text="●", style=TextStyle(color=status_color)),
                        ]
                    )
                )

            table = TableShape(
                position=Position(x=0.5, y=1.8, width=12.333, height=4.5),
                rows=table_rows,
                header_style=TextStyle(
                    font_name=self.tokens.FONT_FAMILY,
                    font_size_pt=self.tokens.BODY_SIZE,
                    bold=True,
                    color=self.tokens.WHITE,
                ),
                cell_style=TextStyle(
                    font_name=self.tokens.FONT_FAMILY,
                    font_size_pt=self.tokens.BODY_SIZE,
                    color=self.tokens.TEXT_DARK,
                ),
                header_background=self.tokens.PRIMARY,
            )
            shapes.append(table)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_priority_ranking_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build priority ranking slide with horizontal bar chart."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Projekt-Priorisierung"
        shapes.append(self._create_slide_title(title_text))

        # Get top projects by priority
        sorted_scores = sorted(
            self.analysis.project_scores,
            key=lambda s: s.priority_score,
            reverse=True,
        )[:8]

        if sorted_scores:
            # Create horizontal bar chart for priority scores
            data_points = [
                ChartDataPoint(
                    label=score.project_name[:20],
                    value=score.priority_score,
                )
                for score in sorted_scores
            ]

            chart = ChartShape(
                position=Position(x=0.5, y=1.6, width=12.333, height=5.0),
                chart_type=ChartType.HORIZONTAL_BAR,
                title="Top-Projekte nach Priorität",
                data_points=data_points,
                show_values=True,
                x_axis_label="Prioritätsscore",
            )

            chart_bytes = self.chart_generator.generate(chart)
            chart_image = ImageShape(
                position=Position(x=0.5, y=1.6, width=12.333, height=5.0),
                image_bytes=chart_bytes,
            )
            shapes.append(chart_image)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_score_overview_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build score overview slide with radar charts for top projects."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Projekt-Profile"
        shapes.append(self._create_slide_title(title_text))

        # Get top 3 critical or highest priority projects
        critical_scores = [s for s in self.analysis.project_scores if s.is_critical][:3]
        if len(critical_scores) < 3:
            non_critical = [s for s in self.analysis.project_scores if not s.is_critical]
            sorted_non_critical = sorted(non_critical, key=lambda s: s.priority_score, reverse=True)
            critical_scores.extend(sorted_non_critical[:3 - len(critical_scores)])

        # Create radar charts for each project
        for i, score in enumerate(critical_scores[:3]):
            radar_chart = create_project_radar_chart(
                project_name=score.project_name[:15],
                urgency=score.urgency.value,
                importance=score.importance.value,
                complexity=score.complexity.value,
                risk=score.risk.value,
                data_quality=score.data_quality.value,
            )
            
            x_pos = 0.5 + i * 4.2
            radar_chart.position = Position(x=x_pos, y=1.8, width=4.0, height=4.0)
            
            chart_bytes = self.chart_generator.generate(radar_chart)
            radar_image = ImageShape(
                position=Position(x=x_pos, y=1.8, width=4.0, height=4.0),
                image_bytes=chart_bytes,
            )
            shapes.append(radar_image)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_risk_clusters_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build risk clusters visualization slide."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Identifizierte Risikomuster"
        shapes.append(self._create_slide_title(title_text))

        if self.analysis.risk_clusters:
            # Display risk clusters as simple bullet points (5-6 max)
            y_pos = 1.8
            max_clusters = 6
            for i, cluster in enumerate(self.analysis.risk_clusters[:max_clusters]):
                indicator_style = TextStyle(
                    font_name=self.tokens.FONT_FAMILY,
                    font_size_pt=self.tokens.BODY_SIZE + 4,
                    bold=True,
                    color=self.tokens.YELLOW if i == 0 else self.tokens.TEXT_LIGHT,
                )
                indicator_box = TextBoxShape(
                    position=Position(x=0.5, y=y_pos, width=0.4, height=0.5),
                    paragraphs=[TextParagraph(runs=[TextRun(text=">")], alignment="center")],
                    default_style=indicator_style,
                )
                shapes.append(indicator_box)

                risk_style = TextStyle(
                    font_name=self.tokens.FONT_FAMILY,
                    font_size_pt=self.tokens.BODY_SIZE,
                    color=self.tokens.TEXT_DARK,
                )
                
                risk_box = TextBoxShape(
                    position=Position(x=1.1, y=y_pos, width=11.733, height=0.6),
                    paragraphs=[TextParagraph(runs=[TextRun(text=cluster)], alignment="left")],
                    default_style=risk_style,
                )
                shapes.append(risk_box)

                y_pos += 0.85
        else:
            no_clusters_style = TextStyle(
                font_name=self.tokens.FONT_FAMILY,
                font_size_pt=self.tokens.BODY_SIZE,
                color=self.tokens.TEXT_LIGHT,
            )
            no_clusters_box = TextBoxShape(
                position=Position(x=0.5, y=3.0, width=12.333, height=1.0),
                paragraphs=[
                    TextParagraph(
                        runs=[TextRun(text="Keine übergreifenden Risikomuster identifiziert")],
                        alignment="center",
                    )
                ],
                default_style=no_clusters_style,
            )
            shapes.append(no_clusters_box)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_recommendations_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build recommendations slide."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Handlungsempfehlungen"
        shapes.append(self._create_slide_title(title_text))

        if self.analysis.recommendations:
            y_pos = 1.8
            for i, recommendation in enumerate(self.analysis.recommendations[:5]):
                # Number badge
                badge_style = TextStyle(
                    font_name=self.tokens.FONT_FAMILY,
                    font_size_pt=self.tokens.BODY_SIZE + 2,
                    bold=True,
                    color=self.tokens.WHITE,
                )
                badge_box = TextBoxShape(
                    position=Position(x=0.5, y=y_pos, width=0.5, height=0.5),
                    paragraphs=[TextParagraph(runs=[TextRun(text=str(i + 1))], alignment="center")],
                    default_style=badge_style,
                )
                shapes.append(badge_box)

                # Recommendation text
                rec_style = TextStyle(
                    font_name=self.tokens.FONT_FAMILY,
                    font_size_pt=self.tokens.BODY_SIZE,
                    color=self.tokens.TEXT_DARK,
                )
                rec_box = TextBoxShape(
                    position=Position(x=1.2, y=y_pos, width=11.633, height=0.8),
                    paragraphs=[TextParagraph(runs=[TextRun(text=recommendation)], alignment="left")],
                    default_style=rec_style,
                )
                shapes.append(rec_box)

                y_pos += 1.0
        else:
            no_rec_style = TextStyle(
                font_name=self.tokens.FONT_FAMILY,
                font_size_pt=self.tokens.BODY_SIZE,
                color=self.tokens.TEXT_LIGHT,
            )
            no_rec_box = TextBoxShape(
                position=Position(x=0.5, y=3.0, width=12.333, height=1.0),
                paragraphs=[
                    TextParagraph(
                        runs=[TextRun(text="Keine spezifischen Empfehlungen")],
                        alignment="center",
                    )
                ],
                default_style=no_rec_style,
            )
            shapes.append(no_rec_box)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )
    
    def _get_risk_cluster_context(self, cluster_text: str) -> List[str]:
        """Add contextual info for detailed risk cluster slides.
        
        Returns a list of context lines to display under the risk cluster.
        """
        if not cluster_text:
            return []
        
        context_lines = []
        cluster_lower = cluster_text.lower()
        
        # Find affected projects based on risk pattern
        affected_projects = self._find_affected_projects(cluster_text)
        
        # Resource/Capacity issues
        if "ressource" in cluster_lower or "kapaz" in cluster_lower or "engpass" in cluster_lower:
            context_lines.append("Betroffene Projekte: Fokus auf Engpassbereiche im Portfolio (siehe Ressourcenanalyse).")
            if affected_projects:
                project_names = [p.project_name for p in affected_projects[:3]]
                if len(affected_projects) > 3:
                    context_lines.append(f"Beispiele: {', '.join(project_names)} und {len(affected_projects) - 3} weitere Projekte.")
                else:
                    context_lines.append(f"Betroffene Projekte: {', '.join(project_names)}.")
                # Add statistics
                avg_risk = sum(p.risk.value for p in affected_projects) / len(affected_projects) if affected_projects else 0
                context_lines.append(f"Durchschnittliches Risiko betroffener Projekte: {avg_risk:.1f}/5.0")
        
        # Data quality issues
        elif "daten" in cluster_lower or "datenqualität" in cluster_lower or "dq" in cluster_lower:
            context_lines.append("Datenqualität wirkt sich auf Analyse und Prognosen aus – Data Governance Maßnahmen priorisieren.")
            if affected_projects:
                low_dq_projects = [p for p in affected_projects if p.data_quality.value <= 2]
                if low_dq_projects:
                    context_lines.append(f"{len(low_dq_projects)} Projekt(e) mit niedriger Datenqualität (DQ ≤ 2) identifiziert.")
                if self.analysis.data_warnings:
                    context_lines.append(f"{len(self.analysis.data_warnings)} Datenqualitätswarnungen im Portfolio vorhanden.")
            if self.analysis.avg_data_quality < 3.0:
                context_lines.append(f"Durchschnittliche Datenqualität im Portfolio: {self.analysis.avg_data_quality:.1f}/5.0 – Handlungsbedarf erkennbar.")
        
        # Timeline/Deadline issues
        elif "timeline" in cluster_lower or "termin" in cluster_lower or "verzögerung" in cluster_lower or "deadline" in cluster_lower:
            context_lines.append("Terminrisiken schlagen direkt auf kritische Projekte durch; frühzeitige Steering-Entscheidungen nötig.")
            if affected_projects:
                high_urgency = [p for p in affected_projects if p.urgency.value >= 4]
                delayed = [p for p in affected_projects if p.milestones_delayed > 0]
                if high_urgency:
                    context_lines.append(f"{len(high_urgency)} betroffene Projekt(e) mit hoher Dringlichkeit (U ≥ 4).")
                if delayed:
                    total_delayed = sum(p.milestones_delayed for p in delayed)
                    context_lines.append(f"{len(delayed)} Projekt(e) mit verzögerten Meilensteinen ({total_delayed} Meilensteine insgesamt).")
        
        # Scope/Complexity issues
        elif "scope" in cluster_lower or "komplex" in cluster_lower or "anforderung" in cluster_lower or "business-case" in cluster_lower:
            context_lines.append("Hohe Scope-Veränderungen erfordern klares Change-Management und abgestimmte Roadmaps.")
            if affected_projects:
                high_complexity = [p for p in affected_projects if p.complexity.value >= 4]
                if high_complexity:
                    context_lines.append(f"{len(high_complexity)} Projekt(e) mit hoher Komplexität (C ≥ 4) betroffen.")
                avg_complexity = sum(p.complexity.value for p in affected_projects) / len(affected_projects) if affected_projects else 0
                context_lines.append(f"Durchschnittliche Komplexität betroffener Projekte: {avg_complexity:.1f}/5.0")
        
        # Legacy system issues
        elif "legacy" in cluster_lower or "alt" in cluster_lower or "incompat" in cluster_lower:
            context_lines.append("Legacy-Systeme erfordern besondere Aufmerksamkeit bei Integration und Migration.")
            if affected_projects:
                project_names = [p.project_name for p in affected_projects[:3]]
                if len(affected_projects) > 3:
                    context_lines.append(f"Betroffene Projekte: {', '.join(project_names)} und {len(affected_projects) - 3} weitere.")
                else:
                    context_lines.append(f"Betroffene Projekte: {', '.join(project_names)}.")
        
        # Budget issues
        elif "budget" in cluster_lower or "kosten" in cluster_lower or "finanz" in cluster_lower:
            context_lines.append("Budgetüberschreitungen erfordern transparente Kostenkontrolle und Priorisierung.")
            if affected_projects:
                high_risk = [p for p in affected_projects if p.risk.value >= 4]
                if high_risk:
                    context_lines.append(f"{len(high_risk)} betroffene Projekt(e) mit hohem Risiko (R ≥ 4).")
        
        # Generic fallback - add affected projects if found
        else:
            if affected_projects:
                project_names = [p.project_name for p in affected_projects[:3]]
                if len(affected_projects) > 3:
                    context_lines.append(f"Betroffene Projekte: {', '.join(project_names)} und {len(affected_projects) - 3} weitere.")
                else:
                    context_lines.append(f"Betroffene Projekte: {', '.join(project_names)}.")
                avg_risk = sum(p.risk.value for p in affected_projects) / len(affected_projects) if affected_projects else 0
                if avg_risk >= 3.5:
                    context_lines.append(f"Durchschnittliches Risiko: {avg_risk:.1f}/5.0 – erhöhte Aufmerksamkeit erforderlich.")
        
        return context_lines
    
    def _find_affected_projects(self, cluster_text: str) -> List[ProjectScore]:
        """Find projects that are likely affected by a given risk cluster.
        
        Uses heuristics based on project scores and cluster keywords.
        """
        affected = []
        cluster_lower = cluster_text.lower()
        
        for project in self.analysis.project_scores:
            is_affected = False
            
            # Resource/Capacity issues
            if "ressource" in cluster_lower or "kapaz" in cluster_lower or "engpass" in cluster_lower:
                # Projects with high complexity and risk might indicate resource issues
                if project.complexity.value >= 4 and project.risk.value >= 3:
                    is_affected = True
            
            # Data quality issues
            elif "daten" in cluster_lower or "datenqualität" in cluster_lower or "dq" in cluster_lower:
                if project.data_quality.value <= 2:
                    is_affected = True
            
            # Timeline issues
            elif "timeline" in cluster_lower or "termin" in cluster_lower or "verzögerung" in cluster_lower:
                if project.urgency.value >= 4 or project.milestones_delayed > 0:
                    is_affected = True
            
            # Scope/Complexity issues
            elif "scope" in cluster_lower or "komplex" in cluster_lower or "anforderung" in cluster_lower:
                if project.complexity.value >= 4:
                    is_affected = True
            
            # Budget issues
            elif "budget" in cluster_lower or "kosten" in cluster_lower:
                if project.risk.value >= 4:
                    is_affected = True
            
            # Critical projects are often affected by various risk patterns
            if project.is_critical and project.risk.value >= 3:
                is_affected = True
            
            if is_affected:
                affected.append(project)
        
        return affected

    def _build_status_distribution_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build status distribution slide with pie chart."""
        shapes = []

        # Title
        title_text = slide_spec.title if slide_spec else "Status-Verteilung"
        shapes.append(self._create_slide_title(title_text))

        # Status pie chart
        status_counts = self._get_status_counts()
        if status_counts:
            status_chart = create_status_pie_chart(
                status_counts=status_counts,
                title="Projektstatus-Verteilung",
            )
            status_chart.position = Position(x=2.0, y=1.6, width=9.333, height=5.0)
            
            chart_bytes = self.chart_generator.generate(status_chart)
            status_image = ImageShape(
                position=Position(x=2.0, y=1.6, width=9.333, height=5.0),
                image_bytes=chart_bytes,
            )
            shapes.append(status_image)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=slide_spec.speaker_notes if slide_spec else None,
        )

    def _build_project_detail_slide(self, slide_spec: Optional[AISlideSpec] = None) -> PptxSlideModel:
        """Build individual project detail slide (legacy method)."""
        # Get the most critical project for detail view
        critical_scores = [s for s in self.analysis.project_scores if s.is_critical]
        if critical_scores:
            project = critical_scores[0]
        elif self.analysis.project_scores:
            project = max(self.analysis.project_scores, key=lambda s: s.priority_score)
        else:
            return PptxSlideModel(layout=SlideLayout.BLANK, shapes=[])

        return self._build_project_radar_slide(project)

    def _build_project_radar_slide(self, project: ProjectScore) -> PptxSlideModel:
        """
        Build a project slide with radar chart and key insights.
        
        Layout:
        - Title: Project name with status indicator
        - Data Warning Banner (if applicable): Prominent warning for incomplete data
        - Left: Radar chart showing U/I/C/R/DQ profile
        - Right: Key insights + Decision Points (for active projects)
        """
        shapes = []
        
        # Check if project is completed for conditional logic
        is_completed = self._is_project_completed(project)

        # Title with appropriate label (no emojis)
        project_label = self._get_project_display_label(project)
        title_text = project.project_name
        
        # Attach descriptive text instead of square-bracket tags
        label_suffix = None
        if project_label == "Kritisch":
            label_suffix = "Kritisch"
        elif project_label == "Review / Lessons Learned":
            label_suffix = "Review / Lessons Learned"
        elif project_label == "Daten-Fehler":
            label_suffix = "Datenfehler festgestellt"
        elif project_label == "Risikobehaftet":
            label_suffix = "Risikobehaftet"
        elif project_label == "Zeitkritisch":
            label_suffix = "Zeitkritisch"

        if label_suffix:
            title_text = f"{title_text} - {label_suffix}"

        shapes.append(self._create_slide_title(title_text[:60]))
        
        # Data Warning Banner (if data quality issues exist)
        warning_text = self._get_data_warning_text(project)
        content_y_offset = 0.0
        if warning_text:
            warning_banner = self._create_data_warning_banner(warning_text, y_position=1.15)
            shapes.append(warning_banner)
            content_y_offset = 0.35  # Shift content down to make room for banner

        # Radar chart on the left
        radar_chart = create_project_radar_chart(
            project_name=project.project_name[:20],
            urgency=project.urgency.value,
            importance=project.importance.value,
            complexity=project.complexity.value,
            risk=project.risk.value,
            data_quality=project.data_quality.value,
        )
        radar_y = 1.4 + content_y_offset
        radar_chart.position = Position(x=0.3, y=radar_y, width=5.5, height=5.5)
        
        chart_bytes = self.chart_generator.generate(radar_chart)
        radar_image = ImageShape(
            position=Position(x=0.3, y=radar_y, width=5.5, height=5.5),
            image_bytes=chart_bytes,
        )
        shapes.append(radar_image)

        # Extract key insights based on detail level
        if self.detail_level == "detailed":
            insights = self._extract_detailed_insights(project)
            max_insights = 5
            box_height = 1.0
            y_spacing = 0.85
            font_size = self.tokens.BODY_SIZE - 3
        else:
            insights = self._extract_project_insights(project)
            max_insights = 4
            box_height = 0.7
            y_spacing = 1.1
            font_size = self.tokens.BODY_SIZE

        # Key insights on the right side
        insights_title_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.BODY_SIZE + 2,
            bold=True,
            color=self.tokens.PRIMARY,
        )
        
        # Title depends on project state
        if is_completed:
            section_title = "Projektabschluss"
        elif self.detail_level == "detailed":
            section_title = "Detailanalyse"
        else:
            section_title = "Kernerkenntnisse"
            
        insights_title_y = 1.5 + content_y_offset
        insights_title = TextBoxShape(
            position=Position(x=6.0, y=insights_title_y, width=6.833, height=0.5),
            paragraphs=[TextParagraph(runs=[TextRun(text=section_title)], alignment="left")],
            default_style=insights_title_style,
        )
        shapes.append(insights_title)

        # Bullet points for insights
        y_pos = 2.0 + content_y_offset
        bullet_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=font_size,
            color=self.tokens.TEXT_DARK,
        )
        
        for insight in insights[:max_insights]:
            # Bullet point
            bullet_box = TextBoxShape(
                position=Position(x=6.0, y=y_pos, width=0.3, height=0.4),
                paragraphs=[TextParagraph(runs=[TextRun(text="▸")], alignment="left")],
                default_style=TextStyle(
                    font_name=self.tokens.FONT_FAMILY,
                    font_size_pt=self.tokens.BODY_SIZE + 1,
                    bold=True,
                    color=self.tokens.PRIMARY,
                ),
            )
            shapes.append(bullet_box)
            
            # Insight text
            insight_box = TextBoxShape(
                position=Position(x=6.4, y=y_pos, width=6.433, height=box_height),
                paragraphs=[TextParagraph(runs=[TextRun(text=insight)], alignment="left")],
                default_style=bullet_style,
            )
            shapes.append(insight_box)
            
            y_pos += y_spacing
        
        # Decision Points section (only for active, non-completed projects)
        decision_points = self._extract_decision_points(project)
        if decision_points and not is_completed:
            decision_points = decision_points[:3]
            decision_block_height = 0.25 + len(decision_points) * 0.3
            min_decision_y = insights_title_y + 0.15
            max_decision_y = self.tokens.SLIDE_HEIGHT - self.tokens.MARGIN - decision_block_height
            adjusted_start = min(y_pos + 0.02, max_decision_y)
            decision_start_y = max(min_decision_y, adjusted_start)

            # Add "Benötigte Entscheidungen" header
            decision_header_style = TextStyle(
                font_name=self.tokens.FONT_FAMILY,
                font_size_pt=self.tokens.BODY_SIZE,
                bold=True,
                color=self.tokens.RED,
            )
            decision_header = TextBoxShape(
                position=Position(x=6.0, y=decision_start_y, width=6.833, height=0.25),
                paragraphs=[TextParagraph(runs=[TextRun(text="Benötigte Entscheidungen:")], alignment="left")],
                default_style=decision_header_style,
            )
            shapes.append(decision_header)
            bullet_y = decision_start_y + 0.3
            
            # Add decision point bullets
            decision_style = TextStyle(
                font_name=self.tokens.FONT_FAMILY,
                font_size_pt=self.tokens.BODY_SIZE - 2,
                color=self.tokens.RED,
            )
            
            for decision in decision_points:
                decision_bullet = TextBoxShape(
                    position=Position(x=6.0, y=bullet_y, width=0.3, height=0.2),
                    paragraphs=[TextParagraph(runs=[TextRun(text="→")], alignment="left")],
                    default_style=decision_style,
                )
                shapes.append(decision_bullet)
                
                decision_box = TextBoxShape(
                    position=Position(x=6.4, y=bullet_y, width=6.433, height=0.35),
                    paragraphs=[TextParagraph(runs=[TextRun(text=decision)], alignment="left")],
                    default_style=decision_style,
                )
                shapes.append(decision_box)
                bullet_y += 0.3

        # Add score summary below the radar chart (left side)
        score_summary = f"Scores: U={project.urgency.value} | I={project.importance.value} | C={project.complexity.value} | R={project.risk.value} | DQ={project.data_quality.value}"
        score_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.CAPTION_SIZE,
            color=self.tokens.TEXT_LIGHT,
        )
        score_box = TextBoxShape(
            position=Position(x=0.3, y=7.0, width=5.5, height=0.4),
            paragraphs=[TextParagraph(runs=[TextRun(text=score_summary)], alignment="center")],
            default_style=score_style,
        )
        shapes.append(score_box)

        return PptxSlideModel(
            layout=SlideLayout.BLANK,
            shapes=shapes,
            notes=project.detailed_analysis if project.detailed_analysis else project.summary,
        )

    def _extract_project_insights(self, project: ProjectScore) -> List[str]:
        """
        Extract 3-4 key insights from project data.
        Complete sentences, no truncation - clear and informative.
        
        WICHTIG: Bei Data Mismatch wird ein Warntext statt Erfolgs-Text generiert.
        """
        insights = []
        
        # Check if project is completed first
        is_completed = self._is_project_completed(project)
        has_mismatch = self._has_data_mismatch(project)
        
        # CRITICAL: Data Mismatch hat Vorrang vor Erfolgs-Meldungen
        if has_mismatch:
            status_info = project.status_label or "Abgeschlossen"
            contradictions = self._get_data_mismatch_details(project)
            insights.append(f"Daten-Widerspruch: Status \"{status_info}\" widerspricht Metriken")
            if contradictions:
                insights.append(f"Probleme: {', '.join(contradictions[:2])}")
            insights.append("Manueller Status-Check erforderlich")
        elif is_completed:
            status_info = project.status_label or "Abgeschlossen"
            insights.append(f"Projekt erfolgreich abgeschlossen (Status: {status_info})")
        
        # 1. Urgency assessment (only if not completed AND no mismatch)
        if not is_completed and not has_mismatch and project.urgency.value == 5:
            insights.append("Kritische Dringlichkeit – sofortiges Handeln erforderlich")
        elif not is_completed and not has_mismatch and project.urgency.value == 4:
            insights.append("Hohe Dringlichkeit – zeitnahe Maßnahmen notwendig")
        
        # 2. Risk assessment (only if not completed AND no mismatch)
        if not is_completed and not has_mismatch and project.risk.value == 5:
            insights.append("Sehr hohes Risiko – intensive Überwachung und Gegenmaßnahmen nötig")
        elif not is_completed and not has_mismatch and project.risk.value == 4:
            insights.append("Erhöhtes Risiko – aktives Risikomanagement erforderlich")
        elif not is_completed and not has_mismatch and project.risk.value == 3 and len(insights) < 3:
            insights.append("Moderates Risiko – regelmäßige Überprüfung empfohlen")
        
        # 3. Milestones - concrete facts (SKIP for data mismatch)
        if has_mismatch:
            pass  # Already covered in mismatch warning
        elif is_completed and project.milestones_total > 0 and project.milestones_completed == project.milestones_total:
            insights.append(f"Alle {project.milestones_total} Meilensteine erfolgreich erreicht")
        elif project.milestones_delayed > 0:
            insights.append(f"{project.milestones_delayed} von {project.milestones_total} Meilensteinen verzögert")
        elif project.milestones_total > 0 and project.milestones_completed > 0:
            insights.append(f"{project.milestones_completed} von {project.milestones_total} Meilensteinen abgeschlossen")
        
        # 4. Effort variance - concrete facts
        if project.planned_effort_hours > 0 and project.actual_effort_hours > 0:
            variance = ((project.actual_effort_hours - project.planned_effort_hours) / project.planned_effort_hours) * 100
            if variance > 20:
                insights.append(f"Budgetüberschreitung von {variance:.0f}% beim Aufwand")
            elif variance < -20:
                insights.append(f"Aufwand {abs(variance):.0f}% unter Budget – effiziente Umsetzung")
        
        # 5. Progress status (skip if already completed)
        if not is_completed and project.progress_percent > 0 and len(insights) < 4:
            if project.progress_percent >= 90:
                insights.append(f"Projekt zu {project.progress_percent:.0f}% abgeschlossen")
            elif project.progress_percent >= 70:
                insights.append(f"Guter Fortschritt mit {project.progress_percent:.0f}% Fertigstellung")
            elif project.progress_percent >= 40:
                insights.append(f"Projekt bei {project.progress_percent:.0f}% Fortschritt")
            else:
                insights.append(f"Projekt in früher Phase ({project.progress_percent:.0f}% Fortschritt)")
        
        # 6. Data quality warning
        if project.data_quality.value <= 2:
            insights.append("Eingeschränkte Datenqualität – Bewertung mit Vorsicht interpretieren")
        
        # 7. Complexity note
        if project.complexity.value >= 4 and len(insights) < 4:
            insights.append("Hohe Projektkomplexität erfordert enge Abstimmung")
        
        # 8. Strategic importance
        if project.importance.value >= 4 and len(insights) < 4:
            insights.append("Strategisch wichtiges Projekt mit hoher Geschäftsrelevanz")
        
        # Fallback: First complete sentence from summary
        if len(insights) < 3 and project.summary:
            first_sentence = project.summary.split('.')[0].strip()
            if 10 < len(first_sentence) <= 80:
                insights.append(first_sentence)
        
        return insights[:4]  # Max 4 insights

    def _extract_detailed_insights(self, project: ProjectScore) -> List[str]:
        """
        Extract 5-6 sehr ausführliche, inhaltlich starke Stichpunkte.
        Jeder Stichpunkt enthält konkrete Fakten, Bewertungen und Handlungsempfehlungen.
        Berücksichtigt den aktuellen Projektstatus (z.B. Abgeschlossen).
        
        WICHTIG: Bei Data Mismatch (Status "Abgeschlossen" widerspricht Metriken)
        wird ein Warntext generiert, NICHT das Erfolgs-Template!
        """
        insights = []
        
        # Prüfen ob Projekt abgeschlossen ist
        is_completed = self._is_project_completed(project)
        status_info = project.status_label or "Unbekannt"
        
        # CRITICAL CHECK: Prüfe auf Data Mismatch VOR dem Erfolgs-Template
        has_mismatch = self._has_data_mismatch(project)
        
        # 1. Projektstatus-Übersicht (IMMER als erstes)
        if has_mismatch:
            # DATA MISMATCH: Generiere Warntext statt Erfolgs-Template
            contradictions = self._get_data_mismatch_details(project)
            contradiction_list = ", ".join(contradictions) if contradictions else "Inkonsistente Metriken"
            
            insights.append(
                f"WIDERSPRÜCHLICHE DATENLAGE: Der Projektstatus in BlueAnt ist \"{status_info}\", "
                f"aber die Metriken widersprechen dem massiv ({contradiction_list}). "
                f"Wahrscheinlicher Status: GESTOPPT oder KRITISCH. "
                f"Dieses Projekt darf NICHT als \"Erfolg\" gewertet werden!"
            )
            insights.append(
                f"NOTWENDIGE AKTION: Manueller Status-Check durch Projektleiter anfordern. "
                f"Die Daten in BlueAnt müssen korrigiert werden, bevor eine valide Bewertung möglich ist. "
                f"Mögliche Ursachen: Projekt wurde abgebrochen/pausiert aber Status nicht aktualisiert, "
                f"oder Datenerfassung wurde versäumt."
            )
        elif is_completed:
            # Nur bei KONSISTENTEN abgeschlossenen Projekten das Erfolgs-Template verwenden
            insights.append(
                f"PROJEKTSTATUS: ABGESCHLOSSEN – Das Projekt wurde erfolgreich beendet (Status: \"{status_info}\"). "
                f"Alle definierten Ziele wurden erreicht und das Projekt ist formal abgeschlossen. "
                f"Die nachfolgenden Bewertungen dienen der retrospektiven Analyse und dem Lessons-Learned-Prozess. "
                f"Eine Projektabschluss-Dokumentation sollte erstellt werden."
            )
        elif project.progress_percent >= 90:
            insights.append(
                f"PROJEKTSTATUS: ABSCHLUSSPHASE – Mit {project.progress_percent:.0f}% Fortschritt befindet sich das "
                f"Projekt in der finalen Phase (Status: \"{status_info}\"). Der Fokus sollte auf Qualitätssicherung, "
                f"Dokumentation und formaler Abnahme liegen. Change-Requests sollten kritisch geprüft werden, "
                f"um den Projektabschluss nicht zu gefährden."
            )
        elif project.urgency.value >= 4 and project.risk.value >= 4:
            insights.append(
                f"PROJEKTSTATUS: KRITISCH – Das Projekt weist sowohl hohe Dringlichkeit ({project.urgency.value}/5) "
                f"als auch erhebliches Risiko ({project.risk.value}/5) auf (Status: \"{status_info}\"). "
                f"Diese Kombination erfordert unmittelbare Management-Intervention, tägliche Statusberichte "
                f"und zusätzliche Ressourcen. Ein dedizierter Eskalationspfad sollte etabliert werden."
            )
        elif project.urgency.value >= 4:
            insights.append(
                f"PROJEKTSTATUS: ZEITKRITISCH – Mit Dringlichkeitsstufe {project.urgency.value}/5 steht das Projekt "
                f"unter erheblichem Zeitdruck (Status: \"{status_info}\"). Termingerechte Fertigstellung erfordert "
                f"priorisierte Ressourcen, parallele Arbeitspakete und beschleunigte Entscheidungsprozesse. "
                f"Wöchentliche Fortschrittsreviews sind essentiell."
            )
        elif project.risk.value >= 4:
            insights.append(
                f"PROJEKTSTATUS: RISIKOBEHAFTET – Die Risikobewertung von {project.risk.value}/5 signalisiert "
                f"potenzielle Gefährdungen (Status: \"{status_info}\"). Aktives Risikomanagement, definierte "
                f"Mitigationsmaßnahmen und regelmäßige Risk-Reviews sind erforderlich. "
                f"Contingency-Pläne sollten vorbereitet werden."
            )
        else:
            insights.append(
                f"PROJEKTSTATUS: STABIL – Mit Dringlichkeit {project.urgency.value}/5 und Risiko {project.risk.value}/5 "
                f"befindet sich das Projekt in kontrolliertem Zustand (Status: \"{status_info}\"). "
                f"Standardmäßige Projektmanagement-Praktiken sind ausreichend. "
                f"Regelmäßige Statusmeetings und proaktive Stakeholder-Kommunikation werden empfohlen."
            )
        
        # 2. Meilenstein- und Fortschrittsstatus
        # SKIP for data mismatch projects - already covered in warning above
        if project.milestones_total > 0 and not has_mismatch:
            completion_rate = (project.milestones_completed / project.milestones_total) * 100
            remaining = project.milestones_total - project.milestones_completed
            
            # Only show "all milestones completed" if actually true (100% completion)
            if completion_rate == 100:
                insights.append(
                    f"MEILENSTEIN-BILANZ: Alle {project.milestones_total} Meilensteine wurden erfolgreich "
                    f"abgeschlossen (100% Erfüllungsgrad). Das Projekt hat alle definierten Etappenziele erreicht. "
                    f"Die Meilenstein-Planung hat sich als realistisch und umsetzbar erwiesen. "
                    f"Diese Erfahrungen sollten für künftige Projekte dokumentiert werden."
                )
            elif project.milestones_delayed > 0:
                insights.append(
                    f"MEILENSTEIN-ANALYSE: Von {project.milestones_total} Meilensteinen wurden "
                    f"{project.milestones_completed} abgeschlossen ({completion_rate:.0f}%). "
                    f"Jedoch zeigen {project.milestones_delayed} Meilensteine Verzögerungen, was auf strukturelle "
                    f"Probleme hindeutet. Root-Cause-Analyse und Plananpassung werden empfohlen. "
                    f"Noch {remaining} Meilensteine stehen aus."
                )
            elif project.milestones_completed > 0:
                insights.append(
                    f"MEILENSTEIN-ANALYSE: Das Projekt zeigt positive Entwicklung mit {project.milestones_completed} "
                    f"von {project.milestones_total} erreichten Meilensteinen ({completion_rate:.0f}% Erfüllungsgrad). "
                    f"Alle bisherigen Meilensteine wurden termingerecht abgeschlossen. "
                    f"Bei Beibehaltung dieses Tempos ist planmäßige Fertigstellung realistisch."
                )
            else:
                # 0 milestones completed - show factual status
                insights.append(
                    f"MEILENSTEIN-ANALYSE: Von {project.milestones_total} definierten Meilensteinen wurde "
                    f"noch keiner als abgeschlossen markiert. "
                    f"Die Meilenstein-Erfassung sollte überprüft werden."
                )
        
        # Fortschrittsanalyse nur wenn nicht abgeschlossen
        if not is_completed and project.progress_percent > 0:
            if project.progress_percent >= 75:
                insights.append(
                    f"FORTSCHRITTSANALYSE: Mit {project.progress_percent:.0f}% Gesamtfortschritt befindet sich das "
                    f"Projekt in der finalen Umsetzungsphase. Der Fokus sollte nun auf Qualitätssicherung, "
                    f"Dokumentation und Abnahmevorbereitungen liegen. Change-Requests sollten kritisch geprüft "
                    f"werden, um Scope-Creep zu vermeiden und den Projektabschluss nicht zu gefährden."
                )
            elif project.progress_percent >= 40:
                insights.append(
                    f"FORTSCHRITTSANALYSE: Bei einem aktuellen Fortschritt von {project.progress_percent:.0f}% "
                    f"befindet sich das Projekt in der aktiven Umsetzungsphase. Regelmäßige Statusprüfungen "
                    f"und proaktives Stakeholder-Management sind in dieser Phase besonders wichtig. "
                    f"Abhängigkeiten zu anderen Projekten sollten kontinuierlich überwacht werden."
                )
            else:
                insights.append(
                    f"FORTSCHRITTSANALYSE: Mit {project.progress_percent:.0f}% Fortschritt befindet sich das "
                    f"Projekt noch in einer frühen Phase. Dies ist der optimale Zeitpunkt, um Scope und "
                    f"Anforderungen final zu validieren, Ressourcenplanung zu optimieren und klare "
                    f"Kommunikationswege mit allen Stakeholdern zu etablieren."
                )
        
        # 3. Umfassende Ressourcen- und Budgetanalyse
        if project.planned_effort_hours > 0 and project.actual_effort_hours > 0:
            variance = ((project.actual_effort_hours - project.planned_effort_hours) / project.planned_effort_hours) * 100
            remaining_budget = project.planned_effort_hours - project.actual_effort_hours
            if variance > 20:
                insights.append(
                    f"RESSOURCENANALYSE KRITISCH: Der aktuelle Aufwand von {project.actual_effort_hours:.0f} Stunden "
                    f"übersteigt die ursprüngliche Planung von {project.planned_effort_hours:.0f} Stunden um "
                    f"{variance:.0f}%. Diese signifikante Abweichung erfordert eine sofortige Budget-Review, "
                    f"Identifikation der Ursachen und ggf. eine Neuverhandlung des Projektumfangs mit dem Auftraggeber. "
                    f"Ohne Gegenmaßnahmen droht eine weitere Eskalation der Kosten."
                )
            elif variance > 0:
                insights.append(
                    f"RESSOURCENANALYSE: Der bisherige Aufwand von {project.actual_effort_hours:.0f} Stunden liegt "
                    f"leicht über der Planung von {project.planned_effort_hours:.0f} Stunden (+{variance:.0f}%). "
                    f"Diese moderate Abweichung sollte beobachtet werden. Es wird empfohlen, die verbleibenden "
                    f"Arbeitspakete kritisch zu prüfen und ggf. Effizienzmaßnahmen zu identifizieren, "
                    f"um eine weitere Überschreitung zu vermeiden."
                )
            else:
                insights.append(
                    f"RESSOURCENANALYSE POSITIV: Mit {project.actual_effort_hours:.0f} von {project.planned_effort_hours:.0f} "
                    f"geplanten Stunden verbraucht, liegt das Projekt im oder unter dem Budget. "
                    f"Verbleibendes Budget: {abs(remaining_budget):.0f} Stunden. Diese effiziente Projektdurchführung "
                    f"schafft Puffer für unvorhergesehene Anforderungen oder ermöglicht Kosteneinsparungen."
                )
        
        # 4. Strategische Einordnung (Komplexität & Wichtigkeit)
        if project.complexity.value >= 4 and project.importance.value >= 4:
            insights.append(
                f"STRATEGISCHE EINORDNUNG: Als Projekt mit hoher Komplexität ({project.complexity.value}/5) und "
                f"hoher strategischer Bedeutung ({project.importance.value}/5) handelt es sich um ein "
                f"unternehmenskritisches Vorhaben. Senior-Management-Sponsorship, dedizierte Top-Ressourcen und "
                f"regelmäßige Steering-Committee-Reviews sind erforderlich. Risiken bei diesem Projekt haben "
                f"direkte Auswirkungen auf Geschäftsziele."
            )
        elif project.complexity.value >= 4:
            insights.append(
                f"KOMPLEXITÄTSANALYSE: Mit einer Komplexitätsbewertung von {project.complexity.value}/5 erfordert "
                f"dieses Projekt besondere technische Expertise und strukturiertes Vorgehen. Klare Architektur-"
                f"Entscheidungen, erfahrene Ressourcen und ein robustes Change-Management sind erfolgskritisch. "
                f"Technische Reviews sollten regelmäßig durchgeführt werden."
            )
        elif project.importance.value >= 4:
            insights.append(
                f"STRATEGISCHE BEDEUTUNG: Mit einer Wichtigkeitsbewertung von {project.importance.value}/5 hat "
                f"dieses Projekt direkten Einfluss auf die Erreichung von Unternehmenszielen. Stakeholder auf "
                f"Führungsebene sollten regelmäßig informiert werden. Eine priorisierte Ressourcenzuweisung "
                f"und proaktive Risikokommunikation sind essenziell für den Projekterfolg."
            )
        else:
            insights.append(
                f"EINORDNUNG: Mit Komplexität {project.complexity.value}/5 und Wichtigkeit {project.importance.value}/5 "
                f"handelt es sich um ein Standardprojekt ohne außergewöhnliche Anforderungen. Reguläre "
                f"Projektmanagement-Methoden sind angemessen. Das Projekt kann mit Standardressourcen und "
                f"-prozessen erfolgreich umgesetzt werden."
            )
        
        # 5. Datenqualität und Bewertungssicherheit
        if project.data_quality.value <= 2:
            insights.append(
                f"DATENQUALITÄTSHINWEIS: Die Bewertung dieses Projekts basiert auf einer eingeschränkten "
                f"Datenbasis (Qualitätsstufe {project.data_quality.value}/5). Die hier getroffenen Aussagen "
                f"sollten daher mit Vorsicht interpretiert werden. Es wird dringend empfohlen, die Datenlage "
                f"zu verbessern, um fundierte Entscheidungen treffen zu können. Fehlende Informationen "
                f"sollten aktiv eingeholt werden."
            )
        elif project.data_quality.value >= 4:
            insights.append(
                f"BEWERTUNGSSICHERHEIT: Die vorliegende Analyse basiert auf einer soliden Datenbasis "
                f"(Qualitätsstufe {project.data_quality.value}/5). Die getroffenen Aussagen und Empfehlungen "
                f"sind belastbar und können als Grundlage für Management-Entscheidungen herangezogen werden. "
                f"Regelmäßige Datenaktualisierung sichert die Aussagekraft auch für zukünftige Bewertungen."
            )
        
        # 6. Kritisch-Flag mit Handlungsempfehlung (NUR für aktive Projekte)
        # Guard: Completed projects should never show escalation language
        if project.is_critical and not is_completed and len(insights) < 6:
            insights.append(
                f"KRITISCHES PROJEKT: Dieses Projekt wurde als kritisch eingestuft und erfordert "
                f"umgehende Management-Attention. Regelmäßige Statusberichte, dedizierte "
                f"Steering-Meetings und klare Verantwortlichkeiten werden empfohlen. Alle Entscheidungen "
                f"sollten dokumentiert werden."
            )
        
        # 6b. Lessons Learned für abgeschlossene Projekte
        if is_completed and len(insights) < 6:
            # Add retrospective insights instead of action items
            if project.planned_effort_hours > 0 and project.actual_effort_hours > 0:
                variance = ((project.actual_effort_hours - project.planned_effort_hours) / project.planned_effort_hours) * 100
                if abs(variance) > 10:
                    variance_text = "über" if variance > 0 else "unter"
                    insights.append(
                        f"LESSONS LEARNED – PLANUNG: Die Aufwandsabweichung von {abs(variance):.0f}% ({variance_text} Plan) "
                        f"sollte für die Kalkulation ähnlicher Projekte berücksichtigt werden. "
                        f"Eine Analyse der Abweichungsursachen unterstützt präzisere Schätzungen in Zukunft."
                    )
            
            if len(insights) < 5:
                insights.append(
                    f"EMPFEHLUNG: Projektabschluss-Dokumentation erstellen und Erfahrungen im Team teilen. "
                    f"Best Practices und Verbesserungspotenziale sollten für künftige Projekte festgehalten werden."
                )
        
        # Fallback: Ausführliche Zusammenfassung
        if len(insights) < 5 and project.summary:
            insights.append(f"PROJEKTKONTEXT: {project.summary}")
        
        return insights[:5]  # Max 5 sehr ausführliche Stichpunkte

    def _is_project_completed(self, project: ProjectScore) -> bool:
        """
        Determine if a project is completed based on status_label or progress.
        Checks common German and English status labels.
        """
        if project.status_label:
            completed_keywords = [
                "abgeschlossen", "completed", "fertig", "beendet", 
                "closed", "done", "finished", "100%", "erledigt"
            ]
            status_lower = project.status_label.lower()
            if any(keyword in status_lower for keyword in completed_keywords):
                return True
        
        # Also check if all milestones are completed
        if project.milestones_total > 0:
            if project.milestones_completed >= project.milestones_total:
                return True
        
        # Check if progress is 100%
        if project.progress_percent >= 100:
            return True
        
        return False

    def _get_status_indicator(self, status: str) -> str:
        """Get text indicator for status color (no emojis)."""
        # Return empty string - status is shown via colors in charts
        return ""

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _create_slide_title(self, text: str) -> TextBoxShape:
        """Create a standardized slide title."""
        title_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.HEADING_SIZE,
            bold=True,
            color=self.tokens.PRIMARY,
        )

        return TextBoxShape(
            position=Position(x=0.5, y=0.5, width=12.333, height=0.8),
            paragraphs=[
                TextParagraph(runs=[TextRun(text=text)], alignment="left")
            ],
            default_style=title_style,
        )

    def _create_metric_card(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        value: str,
        label: str,
        color: RgbColor,
    ) -> List:
        """Create a metric card with large number and label."""
        shapes = []

        # Value text
        value_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.METRIC_SIZE,
            bold=True,
            color=color,
        )
        value_box = TextBoxShape(
            position=Position(x=x, y=y, width=width, height=height * 0.7),
            paragraphs=[TextParagraph(runs=[TextRun(text=value)], alignment="center")],
            default_style=value_style,
        )
        shapes.append(value_box)

        # Label text
        label_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.BODY_SIZE,
            color=self.tokens.TEXT_DARK,
        )
        label_box = TextBoxShape(
            position=Position(x=x, y=y + height * 0.6, width=width, height=height * 0.3),
            paragraphs=[TextParagraph(runs=[TextRun(text=label)], alignment="center")],
            default_style=label_style,
        )
        shapes.append(label_box)

        return shapes

    def _get_status_counts(self) -> dict:
        """Get status color counts from project scores."""
        status_counts = {}
        for score in self.analysis.project_scores:
            color = score.status_color or "gray"
            status_counts[color] = status_counts.get(color, 0) + 1
        return status_counts

    def _get_status_color(self, status: str) -> RgbColor:
        """Map status string to RgbColor."""
        color_map = {
            "green": self.tokens.GREEN,
            "yellow": self.tokens.YELLOW,
            "red": self.tokens.RED,
            "gray": self.tokens.GRAY,
        }
        return color_map.get(status, self.tokens.GRAY)

    def _get_label(self, key: str) -> str:
        """Get localized label."""
        labels = {
            "de": {
                "title_subtitle": "KI-gestützte Portfolioanalyse",
                "generated": "Generiert",
                "executive_summary": "Executive Summary",
                "portfolio_overview": "Portfolio-Übersicht",
                "critical_projects": "Kritische Projekte",
                "recommendations": "Empfehlungen",
                "projects": "Projekte",
                "average": "Durchschnitt",
            },
            "en": {
                "title_subtitle": "AI-Powered Portfolio Analysis",
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

    # =========================================================================
    # Decision Points & Data Quality Methods (Portfolio Manager View)
    # =========================================================================

    def _extract_decision_points(self, project: ProjectScore) -> List[str]:
        """
        Generate decision-oriented bullet points for Portfolio Manager view.
        
        Returns actionable items that require management decisions.
        """
        decisions = []
        
        # Skip decision points for completed projects
        if self._is_project_completed(project):
            return decisions
        
        # Budget decision
        if project.planned_effort_hours > 0 and project.actual_effort_hours > 0:
            if project.actual_effort_hours > project.planned_effort_hours * 1.2:
                overrun_percent = ((project.actual_effort_hours / project.planned_effort_hours) - 1) * 100
                decisions.append(
                    f"Benötigte Entscheidung: Budget-Erhöhung um {overrun_percent:.0f}% "
                    f"({project.actual_effort_hours:.0f}h von {project.planned_effort_hours:.0f}h verbraucht)"
                )
        
        # Resource prioritization decision (only if high risk AND not already high importance)
        if self._should_show_management_attention(project):
            decisions.append(
                "Benötigte Entscheidung: Ressourcen-Priorisierung / Management-Attention erforderlich"
            )
        
        # Timeline decision
        if project.milestones_delayed > 0:
            decisions.append(
                f"Benötigte Entscheidung: Timeline-Anpassung "
                f"({project.milestones_delayed} Meilenstein(e) verzögert)"
            )
        
        # Scope decision for highly complex projects with issues
        if project.complexity.value >= 4 and project.risk.value >= 3:
            decisions.append(
                "Benötigte Entscheidung: Scope-Review – Hohe Komplexität mit erhöhtem Risiko"
            )
        
        return decisions

    def _should_show_management_attention(self, project: ProjectScore) -> bool:
        """
        Determine if "Management Attention needed" should be shown.
        
        Only show if:
        - Risk is high (>3)
        - AND project doesn't already have high importance (which implies attention)
        
        This prevents generic recommendations for projects already flagged as important.
        """
        return project.risk.value > 3 and project.importance.value < 4

    def _create_data_warning_banner(
        self, 
        warning_text: str,
        y_position: float = 1.2,
    ) -> TextBoxShape:
        """
        Create a prominent warning banner for data quality issues.
        
        Displayed at the top of project slides when data is incomplete.
        """
        warning_style = TextStyle(
            font_name=self.tokens.FONT_FAMILY,
            font_size_pt=self.tokens.BODY_SIZE,
            bold=True,
            color=RgbColor(r=180, g=80, b=0),  # Dark orange for warning
        )
        
        return TextBoxShape(
            position=Position(x=0.5, y=y_position, width=12.333, height=0.35),
            paragraphs=[
                TextParagraph(
                    runs=[TextRun(text=warning_text)],
                    alignment="center",
                )
            ],
            default_style=warning_style,
        )

    def _get_project_display_label(self, project: ProjectScore) -> str:
        """
        Get the appropriate display label for a project based on its state.
        
        Uses SanityValidator logic for consistency.
        """
        validator = SanityValidator()
        return validator.get_project_label(project)

    def _has_data_quality_warning(self, project: ProjectScore) -> bool:
        """Check if a project should show a data quality warning."""
        # No effort booked for active projects
        if project.actual_effort_hours == 0 and not self._is_project_completed(project):
            return True
        
        # Very low data quality
        if project.data_quality.value <= 2:
            return True
        
        return False

    def _has_data_mismatch(self, project: ProjectScore) -> bool:
        """
        Check if a project has contradictory data that invalidates its status.
        
        A data mismatch occurs when:
        - Project is marked as "completed" BUT:
          - 0 milestones completed (when milestones exist)
          - 0% progress
          - No effort booked at all
        
        This indicates the BlueAnt status is likely incorrect (project may be
        STOPPED or CRITICAL, not successfully completed).
        """
        is_completed = self._is_project_completed(project)
        
        if not is_completed:
            return False
        
        # Check for contradictions
        contradictions = []
        
        # Mismatch: Completed but 0 milestones reached
        if project.milestones_total > 0 and project.milestones_completed == 0:
            contradictions.append("0 von {} Meilensteinen erreicht".format(project.milestones_total))
        
        # Mismatch: Completed but 0% progress
        if project.progress_percent == 0:
            contradictions.append("0% Fortschritt")
        
        # Mismatch: Completed but no effort booked
        if project.actual_effort_hours == 0 and project.planned_effort_hours > 0:
            contradictions.append("Keine Aufwände gebucht")
        
        # If any contradiction exists, it's a data mismatch
        return len(contradictions) > 0

    def _get_data_mismatch_details(self, project: ProjectScore) -> List[str]:
        """Get a list of specific data contradictions for a project."""
        contradictions = []
        
        if project.milestones_total > 0 and project.milestones_completed == 0:
            contradictions.append(f"0 von {project.milestones_total} Meilensteinen erreicht")
        
        if project.progress_percent == 0:
            contradictions.append("0% Fortschritt gemeldet")
        
        if project.actual_effort_hours == 0 and project.planned_effort_hours > 0:
            contradictions.append("Keine Ist-Aufwände gebucht")
        
        if project.milestones_delayed > 0:
            contradictions.append(f"{project.milestones_delayed} verzögerte Meilensteine")
        
        return contradictions

    def _get_data_warning_text(self, project: ProjectScore) -> Optional[str]:
        """Get the appropriate warning text for a project's data issues (no emojis)."""
        # Skip all warning banners - data quality info is in the analysis text
        return None
