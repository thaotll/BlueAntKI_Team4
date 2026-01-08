/**
 * API client module for backend communication.
 * Includes secure encrypted storage for API keys.
 */

import { encrypt, decrypt, isCryptoAvailable } from './crypto.js';

const API_BASE = 'http://localhost:8000';
const CONFIG_KEY = 'portfolio-analyzer-config';
const STORAGE_MODE_KEY = 'portfolio-analyzer-storage-mode';

// Cache for decrypted config (avoid repeated decryption)
let configCache = null;

/**
 * Get the appropriate storage based on user preference.
 * @returns {Storage} localStorage or sessionStorage
 */
function getStorage() {
    const mode = localStorage.getItem(STORAGE_MODE_KEY);
    return mode === 'session' ? sessionStorage : localStorage;
}

/**
 * Check if session-only mode is enabled.
 * @returns {boolean}
 */
export function isSessionOnly() {
    return localStorage.getItem(STORAGE_MODE_KEY) === 'session';
}

/**
 * Set storage mode.
 * @param {boolean} sessionOnly - True for session storage, false for persistent
 */
export function setStorageMode(sessionOnly) {
    const oldMode = localStorage.getItem(STORAGE_MODE_KEY);
    const newMode = sessionOnly ? 'session' : 'persistent';
    
    // If switching modes, migrate data
    if (oldMode !== newMode) {
        const oldStorage = oldMode === 'session' ? sessionStorage : localStorage;
        const newStorage = sessionOnly ? sessionStorage : localStorage;
        
        // Get existing config from old storage
        const existingConfig = oldStorage.getItem(CONFIG_KEY);
        
        // Clear old storage
        oldStorage.removeItem(CONFIG_KEY);
        
        // Move to new storage if exists
        if (existingConfig) {
            newStorage.setItem(CONFIG_KEY, existingConfig);
        }
    }
    
    localStorage.setItem(STORAGE_MODE_KEY, newMode);
    configCache = null; // Clear cache
}

/**
 * Get custom config from storage if available.
 * Returns decrypted values for API calls.
 */
async function getCustomConfigAsync() {
    if (configCache) return configCache;
    
    const storage = getStorage();
    const config = storage.getItem(CONFIG_KEY);
    if (!config) return null;

    try {
        const parsed = JSON.parse(config);
        
        // Decrypt sensitive fields
        const decrypted = {
            blueant_url: parsed.blueant_url || '',
            blueant_key: parsed.blueant_key ? await decrypt(parsed.blueant_key) : '',
            gemini_key: parsed.gemini_key ? await decrypt(parsed.gemini_key) : '',
            openrouter_key: parsed.openrouter_key ? await decrypt(parsed.openrouter_key) : '',
            llm_provider: parsed.llm_provider || 'gemini',
            llm_model: parsed.llm_model || '',
        };
        
        // Only return if at least one value is set
        if (decrypted.blueant_url || decrypted.blueant_key || decrypted.gemini_key || decrypted.openrouter_key) {
            configCache = decrypted;
            return decrypted;
        }
    } catch (e) {
        console.warn('Failed to parse/decrypt config from storage:', e);
    }
    return null;
}

/**
 * Synchronous wrapper for backward compatibility.
 * Note: First call may return null until async decryption completes.
 */
export function getCustomConfig() {
    // Return cached value if available
    if (configCache) return configCache;
    
    // Trigger async load for next time
    getCustomConfigAsync().catch(console.error);
    
    // Try to return unencrypted fallback for first load
    const storage = getStorage();
    const config = storage.getItem(CONFIG_KEY);
    if (!config) return null;
    
    try {
        const parsed = JSON.parse(config);
        // Check if this is old unencrypted format
        if (parsed.blueant_key && !parsed.blueant_key.includes('=')) {
            // Likely unencrypted, return as-is for backward compatibility
            return parsed;
        }
    } catch (e) {
        // Ignore
    }
    
    return null;
}

/**
 * Search portfolios by name.
 * @param {string} name - Portfolio name to search for
 * @returns {Promise<{success: boolean, portfolios?: Array, error?: string}>}
 */
