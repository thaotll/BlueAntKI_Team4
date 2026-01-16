"""
OpenRouter LLM client for project scoring and portfolio analysis.

OpenRouter provides access to multiple LLM providers through a unified API.
Free tier models available:
- mistralai/devstral-2512:free
- google/gemini-2.0-flash-exp:free

Uses OpenAI-compatible API format.
"""

import json
import logging
import re
from typing import List, Optional

import httpx

from app.config import get_settings, OPENROUTER_MODELS
from app.models.domain import NormalizedPortfolio, NormalizedProject
from app.models.scoring import PortfolioAnalysis, ProjectScore, ScoreValue
from app.ai.prompts import (
    PORTFOLIO_ANALYSIS_PROMPT_TEMPLATE,
    SCORING_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
    PRESENTATION_STRUCTURE_SYSTEM_PROMPT,
    PRESENTATION_STRUCTURE_PROMPT_TEMPLATE,
    format_project_for_prompt,
    format_scores_for_portfolio_prompt,
    format_analysis_for_presentation_prompt,
)
from app.models.pptx import (
    AIPresentationStructure,
    AISlideSpec,
    SlideVisualization,
    SlideType,
    VisualizationType,
)
from app.services.sanity_validator import SanityValidator

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Exception raised for OpenRouter API errors."""
    pass


class OpenRouterService:
    """
    Client for OpenRouter-based project scoring.
    
    Provides access to multiple LLM models through OpenRouter's unified API.
    Compatible with the same interface as GeminiService for easy swapping.

    Implements the 2-phase analysis:
    1. Phase 1: Score individual projects (U/I/C/R/DQ)
    2. Phase 2: Generate portfolio-level analysis
    
    Available free models:
    - devstral: mistralai/devstral-2512:free (Code-focused)
    - gemini-flash: google/gemini-2.0-flash-exp:free (Fast, versatile)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or settings.openrouter_base_url
        self.app_name = settings.openrouter_app_name
        self.app_url = settings.openrouter_app_url
        
        # Resolve model shortname to full model ID
        raw_model = model_name or settings.openrouter_model
        if raw_model in OPENROUTER_MODELS:
            self.model_name = OPENROUTER_MODELS[raw_model]
            logger.info(f"Resolved model shortname '{raw_model}' to '{self.model_name}'")
        else:
            self.model_name = raw_model

        # Initialize headers (always needed for error handling)
        self.headers = {}

        if not self.api_key:
            logger.warning("OpenRouter API key not configured!")
            return

        # Validate API key format
        if not self.api_key.startswith("sk-or-"):
            logger.warning(f"OpenRouter API key has unexpected format (should start with 'sk-or-')")
        
        # Setup HTTP client with proper headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.app_url or "https://github.com/blueant-portfolio",
            "X-Title": self.app_name,
        }

        # Log key info (masked for security)
        key_preview = f"{self.api_key[:10]}...{self.api_key[-4:]}" if len(self.api_key) > 14 else "***"
        logger.info(f"OpenRouter service initialized with model: {self.model_name}, key: {key_preview}")

    async def _chat_completion(
        self,
        messages: List[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        max_retries: int = 3,
    ) -> str:
        """
        Send a chat completion request to OpenRouter with retry logic.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            max_retries: Maximum number of retry attempts
            
        Returns:
            The assistant's response text
        """
        if not self.api_key:
            raise OpenRouterError("OpenRouter API key not configured")

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error = None
        
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=180.0) as client:
                try:
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt + 1}/{max_retries}...")
                        # Slight temperature increase on retry to get different output
                        payload["temperature"] = min(temperature + (attempt * 0.1), 1.0)
                    
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if "error" in data:
                        error_msg = data.get("error", {})
                        if isinstance(error_msg, dict):
                            error_msg = error_msg.get("message", str(error_msg))
                        last_error = OpenRouterError(f"OpenRouter API error: {error_msg}")
                        logger.warning(f"API error on attempt {attempt + 1}: {error_msg}")
                        continue
                    
                    if "choices" not in data or len(data["choices"]) == 0:
                        logger.warning(f"OpenRouter response missing choices on attempt {attempt + 1}")
                        last_error = OpenRouterError("No response choices returned")
                        continue
                    
                    content = data["choices"][0]["message"]["content"]
                    
                    # Log response for debugging (truncated)
                    if content:
                        logger.debug(f"OpenRouter response (first 500 chars): {content[:500]}")
                    else:
                        logger.warning(f"OpenRouter returned empty content on attempt {attempt + 1}!")
                        # Check for reasoning_content (DeepSeek R1 format)
                        reasoning = data["choices"][0]["message"].get("reasoning_content", "")
                        if reasoning:
                            logger.info("DeepSeek R1 reasoning found, extracting from it...")
                            content = reasoning
                    
                    if not content:
                        last_error = OpenRouterError("OpenRouter returned empty response content")
                        continue
                    
                    # Success!
                    return content
                    
                except httpx.HTTPStatusError as e:
                    error_detail = ""
                    try:
                        error_data = e.response.json()
                        error_detail = error_data.get("error", {}).get("message", str(e))
                    except:
                        error_detail = str(e)
                    last_error = OpenRouterError(f"OpenRouter HTTP error: {error_detail}")
                    logger.warning(f"HTTP error on attempt {attempt + 1}: {error_detail}")
                    
                    # Don't retry on 4xx errors (except 429 rate limit)
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                        raise last_error
                        
                except httpx.RequestError as e:
                    last_error = OpenRouterError(f"OpenRouter request failed: {e}")
                    logger.warning(f"Request error on attempt {attempt + 1}: {e}")
        
        # All retries exhausted
        raise last_error or OpenRouterError("All retry attempts failed")

    def _repair_json(self, text: str) -> str:
        """Attempt to repair common JSON issues from LLM responses."""
        # Remove trailing commas before } or ]
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix missing commas between objects in arrays: }{ -> },{
        text = re.sub(r'\}(\s*)\{', r'},\1{', text)
        
        # Fix missing commas after string values: "value" "key" -> "value", "key"
        text = re.sub(r'"\s*\n\s*"', '",\n"', text)
        
        # Fix single quotes to double quotes (common LLM mistake)
        # Only for property names and string values, not in content
        # This is tricky, so we do a conservative approach
        
        # Remove control characters that break JSON
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
        
        # Fix unescaped newlines in strings (replace with \n)
        # This is complex, skip for now
        
        return text

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response text with robust error handling."""
        if not text or not text.strip():
            logger.error("Empty text provided to _extract_json")
            raise OpenRouterError("LLM returned empty response")
        
        original_text = text
        
        # Try to find JSON in code blocks first
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(code_block_pattern, text)
        if matches:
            text = matches[0]
            logger.debug("Found JSON in code block")

        text = text.strip()
        
        # Handle DeepSeek R1's thinking format - skip <think> blocks
        think_pattern = r"<think>[\s\S]*?</think>"
        text = re.sub(think_pattern, "", text).strip()
        
        # Handle potential markdown or extra text
        # Find the first { and last }
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]
        else:
            # Try to find array format
            start_idx = text.find('[')
            end_idx = text.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                text = text[start_idx:end_idx + 1]
                # Wrap in object if it's an array
                text = '{"projects": ' + text + '}'
                logger.debug("Found array format, wrapped in object")

        # First attempt: try parsing as-is
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}, attempting repair...")
        
        # Second attempt: repair common JSON issues
        repaired_text = self._repair_json(text)
        try:
            result = json.loads(repaired_text)
            logger.info("JSON repair successful")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Repaired JSON still invalid: {e}")
        
        # Third attempt: try to extract just the projects array if present
        projects_pattern = r'"projects"\s*:\s*\[([\s\S]*?)\]'
        projects_match = re.search(projects_pattern, text)
        if projects_match:
            try:
                projects_text = '[' + projects_match.group(1) + ']'
                projects_text = self._repair_json(projects_text)
                projects = json.loads(projects_text)
                logger.info("Extracted projects array successfully")
                return {"projects": projects}
            except json.JSONDecodeError:
                pass
        
        # Log detailed error info
        logger.error(f"Failed to parse JSON after all attempts")
        logger.error(f"Extracted text (first 1500 chars): {text[:1500]}")
        logger.error(f"Original text (first 500 chars): {original_text[:500]}")
        raise OpenRouterError(f"Failed to parse LLM response as JSON: Invalid JSON structure")

    def _parse_project_score(self, data: dict) -> ProjectScore:
        """Parse a single project score from LLM response."""
        return ProjectScore(
            project_id=data.get("project_id", "unknown"),
            project_name=data.get("project_name", "Unknown"),
            urgency=ScoreValue(
                value=data.get("urgency", {}).get("value", 3),
                reasoning=data.get("urgency", {}).get("reasoning", "Keine Begründung"),
            ),
            importance=ScoreValue(
                value=data.get("importance", {}).get("value", 3),
                reasoning=data.get("importance", {}).get("reasoning", "Keine Begründung"),
            ),
            complexity=ScoreValue(
                value=data.get("complexity", {}).get("value", 3),
                reasoning=data.get("complexity", {}).get("reasoning", "Keine Begründung"),
            ),
            risk=ScoreValue(
                value=data.get("risk", {}).get("value", 3),
                reasoning=data.get("risk", {}).get("reasoning", "Keine Begründung"),
            ),
            data_quality=ScoreValue(
                value=data.get("data_quality", {}).get("value", 3),
                reasoning=data.get("data_quality", {}).get("reasoning", "Keine Begründung"),
            ),
            is_critical=data.get("is_critical", False),
            summary=data.get("summary", ""),
            detailed_analysis=data.get("detailed_analysis", ""),
        )

    async def score_projects(
        self,
        projects: List[NormalizedProject],
        batch_size: int = 10,
        max_json_retries: int = 2,
    ) -> List[ProjectScore]:
        """
        Phase 1: Score multiple projects using OpenRouter.
        
        Includes retry logic for JSON parsing failures.
        """
        if not self.api_key:
            raise OpenRouterError("OpenRouter API key not configured")

        all_scores: List[ProjectScore] = []

        for i in range(0, len(projects), batch_size):
            batch = projects[i : i + batch_size]
            logger.info(
                f"Scoring projects batch {i // batch_size + 1} ({len(batch)} projects) "
                f"via OpenRouter ({self.model_name})"
            )

            project_data_text = "\n".join(
                format_project_for_prompt(p.model_dump()) for p in batch
            )

            prompt = SCORING_PROMPT_TEMPLATE.format(project_data=project_data_text)
            
            batch_scores = None
            last_error = None
            
            # Retry loop for JSON parsing issues
            for json_attempt in range(max_json_retries + 1):
                try:
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ]
                    
                    # Adjust temperature on retry to get different output
                    temp = 0.7 + (json_attempt * 0.15)
                    response_text = await self._chat_completion(messages, temperature=min(temp, 1.0))
                    response_data = self._extract_json(response_text)
                    
                    batch_scores = []
                    for score_data in response_data.get("projects", []):
                        try:
                            score = self._parse_project_score(score_data)
                            batch_scores.append(score)
                        except Exception as e:
                            logger.warning(f"Failed to parse score for project: {e}")
                            batch_scores.append(
                                ProjectScore(
                                    project_id=score_data.get("project_id", "unknown"),
                                    project_name=score_data.get("project_name", "Unknown"),
                                    urgency=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    importance=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    complexity=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    risk=ScoreValue(value=3, reasoning="Parsing-Fehler"),
                                    data_quality=ScoreValue(value=1, reasoning="Fehler bei der Analyse"),
                                    is_critical=False,
                                    summary="Fehler bei der Analyse dieses Projekts",
                                    detailed_analysis="Die Analyse konnte nicht vollständig durchgeführt werden.",
                                )
                            )
                    
                    # Success - break out of retry loop
                    break
                    
                except OpenRouterError as e:
                    last_error = e
                    if "Failed to parse LLM response as JSON" in str(e):
                        if json_attempt < max_json_retries:
                            logger.warning(f"JSON parsing failed, retrying ({json_attempt + 1}/{max_json_retries})...")
                            continue
                    # Re-raise other errors or final attempt
                    if json_attempt >= max_json_retries:
                        logger.error(f"All JSON parsing attempts failed: {e}")
                        raise OpenRouterError(f"Failed to score projects: {e}")
                    raise
                    
                except Exception as e:
                    logger.error(f"OpenRouter API error during scoring: {e}")
                    raise OpenRouterError(f"Failed to score projects: {e}")
            
            if batch_scores is None:
                raise last_error or OpenRouterError("Failed to score projects: Unknown error")
                
            all_scores.extend(batch_scores)

        return all_scores

    async def analyze_portfolio(
        self,
        portfolio: NormalizedPortfolio,
        project_scores: List[ProjectScore],
    ) -> PortfolioAnalysis:
        """
        Phase 2: Generate portfolio-level analysis based on project scores.
        """
        if not self.api_key:
            raise OpenRouterError("OpenRouter API key not configured")

        logger.info(f"Generating portfolio analysis for: {portfolio.name} via OpenRouter")

        scores_summary = format_scores_for_portfolio_prompt(
            [s.model_dump() for s in project_scores]
        )

        prompt = PORTFOLIO_ANALYSIS_PROMPT_TEMPLATE.format(
            portfolio_name=portfolio.name,
            scores_summary=scores_summary,
        )

        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            
            response_text = await self._chat_completion(messages)
            response_data = self._extract_json(response_text)

            analysis = PortfolioAnalysis(
                portfolio_id=portfolio.id,
                portfolio_name=portfolio.name,
                project_scores=project_scores,
                executive_summary=response_data.get("executive_summary", ""),
                critical_projects=response_data.get("critical_projects", []),
                priority_ranking=response_data.get("priority_ranking", []),
                risk_clusters=response_data.get("risk_clusters", []),
                recommendations=response_data.get("recommendations", []),
            )

            analysis.compute_statistics()
            return analysis

        except Exception as e:
            logger.error(f"OpenRouter API error during portfolio analysis: {e}")
            raise OpenRouterError(f"Failed to analyze portfolio: {e}")

    def _enrich_scores_with_normalized_data(
        self,
        project_scores: List[ProjectScore],
        portfolio: NormalizedPortfolio,
    ) -> None:
        """Enrich ProjectScore objects with data from NormalizedProject."""
        normalized_by_id = {p.id: p for p in portfolio.projects}

        for score in project_scores:
            normalized = normalized_by_id.get(score.project_id)
            if normalized:
                score.progress_percent = normalized.progress_percent
                score.owner_name = normalized.owner_name
                score.status_color = normalized.status_color.value if normalized.status_color else "gray"
                score.status_label = normalized.status_label
                score.milestones_total = normalized.milestones_total
                score.milestones_completed = normalized.milestones_completed
                score.milestones_delayed = normalized.milestones_delayed
                score.planned_effort_hours = normalized.planned_effort_hours
                score.actual_effort_hours = normalized.actual_effort_hours
                score.has_status_mismatch = normalized.has_status_mismatch
                score.status_mismatch_reasons = normalized.status_mismatch_reasons

    async def full_analysis(
        self,
        portfolio: NormalizedPortfolio,
    ) -> PortfolioAnalysis:
        """Run complete 2-phase analysis on a portfolio."""
        logger.info(
            f"Starting full analysis for portfolio: {portfolio.name} "
            f"({len(portfolio.projects)} projects) via OpenRouter ({self.model_name})"
        )

        # Phase 1: Score individual projects
        project_scores = await self.score_projects(portfolio.projects)

        # Enrich scores with normalized data for reporting (BEFORE validation)
        self._enrich_scores_with_normalized_data(project_scores, portfolio)

        # Phase 1.5: Sanity Validation - Fix contradictions
        validator = SanityValidator()
        validated_scores, data_warnings = validator.validate_portfolio_scores(project_scores)
        
        logger.info(
            f"Sanity validation complete. {len(data_warnings)} warnings generated."
        )

        # Phase 2: Portfolio-level analysis with validated scores
        analysis = await self.analyze_portfolio(portfolio, validated_scores)
        
        # Attach data quality warnings to the analysis
        analysis.data_warnings = data_warnings

        logger.info(
            f"Analysis complete. Critical projects: {len(analysis.critical_projects)}, "
            f"Data warnings: {len(data_warnings)}"
        )

        return analysis

    async def generate_presentation_structure(
        self,
        analysis: PortfolioAnalysis,
    ) -> AIPresentationStructure:
        """
        Generate AI-optimized presentation structure based on portfolio analysis.
        """
        if not self.api_key:
            raise OpenRouterError("OpenRouter API key not configured")

        logger.info(f"Generating presentation structure for: {analysis.portfolio_name}")

        prompt_data = format_analysis_for_presentation_prompt(analysis)
        prompt = PRESENTATION_STRUCTURE_PROMPT_TEMPLATE.format(**prompt_data)

        try:
            messages = [
                {"role": "system", "content": PRESENTATION_STRUCTURE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
            
            response_text = await self._chat_completion(messages, temperature=0.5)
            response_data = self._extract_json(response_text)

            # Parse slides
            slides = []
            for slide_data in response_data.get("slides", []):
                visualizations = []
                for viz_data in slide_data.get("visualizations", []):
                    try:
                        viz = SlideVisualization(
                            visualization_type=VisualizationType(viz_data.get("visualization_type", "bar_chart")),
                            data_source=viz_data.get("data_source", ""),
                            description=viz_data.get("description", ""),
                            position_hint=viz_data.get("position_hint", "full"),
                        )
                        visualizations.append(viz)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to parse visualization: {e}")
                
                try:
                    slide_spec = AISlideSpec(
                        slide_type=SlideType(slide_data.get("slide_type", "statistics")),
                        title=slide_data.get("title", ""),
                        subtitle=slide_data.get("subtitle"),
                        visualizations=visualizations,
                        key_message=slide_data.get("key_message"),
                        speaker_notes=slide_data.get("speaker_notes"),
                    )
                    slides.append(slide_spec)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Failed to parse slide: {e}")

            structure = AIPresentationStructure(
                slides=slides,
                total_estimated_slides=response_data.get("total_estimated_slides", len(slides)),
            )

            logger.info(f"Generated presentation structure with {len(slides)} slides")
            return structure

        except Exception as e:
            logger.error(f"Failed to generate presentation structure: {e}", exc_info=True)
            return self._get_default_presentation_structure(analysis)

    def _get_default_presentation_structure(
        self,
        analysis: PortfolioAnalysis,
    ) -> AIPresentationStructure:
        """Return a default presentation structure if AI generation fails."""
        logger.info("Using default presentation structure")
        
        slides = [
            AISlideSpec(
                slide_type=SlideType.TITLE,
                title=analysis.portfolio_name,
                subtitle="KI-gestützte Portfolioanalyse",
            ),
            AISlideSpec(
                slide_type=SlideType.EXECUTIVE_SUMMARY,
                title="Executive Summary",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.METRIC_CARDS,
                        data_source="key_metrics",
                        description="Wichtigste Kennzahlen des Portfolios",
                        position_hint="full",
                    ),
                ],
                key_message=analysis.executive_summary[:200] if analysis.executive_summary else None,
            ),
            AISlideSpec(
                slide_type=SlideType.STATISTICS,
                title="Portfolio-Scores im Überblick",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.BAR_CHART,
                        data_source="avg_scores",
                        description="Durchschnittliche U/I/C/R/DQ Werte",
                        position_hint="left",
                    ),
                    SlideVisualization(
                        visualization_type=VisualizationType.PIE_CHART,
                        data_source="status_distribution",
                        description="Verteilung der Projektstatus",
                        position_hint="right",
                    ),
                ],
            ),
            AISlideSpec(
                slide_type=SlideType.RISK_MATRIX,
                title="Risiko-Dringlichkeits-Matrix",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.SCATTER_PLOT,
                        data_source="risk_urgency",
                        description="Projekte nach Risiko und Dringlichkeit",
                        position_hint="full",
                    ),
                ],
            ),
            AISlideSpec(
                slide_type=SlideType.CRITICAL_PROJECTS,
                title="Kritische Projekte",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.TABLE,
                        data_source="critical_projects",
                        description="Übersicht kritischer Projekte",
                        position_hint="full",
                    ),
                ],
            ),
            AISlideSpec(
                slide_type=SlideType.RECOMMENDATIONS,
                title="Handlungsempfehlungen",
                visualizations=[
                    SlideVisualization(
                        visualization_type=VisualizationType.BULLET_POINTS,
                        data_source="recommendations",
                        description="Priorisierte Empfehlungen",
                        position_hint="full",
                    ),
                ],
            ),
        ]
        
        return AIPresentationStructure(
            slides=slides,
            total_estimated_slides=len(slides),
        )


def get_openrouter_service(model_shortname: Optional[str] = None) -> OpenRouterService:
    """
    Get an OpenRouter service instance.
    
    Args:
        model_shortname: Optional shortname (devstral, gemini-flash)
                        If not provided, uses configured model.
    """
    settings = get_settings()
    model_name = settings.get_openrouter_model_id(model_shortname)
    return OpenRouterService(model_name=model_name)

