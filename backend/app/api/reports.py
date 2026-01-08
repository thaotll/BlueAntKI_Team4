"""
Report generation API endpoints.
Now supports AI-generated presentation structures with visualizations.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from app.models.scoring import PortfolioAnalysis
from app.services.pptx_builder import PptxBuilder
from app.services.pptx_renderer import PptxRenderer
from app.services.docx_builder import DocxBuilder
from app.services.docx_renderer import DocxRenderer
from app.ai.gemini import GeminiService, GeminiError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ReportOptions(BaseModel):
    """Options for report generation."""

    language: str = Field(
        default="de",
        description="Report language (de or en)",
        pattern="^(de|en)$",
    )
    use_ai_structure: bool = Field(
        default=False,
        description="Use AI to dynamically generate presentation structure (False = use fixed structure with radar charts per project)",
    )
    include_charts: bool = Field(
        default=True,
        description="Include chart visualizations in the report",
    )
    detail_level: str = Field(
        default="compact",
        description="Detail level for project insights: 'compact' (short statements) or 'detailed' (fuller explanations)",
        pattern="^(compact|detailed)$",
    )


class GenerateReportRequest(BaseModel):
    """Request to generate a PowerPoint report."""

    analysis: PortfolioAnalysis = Field(
        ..., description="The portfolio analysis data to generate report from"
    )
    options: Optional[ReportOptions] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/pptx",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": {}
            },
            "description": "PowerPoint file",
        }
    },
)
async def generate_pptx_report(request: GenerateReportRequest):
    """
    Generate a PowerPoint report from portfolio analysis.
    
    Supports AI-generated presentation structures with visualizations
    for optimal data presentation with minimal text.

    Returns the PPTX file as a downloadable attachment.
    """
    options = request.options or ReportOptions()

    logger.info(
        f"Generating PPTX report for portfolio '{request.analysis.portfolio_name}' "
        f"(language={options.language}, use_ai_structure={options.use_ai_structure}, detail_level={options.detail_level})"
    )

    try:
        # Build presentation model
        builder = PptxBuilder(
            analysis=request.analysis,
            language=options.language,
            detail_level=options.detail_level,
        )
        
        # Use AI to generate optimal structure if enabled
        if options.use_ai_structure:
            try:
                gemini = GeminiService()
                ai_structure = await gemini.generate_presentation_structure(request.analysis)
                logger.info(f"AI generated {len(ai_structure.slides)} slides")
                presentation_model = builder.build_from_ai_structure(ai_structure)
            except GeminiError as e:
                logger.warning(f"AI structure generation failed, using default: {e}")
                presentation_model = builder.build()
            except Exception as e:
                logger.warning(f"Unexpected error in AI generation, using default: {e}")
                presentation_model = builder.build()
        else:
            presentation_model = builder.build()

        # Render to PPTX bytes
        renderer = PptxRenderer()
        pptx_bytes = renderer.render(presentation_model)

        # Create safe filename
        safe_name = "".join(
            c for c in request.analysis.portfolio_name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        if not safe_name:
            safe_name = "Portfolio"
        filename = f"{safe_name}_Report.pptx"

        logger.info(f"Generated report: {filename} ({len(pptx_bytes)} bytes)")

        return Response(
            content=pptx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        logger.error(f"Failed to generate PPTX report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")


@router.post(
    "/docx",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {}
            },
            "description": "Word document file",
        }
    },
)
async def generate_docx_report(request: GenerateReportRequest):
    """
    Generate a Word document report from portfolio analysis.

    Returns the DOCX file as a downloadable attachment.
    """
    options = request.options or ReportOptions()

    logger.info(
        f"Generating DOCX report for portfolio '{request.analysis.portfolio_name}' "
        f"(language={options.language})"
    )

    try:
        # Build document model
        builder = DocxBuilder(
            analysis=request.analysis,
            language=options.language,
        )
        document_model = builder.build()

        # Render to DOCX bytes
        renderer = DocxRenderer()
        docx_bytes = renderer.render(document_model)

        # Create safe filename
        safe_name = "".join(
            c for c in request.analysis.portfolio_name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        if not safe_name:
            safe_name = "Portfolio"
        filename = f"{safe_name}_Report.docx"

        logger.info(f"Generated report: {filename} ({len(docx_bytes)} bytes)")

        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception as e:
        logger.error(f"Failed to generate DOCX report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
