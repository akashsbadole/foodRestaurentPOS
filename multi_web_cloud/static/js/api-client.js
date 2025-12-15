/**
 * Enhanced API Client for Restaurant POS Application
 * Provides unified API integration with error handling, retries, and offline support
 */

class APIClient {
    constructor(options = {}) {
        this.options = {
            baseURL: '',
            timeout: 30000,
            retries: 3,
            retryDelay: 1000,
            enableOffline: true,
            cacheEnabled: true,
            cacheTimeout: 5 * 60 * 1000, // 5 minutes
            ...options
        };
        
        this.cache = new Map();
        this.offlineQueue = [];
        this.isOnline = navigator.onLine;
        
        this.init();
    }
    
    init() {
        // Setup online/offline listeners
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.processOfflineQueue();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
        
        // Setup periodic queue processing
        setInterval(() => {
            if (this.isOnline && this.offlineQueue.length > 0) {
                this.processOfflineQueue();
            }
        }, 30000); // Every 30 seconds
    }
    
    /**
     * Make API request with error handling and retries
     */
    async request(endpoint, options = {}) {
        const url = this.buildURL(endpoint);
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            ...options
        };
        
        // Add CSRF token if available
        const csrfToken = this.getCSRFToken();
        if (csrfToken) {
            config.headers['X-CSRF-Token'] = csrfToken;
        }
        
        // Check cache for GET requests
        if (config.method === 'GET' && this.options.cacheEnabled) {
            const cached = this.getFromCache(url);
            if (cached) {
                return cached;
            }
        }
        
        // Handle offline mode
        if (!this.isOnline && this.options.enableOffline) {
            return this.handleOfflineRequest(url, config);
        }
        
        let lastError;
        
        for (let attempt = 0; attempt <= this.options.retries; attempt++) {
            try {
                const response = await this.makeRequest(url, config);
                
                // Cache successful GET requests
                if (config.method === 'GET' && this.options.cacheEnabled) {
                    this.setCache(url, response);
                }
                
                return response;
            } catch (error) {
                lastError = error;
                
                if (attempt < this.options.retries) {
                    await this.delay(this.options.retryDelay * Math.pow(2, attempt));
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Make actual HTTP request
     */
    async makeRequest(url, config) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.options.timeout);
        
        try {
            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new APIError(response.statusText, response.status, response);
            }
            
            const data = await response.json();
            
            if (!data.success) {
                throw new APIError(data.message || 'Request failed', response.status, response, data);
            }
            
            return data;
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 408, null);
            }
            
