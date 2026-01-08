"""
Chart generation utilities using matplotlib.
Generates charts as PNG bytes for embedding in PowerPoint presentations.
"""

import logging
from io import BytesIO
from typing import List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.figure import Figure

from app.models.pptx import (
    ChartType,
    ChartShape,
    ChartDataPoint,
    ChartDataSeries,
    RgbColor,
)

logger = logging.getLogger(__name__)


class ChartDesignTokens:
    """Design tokens for consistent chart styling."""
    
    # BlueAnt brand colors
    PRIMARY = (1/255, 107/255, 213/255)  # #016bd5
    ACCENT = (0/255, 141/255, 202/255)   # #008dca
    
    # Chart color palette (for multiple data points)
    PALETTE = [
        (1/255, 107/255, 213/255),     # BlueAnt blue
        (0/255, 141/255, 202/255),     # Light blue
        (52/255, 168/255, 83/255),     # Green
        (251/255, 188/255, 4/255),     # Yellow/Warning
        (234/255, 67/255, 53/255),     # Red
        (103/255, 58/255, 183/255),    # Purple
        (0/255, 172/255, 193/255),     # Cyan
        (255/255, 112/255, 67/255),    # Orange
    ]
    
    # Status colors
    STATUS_COLORS = {
        'green': (52/255, 168/255, 83/255),
        'yellow': (251/255, 188/255, 4/255),
        'red': (234/255, 67/255, 53/255),
        'gray': (128/255, 128/255, 128/255),
    }
    
    # Typography
    FONT_FAMILY = 'sans-serif'
    TITLE_SIZE = 14
    LABEL_SIZE = 11
    TICK_SIZE = 10
    
    # Chart dimensions (in inches, optimized for PowerPoint)
    DEFAULT_WIDTH = 10
    DEFAULT_HEIGHT = 5
    
    # Background
    BACKGROUND_COLOR = 'white'
    GRID_COLOR = '#e0e0e0'
    TEXT_COLOR = '#333333'


def rgb_to_tuple(color: RgbColor) -> Tuple[float, float, float]:
    """Convert RgbColor model to matplotlib tuple."""
    return (color.r / 255, color.g / 255, color.b / 255)


def get_color_for_index(index: int) -> Tuple[float, float, float]:
    """Get color from palette for given index."""
    return ChartDesignTokens.PALETTE[index % len(ChartDesignTokens.PALETTE)]


