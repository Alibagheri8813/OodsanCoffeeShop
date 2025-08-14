/**
 * Order Status Manager - Dynamic Status Updates for Coffee Shop
 * Handles real-time status transitions with sensational UI effects
 */

class OrderStatusManager {
    constructor() {
        this.baseUrl = '/api/orders/';
        this.csrfToken = this.getCSRFToken();
        this.initializeEventListeners();
    }

    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    initializeEventListeners() {
        // Status transition buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('status-transition-btn')) {
                e.preventDefault();
                const orderId = e.target.dataset.orderId;
                const newStatus = e.target.dataset.status;
                this.transitionStatus(orderId, newStatus);
            }
        });

        // Auto-refresh status every 30 seconds for active orders
        this.startAutoRefresh();
    }

    async transitionStatus(orderId, newStatus) {
        try {
            const response = await fetch(`${this.baseUrl}${orderId}/transition/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify({ status: newStatus })
            });

            const data = await response.json();

            if (data.success) {
                this.updateStatusBadge(orderId, data);
                this.showSuccessMessage(data.message);
                this.triggerStatusAnimation(orderId, newStatus);
            } else {
                this.showErrorMessage(data.error);
            }
        } catch (error) {
            console.error('Error transitioning status:', error);
            this.showErrorMessage('خطا در تغییر وضعیت سفارش');
        }
    }

    async getOrderStatus(orderId) {
        try {
            const response = await fetch(`${this.baseUrl}${orderId}/status/`);
            const data = await response.json();
            
            if (data.success) {
                this.updateStatusBadge(orderId, data);
                return data;
            }
        } catch (error) {
            console.error('Error fetching status:', error);
        }
        return null;
    }

    updateStatusBadge(orderId, statusData) {
        const statusBadges = document.querySelectorAll(`[data-order-id="${orderId}"] .coffee-status-badge`);
        
        statusBadges.forEach(badge => {
            // Remove old status classes
            badge.className = badge.className.replace(/status-\w+/g, '');
            
            // Add new status class
            badge.classList.add(`status-${statusData.status}`);
            badge.textContent = statusData.status_display;
            badge.title = statusData.status_display;
            
            // Update color if available
            if (statusData.status_color) {
                badge.style.setProperty('--status-color', statusData.status_color);
            }
        });
    }

    triggerStatusAnimation(orderId, status) {
        const badges = document.querySelectorAll(`[data-order-id="${orderId}"] .coffee-status-badge`);
        
        badges.forEach(badge => {
            // Add celebration animation
            badge.classList.add('status-updated');
            
            // Create floating success indicator
            this.createFloatingIndicator(badge, status);
            
            // Remove animation class after animation completes
            setTimeout(() => {
                badge.classList.remove('status-updated');
            }, 1000);
        });
    }

    createFloatingIndicator(element, status) {
        const indicator = document.createElement('div');
        indicator.className = 'floating-status-indicator';
        
        const icons = {
            'pending_payment': '💳',
            'preparing': '👨‍🍳',
            'ready_shipping_preparation': '✅',
            'in_transit': '🚛',
            'pickup_ready': '🏪'
        };
        
        indicator.textContent = icons[status] || '✨';
        indicator.style.cssText = `
            position: absolute;
            font-size: 24px;
            pointer-events: none;
            z-index: 1000;
            animation: floatUp 2s ease-out forwards;
        `;
        
        const rect = element.getBoundingClientRect();
        indicator.style.left = (rect.left + rect.width / 2 - 12) + 'px';
        indicator.style.top = (rect.top - 10) + 'px';
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.remove();
        }, 2000);
    }

    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    showErrorMessage(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        // Remove existing toasts
        const existingToasts = document.querySelectorAll('.status-toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `status-toast status-toast-${type}`;
        toast.textContent = message;
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : '#dc3545'};
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    startAutoRefresh() {
        // Only refresh for active orders (not completed states)
        const activeStatuses = ['pending_payment', 'preparing', 'ready_shipping_preparation', 'in_transit'];
        
        setInterval(() => {
            const orderElements = document.querySelectorAll('[data-order-id]');
            
            orderElements.forEach(async (element) => {
                const orderId = element.dataset.orderId;
                const currentBadge = element.querySelector('.coffee-status-badge');
                
                if (currentBadge) {
                    const currentStatus = Array.from(currentBadge.classList)
                        .find(cls => cls.startsWith('status-'))
                        ?.replace('status-', '');
                    
                    if (activeStatuses.includes(currentStatus)) {
                        await this.getOrderStatus(orderId);
                    }
                }
            });
        }, 30000); // Refresh every 30 seconds
    }

    // Quick action methods for staff
    async markAsPaid(orderId) {
        return this.makeStatusRequest(orderId, 'mark-paid');
    }

    async markAsReady(orderId) {
        return this.makeStatusRequest(orderId, 'mark-ready');
    }

    async startShipping(orderId) {
        return this.makeStatusRequest(orderId, 'start-shipping');
    }

    async markInTransit(orderId) {
        return this.makeStatusRequest(orderId, 'mark-transit');
    }

    async markDelivered(orderId) {
        return this.makeStatusRequest(orderId, 'mark-delivered');
    }

    async pollOrder(orderId, onUpdate, intervalMs = 1000) {
        let stopped = false;
        const tick = async () => {
            if (stopped) return;
            const data = await this.getOrderStatus(orderId);
            if (data && onUpdate) onUpdate(data);
            if (!stopped) setTimeout(tick, intervalMs);
        };
        tick();
        return () => { stopped = true; };
    }

    async makeStatusRequest(orderId, action) {
        try {
            const response = await fetch(`${this.baseUrl}${orderId}/${action}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                }
            });

            const data = await response.json();

            if (data.success) {
                this.updateStatusBadge(orderId, data);
                this.showSuccessMessage(data.message);
                this.triggerStatusAnimation(orderId, data.status);
                return true;
            } else {
                this.showErrorMessage(data.error);
                return false;
            }
        } catch (error) {
            console.error(`Error in ${action}:`, error);
            this.showErrorMessage('خطا در تغییر وضعیت سفارش');
            return false;
        }
    }
}

// CSS Animations for dynamic effects
const dynamicStyles = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }

    @keyframes floatUp {
        0% { transform: translateY(0) scale(1); opacity: 1; }
        100% { transform: translateY(-50px) scale(1.5); opacity: 0; }
    }

    .status-updated {
        animation: statusUpdatePulse 1s ease-out !important;
    }

    @keyframes statusUpdatePulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); box-shadow: 0 8px 30px rgba(0,0,0,0.4); }
        100% { transform: scale(1); }
    }

    .status-transition-btn {
        background: linear-gradient(135deg, #8B4513, #A0522D);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 4px;
    }

    .status-transition-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(139, 69, 19, 0.4);
    }

    .status-transition-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = dynamicStyles;
document.head.appendChild(styleSheet);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.orderStatusManager = new OrderStatusManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OrderStatusManager;
}