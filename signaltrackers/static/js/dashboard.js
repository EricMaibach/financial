// Market Divergence Dashboard - Main JavaScript

// Global chart instances
let charts = {};

// Utility function to format numbers
function formatNumber(num, decimals = 0) {
    return num.toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// Utility function to format currency
function formatCurrency(num, decimals = 0) {
    return '$' + formatNumber(num, decimals);
}

// Utility function to format percentage
function formatPercentage(num, decimals = 1) {
    const sign = num >= 0 ? '+' : '';
    return sign + num.toFixed(decimals) + '%';
}

// Load chart with error handling
async function loadChart(chartId, endpoint, chartConfig) {
    try {
        const response = await fetch(`/api/chart/${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        const ctx = document.getElementById(chartId);
        if (!ctx) {
            console.error(`Canvas element not found: ${chartId}`);
            return;
        }

        // Destroy existing chart if it exists
        if (charts[chartId]) {
            charts[chartId].destroy();
        }

        // Create chart with provided config and data
        charts[chartId] = new Chart(ctx, chartConfig(data));

    } catch (error) {
        console.error(`Error loading chart ${chartId}:`, error);
    }
}

// Common chart options
const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    interaction: {
        mode: 'index',
        intersect: false,
    },
    plugins: {
        legend: {
            display: true,
            position: 'top'
        }
    }
};

// Initialize tooltips and popovers
function initializeBootstrap() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-refresh functionality
function setupAutoRefresh(refreshInterval = 60000) {
    setInterval(() => {
        const event = new CustomEvent('refresh-dashboard');
        document.dispatchEvent(event);
    }, refreshInterval);
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    initializeBootstrap();
    setupAutoRefresh();
    updateLastUpdatedTime();
});

// Update last updated time
async function updateLastUpdatedTime() {
    try {
        const response = await fetch('/api/reload-status');
        const status = await response.json();

        const updateTimeElement = document.getElementById('update-time');
        if (updateTimeElement && status.last_reload) {
            updateTimeElement.textContent = status.last_reload;
        } else if (updateTimeElement) {
            updateTimeElement.textContent = 'Never';
        }
    } catch (error) {
        console.error('Error fetching last updated time:', error);
    }
}

// Export for use in templates
window.DashboardUtils = {
    formatNumber,
    formatCurrency,
    formatPercentage,
    loadChart,
    commonChartOptions
};

