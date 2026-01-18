// Runtime configuration
// In Docker (nginx reverse proxy): API calls go to same origin
// Local development: API calls go to localhost:8000
window.APP_CONFIG = {
    // If running on port 80 or 443 (Docker/production), use same origin (nginx proxy)
    // Otherwise (local dev on port 3000), use localhost:8000
    API_BASE: (window.location.port === '' || window.location.port === '80' || window.location.port === '443')
        ? window.location.origin
        : 'http://localhost:8000'
};
