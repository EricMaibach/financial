/**
 * Chatbot Widget
 * Feature 3.2: Chatbot Mobile-First Redesign
 * US-3.2.1: Core Widget Structure & Interaction
 *
 * Implements the two-state (minimized / expanded) chatbot widget
 * using a bottom sheet pattern on mobile (< 768px).
 *
 * Message sending/AI integration is added in US-3.2.2.
 * Conversation persistence and badges are added in US-3.2.3.
 * Tablet/desktop layouts are added in US-3.2.4.
 */

class ChatbotWidget {
    constructor() {
        this.fab = document.getElementById('chatbot-fab');
        this.panel = document.getElementById('chatbot-panel');
        this.minimizeBtn = document.querySelector('.chatbot-minimize');
        this.closeBtn = document.querySelector('.chatbot-close');
        this.clearBtn = document.querySelector('.chatbot-clear-link');
        this.form = document.querySelector('.chatbot-input-form');
        this.input = document.getElementById('chatbot-input');
        this.messages = document.querySelector('.chatbot-messages');
        this.badge = document.querySelector('.chatbot-badge');
        this.performanceBanner = document.querySelector('.chatbot-performance-banner');
        this.performanceDismiss = document.querySelector('.chatbot-performance-dismiss');

        this.isOpen = false;
        this.isAnimating = false;
        this.conversation = [];
        this.messageCount = 0;
        this.performanceBannerDismissed = false;
        this.lastUserMessage = null;

        if (!this.fab || !this.panel) {
            console.warn('ChatbotWidget: Required elements not found in DOM');
            return;
        }

        this.init();
    }