class ChartGenerator:
    """
    Generates matplotlib charts as PNG bytes.
    
    Usage:
        generator = ChartGenerator()
        png_bytes = generator.generate(chart_shape)
    """
    
    def __init__(self, dpi: int = 150):
        self.dpi = dpi
        self.tokens = ChartDesignTokens()
    
    def generate(self, chart: ChartShape) -> bytes:
        """
        Generate chart as PNG bytes based on ChartShape model.
        
        Args:
            chart: ChartShape model with data and configuration
            
        Returns:
            PNG image as bytes
        """
        logger.debug(f"Generating {chart.chart_type.value} chart")
        
        # Select generation method based on chart type
        generators = {
            ChartType.BAR: self._generate_bar_chart,
            ChartType.HORIZONTAL_BAR: self._generate_horizontal_bar_chart,
            ChartType.PIE: self._generate_pie_chart,
            ChartType.DONUT: self._generate_donut_chart,
            ChartType.SCATTER: self._generate_scatter_chart,
            ChartType.RADAR: self._generate_radar_chart,
            ChartType.LINE: self._generate_line_chart,
            ChartType.STACKED_BAR: self._generate_stacked_bar_chart,
        }
        
        generator_func = generators.get(chart.chart_type)
        if not generator_func:
            logger.warning(f"Unsupported chart type: {chart.chart_type}")
            return self._generate_placeholder(chart)
        
        try:
            return generator_func(chart)
        except Exception as e:
            logger.error(f"Chart generation failed: {e}", exc_info=True)
            return self._generate_placeholder(chart)
    
    def _create_figure(
        self,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> Tuple[Figure, plt.Axes]:
        """Create a new figure with consistent styling."""
        w = width or self.tokens.DEFAULT_WIDTH
        h = height or self.tokens.DEFAULT_HEIGHT
        
        fig, ax = plt.subplots(figsize=(w, h), facecolor=self.tokens.BACKGROUND_COLOR)
        ax.set_facecolor(self.tokens.BACKGROUND_COLOR)
        
        # Set font properties
        plt.rcParams['font.family'] = self.tokens.FONT_FAMILY
        plt.rcParams['font.size'] = self.tokens.LABEL_SIZE
        
        return fig, ax
    
    def _finalize_figure(self, fig: Figure, title: Optional[str] = None) -> bytes:
        """Add title, adjust layout, and convert to bytes."""
        if title:
            fig.suptitle(
                title,
                fontsize=self.tokens.TITLE_SIZE,
                fontweight='bold',
                color=self.tokens.TEXT_COLOR,
            )
        
        fig.tight_layout()
        
        # Save to bytes
        buffer = BytesIO()
        fig.savefig(
            buffer,
            format='png',
            dpi=self.dpi,
            bbox_inches='tight',
            facecolor=self.tokens.BACKGROUND_COLOR,
            edgecolor='none',
        )
        plt.close(fig)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def _generate_bar_chart(self, chart: ChartShape) -> bytes:
        """Generate vertical bar chart."""
        fig, ax = self._create_figure()
        
        if chart.data_points:
            labels = [dp.label for dp in chart.data_points]
            values = [dp.value for dp in chart.data_points]
            colors = [
                rgb_to_tuple(dp.color) if dp.color else get_color_for_index(i)
                for i, dp in enumerate(chart.data_points)
            ]
            
            bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=0.5)
            
            # Add value labels on bars
            if chart.show_values:
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.annotate(
                        f'{value:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center',
                        va='bottom',
                        fontsize=self.tokens.TICK_SIZE,
                        fontweight='bold',
                    )
        
        # Styling
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='x', rotation=45 if len(chart.data_points) > 5 else 0)
        
        if chart.y_axis_label:
            ax.set_ylabel(chart.y_axis_label)
        if chart.x_axis_label:
            ax.set_xlabel(chart.x_axis_label)
        
        if chart.show_grid:
            ax.yaxis.grid(True, color=self.tokens.GRID_COLOR, linestyle='--', alpha=0.7)
        
        return self._finalize_figure(fig, chart.title)
    
    def _generate_horizontal_bar_chart(self, chart: ChartShape) -> bytes:
        """Generate horizontal bar chart."""
        fig, ax = self._create_figure()
        
        if chart.data_points:
            labels = [dp.label for dp in chart.data_points]
            values = [dp.value for dp in chart.data_points]
            colors = [
                rgb_to_tuple(dp.color) if dp.color else get_color_for_index(i)
                for i, dp in enumerate(chart.data_points)
            ]
            
            # Reverse for top-to-bottom display
            y_pos = np.arange(len(labels))
            bars = ax.barh(y_pos, values, color=colors, edgecolor='white', linewidth=0.5)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels)
            
            # Add value labels
            if chart.show_values:
                for bar, value in zip(bars, values):
                    width = bar.get_width()
                    ax.annotate(
                        f'{value:.1f}',
                        xy=(width, bar.get_y() + bar.get_height() / 2),
                        xytext=(3, 0),
                        textcoords="offset points",
                        ha='left',
                        va='center',
                        fontsize=self.tokens.TICK_SIZE,
                        fontweight='bold',
                    )
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.invert_yaxis()  # Top-to-bottom
        
        if chart.x_axis_label:
            ax.set_xlabel(chart.x_axis_label)
        
        return self._finalize_figure(fig, chart.title)
    
    def _generate_pie_chart(self, chart: ChartShape) -> bytes:
        """Generate pie chart."""
        fig, ax = self._create_figure(height=6)
        
        if chart.data_points:
            labels = [dp.label for dp in chart.data_points]
            values = [dp.value for dp in chart.data_points]
            colors = [
                rgb_to_tuple(dp.color) if dp.color else get_color_for_index(i)
                for i, dp in enumerate(chart.data_points)
            ]
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(
                values,
                labels=labels if not chart.show_legend else None,
                colors=colors,
                autopct='%1.1f%%' if chart.show_values else '',
                startangle=90,
                pctdistance=0.75,
            )
            
            # Style autopct text
            for autotext in autotexts:
                autotext.set_fontsize(self.tokens.TICK_SIZE)
                autotext.set_fontweight('bold')
            
            if chart.show_legend:
                ax.legend(
                    wedges,
                    labels,
                    title="",
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1),
                )
        
        ax.axis('equal')
        return self._finalize_figure(fig, chart.title)
    
    def _generate_donut_chart(self, chart: ChartShape) -> bytes:
        """Generate donut chart (pie with hole)."""
        fig, ax = self._create_figure(height=6)
        
        if chart.data_points:
            labels = [dp.label for dp in chart.data_points]
            values = [dp.value for dp in chart.data_points]
            colors = [
                rgb_to_tuple(dp.color) if dp.color else get_color_for_index(i)
                for i, dp in enumerate(chart.data_points)
            ]
            
            # Create donut chart
            wedges, texts, autotexts = ax.pie(
                values,
                colors=colors,
                autopct='%1.1f%%' if chart.show_values else '',
                startangle=90,
                pctdistance=0.8,
                wedgeprops=dict(width=0.5),  # Creates the hole
            )
            
            for autotext in autotexts:
                autotext.set_fontsize(self.tokens.TICK_SIZE)
                autotext.set_fontweight('bold')
            
            if chart.show_legend:
                ax.legend(
                    wedges,
                    labels,
                    loc="center left",
                    bbox_to_anchor=(1, 0, 0.5, 1),
                )
            
            # Add center text with total
            total = sum(values)
            ax.text(0, 0, f'{int(total)}', ha='center', va='center',
                   fontsize=24, fontweight='bold', color=self.tokens.TEXT_COLOR)
            ax.text(0, -0.15, 'Gesamt', ha='center', va='center',
                   fontsize=self.tokens.LABEL_SIZE, color=self.tokens.TEXT_COLOR)
        
        ax.axis('equal')
        return self._finalize_figure(fig, chart.title)
    
    def _generate_scatter_chart(self, chart: ChartShape) -> bytes:
        """Generate scatter plot (e.g., Risk-Urgency matrix)."""
        fig, ax = self._create_figure()
        
        if chart.x_values and chart.y_values:
            colors = [self.tokens.PRIMARY] * len(chart.x_values)
            sizes = [100] * len(chart.x_values)
            
            scatter = ax.scatter(
                chart.x_values,
                chart.y_values,
                c=colors,
                s=sizes,
                alpha=0.7,
                edgecolors='white',
                linewidth=1,
            )
            
            # Add point labels
            if chart.point_labels:
                for i, label in enumerate(chart.point_labels):
                    ax.annotate(
                        label,
                        (chart.x_values[i], chart.y_values[i]),
                        xytext=(5, 5),
                        textcoords='offset points',
                        fontsize=self.tokens.TICK_SIZE - 1,
                        alpha=0.8,
                    )
            
            # Add quadrant lines at midpoint
            x_mid = (min(chart.x_values) + max(chart.x_values)) / 2
            y_mid = (min(chart.y_values) + max(chart.y_values)) / 2
            ax.axhline(y=y_mid, color=self.tokens.GRID_COLOR, linestyle='--', alpha=0.5)
            ax.axvline(x=x_mid, color=self.tokens.GRID_COLOR, linestyle='--', alpha=0.5)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        if chart.x_axis_label:
            ax.set_xlabel(chart.x_axis_label, fontsize=self.tokens.LABEL_SIZE)
        if chart.y_axis_label:
            ax.set_ylabel(chart.y_axis_label, fontsize=self.tokens.LABEL_SIZE)
        
        ax.grid(True, alpha=0.3)
        
        return self._finalize_figure(fig, chart.title)
    
    def _generate_radar_chart(self, chart: ChartShape) -> bytes:
        """Generate radar/spider chart for U/I/C/R/DQ profiles."""
        fig, ax = plt.subplots(
            figsize=(self.tokens.DEFAULT_HEIGHT + 1, self.tokens.DEFAULT_HEIGHT + 1),
            subplot_kw=dict(polar=True),
            facecolor=self.tokens.BACKGROUND_COLOR,
        )
        
        if chart.data_points:
            labels = [dp.label for dp in chart.data_points]
            values = [dp.value for dp in chart.data_points]
            
            # Number of variables
            num_vars = len(labels)
            
            # Compute angle for each axis (start from top, go clockwise)
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            
            # Complete the loop
            plot_values = values + [values[0]]
            plot_angles = angles + [angles[0]]
            
            # Plot
            ax.plot(plot_angles, plot_values, 'o-', linewidth=2, color=self.tokens.PRIMARY)
            ax.fill(plot_angles, plot_values, alpha=0.25, color=self.tokens.PRIMARY)
            
            # Remove default tick labels
            ax.set_xticks(angles)
            ax.set_xticklabels([])  # Clear default labels
            
            # Add custom labels positioned further outside with values
            label_distance = 5.8  # Distance from center for labels
            for i, (angle, label, value) in enumerate(zip(angles, labels, values)):
                # Calculate position
                x = angle
                
                # Determine horizontal alignment based on angle
                angle_deg = np.degrees(angle) % 360
                if 45 < angle_deg < 135:
                    ha = 'left'
                elif 225 < angle_deg < 315:
                    ha = 'right'
                else:
                    ha = 'center'
                
                # Determine vertical alignment
                if angle_deg < 45 or angle_deg > 315:
                    va = 'bottom'
                elif 135 < angle_deg < 225:
                    va = 'top'
                else:
                    va = 'center'
                
                # Add label with value
                label_text = f"{label}\n({value:.0f})"
                ax.text(
                    x, label_distance, label_text,
                    ha=ha, va=va,
                    fontsize=self.tokens.LABEL_SIZE,
                    fontweight='normal',
                    color=self.tokens.TEXT_COLOR,
                )
            
            # Set y-axis limits (scores are 1-5, with room for labels)
            ax.set_ylim(0, 5)
            ax.set_yticks([1, 2, 3, 4, 5])
            ax.set_yticklabels(['1', '2', '3', '4', '5'], fontsize=self.tokens.TICK_SIZE - 1)
            
        ax.set_facecolor(self.tokens.BACKGROUND_COLOR)
        
        # Start from top (12 o'clock position)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)  # Clockwise
        
        return self._finalize_figure(fig, chart.title)
    
    def _generate_line_chart(self, chart: ChartShape) -> bytes:
        """Generate line chart."""
        fig, ax = self._create_figure()
        
        if chart.series and chart.categories:
            x = np.arange(len(chart.categories))
            
            for i, series in enumerate(chart.series):
                color = rgb_to_tuple(series.color) if series.color else get_color_for_index(i)
                ax.plot(
                    x,
                    series.values,
                    'o-',
                    label=series.name,
                    color=color,
                    linewidth=2,
                    markersize=6,
                )
            
            ax.set_xticks(x)
            ax.set_xticklabels(chart.categories)
            
            if chart.show_legend:
                ax.legend(loc='best')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        if chart.show_grid:
            ax.grid(True, alpha=0.3)
        
        return self._finalize_figure(fig, chart.title)
    
    def _generate_stacked_bar_chart(self, chart: ChartShape) -> bytes:
        """Generate stacked bar chart."""
        fig, ax = self._create_figure()
        
        if chart.series and chart.categories:
            x = np.arange(len(chart.categories))
            width = 0.6
            
            bottom = np.zeros(len(chart.categories))
            
            for i, series in enumerate(chart.series):
                color = rgb_to_tuple(series.color) if series.color else get_color_for_index(i)
                ax.bar(
                    x,
                    series.values,
                    width,
                    label=series.name,
                    bottom=bottom,
                    color=color,
                    edgecolor='white',
                    linewidth=0.5,
                )
                bottom += np.array(series.values)
            
            ax.set_xticks(x)
            ax.set_xticklabels(chart.categories)
            
            if chart.show_legend:
                ax.legend(loc='upper right')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        return self._finalize_figure(fig, chart.title)
    
    def _generate_placeholder(self, chart: ChartShape) -> bytes:
        """Generate placeholder for unsupported chart types."""
        fig, ax = self._create_figure()
        
        ax.text(
            0.5, 0.5,
            f'Chart: {chart.chart_type.value}',
            ha='center',
            va='center',
            fontsize=20,
            color='gray',
            transform=ax.transAxes,
        )
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return self._finalize_figure(fig, chart.title)


