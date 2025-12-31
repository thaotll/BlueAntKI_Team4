/**
 * UI rendering module.
 */

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
 * Render analysis results.
 * @param {Object} analysis - Portfolio analysis result
 * @param {HTMLElement} container - Container element
 */
export function renderAnalysisResults(analysis, container) {
    const { project_scores, executive_summary, recommendations, risk_clusters } = analysis;

    container.innerHTML = `
        <div class="analysis-header">
            <h2 class="analysis-title">${escapeHtml(analysis.portfolio_name)}</h2>
            <div class="analysis-meta">${project_scores.length} Projekte analysiert</div>
        </div>

        <!-- Executive Summary -->
        <div class="card summary-card">
            <h3 class="card-title">Executive Summary</h3>
            <p class="summary-text">${escapeHtml(executive_summary)}</p>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
            ${renderStatCard('Projekte', project_scores.length)}
            ${renderStatCard('Kritisch', analysis.critical_projects?.length || 0)}
            ${renderStatCard('Avg. Risiko', analysis.avg_risk?.toFixed(1) || '-')}
            ${renderStatCard('Avg. Dringlichkeit', analysis.avg_urgency?.toFixed(1) || '-')}
            ${renderStatCard('Avg. Wichtigkeit', analysis.avg_importance?.toFixed(1) || '-')}
        </div>

        <!-- Recommendations -->
        ${recommendations && recommendations.length > 0 ? `
            <div class="card">
                <h3 class="card-title">Empfehlungen</h3>
                <ul class="recommendations-list">
                    ${recommendations.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
                </ul>
            </div>
        ` : ''}

        <!-- Risk Clusters -->
        ${risk_clusters && risk_clusters.length > 0 ? `
            <div class="card" style="margin-top: var(--space-4);">
                <h3 class="card-title">Risikomuster</h3>
                ${risk_clusters.map(r => `<div class="risk-cluster">${escapeHtml(r)}</div>`).join('')}
            </div>
        ` : ''}

        <!-- Projects -->
        <div class="section-header" style="margin-top: var(--space-6);">
            <h3 class="section-title">Projektbewertungen</h3>
        </div>
        <div class="projects-grid">
            ${project_scores.map(p => renderProjectCard(p)).join('')}
        </div>
    `;
}

/**
 * Render a stat card.
 */
function renderStatCard(label, value) {
    return `
        <div class="card stat-card">
            <div class="stat-value">${value}</div>
            <div class="stat-label">${label}</div>
        </div>
    `;
}

/**
 * Render a project card.
 */
function renderProjectCard(project) {
    const statusClass = project.status_color || 'gray';
    const isCritical = project.is_critical;

    return `
        <div class="card project-card" data-id="${project.project_id}">
            <div class="project-card-header">
                <div>
                    <div class="project-name">${escapeHtml(project.project_name)}</div>
                    ${project.owner_name ? `<div class="project-owner">${escapeHtml(project.owner_name)}</div>` : ''}
                </div>
                <span class="project-status ${statusClass}">${statusClass}</span>
            </div>

            ${isCritical ? '<span class="critical-badge">Kritisch</span>' : ''}

            <div class="scores-row">
                ${renderScorePill('U', project.urgency?.value)}
                ${renderScorePill('I', project.importance?.value)}
                ${renderScorePill('C', project.complexity?.value)}
                ${renderScorePill('R', project.risk?.value)}
                ${renderScorePill('DQ', project.data_quality?.value)}
            </div>

            <div class="progress-bar">
                <div class="progress-bar-fill" style="width: ${project.progress_percent || 0}%"></div>
            </div>
            <div class="progress-label">
                <span>Fortschritt</span>
                <span>${Math.round(project.progress_percent || 0)}%</span>
            </div>

            ${project.summary ? `
                <p style="margin-top: var(--space-3); font-size: var(--text-sm); color: var(--color-text-secondary);">
                    ${escapeHtml(project.summary)}
                </p>
            ` : ''}
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
