/**
 * Offline Manager - Client-side offline functionality for Flask POS
 * Handles offline detection, data storage, and synchronization
 */

class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.offlineQueue = [];
        this.syncInProgress = false;
        this.retryAttempts = {};
        this.maxRetries = 3;
        this.syncInterval = null;
        this.statusCheckInterval = null;
        
        // Initialize event listeners
        this.initEventListeners();
        
        // Start status monitoring
        this.startStatusMonitoring();
        
        // Load offline queue from storage
        this.loadOfflineQueue();
        
        console.log('Offline Manager initialized');
    }

    /**
     * Initialize event listeners for online/offline events
     */
    initEventListeners() {
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.handleConnectionChange();
            this.showNotification('Connection restored', 'success');
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.handleConnectionChange();
            this.showNotification('Connection lost - working offline', 'warning');
        });

        // Listen for page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isOnline) {
                this.checkConnectionStatus();
            }
        });
    }

    /**
     * Start monitoring connection status
     */
    startStatusMonitoring() {
        // Check connection status every 30 seconds
        this.statusCheckInterval = setInterval(() => {
            this.checkConnectionStatus();
        }, 30000);

        // Sync every 60 seconds when online
        this.syncInterval = setInterval(() => {
            if (this.isOnline && !this.syncInProgress) {
                this.syncOfflineData();
            }
        }, 60000);
    }

    /**
     * Handle connection state changes
     */
    handleConnectionChange() {
        this.updateUI();
        
        if (this.isOnline) {
            // Trigger sync when coming back online
            setTimeout(() => {
                this.syncOfflineData();
            }, 2000);
        }
    }

    /**
     * Check actual connection status by making a request
     */
    async checkConnectionStatus() {
        try {
            const response = await fetch('/api/offline/check_connection', {
                method: 'GET',
                cache: 'no-cache',
                timeout: 5000
            });
            
            const result = await response.json();
            const wasOnline = this.isOnline;
            this.isOnline = result.data.is_online;
            
            if (wasOnline !== this.isOnline) {
                this.handleConnectionChange();
            }
            
        } catch (error) {
            if (this.isOnline) {
                this.isOnline = false;
                this.handleConnectionChange();
            }
        }
    }

    /**
     * Make API request with offline fallback
     */
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            if (this.isOnline) {
                const response = await fetch(url, finalOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
            } else {
                throw new Error('Offline mode');
            }
        } catch (error) {
            console.warn(`Request failed: ${url}`, error);
            
            // Store request for offline sync if it's a POST/PUT/DELETE
            if (['POST', 'PUT', 'DELETE'].includes(finalOptions.method)) {
                await this.storeOfflineRequest(url, finalOptions);
            }
            
            // Try to get cached data for GET requests
            if (finalOptions.method === 'GET') {
                return this.getCachedData(url);
            }
            
            throw error;
        }
    }

    /**
     * Store request for offline synchronization
     */
    async storeOfflineRequest(url, options) {
        const requestData = {
            url: url,
            method: options.method,
            headers: options.headers,
            body: options.body,
            timestamp: new Date().toISOString(),
            retryCount: 0
        };

        // Add to offline queue
        this.offlineQueue.push(requestData);
        this.saveOfflineQueue();
        
        console.log('Request stored for offline sync:', url);
    }

    /**
     * Get cached data for GET requests
     */
    async getCachedData(url) {
        try {
            // Check if we have cached data for this URL
            if (url.includes('/api/menu/items')) {
                const menuItems = this.getFromStorage('cached_menu_items') || [];
                return { success: true, data: menuItems, offline: true };
            }
            
            if (url.includes('/api/categories')) {
                const categories = this.getFromStorage('cached_categories') || [];
                return { success: true, data: categories, offline: true };
            }
            
            if (url.includes('/api/tables')) {
                const tables = this.getFromStorage('cached_tables') || [];
                return { success: true, data: tables, offline: true };
            }
            
            // Generic fallback
            return { 
                success: false, 
                message: 'No cached data available', 
                offline: true 
            };
            
        } catch (error) {
            console.error('Error getting cached data:', error);
            return { 
                success: false, 
                message: 'Error accessing cached data', 
                offline: true 
            };
        }
    }

    /**
     * Get specific cached data type
     */
    getCachedData(type) {
        try {
            return this.getFromStorage(`cached_${type}`) || [];
        } catch (error) {
            console.error(`Error getting cached ${type}:`, error);
            return [];
        }
    }

    /**
     * Synchronize offline data with conflict resolution
     */
    async syncOfflineData() {
        if (this.syncInProgress || this.offlineQueue.length === 0) {
            return;
        }

        this.syncInProgress = true;
        this.updateSyncStatus('Syncing...');

        try {
            const queue = [...this.offlineQueue];
            const results = [];
            const conflicts = [];

            for (const request of queue) {
                try {
                    // Check for potential conflicts before syncing
                    const conflictCheck = await this.checkForConflicts(request);
                    
                    if (conflictCheck.hasConflict) {
                        const resolution = await this.resolveConflict(request, conflictCheck.serverData);
                        
                        if (resolution.action === 'skip') {
                            results.push({ ...request, success: false, skipped: true, reason: 'Conflict skipped' });
                            this.removeFromQueue(request);
                            continue;
                        } else if (resolution.action === 'merge') {
                            // Update request with merged data
                            request.body = JSON.stringify(resolution.mergedData);
                        }
                        // else: use original request (override)
                    }

                    const result = await this.syncRequest(request);
                    results.push({ ...request, success: true, result });
                    
                    // Remove from queue on success
                    this.removeFromQueue(request);
                    
                } catch (error) {
                    console.error('Sync failed for request:', request, error);
                    results.push({ ...request, success: false, error: error.message });
                    
                    // Update retry count
                    request.retryCount = (request.retryCount || 0) + 1;
                    
                    // Remove if max retries reached
                    if (request.retryCount >= this.maxRetries) {
                        this.removeFromQueue(request);
                        this.showNotification(`Failed to sync: ${request.url}`, 'error');
                    }
                }
            }

            // Handle conflicts separately
            if (conflicts.length > 0) {
                await this.handleConflicts(conflicts);
            }

            this.updateSyncStatus(`Synced ${results.filter(r => r.success).length} items`);
            
        } catch (error) {
            console.error('Sync process failed:', error);
            this.updateSyncStatus('Sync failed');
        } finally {
            this.syncInProgress = false;
            this.saveOfflineQueue();
            this.updateUI();
        }
    }

    /**
     * Check for potential conflicts before syncing
     */
    async checkForConflicts(request) {
        try {
            // For POST requests, check if resource already exists
            if (request.method === 'POST' && request.url.includes('/orders/')) {
                const orderData = JSON.parse(request.body);
                
                // Check if order already exists on server
                const checkResponse = await fetch(`/api/orders/check_conflict`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        order_number: orderData.order_number,
                        customer_mobile: orderData.customer_mobile
                    })
                });
                
                if (checkResponse.ok) {
                    const conflictData = await checkResponse.json();
                    return {
                        hasConflict: conflictData.conflict,
                        serverData: conflictData.serverData,
                        conflictType: 'order_exists'
                    };
                }
            }
            
            // For PUT requests, check if resource was modified
            if (request.method === 'PUT') {
                const requestData = JSON.parse(request.body);
                
                const checkResponse = await fetch(`${request.url.replace('/api/', '/api/check_conflict/')}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        id: requestData.id,
                        last_modified: requestData.last_modified
                    })
                });
                
                if (checkResponse.ok) {
                    const conflictData = await checkResponse.json();
                    return {
                        hasConflict: conflictData.conflict,
                        serverData: conflictData.serverData,
                        conflictType: 'resource_modified'
                    };
                }
            }
            
            return { hasConflict: false };
            
        } catch (error) {
            console.error('Error checking for conflicts:', error);
            return { hasConflict: false };
        }
    }

    /**
     * Resolve conflicts between offline and server data
     */
    async resolveConflict(request, serverData) {
        try {
            const requestData = JSON.parse(request.body);
            
            // Create conflict resolution dialog
            return new Promise((resolve) => {
                this.showConflictDialog(request, serverData, resolve);
            });
            
        } catch (error) {
            console.error('Error resolving conflict:', error);
            return { action: 'override' }; // Default to override
        }
    }

    /**
     * Show conflict resolution dialog
     */
    showConflictDialog(request, serverData, callback) {
        const requestData = JSON.parse(request.body);
        
        // Create modal dialog
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Sync Conflict Detected</h5>
                    </div>
                    <div class="modal-body">
                        <p><strong>Conflict detected when syncing:</strong></p>
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Offline Data:</h6>
                                <pre>${JSON.stringify(requestData, null, 2)}</pre>
                            </div>
                            <div class="col-md-6">
                                <h6>Server Data:</h6>
                                <pre>${JSON.stringify(serverData, null, 2)}</pre>
                            </div>
                        </div>
                        <div class="mt-3">
                            <label><strong>Choose resolution:</strong></label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="conflictResolution" value="override" checked>
                                <label class="form-check-label">Use Offline Data (Override Server)</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="conflictResolution" value="merge">
                                <label class="form-check-label">Try to Merge Data</label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="conflictResolution" value="skip">
                                <label class="form-check-label">Skip This Item</label>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="resolveConflictBtn">Resolve</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Handle resolution
        document.getElementById('resolveConflictBtn').addEventListener('click', () => {
            const selected = document.querySelector('input[name="conflictResolution"]:checked').value;
            
            let resolution = { action: selected };
            
            if (selected === 'merge') {
                resolution.mergedData = this.mergeData(requestData, serverData);
            }
            
            bsModal.hide();
            modal.remove();
            callback(resolution);
        });
        
        // Handle cancel
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
            callback({ action: 'skip' });
        });
    }

    /**
     * Merge offline and server data
     */
    mergeData(offlineData, serverData) {
        try {
            const merged = { ...serverData };
            
            // Merge logic for different data types
            if (offlineData.items && serverData.items) {
                // Merge order items
                const offlineItems = offlineData.items || [];
                const serverItems = serverData.items || [];
                
                // Combine items, remove duplicates
                const allItems = [...offlineItems, ...serverItems];
                const uniqueItems = allItems.reduce((acc, item) => {
                    const exists = acc.find(existing => existing.menu_item_id === item.menu_item_id);
                    if (!exists) {
                        acc.push(item);
                    } else {
                        // If item exists, use the one with higher quantity
                        const existingIndex = acc.findIndex(existing => existing.menu_item_id === item.menu_item_id);
                        acc[existingIndex] = acc[existingIndex].quantity > item.quantity ? acc[existingIndex] : item;
                    }
                    return acc;
                }, []);
                
                merged.items = uniqueItems;
                merged.subtotal = uniqueItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            }
            
            // Merge other fields, preferring offline data
            Object.keys(offlineData).forEach(key => {
                if (key !== 'items' && offlineData[key] !== undefined) {
                    merged[key] = offlineData[key];
                }
            });
            
            return merged;
            
        } catch (error) {
            console.error('Error merging data:', error);
            return offlineData; // Return original data on error
        }
    }

    /**
     * Handle multiple conflicts
     */
    async handleConflicts(conflicts) {
        const conflictSummary = conflicts.map(c => `${c.type}: ${c.description}`).join('\n');
        
        this.showNotification(
            `Multiple conflicts detected:\n${conflictSummary}`,
            'warning',
            10000 // Longer display time
        );
    }

    /**
     * Sync individual request
     */
    async syncRequest(request) {
        const options = {
            method: request.method,
            headers: request.headers,
            body: request.body
        };

        const response = await fetch(request.url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    /**
     * Remove request from queue
     */
    removeFromQueue(request) {
        const index = this.offlineQueue.findIndex(
            item => item.url === request.url && 
                   item.method === request.method && 
                   item.timestamp === request.timestamp
        );
        
        if (index !== -1) {
            this.offlineQueue.splice(index, 1);
        }
    }

    /**
     * Cache data for offline use
     */
    async cacheData(type, data) {
        try {
            this.setToStorage(`cached_${type}`, data);
            console.log(`Cached ${type} data:`, data.length || 'items');
        } catch (error) {
            console.error(`Error caching ${type} data:`, error);
        }
    }

    /**
     * Load and cache all necessary data
     */
    async loadAndCacheData() {
        try {
            // Get cached data from server
            const response = await this.makeRequest('/api/offline/data/cache');
            
            if (response.success) {
                const { menu_items, categories, tables } = response.data;
                
                // Cache locally
                await this.cacheData('menu_items', menu_items);
                await this.cacheData('categories', categories);
                await this.cacheData('tables', tables);
                
                console.log('Data cached successfully for offline use');
            }
        } catch (error) {
            console.error('Error loading data for cache:', error);
        }
    }

    /**
     * Update UI based on offline status
     */
    updateUI() {
        // Update status indicators
        const statusElements = document.querySelectorAll('.offline-status');
        statusElements.forEach(element => {
            element.textContent = this.isOnline ? 'Online' : 'Offline';
            element.className = `offline-status badge ${this.isOnline ? 'bg-success' : 'bg-warning'}`;
        });

        // Update connection status in header
        const connectionStatus = document.querySelector('.connection-status');
        if (connectionStatus) {
            connectionStatus.innerHTML = this.isOnline ? 
                '<i class="bi bi-wifi"></i> Online' : 
                '<i class="bi bi-wifi-off"></i> Offline';
            connectionStatus.className = `connection-status ${this.isOnline ? 'online' : 'offline'}`;
        }

        // Update sync button
        const syncButton = document.querySelector('.sync-button');
        if (syncButton) {
            syncButton.disabled = !this.isOnline || this.syncInProgress;
            syncButton.innerHTML = this.syncInProgress ? 
                '<i class="bi bi-arrow-repeat spinning"></i> Syncing...' : 
                '<i class="bi bi-arrow-repeat"></i> Sync Now';
        }

        // Update queue size indicator
        const queueSize = document.querySelector('.queue-size');
        if (queueSize) {
            queueSize.textContent = this.offlineQueue.length;
            queueSize.className = `queue-size badge ${this.offlineQueue.length > 0 ? 'bg-warning' : 'bg-secondary'}`;
        }

        // Show/hide offline banner
        const offlineBanner = document.querySelector('.offline-banner');
        if (offlineBanner) {
            offlineBanner.style.display = this.isOnline ? 'none' : 'block';
        }
    }

    /**
     * Update sync status
     */
    updateSyncStatus(message) {
        const syncStatus = document.querySelector('.sync-status');
        if (syncStatus) {
            syncStatus.textContent = message;
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Try to use existing notification system
        if (typeof window.POS !== 'undefined' && window.POS.showAlert) {
            window.POS.showAlert(message, type);
        } else {
            // Fallback notification
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
        }
    }

    /**
     * Storage utilities
     */
    setToStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    }

    getFromStorage(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    }

    removeFromStorage(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    }

    /**
     * Offline queue management
     */
    saveOfflineQueue() {
        this.setToStorage('offline_queue', this.offlineQueue);
    }

    loadOfflineQueue() {
        const queue = this.getFromStorage('offline_queue', []);
        this.offlineQueue = queue.filter(item => {
            // Remove old requests (older than 24 hours)
            const itemTime = new Date(item.timestamp);
            const now = new Date();
            const hoursDiff = (now - itemTime) / (1000 * 60 * 60);
            return hoursDiff < 24;
        });
        this.saveOfflineQueue();
    }

    clearOfflineQueue() {
        this.offlineQueue = [];
        this.saveOfflineQueue();
        this.updateUI();
        this.showNotification('Offline queue cleared', 'success');
    }

    /**
     * Get offline statistics
     */
    getOfflineStats() {
        return {
            isOnline: this.isOnline,
            queueSize: this.offlineQueue.length,
            syncInProgress: this.syncInProgress,
            cachedData: {
                menuItems: (this.getFromStorage('cached_menu_items') || []).length,
                categories: (this.getFromStorage('cached_categories') || []).length,
                tables: (this.getFromStorage('cached_tables') || []).length
            }
        };
    }

    /**
     * Cleanup
     */
    cleanup() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
        }
    }
}

// Create global instance
window.OfflineManager = OfflineManager;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (!window.offlineManager) {
        window.offlineManager = new OfflineManager();
        
        // Load and cache data on initialization
        window.offlineManager.loadAndCacheData();
        
        // Update UI initially
        window.offlineManager.updateUI();
        
        console.log('Offline Manager ready');
    }
});

// Export for global access
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OfflineManager;
}