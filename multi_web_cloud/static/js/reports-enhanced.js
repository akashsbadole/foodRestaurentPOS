/**
 * Enhanced Reports JavaScript
 * Handles advanced reporting features with real-time data, charts, and exports
 */

// Enhanced Reports Module
const EnhancedReports = {
  // Chart instances
  charts: {},
  
  // Report configuration
  config: {
    autoRefresh: false,
    refreshInterval: 300000, // 5 minutes
    defaultDateRange: 7, // days
    chartColors: {
      primary: 'rgba(102, 126, 234, 0.8)',
      secondary: 'rgba(118, 75, 162, 0.8)',
      success: 'rgba(40, 167, 69, 0.8)',
      warning: 'rgba(255, 193, 7, 0.8)',
      danger: 'rgba(220, 53, 69, 0.8)',
      info: 'rgba(23, 162, 184, 0.8)'
    }
  },
  
  // Initialize the enhanced reports
  init() {
    this.setupEventListeners();
    this.initializeCharts();
    this.setupAutoRefresh();
    this.setupKeyboardShortcuts();
    this.setupPrintStyles();
    
    console.log('Enhanced Reports initialized');
  },
  
  // Setup event listeners
  setupEventListeners() {
    // Report type change
    document.addEventListener('change', (e) => {
      if (e.target.matches('[data-report-type]')) {
        this.handleReportTypeChange(e.target.value);
      }
    });
    
    // Date range change
    document.addEventListener('change', (e) => {
      if (e.target.matches('[data-date-range]')) {
        this.handleDateRangeChange(e.target);
      }
    });
    
    // Filter change
    document.addEventListener('change', (e) => {
      if (e.target.matches('[data-filter]')) {
        this.handleFilterChange(e.target);
      }
    });
    
    // Export button click
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-export]')) {
        e.preventDefault();
        this.handleExport(e.target.dataset.export);
      }
    });
    
    // Chart export button
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-chart-export]')) {
        e.preventDefault();
        this.exportChart(e.target.dataset.chartExport);
      }
    });
    
    // Print button
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-print-report]')) {
        e.preventDefault();
        this.printReport();
      }
    });
    
    // Real-time toggle
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-realtime-toggle]')) {
        e.preventDefault();
        this.toggleRealtime();
      }
    });
    
    // Save configuration
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-save-config]')) {
        e.preventDefault();
        this.saveConfiguration();
      }
    });
    
    // Schedule report
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-schedule-report]')) {
        e.preventDefault();
        this.openScheduleModal();
      }
    });
    
    // Email report
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-email-report]')) {
        e.preventDefault();
        this.emailReport();
      }
    });
    
    // Reset filters
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-reset-filters]')) {
        e.preventDefault();
        this.resetFilters();
      }
    });
    
    // Chart type toggle
    document.addEventListener('click', (e) => {
      if (e.target.matches('[data-toggle-chart-type]')) {
        e.preventDefault();
        this.toggleChartType(e.target.dataset.toggleChartType);
      }
    });
    
    // Online/Offline status
    window.addEventListener('online', () => {
      this.handleOnlineStatusChange(true);
    });
    
    window.addEventListener('offline', () => {
      this.handleOnlineStatusChange(false);
    });
  },
  
  // Initialize charts
  initializeCharts() {
    // Daily Orders Chart
    this.initDailyOrdersChart();
    
    // Categories Chart
    this.initCategoriesChart();
    
    // Payment Methods Chart
    this.initPaymentMethodsChart();
    
    // Monthly Sales Chart
    this.initMonthlySalesChart();
    
    // GST Charts
    this.initGSTCharts();
  },
  
  // Initialize Daily Orders Chart
  initDailyOrdersChart() {
    const ctx = document.getElementById('dailyOrdersChart');
    if (!ctx) return;
    
    this.charts.dailyOrders = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: [],
        datasets: [{
          label: 'Orders',
          data: [],
          backgroundColor: this.config.chartColors.primary,
          borderColor: this.config.chartColors.primary.replace('0.8', '1'),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                return `Orders: ${context.parsed.y}`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0
            }
          }
        }
      }
    });
  },
  
  // Initialize Categories Chart
  initCategoriesChart() {
    const ctx = document.getElementById('categoriesChart');
    if (!ctx) return;
    
    this.charts.categories = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: [
            this.config.chartColors.primary,
            this.config.chartColors.secondary,
            this.config.chartColors.success,
            this.config.chartColors.warning,
            this.config.chartColors.danger,
            this.config.chartColors.info
          ],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'right'
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || '';
                const value = this.formatCurrency(context.parsed);
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.parsed / total) * 100).toFixed(1);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  },
  
  // Initialize Payment Methods Chart
  initPaymentMethodsChart() {
    const ctx = document.getElementById('paymentMethodsChart');
    if (!ctx) return;
    
    this.charts.paymentMethods = new Chart(ctx, {
      type: 'pie',
      data: {
        labels: [],
        datasets: [{
          data: [],
          backgroundColor: [
            this.config.chartColors.primary,
            this.config.chartColors.secondary,
            this.config.chartColors.success,
            this.config.chartColors.warning,
            this.config.chartColors.danger
          ],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'bottom'
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || '';
                const value = this.formatCurrency(context.parsed);
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((context.parsed / total) * 100).toFixed(1);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  },
  
  // Initialize Monthly Sales Chart
  initMonthlySalesChart() {
    const ctx = document.getElementById('monthlySalesChart');
    if (!ctx) return;
    
    this.charts.monthlySales = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Sales',
          data: [],
          borderColor: this.config.chartColors.primary.replace('0.8', '1'),
          backgroundColor: this.config.chartColors.primary.replace('0.8', '0.1'),
          borderWidth: 2,
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                return `Sales: ${this.formatCurrency(context.parsed.y)}`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) => {
                return this.formatCurrency(value);
              }
            }
          }
        }
      }
    });
  },
  
  // Initialize GST Charts
  initGSTCharts() {
    // CGST Chart
    const cgstCtx = document.getElementById('cgstChart');
    if (cgstCtx) {
      this.charts.cgst = new Chart(cgstCtx, {
        type: 'bar',
        data: {
          labels: [],
          datasets: [{
            label: 'CGST',
            data: [],
            backgroundColor: this.config.chartColors.success,
            borderColor: this.config.chartColors.success.replace('0.8', '1'),
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  return `CGST: ${this.formatCurrency(context.parsed.y)}`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => {
                  return this.formatCurrency(value);
                }
              }
            }
          }
        }
      });
    }
    
    // SGST Chart
    const sgstCtx = document.getElementById('sgstChart');
    if (sgstCtx) {
      this.charts.sgst = new Chart(sgstCtx, {
        type: 'bar',
        data: {
          labels: [],
          datasets: [{
            label: 'SGST',
            data: [],
            backgroundColor: this.config.chartColors.info,
            borderColor: this.config.chartColors.info.replace('0.8', '1'),
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  return `SGST: ${this.formatCurrency(context.parsed.y)}`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: {
                callback: (value) => {
                  return this.formatCurrency(value);
                }
              }
            }
          }
        }
      });
    }
  },
  
  // Handle report type change
  handleReportTypeChange(reportType) {
    // Update chart visibility
    this.updateChartVisibility(reportType);
    
    // Load appropriate data
    this.loadReportData(reportType);
    
    // Update UI
    this.updateReportTypeUI(reportType);
  },
  
  // Handle date range change
  handleDateRangeChange(element) {
    const dateRange = element.value;
    
    if (dateRange === 'custom') {
      // Show custom date pickers
      this.showCustomDatePickers();
    } else {
      // Set dates based on preset
      this.setDateRangeFromPreset(dateRange);
    }
    
    // Reload data
    this.loadReportData();
  },
  
  // Handle filter change
  handleFilterChange(element) {
    // Debounce filter changes
    clearTimeout(this.filterTimeout);
    this.filterTimeout = setTimeout(() => {
      this.loadReportData();
    }, 500);
  },
  
  // Load report data
  async loadReportData(reportType = null) {
    try {
      // Show loading state
      this.showLoadingState();
      
      // Get current filters
      const filters = this.getCurrentFilters(reportType);
      
      // Make API request
      const response = await fetch('/api/reports/data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(filters)
      });
      
      if (!response.ok) {
        throw new Error('Failed to load report data');
      }
      
      const data = await response.json();
      
      // Update charts
      this.updateCharts(data);
      
      // Update stats
      this.updateStats(data.stats);
      
      // Update table
      this.updateTable(data.tableData);
      
      // Update last refreshed time
      this.updateLastRefreshed();
      
    } catch (error) {
      console.error('Error loading report data:', error);
      this.showError('Failed to load report data');
    } finally {
      // Hide loading state
      this.hideLoadingState();
    }
  },
  
  // Update charts with new data
  updateCharts(data) {
    // Update Daily Orders Chart
    if (this.charts.dailyOrders && data.dailyOrders) {
      this.charts.dailyOrders.data.labels = data.dailyOrders.map(item => item.label);
      this.charts.dailyOrders.data.datasets[0].data = data.dailyOrders.map(item => item.value);
      this.charts.dailyOrders.update();
    }
    
    // Update Categories Chart
    if (this.charts.categories && data.categories) {
      this.charts.categories.data.labels = data.categories.map(item => item.label);
      this.charts.categories.data.datasets[0].data = data.categories.map(item => item.value);
      this.charts.categories.update();
    }
    
    // Update Payment Methods Chart
    if (this.charts.paymentMethods && data.paymentMethods) {
      this.charts.paymentMethods.data.labels = data.paymentMethods.map(item => item.label);
      this.charts.paymentMethods.data.datasets[0].data = data.paymentMethods.map(item => item.value);
      this.charts.paymentMethods.update();
    }
    
    // Update Monthly Sales Chart
    if (this.charts.monthlySales && data.monthlySales) {
      this.charts.monthlySales.data.labels = data.monthlySales.map(item => item.label);
      this.charts.monthlySales.data.datasets[0].data = data.monthlySales.map(item => item.value);
      this.charts.monthlySales.update();
    }
    
    // Update GST Charts
    if (this.charts.cgst && data.cgstBreakdown) {
      this.charts.cgst.data.labels = data.cgstBreakdown.map(item => item.label);
      this.charts.cgst.data.datasets[0].data = data.cgstBreakdown.map(item => item.value);
      this.charts.cgst.update();
    }
    
    if (this.charts.sgst && data.sgstBreakdown) {
      this.charts.sgst.data.labels = data.sgstBreakdown.map(item => item.label);
      this.charts.sgst.data.datasets[0].data = data.sgstBreakdown.map(item => item.value);
      this.charts.sgst.update();
    }
  },
  
  // Update stats
  updateStats(stats) {
    if (!stats) return;
    
    // Update stat cards
    const statElements = {
      totalSales: document.querySelector('[data-stat="totalSales"]'),
      totalOrders: document.querySelector('[data-stat="totalOrders"]'),
      cancelledOrders: document.querySelector('[data-stat="cancelledOrders"]'),
      averageOrderValue: document.querySelector('[data-stat="averageOrderValue"]')
    };
    
    Object.keys(statElements).forEach(key => {
      if (statElements[key] && stats[key] !== undefined) {
        if (key.includes('Sales') || key.includes('Value')) {
          statElements[key].textContent = this.formatCurrency(stats[key]);
        } else {
          statElements[key].textContent = stats[key];
        }
      }
    });
  },
  
  // Update table
  updateTable(tableData) {
    if (!tableData) return;
    
    const tableBody = document.querySelector('[data-table-body]');
    if (!tableBody) return;
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Add new rows
    tableData.forEach(row => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${row.date}</td>
        <td>${row.orders}</td>
        <td>${this.formatCurrency(row.grossSales)}</td>
        <td>${this.formatCurrency(row.discount)}</td>
        <td>${this.formatCurrency(row.netSales)}</td>
        <td>${this.formatCurrency(row.cgst)}</td>
        <td>${this.formatCurrency(row.sgst)}</td>
        <td>${this.formatCurrency(row.total)}</td>
      `;
      tableBody.appendChild(tr);
    });
  },
  
  // Handle export
  async handleExport(format) {
    try {
      const filters = this.getCurrentFilters();
      
      const response = await fetch('/api/reports/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...filters,
          format: format
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to export report');
      }
      
      // Get filename from response headers or create one
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `report_${new Date().toISOString().slice(0, 10)}.${format}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      // Show success message
      this.showSuccess(`Report exported as ${format.toUpperCase()}`);
      
    } catch (error) {
      console.error('Error exporting report:', error);
      this.showError('Failed to export report');
    }
  },
  
  // Export specific chart
  exportChart(chartId) {
    const chart = this.charts[chartId];
    if (!chart) return;
    
    // Create download link
    const url = chart.toBase64Image();
    const link = document.createElement('a');
    link.download = `${chartId}_${new Date().toISOString().slice(0, 10)}.png`;
    link.href = url;
    link.click();
  },
  
  // Print report
  printReport() {
    // Add print class to body
    document.body.classList.add('printing');
    
    // Trigger print dialog
    window.print();
    
    // Remove print class after print dialog closes
    setTimeout(() => {
      document.body.classList.remove('printing');
    }, 1000);
  },
  
  // Toggle real-time updates
  toggleRealtime() {
    this.config.autoRefresh = !this.config.autoRefresh;
    
    const toggleBtn = document.querySelector('[data-realtime-toggle]');
    if (toggleBtn) {
      toggleBtn.classList.toggle('active', this.config.autoRefresh);
      toggleBtn.innerHTML = this.config.autoRefresh ? 
        '<i class="bi bi-pause"></i> Pause' : 
        '<i class="bi bi-play"></i> Real-time';
    }
    
    if (this.config.autoRefresh) {
      this.startAutoRefresh();
      this.showSuccess('Real-time updates enabled');
    } else {
      this.stopAutoRefresh();
      this.showInfo('Real-time updates disabled');
    }
  },
  
  // Setup auto refresh
  setupAutoRefresh() {
    this.refreshTimer = null;
  },
  
  // Start auto refresh
  startAutoRefresh() {
    this.stopAutoRefresh(); // Clear any existing timer
    
    this.refreshTimer = setInterval(() => {
      this.loadReportData();
    }, this.config.refreshInterval);
  },
  
  // Stop auto refresh
  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  },
  
  // Save configuration
  async saveConfiguration() {
    try {
      const config = this.getCurrentFilters();
      
      const response = await fetch('/api/reports/save-config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save configuration');
      }
      
      this.showSuccess('Report configuration saved');
      
    } catch (error) {
      console.error('Error saving configuration:', error);
      this.showError('Failed to save configuration');
    }
  },
  
  // Email report
  async emailReport() {
    try {
      const filters = this.getCurrentFilters();
      
      const response = await fetch('/api/reports/email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(filters)
      });
      
      if (!response.ok) {
        throw new Error('Failed to email report');
      }
      
      this.showSuccess('Report emailed successfully');
      
    } catch (error) {
      console.error('Error emailing report:', error);
      this.showError('Failed to email report');
    }
  },
  
  // Open schedule modal
  openScheduleModal() {
    // This would open a modal for scheduling reports
    // For now, just show an info message
    this.showInfo('Schedule report feature coming soon');
  },
  
  // Reset filters
  resetFilters() {
    // Reset form elements
    const form = document.querySelector('[data-reports-form]');
    if (form) {
      form.reset();
    }
    
    // Reset to default values
    const reportTypeSelect = document.querySelector('[data-report-type]');
    if (reportTypeSelect) {
      reportTypeSelect.value = 'dashboard';
    }
    
    // Set default date range
    this.setDateRangeFromPreset(this.config.defaultDateRange);
    
    // Reload data
    this.loadReportData();
    
    this.showInfo('Filters reset to default values');
  },
  
  // Toggle chart type
  toggleChartType(chartId) {
    const chart = this.charts[chartId];
    if (!chart) return;
    
    // Toggle between bar and line chart
    const currentType = chart.config.type;
    const newType = currentType === 'bar' ? 'line' : 'bar';
    
    // Update chart type
    chart.config.type = newType;
    chart.update();
    
    // Update button icon
    const toggleBtn = document.querySelector(`[data-toggle-chart-type="${chartId}"]`);
    if (toggleBtn) {
      toggleBtn.innerHTML = newType === 'bar' ? 
        '<i class="bi bi-bar-chart"></i>' : 
        '<i class="bi bi-graph-up"></i>';
    }
  },
  
  // Handle online status change
  handleOnlineStatusChange(isOnline) {
    const statusElement = document.querySelector('[data-connection-status]');
    if (statusElement) {
      statusElement.textContent = isOnline ? 'Online' : 'Offline';
      statusElement.className = isOnline ? 'status-online' : 'status-offline';
    }
    
    if (isOnline) {
      this.showSuccess('Connection restored');
      // Sync any pending data
      this.syncPendingData();
    } else {
      this.showWarning('Connection lost - Working offline');
    }
  },
  
  // Sync pending data
  async syncPendingData() {
    try {
      const response = await fetch('/api/reports/sync-pending', {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.synced > 0) {
          this.showSuccess(`${result.synced} items synced`);
          this.loadReportData(); // Refresh data
        }
      }
    } catch (error) {
      console.error('Error syncing pending data:', error);
    }
  },
  
  // Setup keyboard shortcuts
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + P: Print
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        this.printReport();
      }
      
      // Ctrl/Cmd + E: Export
      if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
        e.preventDefault();
        this.handleExport('pdf');
      }
      
      // Ctrl/Cmd + R: Refresh
      if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        this.loadReportData();
      }
      
      // F5: Refresh
      if (e.key === 'F5') {
        e.preventDefault();
        this.loadReportData();
      }
    });
  },
  
  // Setup print styles
  setupPrintStyles() {
    const style = document.createElement('style');
    style.textContent = `
      @media print {
        body.printing .no-print {
          display: none !important;
        }
        
        body.printing .reports-chart-container {
          page-break-inside: avoid;
        }
        
        body.printing .reports-data-table {
          page-break-inside: avoid;
        }
      }
    `;
    document.head.appendChild(style);
  },
  
  // Utility methods
  getCurrentFilters(reportType = null) {
    const filters = {};
    
    // Get report type
    const reportTypeSelect = document.querySelector('[data-report-type]');
    if (reportTypeSelect) {
      filters.reportType = reportType || reportTypeSelect.value;
    }
    
    // Get date range
    const fromDateInput = document.querySelector('[data-from-date]');
    const toDateInput = document.querySelector('[data-to-date]');
    
    if (fromDateInput) filters.fromDate = fromDateInput.value;
    if (toDateInput) filters.toDate = toDateInput.value;
    
    // Get other filters
    const comparisonSelect = document.querySelector('[data-comparison]');
    if (comparisonSelect) filters.comparison = comparisonSelect.value;
    
    const categorySelect = document.querySelector('[data-category]');
    if (categorySelect) filters.category = categorySelect.value;
    
    const paymentMethodSelect = document.querySelector('[data-payment-method]');
    if (paymentMethodSelect) filters.paymentMethod = paymentMethodSelect.value;
    
    return filters;
  },
  
  setDateRangeFromPreset(days) {
    const toDate = new Date();
    const fromDate = new Date();
    fromDate.setDate(toDate.getDate() - days);
    
    const fromDateInput = document.querySelector('[data-from-date]');
    const toDateInput = document.querySelector('[data-to-date]');
    
    if (fromDateInput) fromDateInput.value = fromDate.toISOString().split('T')[0];
    if (toDateInput) toDateInput.value = toDate.toISOString().split('T')[0];
  },
  
  showCustomDatePickers() {
    // This would show custom date picker UI
    // For now, just focus on the from date input
    const fromDateInput = document.querySelector('[data-from-date]');
    if (fromDateInput) fromDateInput.focus();
  },
  
  updateChartVisibility(reportType) {
    // Show/hide charts based on report type
    const chartContainers = {
      dailyOrdersChart: document.querySelector('[data-chart="dailyOrders"]'),
      categoriesChart: document.querySelector('[data-chart="categories"]'),
      paymentMethodsChart: document.querySelector('[data-chart="paymentMethods"]'),
      monthlySalesChart: document.querySelector('[data-chart="monthlySales"]'),
      gstCharts: document.querySelector('[data-chart="gst"]')
    };
    
    // Hide all charts first
    Object.values(chartContainers).forEach(container => {
      if (container) container.style.display = 'none';
    });
    
    // Show relevant charts based on report type
    switch (reportType) {
      case 'dashboard':
        if (chartContainers.dailyOrdersChart) chartContainers.dailyOrdersChart.style.display = 'block';
        if (chartContainers.categoriesChart) chartContainers.categoriesChart.style.display = 'block';
        if (chartContainers.paymentMethodsChart) chartContainers.paymentMethodsChart.style.display = 'block';
        break;
      case 'daily':
      case 'weekly':
      case 'monthly':
        if (chartContainers.dailyOrdersChart) chartContainers.dailyOrdersChart.style.display = 'block';
        if (chartContainers.monthlySalesChart) chartContainers.monthlySalesChart.style.display = 'block';
        break;
      case 'gstr1':
      case 'gstr3b':
        if (chartContainers.gstCharts) chartContainers.gstCharts.style.display = 'block';
        break;
      case 'categorywise':
        if (chartContainers.categoriesChart) chartContainers.categoriesChart.style.display = 'block';
        break;
      case 'paymentwise':
        if (chartContainers.paymentMethodsChart) chartContainers.paymentMethodsChart.style.display = 'block';
        break;
    }
  },
  
  updateReportTypeUI(reportType) {
    // Update UI elements based on report type
    const reportTitle = document.querySelector('[data-report-title]');
    if (reportTitle) {
      const titles = {
        dashboard: 'Dashboard Overview',
        daily: 'Daily Sales Report',
        weekly: 'Weekly Sales Report',
        monthly: 'Monthly Sales Report',
        quarterly: 'Quarterly Sales Report',
        yearly: 'Yearly Sales Report',
        gstr1: 'GSTR-1 Report',
        gstr3b: 'GSTR-3B Report',
        itemwise: 'Item-wise Sales Report',
        categorywise: 'Category-wise Sales Report',
        customerwise: 'Customer-wise Sales Report',
        paymentwise: 'Payment Method Analysis',
        staffwise: 'Staff Performance Report'
      };
      
      reportTitle.textContent = titles[reportType] || 'Report';
    }
  },
  
  updateLastRefreshed() {
    const lastUpdatedElement = document.querySelector('[data-last-updated]');
    if (lastUpdatedElement) {
      lastUpdatedElement.textContent = new Date().toLocaleString();
    }
  },
  
  showLoadingState() {
    const loadingElement = document.querySelector('[data-loading]');
    if (loadingElement) loadingElement.style.display = 'flex';
    
    const contentElement = document.querySelector('[data-content]');
    if (contentElement) contentElement.style.display = 'none';
  },
  
  hideLoadingState() {
    const loadingElement = document.querySelector('[data-loading]');
    if (loadingElement) loadingElement.style.display = 'none';
    
    const contentElement = document.querySelector('[data-content]');
    if (contentElement) contentElement.style.display = 'block';
  },
  
  formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR'
    }).format(amount || 0);
  },
  
  showSuccess(message) {
    this.showNotification(message, 'success');
  },
  
  showError(message) {
    this.showNotification(message, 'error');
  },
  
  showWarning(message) {
    this.showNotification(message, 'warning');
  },
  
  showInfo(message) {
    this.showNotification(message, 'info');
  },
  
  showNotification(message, type = 'info') {
    // Dispatch event for global notification system
    document.dispatchEvent(new CustomEvent('showNotification', {
      detail: { message, type }
    }));
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  EnhancedReports.init();
});

// Export for global access
window.EnhancedReports = EnhancedReports;