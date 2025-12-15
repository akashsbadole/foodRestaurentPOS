/**
 * Loyalty Program JavaScript Module
 * Handles loyalty program functionality, rewards, and points management
 */

class LoyaltyManager {
    constructor() {
        this.program = null;
        this.rewards = [];
        this.tiers = [];
        this.customers = [];
        this.stats = {};
        this.loading = false;
        this.filters = {
            tier: '',
            type: ''
        };
        this.pagination = {
            page: 1,
            pages: 1,
            total: 0,
            has_prev: false,
            has_next: false
        };
        this.selectedReward = null;
        this.redemptionForm = {
            customer_id: '',
            quantity: 1
        };
        this.init();
    }

    init() {
        this.loadProgram();
        this.loadTiers();
        this.loadCustomers();
        this.loadRewards();
        this.loadStats();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Refresh program button
        const refreshBtn = document.getElementById('refreshProgramBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshProgram();
            });
        }

        // Expire points button
        const expireBtn = document.getElementById('expirePointsBtn');
        if (expireBtn) {
            expireBtn.addEventListener('click', () => {
                this.expirePoints();
            });
        }

        // Filter changes
        const tierFilter = document.getElementById('tierFilter');
        if (tierFilter) {
            tierFilter.addEventListener('change', () => {
                this.filters.tier = tierFilter.value;
                this.loadRewards(1);
            });
        }

        const typeFilter = document.getElementById('typeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', () => {
                this.filters.type = typeFilter.value;
                this.loadRewards(1);
            });
        }

        // Modal close buttons
        const modalCloseBtns = document.querySelectorAll('.modal-close');
        modalCloseBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    modal.style.display = 'none';
                }
            });
        });

        // Click outside modal to close
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }

    async loadProgram() {
        try {
            const response = await fetch('/loyalty/program');
            const data = await response.json();
            
            if (data.success) {
                this.program = data.program;
                this.updateProgramDisplay();
            }
        } catch (error) {
            console.error('Error loading program:', error);
            this.showAlert('Failed to load loyalty program', 'error');
        }
    }

    updateProgramDisplay() {
        const programInfo = document.getElementById('programInfo');
        if (!programInfo || !this.program) return;

        programInfo.innerHTML = `
            <div class="program-header">
                <div>
                    <div class="program-name">${this.program.name}</div>
                    <span class="program-status ${this.program.is_valid ? 'status-active' : 'status-inactive'}">
                        ${this.program.is_valid ? 'Active' : 'Inactive'}
                    </span>
                </div>
            </div>
            
            <div class="program-details">
                <div class="detail-item">
                    <div class="detail-label">Points per ₹1</div>
                    <div class="detail-value">${this.program.points_per_rupee}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Min Order Amount</div>
                    <div class="detail-value">₹${this.program.min_order_amount}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Max Points per Order</div>
                    <div class="detail-value">${this.program.max_points_per_order}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Points Validity</div>
                    <div class="detail-value">${this.program.points_expiry_days} days</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Birthday Bonus</div>
                    <div class="detail-value">${this.program.birthday_bonus_points}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Anniversary Bonus</div>
                    <div class="detail-value">${this.program.anniversary_bonus_points}</div>
                </div>
            </div>
        `;
    }

    async loadTiers() {
        try {
            const response = await fetch('/loyalty/tiers');
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

    async loadCustomers() {
        try {
            const response = await fetch('/crm/list?per_page=1000');
            const data = await response.json();
            
            if (data.success) {
                this.customers = data.customers;
            }
        } catch (error) {
            console.error('Error loading customers:', error);
        }
    }

    async loadRewards(page = 1) {
        this.loading = true;
        this.updateLoadingDisplay(true);

        try {
            const params = new URLSearchParams({
                page: page,
                tier: this.filters.tier,
                type: this.filters.type
            });
            
            const response = await fetch(`/loyalty/rewards?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.rewards = data.rewards;
                this.pagination = data.pagination;
                this.updateRewardsGrid();
                this.updatePagination();
            } else {
                this.showAlert(data.message || 'Failed to load rewards', 'error');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'error');
            console.error('Error loading rewards:', error);
        } finally {
            this.loading = false;
            this.updateLoadingDisplay(false);
        }
    }

    updateLoadingDisplay(loading) {
        const loadingElement = document.getElementById('rewardsLoading');
        if (loadingElement) {
            loadingElement.style.display = loading ? 'block' : 'none';
        }

        const gridElement = document.getElementById('rewardsGrid');
        if (gridElement) {
            gridElement.style.display = loading ? 'none' : 'grid';
        }
    }

    updateRewardsGrid() {
        const grid = document.getElementById('rewardsGrid');
        if (!grid) return;

        grid.innerHTML = '';

        if (this.rewards.length === 0) {
            grid.innerHTML = '<div class="no-rewards">No rewards found matching your criteria</div>';
            return;
        }

        this.rewards.forEach(reward => {
            const card = this.createRewardCard(reward);
            grid.appendChild(card);
        });
    }

    createRewardCard(reward) {
        const card = document.createElement('div');
        card.className = 'reward-card';
        
        const imageUrl = reward.image_url || '/static/images/default-reward.png';
        
        card.innerHTML = `
            <div class="reward-image">
                <img src="${imageUrl}" alt="${reward.name}" 
                     style="max-width: 100%; max-height: 100%; object-fit: cover;"
                     onerror="this.src='/static/images/default-reward.png'">
            </div>
            <div class="reward-content">
                <h3 class="reward-name">${reward.name}</h3>
                <p class="reward-description">${reward.description || ''}</p>
                
                <div class="reward-details">
                    <div class="points-required">
                        <i class="bi bi-star-fill"></i> ${reward.points_required} points
                    </div>
                    <div class="reward-value">${reward.formatted_reward_value || ''}</div>
                </div>
                
                <div class="reward-terms" style="display: ${reward.terms_conditions ? 'block' : 'none'}">
                    ${reward.terms_conditions || ''}
                </div>
                
                <div class="reward-actions">
                    <button class="btn btn-primary reward-redeem-btn" 
                            data-reward-id="${reward.id}"
                            data-points-required="${reward.points_required}">
                        <i class="bi bi-gift"></i> Redeem
                    </button>
                    <button class="btn btn-secondary reward-details-btn" 
                            data-reward-id="${reward.id}">
                        <i class="bi bi-eye"></i> Details
                    </button>
                </div>
            </div>
        `;

        // Add event listeners
        const redeemBtn = card.querySelector('.reward-redeem-btn');
        if (redeemBtn) {
            redeemBtn.addEventListener('click', () => {
                this.selectReward(reward);
            });
        }

        const detailsBtn = card.querySelector('.reward-details-btn');
        if (detailsBtn) {
            detailsBtn.addEventListener('click', () => {
                this.viewRewardDetails(reward);
            });
        }

        return card;
    }

    updatePagination() {
        const paginationContainer = document.getElementById('rewardsPagination');
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
        button.onclick = () => this.loadRewards(page);
        return button;
    }

    async loadStats() {
        try {
            const response = await fetch('/loyalty/stats');
            const data = await response.json();
            
            if (data.success) {
                this.stats = data.stats;
                this.updateStatsDisplay();
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateStatsDisplay() {
        const elements = {
            totalCustomers: document.getElementById('totalCustomers'),
            customersWithPoints: document.getElementById('customersWithPoints'),
            totalPointsEarned: document.getElementById('totalPointsEarned'),
            totalPointsRedeemed: document.getElementById('totalPointsRedeemed')
        };

        if (this.stats.customer_stats) {
            if (elements.totalCustomers) {
                elements.totalCustomers.textContent = this.stats.customer_stats.total_customers;
            }
            if (elements.customersWithPoints) {
                elements.customersWithPoints.textContent = this.stats.customer_stats.customers_with_points;
            }
        }

        if (this.stats.points_stats) {
            if (elements.totalPointsEarned) {
                elements.totalPointsEarned.textContent = this.stats.points_stats.total_points_earned;
            }
            if (elements.totalPointsRedeemed) {
                elements.totalPointsRedeemed.textContent = this.stats.points_stats.total_points_redeemed;
            }
        }
    }

    refreshProgram() {
        this.loadProgram();
        this.loadStats();
    }

    async expirePoints() {
        if (!confirm('Are you sure you want to expire all expired points?')) {
            return;
        }
        
        try {
            const response = await fetch('/loyalty/points/expire', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message, 'success');
                setTimeout(() => {
                    this.loadStats();
                }, 3000);
            } else {
                this.showAlert(data.message || 'Failed to expire points', 'error');
            }
        } catch (error) {
            this.showAlert('Network error occurred', 'error');
            console.error('Error expiring points:', error);
        }
    }

    canAffordReward(reward) {
        const customer = this.customers.find(c => c.id == this.redemptionForm.customer_id);
        return customer && customer.current_points >= (reward.points_required * this.redemptionForm.quantity);
    }

    selectReward(reward) {
        this.selectedReward = reward;
        this.redemptionForm = {
            customer_id: '',
            quantity: 1
        };
        this.showRedemptionModal();
    }

    viewRewardDetails(reward) {
        const details = `
Reward Details:

Name: ${reward.name}
Description: ${reward.description || 'No description available'}
Points Required: ${reward.points_required}
Value: ${reward.formatted_reward_value || 'N/A'}
${reward.terms_conditions ? `Terms: ${reward.terms_conditions}` : ''}
        `.trim();
        
        alert(details);
    }

    showRedemptionModal() {
        const modal = document.getElementById('redemptionModal');
        if (!modal || !this.selectedReward) return;

        // Update modal content
        const rewardInfo = modal.querySelector('.reward-info');
        if (rewardInfo) {
            rewardInfo.innerHTML = `
                <h3>${this.selectedReward.name}</h3>
                <p>${this.selectedReward.description || ''}</p>
                <div class="points-required-display">
                    <strong>Points Required:</strong> ${this.selectedReward.points_required}
                </div>
            `;
        }

        // Update customer select
        const customerSelect = modal.querySelector('#customerSelect');
        if (customerSelect) {
            customerSelect.innerHTML = '<option value="">Select Customer</option>';
            this.customers.forEach(customer => {
                const option = document.createElement('option');
                option.value = customer.id;
                option.textContent = `${customer.name} (${customer.mobile}) - ${customer.current_points} points`;
                customerSelect.appendChild(option);
            });
        }

        // Reset form
        this.redemptionForm = {
            customer_id: '',
            quantity: 1
        };

        const quantityInput = modal.querySelector('#quantityInput');
        if (quantityInput) {
            quantityInput.value = 1;
        }

        // Clear messages
        this.clearModalMessages();

        modal.style.display = 'block';
    }

    async redeemReward() {
        if (!this.selectedReward || !this.redemptionForm.customer_id) {
            this.showModalMessage('Please select a customer', 'error');
            return;
        }

        const customer = this.customers.find(c => c.id == this.redemptionForm.customer_id);
        if (!customer || customer.current_points < (this.selectedReward.points_required * this.redemptionForm.quantity)) {
            this.showModalMessage('Insufficient points', 'error');
            return;
        }

        this.setRedeemButtonState(true);

        try {
            const response = await fetch(`/loyalty/rewards/${this.selectedReward.id}/redeem`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(this.redemptionForm)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showModalMessage(data.message, 'success');
                setTimeout(() => {
                    this.closeRedemptionModal();
                    this.loadCustomers();
                    this.loadStats();
                }, 2000);
            } else {
                this.showModalMessage(data.message || 'Failed to redeem reward', 'error');
            }
        } catch (error) {
            this.showModalMessage('Network error occurred', 'error');
            console.error('Error redeeming reward:', error);
        } finally {
            this.setRedeemButtonState(false);
        }
    }

    setRedeemButtonState(processing) {
        const redeemBtn = document.querySelector('#redeemRewardBtn');
        if (redeemBtn) {
            redeemBtn.disabled = processing;
            redeemBtn.innerHTML = processing ? 
                '<span class="spinner"></span> Processing...' : 
                'Redeem Reward';
        }
    }

    showModalMessage(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        const modal = document.getElementById('redemptionModal');
        if (modal) {
            const modalContent = modal.querySelector('.modal-content');
            if (modalContent) {
                modalContent.insertBefore(alertDiv, modalContent.firstChild);
                
                // Auto-remove after 5 seconds
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, 5000);
            }
        }
    }

    clearModalMessages() {
        const alerts = document.querySelectorAll('#redemptionModal .alert');
        alerts.forEach(alert => alert.remove());
    }

    closeRedemptionModal() {
        const modal = document.getElementById('redemptionModal');
        if (modal) {
            modal.style.display = 'none';
            this.selectedReward = null;
            this.clearModalMessages();
        }
    }

    getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        const container = document.querySelector('.loyalty-container');
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

// Initialize Loyalty Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.loyalty-container')) {
        window.loyaltyManager = new LoyaltyManager();
    }
});

// Export for use in other modules
window.LoyaltyManager = LoyaltyManager;