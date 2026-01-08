/**
 * Cryptographic utilities for secure key storage.
 * Uses Web Crypto API for AES-GCM encryption.
 */

// Encryption key derived from a device-specific fingerprint
// This provides defense-in-depth, not absolute security
const SALT = 'portfolio-analyzer-v1';

/**
 * Generate a cryptographic key from a passphrase using PBKDF2.
 * Uses browser fingerprint as additional entropy.
 * @returns {Promise<CryptoKey>}
 */
async function deriveKey() {
    // Create a device fingerprint for key derivation
    // This makes stored data harder to extract and use elsewhere
    const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width,
        screen.height,
        new Date().getTimezoneOffset(),
        SALT
    ].join('|');

    const encoder = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
        'raw',
        encoder.encode(fingerprint),
        'PBKDF2',
        false,
        ['deriveKey']
    );

    return crypto.subtle.deriveKey(
        {
            name: 'PBKDF2',
            salt: encoder.encode(SALT),
            iterations: 100000,
            hash: 'SHA-256'
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
    );
}

/**
 * Encrypt data using AES-GCM.
 * @param {string} plaintext - Data to encrypt
 * @returns {Promise<string>} Base64-encoded encrypted data with IV
 */
export async function encrypt(plaintext) {
    if (!plaintext) return '';
    
    try {
        const key = await deriveKey();
        const encoder = new TextEncoder();
        const data = encoder.encode(plaintext);
        
        // Generate random IV for each encryption
        const iv = crypto.getRandomValues(new Uint8Array(12));
        
        const encrypted = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            key,
            data
        );
        
        // Combine IV and encrypted data
        const combined = new Uint8Array(iv.length + encrypted.byteLength);
        combined.set(iv);
        combined.set(new Uint8Array(encrypted), iv.length);
        
        // Return as base64
        return btoa(String.fromCharCode(...combined));
    } catch (error) {
        console.error('Encryption error:', error);
        throw new Error('Failed to encrypt data');
    }
}

/**
 * Decrypt data using AES-GCM.
 * @param {string} ciphertext - Base64-encoded encrypted data
 * @returns {Promise<string>} Decrypted plaintext
 */
export async function decrypt(ciphertext) {
    if (!ciphertext) return '';
    
    try {
        const key = await deriveKey();
        
        // Decode base64
        const combined = Uint8Array.from(atob(ciphertext), c => c.charCodeAt(0));
        
        // Extract IV and encrypted data
        const iv = combined.slice(0, 12);
        const data = combined.slice(12);
        
        const decrypted = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            key,
            data
        );
        
        const decoder = new TextDecoder();
        return decoder.decode(decrypted);
    } catch (error) {
        console.error('Decryption error:', error);
        // Return empty on decryption failure (e.g., different device)
        return '';
    }
}

/**
 * Check if Web Crypto API is available.
 * @returns {boolean}
 */
export function isCryptoAvailable() {
    return typeof crypto !== 'undefined' && 
           typeof crypto.subtle !== 'undefined' &&
           typeof crypto.getRandomValues !== 'undefined';
}