            throw error;
        }
    }
    
    /**
     * Handle requests when offline
     */
    handleOfflineRequest(url, config) {
        const requestData = {
            url,
            config,
            timestamp: Date.now(),
            id: this.generateRequestId()
        };
        
        // Queue the request
        this.offlineQueue.push(requestData);
        
        // Save to localStorage
        this.saveOfflineQueue();
        
        // Show offline notification
        this.showNotification('You are currently offline. Request will be processed when connection is restored.', 'warning');
        
        // Return a mock response for immediate UI feedback
        return {
            success: false,
            offline: true,
            message: 'Offline - Request queued',
            data: null
        };
    }
    
    /**
     * Process offline queue when back online
     */
    async processOfflineQueue() {
        if (this.offlineQueue.length === 0) return;
        
        this.showNotification('Processing offline requests...', 'info');
        
        const queue = [...this.offlineQueue];
        this.offlineQueue = [];
        this.saveOfflineQueue();
        
        for (const request of queue) {
            try {
                await this.makeRequest(request.url, request.config);
            } catch (error) {
                console.error('Failed to process offline request:', error);
                this.showNotification('Failed to process some offline requests', 'error');
            }
        }
        
        this.showNotification('Offline requests processed', 'success');
    }
    
    /**
     * Build full URL from endpoint
     */
    buildURL(endpoint) {
        if (endpoint.startsWith('http')) {
            return endpoint;
        }
        
        const baseURL = this.options.baseURL || '';
        return baseURL.replace(/\/$/, '') + '/' + endpoint.replace(/^\//, '');
    }
    
    /**
     * Cache management
     */
    getFromCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.options.cacheTimeout) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }
    
    setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }
    
    /**
     * Offline queue management
     */
    saveOfflineQueue() {
        try {
            localStorage.setItem('api_offline_queue', JSON.stringify(this.offlineQueue));
        } catch (error) {
            console.error('Failed to save offline queue:', error);
        }
    }
    
    loadOfflineQueue() {
        try {
            const saved = localStorage.getItem('api_offline_queue');
            if (saved) {
                this.offlineQueue = JSON.parse(saved);
            }
        } catch (error) {
            console.error('Failed to load offline queue:', error);
        }
    }
    
    /**
     * Utility methods
     */
    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        const input = document.querySelector('input[name="csrf_token"]');
        return input ? input.value : '';
    }
    
    generateRequestId() {
        return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    showNotification(message, type = 'info') {
        // Dispatch event for global notification system
        document.dispatchEvent(new CustomEvent('showNotification', {
            detail: { message, type }
        }));
    }
    
    /**
     * API endpoint methods
     */
    
    // Authentication APIs
    async login(credentials) {
        return this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
    }
    
    async logout() {
        return this.request('/api/auth/logout', {
            method: 'POST'
        });
    }
    
    async checkSession() {
        return this.request('/api/auth/check');
    }
    
    async refreshToken() {
        return this.request('/api/auth/refresh', {
            method: 'POST'
        });
    }
    
    // Dashboard APIs
    async getDashboardStats() {
        return this.request('/api/dashboard/stats');
    }
    
    async getRealtimeMetrics() {
        return this.request('/api/dashboard/realtime');
    }
    
    async getRecentOrders() {
        return this.request('/api/dashboard/recent-orders');
    }
    
    // Order Management APIs
    async getOrders(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request('/api/orders' + (params ? '?' + params : ''));
    }
    
    async getOrder(orderId) {
        return this.request(`/api/orders/${orderId}`);
    }
    
    async createOrder(orderData) {
        return this.request('/api/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }
    
    async updateOrder(orderId, orderData) {
        return this.request(`/api/orders/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify(orderData)
        });
    }
    
    async deleteOrder(orderId) {
        return this.request(`/api/orders/${orderId}`, {
            method: 'DELETE'
        });
    }
    
    // Menu Management APIs
    async getMenuItems(categoryId = null) {
        const url = categoryId ? `/api/menu/items?category=${categoryId}` : '/api/menu/items';
        return this.request(url);
    }
    
    async getCategories() {
        return this.request('/api/menu/categories');
    }
    
    async createMenuItem(itemData) {
        return this.request('/api/menu/items', {
            method: 'POST',
            body: JSON.stringify(itemData)
        });
    }
    
    async updateMenuItem(itemId, itemData) {
        return this.request(`/api/menu/items/${itemId}`, {
            method: 'PUT',
            body: JSON.stringify(itemData)
        });
    }
    
    // Table Management APIs
    async getTables() {
        return this.request('/api/tables');
    }
    
    async updateTableStatus(tableId, status) {
        return this.request(`/api/tables/${tableId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    }
    
    // Payment APIs
    async processPayment(paymentData) {
        return this.request('/api/payment/process', {
            method: 'POST',
            body: JSON.stringify(paymentData)
        });
    }
    
    async getPaymentMethods() {
        return this.request('/api/payment/methods');
    }
    
    async refundPayment(paymentId, refundData) {
        return this.request(`/api/payment/${paymentId}/refund`, {
            method: 'POST',
            body: JSON.stringify(refundData)
        });
    }
    
    // Settings APIs
    async getSettings() {
        return this.request('/api/settings');
    }
    
    async updateSettings(settingsData) {
        return this.request('/api/settings', {
            method: 'PUT',
            body: JSON.stringify(settingsData)
        });
    }
    
    async getValidationConfig(formType) {
        return this.request(`/api/validation/get-validation-config/${formType}`);
    }
    
    // Security APIs
    async getSecurityStatus() {
        return this.request('/api/security/status');
    }
    
    async getSecurityLogs() {
        return this.request('/api/security/logs');
    }
    
    async reportSecurityEvent(eventData) {
        return this.request('/api/security/report-event', {
            method: 'POST',
            body: JSON.stringify(eventData)
        });
    }
    
    // Offline Sync APIs
    async getOfflineStatus() {
        return this.request('/api/offline/status');
    }
    
    async syncOfflineData() {
        return this.request('/api/offline/sync', {
            method: 'POST'
        });
    }
    
    async getPendingSyncItems() {
        return this.request('/api/offline/pending-items');
    }
    
    // Session Management APIs
    async getSessionInfo() {
        return this.request('/api/session/info');
    }
    
    async extendSession() {
        return this.request('/api/session/extend', {
            method: 'POST'
        });
    }
    
    async getActiveSessions() {
        return this.request('/api/session/active');
    }
    
    async terminateSession(sessionId) {
        return this.request('/api/session/terminate', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId })
        });
    }
    
    // Validation APIs
    async validateField(fieldName, value, fieldType) {
        return this.request('/api/validation/validate-field', {
            method: 'POST',
            body: JSON.stringify({
                field_name: fieldName,
                value,
                field_type: fieldType
            })
        });
    }
    
    async validateForm(formData, formConfig) {
        return this.request('/api/validation/validate-form', {
            method: 'POST',
            body: JSON.stringify({
                form_data: formData,
                form_config: formConfig
            })
        });
    }
    
    async validatePasswordStrength(password) {
        return this.request('/api/validation/validate-password-strength', {
            method: 'POST',
            body: JSON.stringify({ password })
        });
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status = null, response = null, data = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.response = response;
        this.data = data;
    }
}

/**
 * Create global API client instance
 */
window.apiClient = new APIClient({
    baseURL: window.location.origin,
    timeout: 30000,
    retries: 3,
    enableOffline: true,
    cacheEnabled: true
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, APIError };
}