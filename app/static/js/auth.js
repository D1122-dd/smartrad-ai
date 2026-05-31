/**
 * auth.js — SmartRAD AI Shared Auth Utilities
 * Handles: token storage, auth guard, logout, and API helper.
 */

const Auth = {
    /**
     * Save token + user info after login/register
     */
    save(token, userName, userId, profileImage) {
        localStorage.setItem('xray_token', token);
        localStorage.setItem('xray_user_name', userName);
        localStorage.setItem('xray_user_id', userId);
        localStorage.setItem('xray_user_image', profileImage || '');
    },

    /**
     * Get stored token
     */
    getToken() {
        return localStorage.getItem('xray_token');
    },

    /**
     * Get stored user name
     */
    getUserName() {
        return localStorage.getItem('xray_user_name') || 'User';
    },

    /**
     * Get stored profile image
     */
    getProfileImage() {
        return localStorage.getItem('xray_user_image') || null;
    },

    /**
     * Clear all auth data and redirect to login
     */
    logout() {
        localStorage.removeItem('xray_token');
        localStorage.removeItem('xray_user_name');
        localStorage.removeItem('xray_user_id');
        localStorage.removeItem('xray_user_image');
        window.location.href = '/';
    },

    /**
     * Guard: call on any protected page.
     * Verifies the token with the server; if invalid, redirects to login.
     */
    async guard() {
        const token = Auth.getToken();
        if (!token) {
            window.location.href = '/login';
            return false;
        }
        try {
            const response = await fetch('/api/auth/verify-token', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const result = await response.json();
            if (!result.success) {
                Auth.logout();
                return false;
            }
            // Update local info in case name or image changed
            localStorage.setItem('xray_user_name', result.user_name);
            localStorage.setItem('xray_user_image', result.profile_image || '');
            return true;
        } catch (e) {
            Auth.logout();
            return false;
        }
    },

    /**
     * Guard for public pages (login/register):
     * If user is already logged in, redirect to dashboard.
     */
    async guardPublic() {
        const token = Auth.getToken();
        if (!token) return; // Not logged in, stay on page
        try {
            const response = await fetch('/api/auth/verify-token', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const result = await response.json();
            if (result.success) {
                window.location.href = '/dashboard';
            }
        } catch (e) { /* ignore, stay on page */ }
    },

    /**
     * Authenticated fetch — auto-attaches the Bearer token
     */
    async fetch(url, options = {}) {
        const token = Auth.getToken();
        options.headers = options.headers || {};
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Only set default Content-Type if not already set and not sending FormData
        if (!options.headers['Content-Type'] && !(options.body instanceof FormData)) {
            options.headers['Content-Type'] = 'application/json';
        }
        
        return fetch(url, options);
    }
};