export async function searchPortfolios(name) {
    const customConfig = await getCustomConfigAsync();
    
    const response = await fetch(`${API_BASE}/api/portfolios/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            custom_config: customConfig,
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
    const customConfig = await getCustomConfigAsync();
    
    // Build request body with LLM selection
    const requestBody = {
        portfolio_id: portfolioId,
        custom_config: customConfig ? {
            blueant_url: customConfig.blueant_url,
            blueant_key: customConfig.blueant_key,
            gemini_key: customConfig.gemini_key,
            openrouter_key: customConfig.openrouter_key,
        } : null,
    };
    
    // Add LLM provider/model selection
    if (customConfig?.llm_provider) {
        requestBody.llm_provider = customConfig.llm_provider;
    }
    if (customConfig?.llm_model) {
        requestBody.llm_model = customConfig.llm_model;
    }
    
    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
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
 * @param {string} detailLevel - Detail level ('compact' or 'detailed')
 * @returns {Promise<Blob>} PPTX file as blob
 */
export async function generateReport(analysis, language = 'de', detailLevel = 'compact') {
    const response = await fetch(`${API_BASE}/api/reports/pptx`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            analysis,
            options: { language, detail_level: detailLevel },
        }),
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.blob();
}

/**
 * Generate detailed PowerPoint report from analysis.
 * @param {Object} analysis - Portfolio analysis data
 * @param {string} language - Report language (de or en)
 * @returns {Promise<Blob>} PPTX file as blob
 */
export async function generateDetailedReport(analysis, language = 'de') {
    return generateReport(analysis, language, 'detailed');
}

/**
 * Generate Word document report from analysis.
 * @param {Object} analysis - Portfolio analysis data
 * @param {string} language - Report language (de or en)
 * @returns {Promise<Blob>} DOCX file as blob
 */
export async function generateWordReport(analysis, language = 'de') {
    const response = await fetch(`${API_BASE}/api/reports/docx`, {
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
 * Save config to storage with encryption.
 * @param {Object} config - Configuration object with plaintext values
 */
export async function saveConfig(config) {
    try {
        // Encrypt sensitive fields (API keys only)
        const encrypted = {
            blueant_url: config.blueant_url || '', // URL doesn't need encryption
            blueant_key: config.blueant_key ? await encrypt(config.blueant_key) : '',
            gemini_key: config.gemini_key ? await encrypt(config.gemini_key) : '',
            openrouter_key: config.openrouter_key ? await encrypt(config.openrouter_key) : '',
            llm_provider: config.llm_provider || 'gemini', // Not sensitive
            llm_model: config.llm_model || '', // Not sensitive
            encrypted: true, // Mark as encrypted format
            timestamp: Date.now(),
        };
        
        const storage = getStorage();
        storage.setItem(CONFIG_KEY, JSON.stringify(encrypted));
        
        // Update cache with plaintext values
        configCache = {
            blueant_url: config.blueant_url || '',
            blueant_key: config.blueant_key || '',
            gemini_key: config.gemini_key || '',
            openrouter_key: config.openrouter_key || '',
            llm_provider: config.llm_provider || 'gemini',
            llm_model: config.llm_model || '',
        };
        
        return true;
    } catch (error) {
        console.error('Failed to save config:', error);
        throw error;
    }
}

/**
 * Load config from storage (decrypted).
 * @returns {Promise<Object>} Configuration object with plaintext values
 */
export async function loadConfig() {
    const storage = getStorage();
    const config = storage.getItem(CONFIG_KEY);
    
    const defaultConfig = {
        blueant_url: '',
        blueant_key: '',
        gemini_key: '',
        openrouter_key: '',
        llm_provider: 'gemini',
        llm_model: '',
    };
    
    if (!config) {
        return defaultConfig;
    }
    
    try {
        const parsed = JSON.parse(config);
        
        // Check if encrypted format
        if (parsed.encrypted) {
            return {
                blueant_url: parsed.blueant_url || '',
                blueant_key: parsed.blueant_key ? await decrypt(parsed.blueant_key) : '',
                gemini_key: parsed.gemini_key ? await decrypt(parsed.gemini_key) : '',
                openrouter_key: parsed.openrouter_key ? await decrypt(parsed.openrouter_key) : '',
                llm_provider: parsed.llm_provider || 'gemini',
                llm_model: parsed.llm_model || '',
            };
        }
        
        // Legacy unencrypted format - migrate on next save
        return {
            blueant_url: parsed.blueant_url || '',
            blueant_key: parsed.blueant_key || '',
            gemini_key: parsed.gemini_key || '',
            openrouter_key: '',
            llm_provider: 'gemini',
            llm_model: '',
        };
    } catch (e) {
        console.warn('Failed to load config:', e);
        return defaultConfig;
    }
}

/**
 * Clear all stored credentials.
 */
export function clearConfig() {
    localStorage.removeItem(CONFIG_KEY);
    sessionStorage.removeItem(CONFIG_KEY);
    configCache = null;
}

/**
 * Check if encryption is available.
 * @returns {boolean}
 */
export function isEncryptionAvailable() {
    return isCryptoAvailable();
}
