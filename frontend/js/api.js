/**
 * API client module for backend communication.
 */

const API_BASE = 'http://localhost:8000';

/**
 * Get custom config from localStorage if available.
 */
function getCustomConfig() {
    const config = localStorage.getItem('portfolio-analyzer-config');
    if (!config) return null;

    try {
        const parsed = JSON.parse(config);
        // Only return if at least one value is set
        if (parsed.blueant_url || parsed.blueant_key || parsed.gemini_key) {
            return parsed;
        }
    } catch (e) {
        console.warn('Failed to parse config from localStorage:', e);
    }
    return null;
}

/**
 * Search portfolios by name.
 * @param {string} name - Portfolio name to search for
 * @returns {Promise<{success: boolean, portfolios?: Array, error?: string}>}
 */
export async function searchPortfolios(name) {
    const response = await fetch(`${API_BASE}/api/portfolios/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            custom_config: getCustomConfig(),
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get portfolio details by ID.
 * @param {string} portfolioId - Portfolio ID
 * @returns {Promise<{success: boolean, portfolio?: Object, error?: string}>}
 */
export async function getPortfolio(portfolioId) {
    const response = await fetch(`${API_BASE}/api/portfolios/${portfolioId}`);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Run portfolio analysis.
 * @param {string} portfolioId - Portfolio ID to analyze
 * @returns {Promise<{success: boolean, analysis?: Object, error?: string, metadata?: Object}>}
 */
export async function analyzePortfolio(portfolioId) {
    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            portfolio_id: portfolioId,
            custom_config: getCustomConfig(),
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Generate PowerPoint report from analysis.
 * @param {Object} analysis - Portfolio analysis data
 * @param {string} language - Report language (de or en)
 * @returns {Promise<Blob>} PPTX file as blob
 */
export async function generateReport(analysis, language = 'de') {
    const response = await fetch(`${API_BASE}/api/reports/pptx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            analysis,
            options: { language },
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.blob();
}

/**
 * Save config to localStorage.
 * @param {Object} config - Configuration object
 */
export function saveConfig(config) {
    localStorage.setItem('portfolio-analyzer-config', JSON.stringify(config));
}

/**
 * Load config from localStorage.
 * @returns {Object} Configuration object
 */
export function loadConfig() {
    const config = localStorage.getItem('portfolio-analyzer-config');
    if (!config) {
        return { blueant_url: '', blueant_key: '', gemini_key: '' };
    }
    try {
        return JSON.parse(config);
    } catch (e) {
        return { blueant_url: '', blueant_key: '', gemini_key: '' };
    }
}
