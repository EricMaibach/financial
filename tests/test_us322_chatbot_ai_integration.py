"""
Static verification tests for US-3.2.2: Message Interaction and AI Integration.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required code patterns are present.
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'dashboard.py')
CHATBOT_JS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'js', 'components', 'chatbot.js')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


class TestChatbotAPIEndpoint(unittest.TestCase):
    """Verify the /api/chatbot backend endpoint exists in dashboard.py."""

    def setUp(self):
        self.dashboard = read_file(DASHBOARD_PATH)

    def test_api_chatbot_route_defined(self):
        """POST /api/chatbot route must be defined."""
        self.assertIn("@app.route('/api/chatbot', methods=['POST'])", self.dashboard)

    def test_api_chatbot_uses_login_required(self):
        """Chatbot endpoint must require authentication."""
        # Find the block around the /api/chatbot route
        idx = self.dashboard.find("@app.route('/api/chatbot', methods=['POST'])")
        self.assertGreater(idx, 0)
        nearby = self.dashboard[idx:idx + 200]
        self.assertIn('@login_required', nearby)

    def test_api_chatbot_is_csrf_exempt(self):
        """Chatbot API endpoint must be CSRF exempt (uses login_required for auth)."""
        idx = self.dashboard.find("@app.route('/api/chatbot', methods=['POST'])")
        nearby = self.dashboard[idx:idx + 200]
        self.assertIn('@csrf.exempt', nearby)

    def test_api_chatbot_uses_user_ai_client(self):
        """Chatbot endpoint must use get_user_ai_client() (user pays for chatbot)."""
        self.assertIn('get_user_ai_client()', self.dashboard)

    def test_api_chatbot_handles_anthropic(self):
        """Chatbot endpoint must handle Anthropic provider."""
        idx = self.dashboard.find('def api_chatbot')
        self.assertGreater(idx, 0)
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn("provider == 'anthropic'", func_body)
        self.assertIn('client.messages.create', func_body)

    def test_api_chatbot_handles_openai(self):
        """Chatbot endpoint must handle OpenAI provider."""
        idx = self.dashboard.find('def api_chatbot')
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn('client.chat.completions.create', func_body)

    def test_api_chatbot_returns_response_key(self):
        """Chatbot response JSON must include 'response' key."""
        idx = self.dashboard.find('def api_chatbot')
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn("'response': ai_response", func_body)

    def test_api_chatbot_returns_503_on_ai_error(self):
        """Chatbot endpoint must return 503 when AI call fails."""
        idx = self.dashboard.find('def api_chatbot')
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn('503', func_body)

    def test_api_chatbot_returns_400_on_auth_error(self):
        """Chatbot endpoint must return 400 when user has no API key configured."""
        idx = self.dashboard.find('def api_chatbot')
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn('AIServiceError', func_body)
        self.assertIn('400', func_body)

    def test_api_chatbot_accepts_conversation_history(self):
        """Chatbot endpoint must accept and use conversation_history from request."""
        idx = self.dashboard.find('def api_chatbot')
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn("conversation_history = data.get('conversation'", func_body)

    def test_api_chatbot_accepts_page_context(self):
        """Chatbot endpoint must accept page context for context-aware responses."""
        idx = self.dashboard.find('def api_chatbot')
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn("context.get('page'", func_body)

    def test_api_chatbot_has_system_prompt(self):
        """Chatbot endpoint must define a system prompt."""
        idx = self.dashboard.find('def api_chatbot')
        func_body = self.dashboard[idx:idx + 4000]
        self.assertIn('system_prompt', func_body)


class TestChatbotJSMessageInteraction(unittest.TestCase):
    """Verify JavaScript chatbot.js has the US-3.2.2 features."""

    def setUp(self):
        self.chatbot_js = read_file(CHATBOT_JS_PATH)

    def test_enter_key_sends_message(self):
        """Enter key (without Shift) must submit the form."""
        self.assertIn("e.key === 'Enter'", self.chatbot_js)
        self.assertIn('!e.shiftKey', self.chatbot_js)

    def test_shift_enter_allowed(self):
        """Shift+Enter must NOT trigger send (creates newline instead)."""
        # The condition is `e.key === 'Enter' && !e.shiftKey` — verify it exists
        pattern = r"key === 'Enter'.*shiftKey|shiftKey.*key === 'Enter'"
        self.assertTrue(re.search(pattern, self.chatbot_js))

    def test_fetch_api_chatbot_endpoint(self):
        """fetchAIResponse must POST to /api/chatbot."""
        self.assertIn("fetch('/api/chatbot'", self.chatbot_js)
        self.assertIn("method: 'POST'", self.chatbot_js)

    def test_request_includes_conversation_history(self):
        """Request body must include conversation history."""
        self.assertIn('conversation: this.conversation', self.chatbot_js)

    def test_request_includes_page_context(self):
        """Request body must include page context."""
        self.assertIn('window.location.pathname', self.chatbot_js)

    def test_optimistic_ui_user_message(self):
        """User message must appear immediately (optimistic UI)."""
        # addMessage is called before the await fetch
        idx = self.chatbot_js.find('async sendMessage')
        func_body = self.chatbot_js[idx:idx + 2000]
        add_msg_idx = func_body.find("this.addMessage('user'")
        fetch_idx = func_body.find('fetchAIResponse')
        self.assertGreater(add_msg_idx, 0, "addMessage('user') not found in sendMessage")
        self.assertGreater(fetch_idx, 0, "fetchAIResponse not found in sendMessage")
        self.assertLess(add_msg_idx, fetch_idx, "User message must be added before AI fetch")

    def test_input_clears_after_send(self):
        """Input field must clear after message is sent."""
        self.assertIn("this.input.value = ''", self.chatbot_js)

    def test_submit_button_disabled_while_waiting(self):
        """Submit button must be disabled while AI is responding."""
        self.assertIn('.disabled = true', self.chatbot_js)
        self.assertIn('.disabled = false', self.chatbot_js)

    def test_typing_indicator_shown(self):
        """Typing indicator must show while waiting for AI."""
        self.assertIn('showTypingIndicator()', self.chatbot_js)

    def test_typing_indicator_hidden_on_response(self):
        """Typing indicator must be hidden when AI responds."""
        self.assertIn('hideTypingIndicator()', self.chatbot_js)

    def test_ai_message_added_to_ui(self):
        """AI response must be added to message area."""
        self.assertIn("this.addMessage('ai', response)", self.chatbot_js)

    def test_error_handling_network_failure(self):
        """Network errors must be caught and shown to user."""
        idx = self.chatbot_js.find('async sendMessage')
        func_body = self.chatbot_js[idx:idx + 2000]
        self.assertIn('catch (error)', func_body)
        self.assertIn('showError', func_body)

    def test_try_again_button_on_error(self):
        """Error messages must include a Try Again button for network errors."""
        self.assertIn('Try Again', self.chatbot_js)
        self.assertIn('canRetry', self.chatbot_js)

    def test_retry_restores_last_message(self):
        """Retry must resend the last failed user message."""
        self.assertIn('retryLastMessage', self.chatbot_js)
        self.assertIn('this.lastUserMessage', self.chatbot_js)

    def test_message_auto_scrolls(self):
        """Message area must auto-scroll to show new messages."""
        self.assertIn('scrollToBottom()', self.chatbot_js)

    def test_ai_message_announced_to_screen_reader(self):
        """AI messages must be announced to screen readers."""
        self.assertIn("AI says:", self.chatbot_js)
        self.assertIn("this.announce(", self.chatbot_js)

    def test_error_announced_assertive(self):
        """Errors must be announced with aria-live assertive."""
        self.assertIn("'assertive'", self.chatbot_js)

    def test_conversation_saved_after_ai_response(self):
        """Conversation must be saved to sessionStorage after AI responds."""
        self.assertIn('this.saveConversation()', self.chatbot_js)

    def test_performance_banner_at_30_messages(self):
        """Performance banner must appear after 30 messages."""
        self.assertIn('this.messageCount === 30', self.chatbot_js)
        self.assertIn('showPerformanceBanner()', self.chatbot_js)

    def test_csrf_token_in_request(self):
        """CSRF token must be included in the request headers."""
        self.assertIn('csrf-token', self.chatbot_js)
        self.assertIn('X-CSRFToken', self.chatbot_js)


if __name__ == '__main__':
    unittest.main()
