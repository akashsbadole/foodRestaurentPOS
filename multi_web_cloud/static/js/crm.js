/**
 * CRM JavaScript Module
 * Handles customer management functionality
 */

class CRMManager {
    constructor() {
        this.customers = [];
        this.tiers = [];
        this.stats = {};
        this.loading = false;
        this.filters = {
            search: '',
            tier: '',
            status: ''
        };
        this.pagination = {
            page: 1,
            pages: 1,
            total: 0,
            has_prev: false,
            has_next: false
        };
        this.init();
    }

    init() {
        this.loadStats();
        this.loadTiers();
        this.loadCustomers();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Search debounce
        const searchInput = document.getElementById('customerSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(() => {
                this.filters.search = searchInput.value;
                this.loadCustomers(1);
            }, 500));
        }

        // Filter changes
        const tierFilter = document.getElementById('tierFilter');
        if (tierFilter) {
            tierFilter.addEventListener('change', () => {
                this.filters.tier = tierFilter.value;
                this.loadCustomers(1);
            });
        }

        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => {
                this.filters.status = statusFilter.value;
                this.loadCustomers(1);
            });
        }

        // Reset filters
        const resetBtn = document.getElementById('resetFilters');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetFilters();
            });
        }

        // Add customer modal
        const addCustomerBtn = document.getElementById('addCustomerBtn');
        if (addCustomerBtn) {
            addCustomerBtn.addEventListener('click', () => {
                this.showCreateModal();
            });
        }

        // Export customers
        const exportBtn = document.getElementById('exportCustomersBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportCustomers();
            });
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async loadStats() {
        try {
            const response = await fetch('/crm/stats');
            const data = await response.json();
            
            if (data.success) {
                this.stats = data.stats;
                this.updateStatsDisplay();
            }
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showAlert('Failed to load statistics', 'error');
        }
    }

    updateStatsDisplay() {
        const elements = {
            totalCustomers: document.getElementById('totalCustomers'),
            activeCustomers: document.getElementById('activeCustomers'),
            totalPointsEarned: document.getElementById('totalPointsEarned'),
            currentPointsTotal: document.getElementById('currentPointsTotal')
        };

        Object.keys(elements).forEach(key => {
            if (elements[key] && this.stats[key]) {
                elements[key].textContent = this.stats[key];
            }
        });
    }

    async loadTiers() {
        try {
            const response = await fetch('/crm/tiers');
            const data = await response.json();
            
            if (data.success) {
                this.tiers = data.tiers;
                this.updateTierFilter();
            }
        } catch (error) {
            console.error('Error loading tiers:', error);
        }
    }

    updateTierFilter() {
        const tierFilter = document.getElementById('tierFilter');
        if (tierFilter) {
            // Clear existing options except first one
            while (tierFilter.children.length > 1) {
                tierFilter.removeChild(tierFilter.lastChild);
            }

            // Add tier options
            this.tiers.forEach(tier => {
                const option = document.createElement('option');
                option.value = tier.id;
                option.textContent = tier.name;
                tierFilter.appendChild(option);
            });
        }
    }

    async loadCustomers(page = 1) {
        this.loading = true;
        this.updateLoadingDisplay(true);

        try {
            const params = new URLSearchParams({
                page: page,
                search: this.filters.search,
                tier: this.filters.tier,
                status: this.filters.status
            });
            
            const response = await fetch(`/crm/list?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.customers = data.customers;
                this.pagination = data.pagination;
                this.updateCustomersTable();
                this.updatePagination();
            } else {
                this.showAlert(data.message || 'Failed to load customers', 'error');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'error');
            console.error('Error loading customers:', error);
        } finally {
            this.loading = false;
            this.updateLoadingDisplay(false);
        }
    }

    updateLoadingDisplay(loading) {
        const loadingElement = document.getElementById('customersLoading');
        if (loadingElement) {
            loadingElement.style.display = loading ? 'block' : 'none';
        }

        const tableElement = document.getElementById('customersTable');
        if (tableElement) {
            tableElement.style.display = loading ? 'none' : 'block';
        }
    }

    updateCustomersTable() {
        const tbody = document.querySelector('#customersTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (this.customers.length === 0) {
            const row = tbody.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 8;
            cell.className = 'text-center';
            cell.textContent = 'No customers found';
            return;
        }

        this.customers.forEach(customer => {
            const row = tbody.insertRow();
            
            // Name
            row.insertCell().textContent = customer.name || '-';
            
            // Mobile
            row.insertCell().textContent = customer.mobile || '-';
            
            // Email
            row.insertCell().textContent = customer.email || '-';
            
            // Tier
            const tierCell = row.insertCell();
            if (customer.loyalty_tier_name) {
                const badge = document.createElement('span');
                badge.className = 'tier-badge';
                badge.style.backgroundColor = customer.loyalty_tier_color || '#ccc';
                badge.textContent = customer.loyalty_tier_name;
                tierCell.appendChild(badge);
            } else {
                tierCell.textContent = 'No Tier';
            }
            
            // Points
            const pointsCell = row.insertCell();
            pointsCell.className = 'points-display';
            pointsCell.textContent = customer.current_points || 0;
            
            // Total Spent
            row.insertCell().textContent = `₹${(customer.total_spent || 0).toFixed(2)}`;
            
            // Orders
            row.insertCell().textContent = customer.total_orders || 0;
            
            // Actions
            const actionsCell = row.insertCell();
            
            const viewBtn = document.createElement('button');
            viewBtn.className = 'btn btn-sm btn-primary';
            viewBtn.innerHTML = '<i class="bi bi-eye"></i> View';
            viewBtn.onclick = () => this.viewCustomer(customer.id);
            
            const editBtn = document.createElement('button');
            editBtn.className = 'btn btn-sm btn-secondary';
            editBtn.innerHTML = '<i class="bi bi-pencil"></i> Edit';
            editBtn.onclick = () => this.editCustomer(customer.id);
            
            actionsCell.appendChild(viewBtn);
            actionsCell.appendChild(editBtn);
        });
    }

    updatePagination() {
        const paginationContainer = document.getElementById('customersPagination');
        if (!paginationContainer) return;

        paginationContainer.innerHTML = '';

        if (this.pagination.pages <= 1) return;

        // Previous button
        if (this.pagination.has_prev) {
            const prevBtn = this.createPaginationButton('‹', this.pagination.page - 1);
            paginationContainer.appendChild(prevBtn);
        }

        // Page numbers
        for (let i = 1; i <= this.pagination.pages; i++) {
            const pageBtn = this.createPaginationButton(i, i, i === this.pagination.page);
            paginationContainer.appendChild(pageBtn);
        }

        // Next button
        if (this.pagination.has_next) {
            const nextBtn = this.createPaginationButton('›', this.pagination.page + 1);
            paginationContainer.appendChild(nextBtn);
        }
    }

    createPaginationButton(text, page, isActive = false) {
        const button = document.createElement('button');
        button.className = `page-btn ${isActive ? 'active' : ''}`;
        button.textContent = text;
        button.onclick = () => this.loadCustomers(page);
        return button;
    }

    resetFilters() {
        this.filters = {
            search: '',
            tier: '',
            status: ''
        };

        // Reset form inputs
        const searchInput = document.getElementById('customerSearch');
        if (searchInput) searchInput.value = '';

        const tierFilter = document.getElementById('tierFilter');
        if (tierFilter) tierFilter.value = '';

        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) statusFilter.value = '';

        this.loadCustomers(1);
    }

    showCreateModal() {
        const modal = document.getElementById('customerModal');
        if (modal) {
            this.resetCustomerForm();
            modal.style.display = 'block';
        }
    }

    resetCustomerForm() {
        const form = document.getElementById('customerForm');
        if (form) {
            form.reset();
            // Clear any validation messages
            this.clearValidationMessages();
        }
    }

    clearValidationMessages() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => alert.remove());
    }

    viewCustomer(customerId) {
        window.location.href = `/crm/customers/${customerId}`;
    }

    editCustomer(customerId) {
        window.location.href = `/crm/customers/${customerId}/edit`;
    }

    async exportCustomers() {
        try {
            const params = new URLSearchParams({
                search: this.filters.search,
                tier: this.filters.tier,
                status: this.filters.status
            });
            
            const response = await fetch(`/crm/export?${params}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `customers_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } else {
                this.showAlert('Failed to export customers', 'error');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'error');
            console.error('Error exporting customers:', error);
        }
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        const container = document.querySelector('.crm-container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.parentNode.removeChild(alertDiv);
                }
            }, 5000);
        }
    }
}

// Initialize CRM when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.crm-container')) {
        window.crmManager = new CRMManager();
    }
});

// Export for use in other modules
window.CRMManager = CRMManager;