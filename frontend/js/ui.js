/**
 * UI rendering module.
 */

// Text-to-Speech state (using backend edge-tts)
let currentAudio = null;
let isSpeaking = false;
let currentButtonId = null;

// API base URL
const API_BASE = 'http://localhost:8000';

/**
 * Speak text using backend edge-tts (high-quality German voices)
 * @param {string} text - Text to speak
 * @param {string} buttonId - ID of the button that triggered speech
 */
async function speakText(text, buttonId) {
    // Stop any current speech
    if (isSpeaking && currentButtonId === buttonId) {
        stopSpeech();
        return;
    }
    
    // Stop previous speech if different button
    if (isSpeaking) {
        stopSpeech();
    }

    if (!text) {
        console.warn('No text provided for TTS');
        return;
    }

    currentButtonId = buttonId;
    updateSpeakButton(buttonId, true, true); // Show loading state

    try {
        // Call backend TTS API
        const response = await fetch(`${API_BASE}/api/tts/speak`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                voice: 'de-DE-KatjaNeural', // High-quality German female voice
                rate: '-5%'
            })
        });

        if (!response.ok) {
            throw new Error(`TTS failed: ${response.status}`);
        }

        // Get audio blob and play
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        currentAudio = new Audio(audioUrl);
        
        currentAudio.onplay = () => {
            isSpeaking = true;
            updateSpeakButton(buttonId, true, false);
        };
        
        currentAudio.onended = () => {
            isSpeaking = false;
            currentButtonId = null;
            updateSpeakButton(buttonId, false, false);
            URL.revokeObjectURL(audioUrl);
        };
        
        currentAudio.onerror = () => {
            isSpeaking = false;
            currentButtonId = null;
            updateSpeakButton(buttonId, false, false);
            URL.revokeObjectURL(audioUrl);
            console.error('Audio playback error');
        };

        await currentAudio.play();
        
    } catch (error) {
        console.error('TTS error:', error);
        isSpeaking = false;
        currentButtonId = null;
        updateSpeakButton(buttonId, false, false);
        
        // Fallback to browser TTS if backend fails
        fallbackBrowserTTS(text, buttonId);
    }
}

/**
 * Fallback to browser's built-in TTS if backend fails
 */
function fallbackBrowserTTS(text, buttonId) {
    if (!window.speechSynthesis) return;
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'de-DE';
    utterance.rate = 0.9;
    
    utterance.onstart = () => {
        isSpeaking = true;
        updateSpeakButton(buttonId, true, false);
    };
    
    utterance.onend = () => {
        isSpeaking = false;
        updateSpeakButton(buttonId, false, false);
    };
    
    window.speechSynthesis.speak(utterance);
}

/**
 * Update speak button appearance
 */
