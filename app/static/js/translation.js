/**
 * app/static/js/translation.js
 * 
 * i18n Translation Engine for SmartRAD AI.
 * Loads translation.json dynamically and exposes t() function.
 * Supports static translating of elements with data-i18n, placeholders with data-i18n-placeholder.
 */

'use strict';

let translations = {};
let currentLanguage = localStorage.getItem('language') || 'ar'; // defaults to Arabic

// Synchronize cookie with current language
function syncLanguageCookie(lang) {
    document.cookie = `lang=${lang}; max-age=31536000; path=/; SameSite=Lax`;
}

/**
 * Load translations from JSON file
 */
async function loadTranslations() {
    try {
        const response = await fetch('/static/js/translation.json');
        if (!response.ok) throw new Error('Failed to load translations');
        translations = await response.json();
        console.log('✓ SmartRAD Translations loaded successfully');
    } catch (err) {
        console.error('✗ Error loading translations:', err);
        translations = { ar: {}, en: {} };
    }
}

/**
 * Get translation by key
 * Usage: t('common.loading') or t('dashboard.waiting_cases')
 * Returns: Translated text or the key itself if not found
 */
function t(key) {
    if (!key) return '';
    
    const keys = key.split('.');
    let value = translations[currentLanguage];
    
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            return key; // return key as fallback
        }
    }
    return value || key;
}

/**
 * Set active language
 * Updates HTML attributes, direction (RTL/LTR), cookie, and localStorage
 */
function setLanguage(lang) {
    currentLanguage = lang === 'en' ? 'en' : 'ar';
    localStorage.setItem('language', currentLanguage);
    syncLanguageCookie(currentLanguage);
    
    // Update HTML element direction and attributes
    const htmlElement = document.documentElement;
    htmlElement.setAttribute('data-lang', currentLanguage);
    htmlElement.setAttribute('lang', currentLanguage);
    htmlElement.dir = currentLanguage === 'ar' ? 'rtl' : 'ltr';
    
    if (currentLanguage === 'ar') {
        htmlElement.classList.add('rtl');
        htmlElement.classList.remove('ltr');
    } else {
        htmlElement.classList.add('ltr');
        htmlElement.classList.remove('rtl');
    }

    // Update language toggle button label — shows the OTHER language (what you'll switch TO)
    const langTextEl = document.getElementById('langText');
    if (langTextEl) {
        langTextEl.textContent = currentLanguage === 'ar' ? 'English' : 'العربية';
    }
    
    // Auto-update any DOM elements with data-i18n
    translatePage();
}

/**
 * Toggle language
 */
function toggleLanguage() {
    const newLang = currentLanguage === 'ar' ? 'en' : 'ar';
    setLanguage(newLang);
    // Redirect to Flask route to ensure server-side context matches and triggers redirection/refresh
    window.location.href = '/set-lang/' + newLang;
}

/**
 * Get current language
 */
function getLanguage() {
    return currentLanguage;
}

/**
 * Scan page and translate elements with data-i18n and data-i18n-placeholder
 */
function translatePage() {
    // Translate text content
    const textElements = document.querySelectorAll('[data-i18n]');
    textElements.forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translated = t(key);
        // Avoid replacing inside nested children if they have their own i18n
        el.textContent = translated;
    });

    // Translate placeholder attributes
    const inputElements = document.querySelectorAll('[data-i18n-placeholder]');
    inputElements.forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.setAttribute('placeholder', t(key));
    });
}

/**
 * Initialize translations
 */
async function initializeTranslations() {
    await loadTranslations();
    
    // Server cookie always wins — it is the source of truth set by /set-lang/<lang>
    const match = document.cookie.match(new RegExp('(^| )lang=([^;]*)'));
    if (match && (match[2] === 'en' || match[2] === 'ar')) {
        currentLanguage = match[2];
        localStorage.setItem('language', currentLanguage);
    } else {
        // Fall back to localStorage, then default to Arabic
        currentLanguage = localStorage.getItem('language') || 'ar';
    }
    
    setLanguage(currentLanguage);
}

// Auto init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTranslations);
} else {
    initializeTranslations();
}
