/**
 * Enhanced Templates Integration JavaScript
 * Integrates all enhanced template features including:
 * - Alert system
 * - Security status
 * - Offline sync
 * - Session management
 * - Validation feedback
 * - Mobile optimization
 * - Accessibility features
 */

// Enhanced Templates Module
const EnhancedTemplates = {
  // Configuration
  config: {
    apiBaseUrl: '/api',
    notificationTimeout: 5000,
    sessionRefreshInterval: 30000, // 30 seconds
    syncCheckInterval: 10000, // 10 seconds
    securityCheckInterval: 30000, // 30 seconds
    autoSaveInterval: 30000, // 30 seconds
    animationDuration: 300,
    debounceDelay: 300,
    mobileBreakpoint: 768,
    tabletBreakpoint: 1024
  },
  
  // State
  state: {
    isOnline: navigator.onLine,
    currentUser: null,
    sessionId: null,
    notifications: [],
    securityLevel: 'unknown',
    syncStatus: 'idle',
    sessionExpiryTime: null,
    activeModals: [],
    formValidation: {},
    autoSaveQueue: [],
    theme: 'light',
    language: 'en'
  },
  
  // Initialize enhanced templates
  init() {
    this.setupEventListeners();
    this.setupNetworkListeners();
    this.setupKeyboardShortcuts();
    this.setupAccessibilityFeatures();
    this.setupMobileOptimizations();
    this.setupThemeSupport();
    this.setupInternationalization();
    this.startBackgroundTasks();
    
    console.log('Enhanced Templates initialized');
  },
  
  // Setup global event listeners
  setupEventListeners() {
    // Custom events for component communication
    document.addEventListener('showNotification', (e) => {
      this.handleNotification(e.detail);
    });
    
    document.addEventListener('showAlert', (e) => {
      this.handleAlert(e.detail);
    });
    
    document.addEventListener('showValidation', (e) => {
      this.handleValidation(e.detail);
    });
    
    document.addEventListener('securityUpdate', (e) => {
      this.handleSecurityUpdate(e.detail);
    });
    
    document.addEventListener('syncUpdate', (e) => {
      this.handleSyncUpdate(e.detail);
    });
    
    document.addEventListener('sessionUpdate', (e) => {
      this.handleSessionUpdate(e.detail);
    });
    
    // Form events
    document.addEventListener('submit', (e) => {
      this.handleFormSubmit(e);
    });
    
    document.addEventListener('input', (e) => {
      this.handleFormInput(e);
    });
    
    document.addEventListener('change', (e) => {
      this.handleFormChange(e);
    });
    
    // Page visibility events
    document.addEventListener('visibilitychange', () => {
      this.handleVisibilityChange();
    });
    
    // Before unload event
    window.addEventListener('beforeunload', (e) => {
      this.handleBeforeUnload(e);
    });
    
    // Error handling
    window.addEventListener('error', (e) => {
      this.handleGlobalError(e);
    });
    
    window.addEventListener('unhandledrejection', (e) => {
      this.handleUnhandledRejection(e);
    });
  },
  
  // Setup network listeners
  setupNetworkListeners() {
    window.addEventListener('online', () => {
      this.state.isOnline = true;
      this.handleNetworkChange(true);
    });
    
    window.addEventListener('offline', () => {
      this.state.isOnline = false;
      this.handleNetworkChange(false);
    });
  },
  
  // Setup keyboard shortcuts
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + K: Quick search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        this.openQuickSearch();
      }
      
      // Ctrl/Cmd + /: Show keyboard shortcuts
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        this.showKeyboardShortcuts();
      }
      
      // Escape: Close modals
      if (e.key === 'Escape') {
        this.closeAllModals();
      }
      
      // Ctrl/Cmd + S: Save (if form is active)
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        this.saveCurrentForm();
      }
      
      // Alt + N: New notification
      if (e.altKey && e.key === 'n') {
        e.preventDefault();
        this.showNotificationPanel();
      }
      
      // Alt + S: Session management
      if (e.altKey && e.key === 's') {
        e.preventDefault();
        this.showSessionPanel();
      }
      
      // Alt + O: Offline sync
      if (e.altKey && e.key === 'o') {
        e.preventDefault();
        this.showSyncPanel();
      }
    });
  },
  
  // Setup accessibility features
  setupAccessibilityFeatures() {
    // Skip to main content link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.className = 'skip-to-main';
    skipLink.textContent = 'Skip to main content';
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // ARIA live regions
    this.createAriaLiveRegion('polite', 'aria-live-polite');
    this.createAriaLiveRegion('assertive', 'aria-live-assertive');
    
    // Focus management
    this.setupFocusManagement();
    
    // Screen reader announcements
    this.setupScreenReaderSupport();
    
    // High contrast mode detection
    this.setupHighContrastDetection();
    
    // Reduced motion detection
    this.setupReducedMotionDetection();
  },
  
  // Setup mobile optimizations
  setupMobileOptimizations() {
    // Touch event handling
    this.setupTouchEvents();
    
    // Viewport handling
    this.setupViewportHandling();
    
    // Responsive navigation
    this.setupResponsiveNavigation();
    
    // Mobile-specific gestures
    this.setupMobileGestures();
    
    // Performance optimizations
    this.setupPerformanceOptimizations();
  },
  
  // Setup theme support
  setupThemeSupport() {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.state.theme = savedTheme;
    this.applyTheme(savedTheme);
    
    // Listen for system theme changes
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      mediaQuery.addListener((e) => {
        if (!localStorage.getItem('theme')) {
          this.applyTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  },
  
  // Setup internationalization
  setupInternationalization() {
    // Detect language
    const browserLang = navigator.language || navigator.userLanguage;
    const savedLang = localStorage.getItem('language') || browserLang.split('-')[0];
    this.state.language = savedLang;
    
    // Load translations
    this.loadTranslations(savedLang);
    
    // Format dates and numbers according to locale
    this.setupLocaleFormatting();
  },
  
  // Start background tasks
  startBackgroundTasks() {
    // Session refresh
    setInterval(() => {
      this.refreshSession();
    }, this.config.sessionRefreshInterval);
    
    // Sync status check
    setInterval(() => {
      this.checkSyncStatus();
    }, this.config.syncCheckInterval);
    
    // Security status check
    setInterval(() => {
      this.checkSecurityStatus();
    }, this.config.securityCheckInterval);
    
    // Auto-save
    setInterval(() => {
      this.autoSave();
    }, this.config.autoSaveInterval);
    
    // Cleanup old notifications
    setInterval(() => {
      this.cleanupNotifications();
    }, 60000); // Every minute
  },
  
  // Handle notifications
  handleNotification(options) {
    const notification = {
      id: this.generateId(),
      type: options.type || 'info',
      title: options.title || 'Notification',
      message: options.message || '',
      timestamp: new Date(),
      autoDismiss: options.autoDismiss !== false,
      duration: options.duration || this.config.notificationTimeout,
      actions: options.actions || [],
      important: options.important || false,
      read: false
    };
    
    this.state.notifications.unshift(notification);
    
    // Show toast notification
    this.showToast(notification);
    
    // Update notification badge
    this.updateNotificationBadge();
    
    // Announce to screen readers
    this.announceToScreenReader(`${notification.title}: ${notification.message}`, 'polite');
    
    // Auto-dismiss if enabled
    if (notification.autoDismiss) {
      setTimeout(() => {
        this.dismissNotification(notification.id);
      }, notification.duration);
    }
  },
  
  // Handle alerts
  handleAlert(options) {
    // Create page-level alert
    const alert = {
      id: this.generateId(),
      type: options.type || 'info',
      title: options.title,
      message: options.message || '',
      allowDismiss: options.allowDismiss !== false,
      actions: options.actions || []
    };
    
    this.showPageAlert(alert);
    
    // Announce to screen readers
    this.announceToScreenReader(`${alert.title}: ${alert.message}`, 'assertive');
  },
  
  // Handle validation
  handleValidation(options) {
    const validation = {
      field: options.field,
      valid: options.valid,
      errors: options.errors || [],
      warnings: options.warnings || []
    };
    
    this.state.formValidation[options.field] = validation;
    
    // Update field UI
    this.updateFieldValidation(validation);
    
    // Show validation feedback
    if (!validation.valid) {
      this.showValidationFeedback(validation);
    }
  },
  
  // Handle security updates
  handleSecurityUpdate(data) {
    this.state.securityLevel = data.security_level || 'unknown';
    
    // Update security indicator
    this.updateSecurityIndicator(data);
    
    // Show security alerts if needed
    if (data.alerts && data.alerts.length > 0) {
      data.alerts.forEach(alert => {
        this.handleNotification({
          type: 'warning',
          title: 'Security Alert',
          message: alert.message,
          important: true
        });
      });
    }
  },
  
  // Handle sync updates
  handleSyncUpdate(data) {
    this.state.syncStatus = data.status || 'idle';
    
    // Update sync indicator
    this.updateSyncIndicator(data);
    
    // Show sync notifications
    if (data.notification) {
      this.handleNotification(data.notification);
    }
  },
  
  // Handle session updates
  handleSessionUpdate(data) {
    this.state.sessionExpiryTime = data.expires_at;
    
    // Update session indicator
    this.updateSessionIndicator(data);
    
    // Show session expiry warnings
    if (data.expiring_soon) {
      this.handleNotification({
        type: 'warning',
        title: 'Session Expiring Soon',
        message: `Your session will expire in ${data.time_remaining}`,
        important: true,
        actions: [
          {
            label: 'Extend Session',
            action: () => this.extendSession()
          }
        ]
      });
    }
  },
  
  // Handle network changes
  handleNetworkChange(isOnline) {
    const message = isOnline ? 
      'Connection restored. You are back online.' : 
      'Connection lost. You are now working offline.';
    
    this.handleNotification({
      type: isOnline ? 'success' : 'warning',
      title: isOnline ? 'Online' : 'Offline',
      message: message,
      important: !isOnline
    });
    
    // Trigger sync if coming back online
    if (isOnline) {
      this.triggerSync();
    }
  },
  
  // Handle form submission
  handleFormSubmit(e) {
    const form = e.target;
    
    // Validate form
    if (!this.validateForm(form)) {
      e.preventDefault();
      return false;
    }
    
    // Show loading state
    this.setFormLoading(form, true);
    
    // Add to auto-save queue
    this.addToAutoSaveQueue(form);
  },
  
  // Handle form input
  handleFormInput(e) {
    const field = e.target;
    
    // Real-time validation
    if (field.dataset.validate) {
      this.validateField(field);
    }
    
    // Auto-save
    if (field.dataset.autoSave) {
      this.debounce(() => {
        this.saveField(field);
      }, this.config.debounceDelay);
    }
  },
  
  // Handle form change
  handleFormChange(e) {
    const field = e.target;
    
    // Update UI state
    this.updateFieldState(field);
  },
  
  // Handle visibility change
  handleVisibilityChange() {
    if (document.hidden) {
      // Page is hidden, pause background tasks
      this.pauseBackgroundTasks();
    } else {
      // Page is visible, resume background tasks
      this.resumeBackgroundTasks();
      
      // Refresh data
      this.refreshData();
    }
  },
  
  // Handle before unload
  handleBeforeUnload(e) {
    // Check for unsaved changes
    if (this.hasUnsavedChanges()) {
      e.preventDefault();
      e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      return e.returnValue;
    }
  },
  
  // Handle global errors
  handleGlobalError(e) {
    console.error('Global error:', e.error);
    
    this.handleNotification({
      type: 'error',
      title: 'Application Error',
      message: 'An unexpected error occurred. Please try again.',
      important: true
    });
  },
  
  // Handle unhandled rejections
  handleUnhandledRejection(e) {
    console.error('Unhandled promise rejection:', e.reason);
    
    this.handleNotification({
      type: 'error',
      title: 'Application Error',
      message: 'An unexpected error occurred. Please try again.',
      important: true
    });
  },
  
  // Utility methods
  generateId() {
    return 'id_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  },
  
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
  },
  
  throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
  
  // Theme methods
  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    this.state.theme = theme;
    localStorage.setItem('theme', theme);
  },
  
  toggleTheme() {
    const newTheme = this.state.theme === 'light' ? 'dark' : 'light';
    this.applyTheme(newTheme);
  },
  
  // Accessibility methods
  createAriaLiveRegion(politeness, id) {
    const region = document.createElement('div');
    region.id = id;
    region.setAttribute('aria-live', politeness);
    region.setAttribute('aria-atomic', 'true');
    region.className = 'sr-only';
    document.body.appendChild(region);
  },
  
  announceToScreenReader(message, politeness = 'polite') {
    const region = document.getElementById(`aria-live-${politeness}`);
    if (region) {
      region.textContent = message;
      setTimeout(() => {
        region.textContent = '';
      }, 1000);
    }
  },
  
  // Mobile optimization methods
  setupTouchEvents() {
    let touchStartX = 0;
    let touchStartY = 0;
    
    document.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    });
    
    document.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      
      const deltaX = touchEndX - touchStartX;
      const deltaY = touchEndY - touchStartY;
      
      // Handle swipe gestures
      if (Math.abs(deltaX) > Math.abs(deltaY)) {
        if (deltaX > 50) {
          this.handleSwipeRight();
        } else if (deltaX < -50) {
          this.handleSwipeLeft();
        }
      }
    });
  },
  
  // API methods
  async apiCall(endpoint, options = {}) {
    const url = `${this.config.apiBaseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      },
      ...options
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  },
  
  // Storage methods
  saveToLocalStorage(key, data) {
    try {
      localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },
  
  loadFromLocalStorage(key) {
    try {
      const data = localStorage.getItem(key);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Failed to load from localStorage:', error);
      return null;
    }
  },
  
  // Validation methods
  validateForm(form) {
    let isValid = true;
    const fields = form.querySelectorAll('[data-validate]');
    
    fields.forEach(field => {
      if (!this.validateField(field)) {
        isValid = false;
      }
    });
    
    return isValid;
  },
  
  validateField(field) {
    const rules = field.dataset.validate.split('|');
    let isValid = true;
    const errors = [];
    
    rules.forEach(rule => {
      const [ruleName, ruleValue] = rule.split(':');
      
      if (!this.validateRule(field.value, ruleName, ruleValue)) {
        isValid = false;
        errors.push(this.getValidationMessage(ruleName, ruleValue));
      }
    });
    
    this.handleValidation({
      field: field.name,
      valid: isValid,
      errors: errors
    });
    
    return isValid;
  },
  
  validateRule(value, rule, ruleValue) {
    switch (rule) {
      case 'required':
        return value.trim() !== '';
      case 'email':
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
      case 'min':
        return value.length >= parseInt(ruleValue);
      case 'max':
        return value.length <= parseInt(ruleValue);
      case 'pattern':
        return new RegExp(ruleValue).test(value);
      default:
        return true;
    }
  },
  
  getValidationMessage(rule, ruleValue) {
    const messages = {
      required: 'This field is required',
      email: 'Please enter a valid email address',
      min: `Minimum length is ${ruleValue} characters`,
      max: `Maximum length is ${ruleValue} characters`,
      pattern: 'Please enter a valid value'
    };
    
    return messages[rule] || 'Invalid value';
  },
  
  // Performance optimization methods
  setupPerformanceOptimizations() {
    // Lazy load images
    this.setupLazyLoading();
    
    // Optimize scroll events
    this.setupOptimizedScroll();
    
    // Reduce animations on low-end devices
    this.setupReducedAnimations();
  },
  
  setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          imageObserver.unobserve(img);
        }
      });
    });
    
    images.forEach(img => imageObserver.observe(img));
  },
  
  setupOptimizedScroll() {
    let ticking = false;
    
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          this.handleScroll();
          ticking = false;
        });
        ticking = true;
      }
    });
  },
  
  // Placeholder methods for features that need implementation
  showToast(notification) {
    // This will be implemented by the alert system component
    console.log('Show toast:', notification);
  },
  
  showPageAlert(alert) {
    // This will be implemented by the alert system component
    console.log('Show page alert:', alert);
  },
  
  showValidationFeedback(validation) {
    // This will be implemented by the validation feedback component
    console.log('Show validation feedback:', validation);
  },
  
  updateSecurityIndicator(data) {
    // This will be implemented by the security status component
    console.log('Update security indicator:', data);
  },
  
  updateSyncIndicator(data) {
    // This will be implemented by the offline sync component
    console.log('Update sync indicator:', data);
  },
  
  updateSessionIndicator(data) {
    // This will be implemented by the session management component
    console.log('Update session indicator:', data);
  },
  
  updateNotificationBadge() {
    // This will be implemented by the notification center component
    console.log('Update notification badge');
  },
  
  updateFieldValidation(validation) {
    // This will update the field UI based on validation
    console.log('Update field validation:', validation);
  },
  
  // Placeholder methods for actions
  openQuickSearch() {
    console.log('Open quick search');
  },
  
  showKeyboardShortcuts() {
    console.log('Show keyboard shortcuts');
  },
  
  closeAllModals() {
    console.log('Close all modals');
  },
  
  saveCurrentForm() {
    console.log('Save current form');
  },
  
  showNotificationPanel() {
    console.log('Show notification panel');
  },
  
  showSessionPanel() {
    console.log('Show session panel');
  },
  
  showSyncPanel() {
    console.log('Show sync panel');
  },
  
  refreshSession() {
    console.log('Refresh session');
  },
  
  checkSyncStatus() {
    console.log('Check sync status');
  },
  
  checkSecurityStatus() {
    console.log('Check security status');
  },
  
  autoSave() {
    console.log('Auto save');
  },
  
  cleanupNotifications() {
    console.log('Cleanup notifications');
  },
  
  dismissNotification(id) {
    this.state.notifications = this.state.notifications.filter(n => n.id !== id);
    this.updateNotificationBadge();
  },
  
  triggerSync() {
    console.log('Trigger sync');
  },
  
  setFormLoading(form, loading) {
    console.log('Set form loading:', loading);
  },
  
  addToAutoSaveQueue(form) {
    console.log('Add to auto-save queue:', form);
  },
  
  saveField(field) {
    console.log('Save field:', field);
  },
  
  updateFieldState(field) {
    console.log('Update field state:', field);
  },
  
  pauseBackgroundTasks() {
    console.log('Pause background tasks');
  },
  
  resumeBackgroundTasks() {
    console.log('Resume background tasks');
  },
  
  refreshData() {
    console.log('Refresh data');
  },
  
  hasUnsavedChanges() {
    console.log('Check for unsaved changes');
    return false;
  },
  
  extendSession() {
    console.log('Extend session');
  },
  
  handleSwipeRight() {
    console.log('Handle swipe right');
  },
  
  handleSwipeLeft() {
    console.log('Handle swipe left');
  },
  
  handleScroll() {
    console.log('Handle scroll');
  },
  
  setupFocusManagement() {
    console.log('Setup focus management');
  },
  
  setupScreenReaderSupport() {
    console.log('Setup screen reader support');
  },
  
  setupHighContrastDetection() {
    console.log('Setup high contrast detection');
  },
  
  setupReducedMotionDetection() {
    console.log('Setup reduced motion detection');
  },
  
  setupViewportHandling() {
    console.log('Setup viewport handling');
  },
  
  setupResponsiveNavigation() {
    console.log('Setup responsive navigation');
  },
  
  setupMobileGestures() {
    console.log('Setup mobile gestures');
  },
  
  setupReducedAnimations() {
    console.log('Setup reduced animations');
  },
  
  loadTranslations(lang) {
    console.log('Load translations for:', lang);
  },
  
  setupLocaleFormatting() {
    console.log('Setup locale formatting');
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  EnhancedTemplates.init();
});

// Export for global access
window.EnhancedTemplates = EnhancedTemplates;