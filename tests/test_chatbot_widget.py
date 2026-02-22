"""
Chatbot Widget Integration Tests
Feature 3.2: Chatbot Mobile-First Redesign
US-3.2.1: Core Widget Structure (Mobile)

Verifies the chatbot widget HTML structure, ARIA attributes,
and design system compliance in the rendered page.

Requires the application to be running at http://localhost:5000.
Run with: python3 -m pytest tests/test_chatbot_widget.py -v
"""

import pytest
import requests

BASE_URL = "http://localhost:5000"


@pytest.fixture(scope="module")
def page():
    """Fetch and cache the rendered home page HTML."""
    try:
        response = requests.get(BASE_URL + "/", timeout=5)
        response.raise_for_status()
        return response.text
    except requests.ConnectionError:
        pytest.skip("Application not running at http://localhost:5000")


# ---------------------------------------------------------------------------
# FAB (Floating Action Button)
# ---------------------------------------------------------------------------

class TestChatbotFAB:
    def test_fab_button_present(self, page):
        assert 'id="chatbot-fab"' in page

    def test_fab_aria_label(self, page):
        assert 'aria-label="Open AI chatbot"' in page

    def test_fab_aria_expanded_false_initially(self, page):
        assert 'aria-expanded="false"' in page

    def test_fab_has_robot_icon(self, page):
        assert 'bi-robot' in page

    def test_fab_badge_present(self, page):
        assert 'chatbot-badge' in page


# ---------------------------------------------------------------------------
# Panel (Expanded State)
# ---------------------------------------------------------------------------

class TestChatbotPanel:
    def test_panel_aside_element(self, page):
        assert '<aside' in page

    def test_panel_id_present(self, page):
        assert 'id="chatbot-panel"' in page

    def test_panel_role_complementary(self, page):
        assert 'role="complementary"' in page

    def test_panel_aria_hidden_true_initially(self, page):
        assert 'aria-hidden="true"' in page

    def test_panel_aria_labelledby(self, page):
        assert 'aria-labelledby="chatbot-title"' in page

    def test_panel_header_element(self, page):
        assert '<header class="chatbot-header"' in page

    def test_panel_title_text(self, page):
        assert '>AI Chatbot<' in page

    def test_panel_title_id(self, page):
        assert 'id="chatbot-title"' in page


# ---------------------------------------------------------------------------
# Panel Controls
# ---------------------------------------------------------------------------

class TestChatbotControls:
    def test_minimize_button_present(self, page):
        assert 'class="chatbot-minimize"' in page

    def test_minimize_button_aria_label(self, page):
        assert 'aria-label="Minimize chatbot"' in page

    def test_close_button_present(self, page):
        assert 'class="chatbot-close"' in page

    def test_close_button_aria_label(self, page):
        assert 'aria-label="Close chatbot"' in page

    def test_minimize_has_aria_controls(self, page):
        assert 'aria-controls="chatbot-panel"' in page


# ---------------------------------------------------------------------------
# Message Area
# ---------------------------------------------------------------------------

class TestChatbotMessages:
    def test_messages_role_log(self, page):
        assert 'role="log"' in page

    def test_messages_aria_live_polite(self, page):
        assert 'aria-live="polite"' in page

    def test_messages_aria_atomic_false(self, page):
        assert 'aria-atomic="false"' in page

    def test_messages_aria_label(self, page):
        assert 'aria-label="Chat messages"' in page

    def test_empty_state_present(self, page):
        assert 'chatbot-empty-state' in page

    def test_empty_state_text(self, page):
        assert 'markets today' in page

    def test_clear_link_present(self, page):
        assert 'chatbot-clear-link' in page


# ---------------------------------------------------------------------------
# Input Form
# ---------------------------------------------------------------------------

class TestChatbotInput:
    def test_form_present(self, page):
        assert 'class="chatbot-input-form"' in page

    def test_form_aria_label(self, page):
        assert 'aria-label="Send message to AI"' in page

    def test_input_label_for_attribute(self, page):
        assert 'for="chatbot-input"' in page

    def test_input_id(self, page):
        assert 'id="chatbot-input"' in page

    def test_input_aria_describedby(self, page):
        assert 'aria-describedby="chatbot-input-hint"' in page

    def test_submit_button_aria_label(self, page):
        assert 'aria-label="Send message"' in page

    def test_submit_type_submit(self, page):
        assert 'type="submit"' in page


# ---------------------------------------------------------------------------
# Performance Banner
# ---------------------------------------------------------------------------

class TestChatbotPerformanceBanner:
    def test_performance_banner_present(self, page):
        assert 'chatbot-performance-banner' in page

    def test_performance_banner_hidden_initially(self, page):
        assert 'chatbot-performance-banner" role="status" aria-live="polite" hidden' in page

    def test_performance_dismiss_button(self, page):
        assert 'chatbot-performance-dismiss' in page

    def test_performance_dismiss_aria_label(self, page):
        assert 'aria-label="Dismiss performance notice"' in page


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

class TestChatbotAssets:
    def test_chatbot_css_linked(self, page):
        assert 'css/components/chatbot.css' in page

    def test_chatbot_js_linked(self, page):
        assert 'js/components/chatbot.js' in page


# ---------------------------------------------------------------------------
# Old Chatbot Removed
# ---------------------------------------------------------------------------

class TestOldChatbotRemoved:
    def test_no_ai_chat_module_in_page(self, page):
        """Verify old AIChatModule CSS classes not present."""
        assert 'ai-chat-container' not in page
        assert 'ai-chat-panel' not in page

    def test_new_chatbot_class_present(self, page):
        """New chatbot CSS classes are present."""
        assert 'chatbot-fab' in page
        assert 'chatbot-panel' in page
