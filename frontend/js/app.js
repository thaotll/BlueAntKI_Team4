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
            ui.renderAnalysisResults(result.analysis, resultsContainer);
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
