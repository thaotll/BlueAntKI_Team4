/**
 * Main application module.
 */

import * as api from './api.js';
import * as ui from './ui.js';

// State
let selectedPortfolio = null;

// DOM Elements
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const searchResults = document.getElementById('search-results');
const selectedSection = document.getElementById('selected-section');
const selectedPortfolioEl = document.getElementById('selected-portfolio');
const analyzeBtn = document.getElementById('analyze-btn');
const resultsContainer = document.getElementById('results');

// Settings
const settingsBtn = document.getElementById('settings-btn');
const settingsModal = document.getElementById('settings-modal');
const settingsClose = document.getElementById('settings-close');
const settingsSave = document.getElementById('settings-save');
const blueantUrlInput = document.getElementById('blueant-url');
const blueantKeyInput = document.getElementById('blueant-key');
const geminiKeyInput = document.getElementById('gemini-key');

/**
 * Initialize the application.
 */
function init() {
    // Load saved config
    loadSettings();

    // Event listeners
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    analyzeBtn.addEventListener('click', handleAnalyze);

    // Settings modal
    settingsBtn.addEventListener('click', openSettings);
    settingsClose.addEventListener('click', closeSettings);
    settingsSave.addEventListener('click', saveSettings);
    settingsModal.querySelector('.modal-backdrop').addEventListener('click', closeSettings);

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && settingsModal.style.display !== 'none') {
            closeSettings();
        }
    });
}

/**
 * Handle portfolio search.
 */
async function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        searchResults.innerHTML = '<p class="message message-info">Bitte einen Suchbegriff eingeben</p>';
        return;
    }

    searchBtn.disabled = true;
    searchBtn.textContent = 'Suche...';

    try {
        const result = await api.searchPortfolios(query);

        if (result.success) {
            ui.renderSearchResults(result.portfolios, searchResults, handlePortfolioSelect);
        } else {
            ui.showError(result.error || 'Suche fehlgeschlagen', searchResults);
        }
    } catch (error) {
        console.error('Search error:', error);
        ui.showError(`Fehler: ${error.message}`, searchResults);
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = 'Suchen';
    }
}

/**
 * Handle portfolio selection.
 */
function handlePortfolioSelect(portfolio) {
    selectedPortfolio = portfolio;

    // Show selected section
    selectedSection.style.display = 'block';
    ui.renderSelectedPortfolio(portfolio, selectedPortfolioEl);

    // Enable analyze button
    analyzeBtn.disabled = false;
}

/**
 * Handle portfolio analysis.
 */
async function handleAnalyze() {
    if (!selectedPortfolio) {
        alert('Bitte zuerst ein Portfolio auswählen');
        return;
    }

    ui.showLoading();
    analyzeBtn.disabled = true;

    try {
        const result = await api.analyzePortfolio(selectedPortfolio.id);

        if (result.success && result.analysis) {
            ui.renderAnalysisResults(result.analysis, resultsContainer, handleDownloadReport, handleDownloadWordReport);
        } else {
            ui.showError(result.error || 'Analyse fehlgeschlagen', resultsContainer);
        }
    } catch (error) {
        console.error('Analysis error:', error);
        ui.showError(`Fehler: ${error.message}`, resultsContainer);
    } finally {
        ui.hideLoading();
        analyzeBtn.disabled = false;
    }
}

/**
 * Handle PowerPoint report download.
 */
async function handleDownloadReport(analysis) {
    const downloadBtn = document.getElementById('download-report-btn');
    if (downloadBtn) {
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px; animation: spin 1s linear infinite;">
                <circle cx="12" cy="12" r="10"></circle>
            </svg>
            ...
        `;
    }

    try {
        const blob = await api.generateReport(analysis);

        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${analysis.portfolio_name}_Report.pptx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Report generation error:', error);
        alert(`Fehler beim Generieren des Reports: ${error.message}`);
    } finally {
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                PPTX
            `;
        }
    }
}

/**
 * Handle Word document report download.
 */
async function handleDownloadWordReport(analysis) {
    const downloadBtn = document.getElementById('download-word-btn');
    if (downloadBtn) {
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px; animation: spin 1s linear infinite;">
                <circle cx="12" cy="12" r="10"></circle>
            </svg>
            ...
        `;
    }

    try {
        const blob = await api.generateWordReport(analysis);

        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${analysis.portfolio_name}_Report.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Word report generation error:', error);
        alert(`Fehler beim Generieren des Word-Reports: ${error.message}`);
    } finally {
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                DOCX
            `;
        }
    }
}

/**
 * Open settings modal.
 */
function openSettings() {
    settingsModal.style.display = 'flex';
}

/**
 * Close settings modal.
 */
function closeSettings() {
    settingsModal.style.display = 'none';
}

/**
 * Load settings from localStorage.
 */
function loadSettings() {
    const config = api.loadConfig();
    blueantUrlInput.value = config.blueant_url || '';
    blueantKeyInput.value = config.blueant_key || '';
    geminiKeyInput.value = config.gemini_key || '';
}

/**
 * Save settings to localStorage.
 */
function saveSettings() {
    const config = {
        blueant_url: blueantUrlInput.value.trim(),
        blueant_key: blueantKeyInput.value.trim(),
        gemini_key: geminiKeyInput.value.trim(),
    };

    api.saveConfig(config);
    closeSettings();

    // Show confirmation
    const toast = document.createElement('div');
    toast.className = 'message message-success';
    toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1001;';
    toast.textContent = 'Einstellungen gespeichert';
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