# =============================================================================
# Convenience functions for common chart types
# =============================================================================


def create_score_bar_chart(
    labels: List[str],
    values: List[float],
    title: str = "Durchschnittliche Scores",
) -> ChartShape:
    """Create a bar chart for U/I/C/R/DQ scores."""
    # Color-code based on score value
    def score_color(value: float) -> RgbColor:
        if value >= 4:
            return RgbColor(r=234, g=67, b=53)  # Red - high urgency/risk
        elif value >= 3:
            return RgbColor(r=251, g=188, b=4)  # Yellow - medium
        else:
            return RgbColor(r=52, g=168, b=83)  # Green - low
    
    data_points = [
        ChartDataPoint(label=label, value=value, color=score_color(value))
        for label, value in zip(labels, values)
    ]
    
    return ChartShape(
        position=None,  # Will be set by builder
        chart_type=ChartType.BAR,
        title=title,
        data_points=data_points,
        show_values=True,
        y_axis_label="Score (1-5)",
    )


def create_status_pie_chart(
    status_counts: dict,
    title: str = "Projektstatus-Verteilung",
) -> ChartShape:
    """Create a pie chart for project status distribution."""
    status_colors = {
        'green': RgbColor(r=52, g=168, b=83),
        'yellow': RgbColor(r=251, g=188, b=4),
        'red': RgbColor(r=234, g=67, b=53),
        'gray': RgbColor(r=128, g=128, b=128),
    }
    
    status_labels = {
        'green': 'Grün',
        'yellow': 'Gelb',
        'red': 'Rot',
        'gray': 'Keine Angabe',
    }
    
    data_points = [
        ChartDataPoint(
            label=status_labels.get(status, status),
            value=count,
            color=status_colors.get(status),
        )
        for status, count in status_counts.items()
        if count > 0
    ]
    
    return ChartShape(
        position=None,
        chart_type=ChartType.DONUT,
        title=title,
        data_points=data_points,
        show_values=True,
        show_legend=True,
    )