function updateSpeakButton(buttonId, speaking, loading = false) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;

    if (loading) {
        btn.classList.add('loading');
        btn.classList.remove('speaking');
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 6v6l4 2"></path>
            </svg>
            Lädt...
        `;
    } else if (speaking) {
        btn.classList.add('speaking');
        btn.classList.remove('loading');
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="6" y="4" width="4" height="16"></rect>
                <rect x="14" y="4" width="4" height="16"></rect>
            </svg>
            Stop
        `;
    } else {
        btn.classList.remove('speaking', 'loading');
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
            </svg>
            Vorlesen
        `;
    }
}

/**
 * Stop all speech
 */
export function stopSpeech() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
    if (currentButtonId) {
        updateSpeakButton(currentButtonId, false, false);
    }
    isSpeaking = false;
    currentButtonId = null;
}

/**
 * Render search results.
 * @param {Array} portfolios - List of portfolios
 * @param {HTMLElement} container - Container element
 * @param {Function} onSelect - Callback when portfolio is selected
 */
export function renderSearchResults(portfolios, container, onSelect) {
    if (!portfolios || portfolios.length === 0) {
        container.innerHTML = '<p class="message message-info">Keine Portfolios gefunden</p>';
        return;
    }

    container.innerHTML = portfolios.map(p => `
        <div class="search-result-item" data-id="${p.id}">
            <div class="search-result-name">${escapeHtml(p.name)}</div>
            <div class="search-result-meta">${p.project_count} Projekte</div>
        </div>
    `).join('');

    // Add click handlers
    container.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', () => {
            // Remove previous selection
            container.querySelectorAll('.search-result-item').forEach(i => i.classList.remove('selected'));
            // Mark as selected
            item.classList.add('selected');
            // Call callback
            const portfolio = portfolios.find(p => String(p.id) === item.dataset.id);
            if (portfolio) onSelect(portfolio);
        });
    });
}

/**
 * Render selected portfolio.
 * @param {Object} portfolio - Selected portfolio
 * @param {HTMLElement} container - Container element
 */
export function renderSelectedPortfolio(portfolio, container) {
    container.innerHTML = `
        <div class="selected-portfolio-name">${escapeHtml(portfolio.name)}</div>
        <div class="selected-portfolio-meta">${portfolio.project_count} Projekte</div>
    `;
}

/**
 * Render analysis results - matching Word document structure.
 * @param {Object} analysis - Portfolio analysis result
 * @param {HTMLElement} container - Container element
 */
export function renderAnalysisResults(analysis, container, onDownloadReport, onDownloadWordReport, onDownloadDetailedReport) {
    const { project_scores, executive_summary, recommendations } = analysis;
    
    // Limit recommendations to 3 (like in Word document)
    const topRecommendations = recommendations ? recommendations.slice(0, 3) : [];

    container.innerHTML = `
        <div class="analysis-header">
            <div>
                <h2 class="analysis-title">${escapeHtml(analysis.portfolio_name)}</h2>
                <div class="analysis-subtitle">KI-gestützte Portfolioanalyse</div>
                <div class="analysis-meta">${project_scores.length} Projekte analysiert</div>
            </div>
            <div class="download-buttons">
                <button id="download-report-btn" class="btn btn-primary" title="Kompakte PowerPoint-Präsentation">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    PPTX
                </button>
                <button id="download-detailed-btn" class="btn btn-primary-outline" title="Ausführliche PowerPoint-Präsentation">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    PPTX+
                </button>
                <button id="download-word-btn" class="btn btn-secondary">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    DOCX
                </button>
            </div>
        </div>

        <!-- Executive Summary (like Word document) -->
        <div class="card summary-card">
            <div class="card-title-row">
                <h3 class="card-title">Executive Summary</h3>
                <button id="speak-summary-btn" class="btn btn-speak" title="Vorlesen">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                    </svg>
                    Vorlesen
                </button>
            </div>
            <p class="summary-text" id="summary-text">${escapeHtml(executive_summary)}</p>
        </div>

        <!-- Projects Section (like Word document: "Projektanalysen im Detail") -->
        <div class="section-header" style="margin-top: var(--space-6);">
            <h3 class="section-title">Projektanalysen im Detail</h3>
        </div>
        <div class="projects-list">
            ${project_scores.map((p, idx) => renderProjectDetailCard(p, idx)).join('')}
        </div>

        <!-- Recommendations (like Word document: max 3, short) -->
        ${topRecommendations.length > 0 ? `
            <div class="card" style="margin-top: var(--space-6);">
                <h3 class="card-title">Handlungsempfehlungen</h3>
                <ol class="recommendations-list">
                    ${topRecommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
                </ol>
            </div>
        ` : ''}
    `;

    // Bind download button handlers
    if (onDownloadReport) {
        const downloadBtn = document.getElementById('download-report-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => onDownloadReport(analysis));
        }
    }

    if (onDownloadDetailedReport) {
        const downloadDetailedBtn = document.getElementById('download-detailed-btn');
        if (downloadDetailedBtn) {
            downloadDetailedBtn.addEventListener('click', () => onDownloadDetailedReport(analysis));
        }
    }

    if (onDownloadWordReport) {
        const downloadWordBtn = document.getElementById('download-word-btn');
        if (downloadWordBtn) {
            downloadWordBtn.addEventListener('click', () => onDownloadWordReport(analysis));
        }
    }

    // Bind text-to-speech handlers
    const speakSummaryBtn = document.getElementById('speak-summary-btn');
    if (speakSummaryBtn && executive_summary) {
        speakSummaryBtn.addEventListener('click', () => {
            speakText(executive_summary, 'speak-summary-btn');
        });
    }

    // Bind speak buttons for each project
    project_scores.forEach((project, index) => {
        const speakBtn = document.getElementById(`speak-project-${index}`);
        if (speakBtn) {
            const textToSpeak = project.detailed_analysis || project.summary || '';
            speakBtn.addEventListener('click', () => {
                speakText(textToSpeak, `speak-project-${index}`);
            });
        }
    });
}

/**
 * Render a project detail card - matching Word document structure.
 * Shows detailed_analysis text and keeps score pills.
 * @param {Object} project - Project data
 * @param {number} index - Index for unique ID generation
 */
function renderProjectDetailCard(project, index) {
    const statusClass = project.status_color || 'gray';
    const isCritical = project.is_critical;
    
    // Build project info line (like Word: "Verantwortlich: X | Fortschritt: Y% | Meilensteine: Z")
    const infoParts = [];
    if (project.owner_name) {
        infoParts.push(`Verantwortlich: ${escapeHtml(project.owner_name)}`);
    }
    infoParts.push(`Fortschritt: ${Math.round(project.progress_percent || 0)}%`);
    if (project.milestones_total > 0) {
        let milestoneText = `Meilensteine: ${project.milestones_completed || 0}/${project.milestones_total}`;
        if (project.milestones_delayed > 0) {
            milestoneText += ` (${project.milestones_delayed} verzögert)`;
        }
        infoParts.push(milestoneText);
    }

    // Use detailed_analysis if available, fallback to summary
    const analysisText = project.detailed_analysis || project.summary || '';
    const hasTextToSpeak = analysisText.length > 0;

    return `
        <div class="card project-detail-card ${isCritical ? 'project-critical' : ''}" data-id="${project.project_id}">
            <div class="project-detail-header">
                <div class="project-title-row">
                    <h4 class="project-name ${isCritical ? 'critical-name' : ''}">${escapeHtml(project.project_name)}${isCritical ? ' [KRITISCH]' : ''}</h4>
                    <div class="project-actions">
                        ${hasTextToSpeak ? `
                            <button id="speak-project-${index}" class="btn btn-speak btn-speak-sm" title="Analyse vorlesen">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                                    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                                </svg>
                            </button>
                        ` : ''}
                        <span class="project-status ${statusClass}">${statusClass}</span>
                    </div>
                </div>
                <div class="project-info-line">${infoParts.join(' | ')}</div>
            </div>

            <!-- Radar Chart and Analysis Section -->
            <div class="project-content-row">
                <!-- Radar Chart -->
                <div class="project-radar-chart">
                    ${renderRadarChart(project, 180)}
                </div>
                
                <!-- Analysis and Scores -->
                <div class="project-analysis-section">
                    <!-- Progress Bar -->
                    <div class="progress-bar">
                        <div class="progress-bar-fill" style="width: ${project.progress_percent || 0}%"></div>
                    </div>
                    <div class="progress-label">${Math.round(project.progress_percent || 0)}% Fortschritt</div>

                    <!-- Detailed Analysis Text -->
                    ${analysisText ? `
                        <div class="project-analysis-text">
                            ${escapeHtml(analysisText)}
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Render a score pill.
 */
function renderScorePill(label, value) {
    const scoreClass = value ? `score-${value}` : '';
    return `
        <div class="score-pill ${scoreClass}">
            <span class="label">${label}</span>
            <span class="value">${value || '-'}</span>
        </div>
    `;
}

/**
 * Render an SVG radar chart for project scores with legend.
 * @param {Object} project - Project with score values
 * @param {number} size - Size of the chart in pixels
 */
function renderRadarChart(project, size = 200) {
    const scores = [
        { label: 'U', fullLabel: 'Dringlichkeit (Urgency)', value: project.urgency?.value || 0 },
        { label: 'I', fullLabel: 'Wichtigkeit (Importance)', value: project.importance?.value || 0 },
        { label: 'C', fullLabel: 'Komplexität (Complexity)', value: project.complexity?.value || 0 },
        { label: 'R', fullLabel: 'Risiko (Risk)', value: project.risk?.value || 0 },
        { label: 'DQ', fullLabel: 'Datenqualität (Data Quality)', value: project.data_quality?.value || 0 },
    ];
    
    const centerX = size / 2;
    const centerY = size / 2;
    const maxRadius = size * 0.38;
    const numAxes = scores.length;
    const angleStep = (2 * Math.PI) / numAxes;
    const startAngle = -Math.PI / 2; // Start from top
    
    // Generate grid circles (for scale 1-5)
    let gridCircles = '';
    for (let i = 1; i <= 5; i++) {
        const r = (maxRadius * i) / 5;
        gridCircles += `<circle cx="${centerX}" cy="${centerY}" r="${r}" fill="none" stroke="#e0e0e0" stroke-width="1"/>`;
    }
    
    // Generate axis lines
    let axisLines = '';
    for (let i = 0; i < numAxes; i++) {
        const angle = startAngle + i * angleStep;
        const x2 = centerX + maxRadius * Math.cos(angle);
        const y2 = centerY + maxRadius * Math.sin(angle);
        axisLines += `<line x1="${centerX}" y1="${centerY}" x2="${x2}" y2="${y2}" stroke="#e0e0e0" stroke-width="1"/>`;
    }
    
    // Generate data polygon points
    const dataPoints = scores.map((score, i) => {
        const angle = startAngle + i * angleStep;
        const r = (maxRadius * score.value) / 5;
        const x = centerX + r * Math.cos(angle);
        const y = centerY + r * Math.sin(angle);
        return `${x},${y}`;
    }).join(' ');
    
    // Generate labels with values
    let labels = '';
    const labelRadius = maxRadius + 25;
    for (let i = 0; i < numAxes; i++) {
        const angle = startAngle + i * angleStep;
        const x = centerX + labelRadius * Math.cos(angle);
        const y = centerY + labelRadius * Math.sin(angle);
        
        // Adjust text anchor based on position
        let textAnchor = 'middle';
        if (Math.cos(angle) > 0.3) textAnchor = 'start';
        else if (Math.cos(angle) < -0.3) textAnchor = 'end';
        
        labels += `
            <text x="${x}" y="${y}" text-anchor="${textAnchor}" dominant-baseline="middle" 
                  font-size="11" fill="#333" font-weight="500">
                ${scores[i].label}
                <tspan font-size="10" fill="#666"> (${scores[i].value})</tspan>
            </text>
        `;
    }
    
    // Generate data points
    let dataPointDots = '';
    scores.forEach((score, i) => {
        const angle = startAngle + i * angleStep;
        const r = (maxRadius * score.value) / 5;
        const x = centerX + r * Math.cos(angle);
        const y = centerY + r * Math.sin(angle);
        dataPointDots += `<circle cx="${x}" cy="${y}" r="4" fill="#016bd5" stroke="white" stroke-width="1.5"/>`;
    });
    
    // Generate legend items
    const legendItems = scores.map(s => 
        `<span class="radar-legend-item"><strong>${s.label}</strong> = ${s.fullLabel}</span>`
    ).join('');
    
    return `
        <div class="radar-chart-container">
            <svg width="${size + 60}" height="${size + 40}" viewBox="-30 -10 ${size + 60} ${size + 40}" class="radar-chart">
                ${gridCircles}
                ${axisLines}
                <polygon points="${dataPoints}" fill="rgba(1, 107, 213, 0.2)" stroke="#016bd5" stroke-width="2"/>
                ${dataPointDots}
                ${labels}
            </svg>
            <div class="radar-legend">
                <div class="radar-legend-toggle" title="Legende anzeigen">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="16" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12.01" y2="8"></line>
                    </svg>
                    <span>Legende</span>
                </div>
                <div class="radar-legend-tooltip">
                    <div class="radar-legend-title">Score-Dimensionen (Skala 1-5)</div>
                    <div class="radar-legend-items">
                        ${scores.map(s => `
                            <div class="radar-legend-row">
                                <span class="radar-legend-abbr">${s.label}</span>
                                <span class="radar-legend-full">${s.fullLabel}</span>
                            </div>
                        `).join('')}
                    </div>
                    <div class="radar-legend-note">
                        1 = niedrig, 5 = hoch
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Show loading overlay.
 */
export function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

/**
 * Hide loading overlay.
 */
export function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

/**
 * Show error message in container.
 */
export function showError(message, container) {
    container.innerHTML = `<div class="message message-error">${escapeHtml(message)}</div>`;
}

/**
 * Show empty state.
 */
export function showEmptyState(container) {
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-state-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
            </div>
            <h3>Kein Portfolio ausgewählt</h3>
            <p>Suche ein Portfolio und starte die Analyse</p>
        </div>
    `;
}

/**
 * Escape HTML to prevent XSS.
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