    init() {
        // Core toggle events
        this.fab.addEventListener('click', () => this.toggle());
        this.minimizeBtn.addEventListener('click', () => this.close());
        this.closeBtn.addEventListener('click', () => this.close()); // X minimizes per PM decision

        // Clear conversation
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearConversation());
        }

        // Message form
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.sendMessage(e));
        }

        // Enter key sends message; Shift+Enter creates newline
        if (this.input) {
            this.input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.form.dispatchEvent(new Event('submit'));
                }
            });
        }

        // Performance banner dismiss
        if (this.performanceDismiss) {
            this.performanceDismiss.addEventListener('click', () => this.dismissPerformanceBanner());
        }

        // Keyboard shortcut: Escape minimizes panel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Restore conversation state from sessionStorage
        this.restoreConversation();
        this.performanceBannerDismissed = sessionStorage.getItem('chatbot-perf-dismissed') === 'true';
    }

    toggle() {
        if (this.isAnimating) return;
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        this.isOpen = true;

        this.panel.setAttribute('aria-hidden', 'false');
        this.fab.setAttribute('aria-expanded', 'true');

        this.clearBadge();

        // Focus input after animation completes
        setTimeout(() => {
            this.isAnimating = false;
            if (this.input) {
                this.input.focus();
            }
        }, 250);

        // Announce to screen readers
        this.announce('AI Chatbot opened');
    }

    close() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        this.isOpen = false;

        this.panel.setAttribute('aria-hidden', 'true');
        this.fab.setAttribute('aria-expanded', 'false');

        // Return focus to FAB after animation
        setTimeout(() => {
            this.isAnimating = false;
            this.fab.focus();
        }, 250);

        // Announce to screen readers
        this.announce('AI Chatbot minimized');
    }

    async sendMessage(e) {
        e.preventDefault();

        const message = this.input.value.trim();
        if (!message) return;

        // Add user message immediately (optimistic UI)
        this.addMessage('user', message);
        this.conversation.push({ role: 'user', content: message });
        this.messageCount++;
        this.lastUserMessage = message;
        this.input.value = '';

        // Show clear link once messages exist
        if (this.clearBtn) {
            this.clearBtn.classList.add('visible');
        }

        // Check for performance banner at 30 messages
        if (this.messageCount === 30 && !this.performanceBannerDismissed) {
            this.showPerformanceBanner();
        }

        // Show typing indicator
        this.showTypingIndicator();

        // Disable submit while waiting
        if (this.form.querySelector('.chatbot-submit')) {
            this.form.querySelector('.chatbot-submit').disabled = true;
        }

        try {
            const response = await this.fetchAIResponse(message);
            this.hideTypingIndicator();
            this.addMessage('ai', response);
            this.conversation.push({ role: 'ai', content: response });

            // If minimized, show badge
            if (!this.isOpen) {
                this.showBadge();
            }

            this.saveConversation();

        } catch (error) {
            this.hideTypingIndicator();
            if (error.message === 'AI_UNAVAILABLE') {
                this.showError('AI Temporarily Unavailable. Please try again later.', false, '🤖');
            } else {
                // Network errors (fetch threw) or other server errors — show retry option
                this.showError('Connection Error. Could not reach the AI. Check your internet connection.', true, '⚠️');
            }
        } finally {
            if (this.form.querySelector('.chatbot-submit')) {
                this.form.querySelector('.chatbot-submit').disabled = false;
            }
        }
    }

    async fetchAIResponse(message) {
        const response = await fetch('/api/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify({
                message,
                conversation: this.conversation,
                context: {
                    page: window.location.pathname
                }
            })
        });

        if (response.status === 503) throw new Error('AI_UNAVAILABLE');
        if (!response.ok) throw new Error('AI_REQUEST_FAILED');

        const data = await response.json();
        return data.response;
    }

    addMessage(role, text) {
        // Hide empty state once messages appear
        const emptyState = this.messages.querySelector('.chatbot-empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }

        const messageEl = document.createElement('div');
        messageEl.className = `chatbot-message chatbot-message--${role}`;

        if (role === 'ai') {
            messageEl.innerHTML = `
                <span class="chatbot-message-icon" aria-hidden="true">🤖</span>
                <span class="chatbot-message-label sr-only">AI said:</span>
                <p class="chatbot-message-text">${this.escapeHTML(text)}</p>
            `;
        } else {
            messageEl.innerHTML = `
                <span class="chatbot-message-label sr-only">You said:</span>
                <p class="chatbot-message-text">${this.escapeHTML(text)}</p>
            `;
        }

        this.messages.appendChild(messageEl);
        this.scrollToBottom();

        // Announce AI messages via live region (the role="log" on .chatbot-messages handles this)
        if (role === 'ai') {
            this.announce(`AI says: ${text}`);
        }
    }

    showTypingIndicator() {
        const existing = this.messages.querySelector('.chatbot-typing');
        if (existing) return;

        const indicator = document.createElement('div');
        indicator.className = 'chatbot-typing';
        indicator.setAttribute('aria-label', 'AI is typing');
        indicator.innerHTML = `
            <span class="chatbot-typing-dot"></span>
            <span class="chatbot-typing-dot"></span>
            <span class="chatbot-typing-dot"></span>
        `;
        this.messages.appendChild(indicator);
        this.scrollToBottom();
        this.announce('AI is typing');
    }

    hideTypingIndicator() {
        const indicator = this.messages.querySelector('.chatbot-typing');
        if (indicator) {
            indicator.remove();
        }
    }

    showBadge() {
        if (this.badge) {
            this.badge.textContent = '1';
            this.badge.setAttribute('aria-label', '1 new message');
        }
    }

    clearBadge() {
        if (this.badge) {
            this.badge.textContent = '';
            this.badge.removeAttribute('aria-label');
        }
    }

    scrollToBottom() {
        this.messages.scrollTop = this.messages.scrollHeight;
    }

    showError(errorMessage, canRetry = false, icon = '⚠️') {
        const errorEl = document.createElement('div');
        errorEl.className = 'chatbot-message chatbot-message--error';
        errorEl.innerHTML = `
            <span aria-hidden="true">${icon}</span>
            <div>
                <p style="margin:0">${this.escapeHTML(errorMessage)}</p>
                ${canRetry ? '<button class="chatbot-retry-btn">Try Again</button>' : ''}
            </div>
        `;

        if (canRetry) {
            const retryBtn = errorEl.querySelector('.chatbot-retry-btn');
            retryBtn.addEventListener('click', () => {
                errorEl.remove();
                this.retryLastMessage();
            });
        }

        this.messages.appendChild(errorEl);
        this.scrollToBottom();
        this.announce(`Error: ${errorMessage}`, 'assertive');
    }

    async retryLastMessage() {
        if (!this.lastUserMessage) return;

        // Remove last user message from conversation history (will be re-added on send)
        const lastIdx = this.conversation.findLastIndex(m => m.role === 'user' && m.content === this.lastUserMessage);
        if (lastIdx !== -1) {
            this.conversation.splice(lastIdx, 1);
            this.messageCount--;
        }

        // Put message back in input and submit
        this.input.value = this.lastUserMessage;
        this.form.dispatchEvent(new Event('submit'));
    }

    showPerformanceBanner() {
        if (this.performanceBanner) {
            this.performanceBanner.removeAttribute('hidden');
            this.announce('Long conversation may affect performance', 'polite');
        }
    }

    dismissPerformanceBanner() {
        if (this.performanceBanner) {
            this.performanceBanner.setAttribute('hidden', '');
        }
        this.performanceBannerDismissed = true;
        sessionStorage.setItem('chatbot-perf-dismissed', 'true');
    }

    clearConversation() {
        const confirmed = confirm('Clear conversation? This will delete your chat history.');
        if (!confirmed) return;

        this.conversation = [];
        this.messageCount = 0;

        // Reset message area UI
        this.messages.innerHTML = `
            <button class="chatbot-clear-link" aria-label="Clear conversation">
                Clear conversation
            </button>
            <div class="chatbot-empty-state">
                <p class="chatbot-empty-text">Hello! How can I help you understand the markets today?</p>
            </div>
        `;

        // Reset performance banner
        if (this.performanceBanner) {
            this.performanceBanner.setAttribute('hidden', '');
        }
        this.performanceBannerDismissed = false;
        sessionStorage.removeItem('chatbot-perf-dismissed');

        // Re-attach event listener to rebuilt clear button
        this.clearBtn = this.messages.querySelector('.chatbot-clear-link');
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.clearConversation());
        }

        this.saveConversation();
        this.close();
        this.announce('Conversation cleared');
    }

    saveConversation() {
        const state = {
            conversation: this.conversation,
            messageCount: this.messageCount
        };
        sessionStorage.setItem('chatbot-conversation', JSON.stringify(state));
    }

    restoreConversation() {
        const saved = sessionStorage.getItem('chatbot-conversation');
        if (!saved) return;

        try {
            const state = JSON.parse(saved);
            this.conversation = state.conversation || [];
            this.messageCount = state.messageCount || 0;

            this.conversation.forEach(msg => {
                this.addMessage(msg.role, msg.content);
            });

            if (this.messageCount >= 30 && !this.performanceBannerDismissed) {
                this.showPerformanceBanner();
            }

            // Show clear link if conversation exists
            if (this.conversation.length > 0 && this.clearBtn) {
                this.clearBtn.classList.add('visible');
            }
        } catch (e) {
            console.warn('ChatbotWidget: Could not restore conversation from sessionStorage', e);
        }
    }

    announce(message, priority = 'polite') {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', priority);
        announcement.className = 'sr-only';
        announcement.textContent = message;
        document.body.appendChild(announcement);

        setTimeout(() => announcement.remove(), 1000);
    }

    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatbotWidget();
});
