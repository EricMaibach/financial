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

// AI Chat Functionality
const AIChatModule = {
    chatContainer: null,
    chatMessages: null,
    chatInput: null,
    chatButton: null,
    sendButton: null,
    closeButton: null,
    isOpen: false,
    conversationHistory: [],  // Store conversation history
    maxHistoryMessages: 10,   // Keep last 10 messages (5 exchanges)

    init() {
        // Get DOM elements
        this.chatContainer = document.getElementById('ai-chat-container');
        this.chatMessages = document.getElementById('ai-chat-messages');
        this.chatInput = document.getElementById('ai-chat-input');
        this.chatButton = document.getElementById('ai-chat-button');
        this.sendButton = document.getElementById('ai-chat-send');
        this.closeButton = document.getElementById('ai-chat-close');

        if (!this.chatContainer) return;

        // Event listeners
        this.chatButton.addEventListener('click', () => this.toggleChat());
        this.closeButton.addEventListener('click', () => this.closeChat());
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Add welcome message
        this.addWelcomeMessage();
    },

    toggleChat() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.chatContainer.classList.remove('ai-chat-hidden');
            this.chatInput.focus();
        } else {
            this.chatContainer.classList.add('ai-chat-hidden');
        }
    },

    closeChat() {
        this.isOpen = false;
        this.chatContainer.classList.add('ai-chat-hidden');
    },

    addWelcomeMessage() {
        const welcomeMsg = document.createElement('div');
        welcomeMsg.className = 'ai-chat-message';
        welcomeMsg.innerHTML = `
            <div class="ai-chat-message-label">AI Assistant</div>
            <div class="ai-chat-message-ai">
                Hi! I'm your Financial Markets AI Assistant. I have access to real-time market data across equities, credit, safe havens, and economic indicators.
                <br><br>
                Ask me about:
                <ul style="margin: 8px 0 0 0; padding-left: 20px;">
                    <li>Specific metrics (VIX, credit spreads, yield curves, etc.)</li>
                    <li>Market conditions and historical context</li>
                    <li>Correlations between different indicators</li>
                    <li>Economic data and recession indicators</li>
                </ul>
            </div>
        `;
        this.chatMessages.appendChild(welcomeMsg);
    },

    async sendMessage() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        // Disable input while sending
        this.chatInput.disabled = true;
        this.sendButton.disabled = true;

        // Add user message to history
        this.conversationHistory.push({ role: 'user', content: message });

        // Add user message to UI
        this.addMessage('user', message);

        // Clear input
        this.chatInput.value = '';

        // Show loading indicator
        const loadingId = this.addLoadingIndicator();

        try {
            // Send to API with conversation history
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message,
                    history: this.conversationHistory.slice(-this.maxHistoryMessages)
                })
            });

            // Remove loading indicator
            this.removeLoadingIndicator(loadingId);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to get response');
            }

            const data = await response.json();

            // Add AI response to history
            this.conversationHistory.push({ role: 'assistant', content: data.message });

            // Trim history if too long
            if (this.conversationHistory.length > this.maxHistoryMessages) {
                this.conversationHistory = this.conversationHistory.slice(-this.maxHistoryMessages);
            }

            // Add AI response to UI
            this.addMessage('ai', data.message);

        } catch (error) {
            console.error('Chat error:', error);
            this.removeLoadingIndicator(loadingId);
            this.addMessage('ai', `Sorry, I encountered an error: ${error.message}. Please check your API key configuration in Settings.`);
            // Remove the failed user message from history
            this.conversationHistory.pop();
        } finally {
            // Re-enable input
            this.chatInput.disabled = false;
            this.sendButton.disabled = false;
            this.chatInput.focus();
        }
    },

    addMessage(type, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'ai-chat-message';

        const label = type === 'user' ? 'You' : 'AI Assistant';
        const messageClass = type === 'user' ? 'ai-chat-message-user' : 'ai-chat-message-ai';

        msgDiv.innerHTML = `
            <div class="ai-chat-message-label">${label}</div>
            <div class="${messageClass}">${this.formatMessage(text)}</div>
        `;

        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    },

    formatMessage(text) {
        // Use marked library for full markdown rendering
        if (typeof marked !== 'undefined') {
            // Configure marked for safe rendering
            marked.setOptions({
                breaks: true,  // Convert \n to <br>
                gfm: true,     // GitHub Flavored Markdown
                sanitize: false
            });
            return marked.parse(text);
        }
        // Fallback if marked isn't loaded
        let formatted = text
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        return formatted;
    },

    addLoadingIndicator() {
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'ai-chat-message';
        loadingDiv.innerHTML = `
            <div class="ai-chat-message-label">AI Assistant</div>
            <div class="ai-chat-loading">
                <div class="ai-chat-loading-dots">
                    <div class="ai-chat-loading-dot"></div>
                    <div class="ai-chat-loading-dot"></div>
                    <div class="ai-chat-loading-dot"></div>
                </div>
            </div>
        `;

        this.chatMessages.appendChild(loadingDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;

        return loadingId;
    },

    removeLoadingIndicator(loadingId) {
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
};

// Initialize AI chat when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    AIChatModule.init();
});