def create_risk_urgency_scatter(
    projects: List[dict],
    title: str = "Risiko-Dringlichkeits-Matrix",
) -> ChartShape:
    """Create a scatter plot for risk vs urgency."""
    x_values = [p.get('risk', 3) for p in projects]
    y_values = [p.get('urgency', 3) for p in projects]
    labels = [p.get('name', '')[:15] for p in projects]  # Truncate names
    
    return ChartShape(
        position=None,
        chart_type=ChartType.SCATTER,
        title=title,
        x_values=x_values,
        y_values=y_values,
        point_labels=labels,
        x_axis_label="Risiko",
        y_axis_label="Dringlichkeit",
    )


def create_project_radar_chart(
    project_name: str,
    urgency: float,
    importance: float,
    complexity: float,
    risk: float,
    data_quality: float,
) -> ChartShape:
    """Create a radar chart for single project U/I/C/R/DQ profile."""
    return ChartShape(
        position=None,
        chart_type=ChartType.RADAR,
        title="",  # No title - project name is already in slide title
        data_points=[
            ChartDataPoint(label="Dringlichkeit (U)", value=urgency),
            ChartDataPoint(label="Wichtigkeit (I)", value=importance),
            ChartDataPoint(label="Komplexität (C)", value=complexity),
            ChartDataPoint(label="Risiko (R)", value=risk),
            ChartDataPoint(label="Datenqualität (DQ)", value=data_quality),
        ],
        show_values=False,
    )


def get_chart_generator() -> ChartGenerator:
    """Get a ChartGenerator instance."""
    return ChartGenerator()


