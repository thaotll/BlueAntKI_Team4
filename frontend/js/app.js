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
const settingsClear = document.getElementById('settings-clear');
const blueantUrlInput = document.getElementById('blueant-url');
const blueantKeyInput = document.getElementById('blueant-key');
const geminiKeyInput = document.getElementById('gemini-key');
const openrouterKeyInput = document.getElementById('openrouter-key');
const llmProviderSelect = document.getElementById('llm-provider');
const openrouterModelSelect = document.getElementById('openrouter-model');
const geminiSettings = document.getElementById('gemini-settings');
const openrouterSettings = document.getElementById('openrouter-settings');
const sessionOnlyCheckbox = document.getElementById('session-only');
const securityNotice = document.getElementById('security-notice');

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
    if (settingsClear) {
        settingsClear.addEventListener('click', clearSettings);
    }
    settingsModal.querySelector('.modal-backdrop').addEventListener('click', closeSettings);

    // Session-only toggle
    if (sessionOnlyCheckbox) {
        sessionOnlyCheckbox.addEventListener('change', handleStorageModeChange);
    }

    // LLM Provider toggle
    if (llmProviderSelect) {
        llmProviderSelect.addEventListener('change', handleProviderChange);
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && settingsModal.style.display !== 'none') {
            closeSettings();
        }
    });

    // Check encryption availability
    if (!api.isEncryptionAvailable()) {
        console.warn('Web Crypto API not available - falling back to unencrypted storage');
        if (securityNotice) {
            securityNotice.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    <line x1="12" y1="9" x2="12" y2="13"></line>
                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
                <span>Verschlüsselung nicht verfügbar. Nutzen Sie HTTPS für bessere Sicherheit.</span>
            `;
            securityNotice.classList.add('warning');
        }
    }
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
            ui.renderAnalysisResults(result.analysis, resultsContainer, handleDownloadReport, handleDownloadWordReport, handleDownloadDetailedReport);
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
 * Handle detailed PowerPoint report download.
 */
async function handleDownloadDetailedReport(analysis) {
    const downloadBtn = document.getElementById('download-detailed-btn');
    if (downloadBtn) {
        downloadBtn.disabled = true;
        downloadBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px; animation: spin 1s linear infinite;">
                <circle cx="12" cy="12" r="10"></circle>
            </svg>
            Generiere...
        `;
    }

    try {
        const blob = await api.generateDetailedReport(analysis);

        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${analysis.portfolio_name}_Report_Detailliert.pptx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Detailed report generation error:', error);
        alert(`Fehler beim Generieren des detaillierten Reports: ${error.message}`);
    } finally {
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 6px;">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                PPTX+
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
 * Handle storage mode change.
 */
function handleStorageModeChange() {
    const isSessionOnly = sessionOnlyCheckbox.checked;
    api.setStorageMode(isSessionOnly);
    
    // Update UI hint
    updateSecurityNotice(isSessionOnly);
}

/**
 * Handle LLM provider change.
 */
function handleProviderChange() {
    const provider = llmProviderSelect.value;
    
    if (provider === 'gemini') {
        geminiSettings.style.display = 'block';
        openrouterSettings.style.display = 'none';
    } else if (provider === 'openrouter') {
        geminiSettings.style.display = 'none';
        openrouterSettings.style.display = 'block';
    }
}

/**
 * Update security notice based on storage mode.
 */
function updateSecurityNotice(isSessionOnly) {
    if (!securityNotice) return;
    
    if (isSessionOnly) {
        securityNotice.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            <span>Session-Modus aktiv: Daten werden nach Schließen des Browsers gelöscht.</span>
        `;
        securityNotice.classList.remove('warning');
        securityNotice.classList.add('success');
    } else {
        securityNotice.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <span>API-Keys werden verschlüsselt im Browser gespeichert.</span>
        `;
        securityNotice.classList.remove('warning', 'success');
    }
}

/**
 * Load settings from storage (async).
 */
async function loadSettings() {
    try {
        const config = await api.loadConfig();
        blueantUrlInput.value = config.blueant_url || '';
        blueantKeyInput.value = config.blueant_key || '';
        geminiKeyInput.value = config.gemini_key || '';
        
        // Load OpenRouter settings
        if (openrouterKeyInput) {
            openrouterKeyInput.value = config.openrouter_key || '';
        }
        if (llmProviderSelect) {
            llmProviderSelect.value = config.llm_provider || 'gemini';
            handleProviderChange(); // Update UI visibility
        }
        if (openrouterModelSelect && config.llm_model) {
            openrouterModelSelect.value = config.llm_model;
        }
        
        // Load storage mode
        if (sessionOnlyCheckbox) {
            const isSessionOnly = api.isSessionOnly();
            sessionOnlyCheckbox.checked = isSessionOnly;
            updateSecurityNotice(isSessionOnly);
        }
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

/**
 * Save settings to storage (async with encryption).
 */
async function saveSettings() {
    const provider = llmProviderSelect ? llmProviderSelect.value : 'gemini';
    
    const config = {
        blueant_url: blueantUrlInput.value.trim(),
        blueant_key: blueantKeyInput.value.trim(),
        gemini_key: geminiKeyInput.value.trim(),
        openrouter_key: openrouterKeyInput ? openrouterKeyInput.value.trim() : '',
        llm_provider: provider,
        llm_model: provider === 'openrouter' && openrouterModelSelect 
            ? openrouterModelSelect.value 
            : '',
    };

    // Show saving state
    settingsSave.disabled = true;
    settingsSave.textContent = 'Speichere...';

    try {
        await api.saveConfig(config);
        closeSettings();

        // Show confirmation with provider info
        const providerName = provider === 'gemini' ? 'Google Gemini' : 'OpenRouter';
        showToast(`Einstellungen gespeichert (${providerName})`, 'success');
    } catch (error) {
        console.error('Failed to save settings:', error);
        showToast('Fehler beim Speichern', 'error');
    } finally {
        settingsSave.disabled = false;
        settingsSave.textContent = 'Speichern';
    }
}

/**
 * Clear all stored credentials.
 */
function clearSettings() {
    if (!confirm('Alle gespeicherten API-Keys löschen?')) return;
    
    api.clearConfig();
    
    // Clear form
    blueantUrlInput.value = '';
    blueantKeyInput.value = '';
    geminiKeyInput.value = '';
    if (openrouterKeyInput) openrouterKeyInput.value = '';
    if (llmProviderSelect) {
        llmProviderSelect.value = 'gemini';
        handleProviderChange();
    }
    if (openrouterModelSelect) openrouterModelSelect.value = 'gemini-flash';
    
    showToast('Alle Zugangsdaten gelöscht', 'success');
}

/**
 * Show toast notification.
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `message message-${type}`;
    toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 1001; animation: fadeIn 0.3s ease;';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
