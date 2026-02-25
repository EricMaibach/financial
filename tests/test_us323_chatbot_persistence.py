"""
Static verification tests for US-3.2.3: Conversation Persistence, Notifications, and Polish Features.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required code patterns are present.
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATBOT_JS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'js', 'components', 'chatbot.js')
CHATBOT_CSS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css', 'components', 'chatbot.css')
BASE_HTML_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'templates', 'base.html')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


class TestConversationPersistence(unittest.TestCase):
    """Verify sessionStorage-based conversation persistence."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def test_save_conversation_uses_session_storage(self):
        """saveConversation() must store state in sessionStorage."""
        self.assertIn("sessionStorage.setItem('chatbot-conversation'", self.js)

    def test_save_conversation_saves_messages_and_count(self):
        """saveConversation() must persist conversation array and messageCount."""
        # Search for method definition
        idx = self.js.find('saveConversation() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 300]
        self.assertIn('conversation: this.conversation', func_body)
        self.assertIn('messageCount: this.messageCount', func_body)

    def test_restore_conversation_reads_session_storage(self):
        """restoreConversation() must read from sessionStorage."""
        self.assertIn("sessionStorage.getItem('chatbot-conversation')", self.js)

    def test_restore_conversation_replays_messages(self):
        """restoreConversation() must call addMessage() for each stored message."""
        idx = self.js.find('restoreConversation() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 600]
        self.assertIn('addMessage(', func_body)

    def test_restore_handles_parse_error_gracefully(self):
        """restoreConversation() must catch JSON parse errors without crashing."""
        idx = self.js.find('restoreConversation() {')
        func_body = self.js[idx:idx + 900]
        self.assertIn('catch', func_body)

    def test_save_called_after_ai_response(self):
        """saveConversation() must be called after each AI response."""
        idx = self.js.find('this.saveConversation()')
        self.assertGreater(idx, 0)

    def test_clear_resets_session_storage(self):
        """Clearing conversation must reset chatbot-conversation in sessionStorage (via saveConversation)."""
        # After clear, saveConversation() is called which writes empty state to sessionStorage
        idx = self.js.find('executeClearConversation() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 1200]
        self.assertIn('this.saveConversation()', func_body)

    def test_clear_removes_perf_dismissed_flag(self):
        """Clearing conversation must remove chatbot-perf-dismissed sessionStorage flag."""
        self.assertIn("sessionStorage.removeItem('chatbot-perf-dismissed')", self.js)

    def test_perf_dismissed_state_restored_on_init(self):
        """Performance banner dismissed state must be restored from sessionStorage on init."""
        self.assertIn("sessionStorage.getItem('chatbot-perf-dismissed')", self.js)


class TestBadgeNotifications(unittest.TestCase):
    """Verify badge count tracking for AI messages received while minimized."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)
        self.css = read_file(CHATBOT_CSS_PATH)
        self.html = read_file(BASE_HTML_PATH)

    def test_unread_count_property_in_constructor(self):
        """Widget must track unreadCount in constructor state."""
        self.assertIn('this.unreadCount = 0', self.js)

    def test_show_badge_increments_unread_count(self):
        """showBadge() must increment unreadCount (not always show '1')."""
        idx = self.js.find('showBadge() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 300]
        self.assertIn('this.unreadCount++', func_body)

    def test_show_badge_displays_count(self):
        """showBadge() must display actual unreadCount value in badge text."""
        idx = self.js.find('showBadge() {')
        func_body = self.js[idx:idx + 300]
        self.assertIn('this.unreadCount', func_body)
        # Must not hardcode '1'
        self.assertNotIn("textContent = '1'", func_body)

    def test_show_badge_sets_accessible_aria_label(self):
        """showBadge() must set aria-label with message count."""
        # US-4.2.1: aria-label appears deeper in the method body (~320+ chars)
        idx = self.js.find('showBadge() {')
        func_body = self.js[idx:idx + 700]
        self.assertIn('aria-label', func_body)

    def test_clear_badge_resets_unread_count(self):
        """clearBadge() must reset unreadCount to 0."""
        idx = self.js.find('clearBadge() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 200]
        self.assertIn('this.unreadCount = 0', func_body)

    def test_clear_badge_clears_badge_text(self):
        """clearBadge() must clear badge text content."""
        idx = self.js.find('clearBadge() {')
        func_body = self.js[idx:idx + 200]
        self.assertIn("textContent = ''", func_body)

    def test_badge_cleared_on_open(self):
        """Opening chatbot must clear badge (user has seen messages)."""
        # US-4.2.1: open() renamed to expand() in three-state model; method is long (~1000 chars)
        idx = self.js.find('expand() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 1200]
        self.assertIn('clearBadge()', func_body)

    def test_badge_shown_only_when_minimized(self):
        """Badge must only show when chatbot is not expanded (minimized or closed)."""
        # US-4.2.1: showBadge() is guarded by state check; look backwards from the call
        idx = self.js.find('showBadge()')
        self.assertGreater(idx, 0)
        context = self.js[max(0, idx - 200):idx + 50]
        self.assertIn("this.state !== 'expanded'", context)

    def test_badge_element_in_html(self):
        """FAB must include badge span element."""
        self.assertIn('class="chatbot-badge"', self.html)

    def test_badge_empty_hides_via_css(self):
        """.chatbot-badge:empty must use display:none to auto-hide badge."""
        self.assertIn('.chatbot-badge:empty', self.css)
        idx = self.css.find('.chatbot-badge:empty')
        rule = self.css[idx:idx + 50]
        self.assertIn('none', rule)


class TestClearConversationDialog(unittest.TestCase):
    """Verify styled confirmation dialog replaces native confirm()."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)
        self.css = read_file(CHATBOT_CSS_PATH)
        self.html = read_file(BASE_HTML_PATH)

    def test_no_native_confirm_call(self):
        """clearConversation() must NOT use native browser confirm() dialog."""
        # Native confirm() must not appear in the chatbot.js file
        self.assertNotIn("confirm('", self.js)
        self.assertNotIn('confirm("', self.js)

    def test_show_clear_dialog_method_exists(self):
        """showClearDialog() method must exist."""
        self.assertIn('showClearDialog()', self.js)

    def test_hide_clear_dialog_method_exists(self):
        """hideClearDialog() method must exist."""
        self.assertIn('hideClearDialog()', self.js)

    def test_execute_clear_conversation_method_exists(self):
        """executeClearConversation() method must exist for confirmed clear."""
        self.assertIn('executeClearConversation()', self.js)

    def test_clear_conversation_delegates_to_show_dialog(self):
        """clearConversation() must call showClearDialog() to show the dialog."""
        idx = self.js.find('clearConversation() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 150]
        self.assertIn('showClearDialog()', func_body)

    def test_cancel_button_gets_default_focus(self):
        """showClearDialog() must focus the Cancel button by default (safer choice)."""
        idx = self.js.find('showClearDialog()')
        self.assertGreater(idx, 0)
        # Find the method body
        method_idx = self.js.find('showClearDialog()', idx)
        func_body = self.js[method_idx:method_idx + 400]
        self.assertIn('chatbot-dialog-cancel', func_body)
        self.assertIn('.focus()', func_body)

    def test_dialog_element_referenced_in_constructor(self):
        """Widget constructor must reference chatbot-clear-dialog element."""
        self.assertIn("'chatbot-clear-dialog'", self.js)

    def test_dialog_html_exists_in_base(self):
        """base.html must include the chatbot-clear-dialog element."""
        self.assertIn('id="chatbot-clear-dialog"', self.html)

    def test_dialog_has_correct_role(self):
        """Dialog element must have role='dialog' for accessibility."""
        idx = self.html.find('id="chatbot-clear-dialog"')
        surrounding = self.html[idx - 50:idx + 300]
        self.assertIn('role="dialog"', surrounding)

    def test_dialog_has_aria_modal(self):
        """Dialog must declare aria-modal='true'."""
        idx = self.html.find('id="chatbot-clear-dialog"')
        surrounding = self.html[idx - 50:idx + 300]
        self.assertIn('aria-modal="true"', surrounding)

    def test_dialog_has_aria_labelledby(self):
        """Dialog must be labelled by its title via aria-labelledby."""
        idx = self.html.find('id="chatbot-clear-dialog"')
        surrounding = self.html[idx - 50:idx + 300]
        self.assertIn('aria-labelledby', surrounding)

    def test_dialog_hidden_by_default(self):
        """Dialog must start hidden."""
        idx = self.html.find('id="chatbot-clear-dialog"')
        surrounding = self.html[idx - 50:idx + 300]
        self.assertIn('hidden', surrounding)

    def test_dialog_cancel_button_in_html(self):
        """Dialog must have a Cancel button."""
        self.assertIn('chatbot-dialog-cancel', self.html)

    def test_dialog_confirm_button_in_html(self):
        """Dialog must have a Clear Chat button."""
        self.assertIn('chatbot-dialog-confirm', self.html)

    def test_cancel_button_css_uses_outlined_style(self):
        """Cancel button must use outlined border style (not filled background)."""
        idx = self.css.find('.chatbot-dialog-cancel')
        self.assertGreater(idx, 0)
        rule = self.css[idx:idx + 400]
        self.assertIn('border:', rule)
        self.assertIn('background: none', rule)

    def test_confirm_button_css_uses_danger_color(self):
        """Clear Chat button must use danger-600 (#DC2626) background."""
        idx = self.css.find('.chatbot-dialog-confirm')
        self.assertGreater(idx, 0)
        rule = self.css[idx:idx + 400]
        self.assertIn('#DC2626', rule)

    def test_dialog_buttons_meet_touch_target(self):
        """Dialog buttons must have min-height: 44px for touch target compliance."""
        # Check cancel button
        idx = self.css.find('.chatbot-dialog-cancel')
        rule = self.css[idx:idx + 400]
        self.assertIn('min-height: 44px', rule)
        # Check confirm button
        idx2 = self.css.find('.chatbot-dialog-confirm')
        rule2 = self.css[idx2:idx2 + 400]
        self.assertIn('min-height: 44px', rule2)

    def test_dialog_overlay_css_exists(self):
        """Dialog overlay must use fixed positioning to cover full viewport."""
        self.assertIn('.chatbot-dialog-overlay', self.css)
        idx = self.css.find('.chatbot-dialog-overlay')
        rule = self.css[idx:idx + 200]
        self.assertIn('position: fixed', rule)
        self.assertIn('z-index: 2000', rule)

    def test_escape_key_closes_dialog(self):
        """Escape key handler must close the dialog (not just the panel)."""
        idx = self.js.find("'Escape'")
        self.assertGreater(idx, 0)
        # Should call hideClearDialog somewhere in the file when Escape is pressed
        self.assertIn('hideClearDialog()', self.js)

    def test_focus_trap_within_dialog(self):
        """Dialog must trap Tab focus within its buttons."""
        self.assertIn("'Tab'", self.js)
        # Tab trap logic should reference the dialog element and call focus()
        idx = self.js.find("'Tab'")
        nearby = self.js[idx:idx + 500]
        self.assertIn('clearDialog', nearby)
        self.assertIn('.focus()', nearby)


class TestPerformanceBanner(unittest.TestCase):
    """Verify the 30-message performance banner behavior."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)
        self.css = read_file(CHATBOT_CSS_PATH)
        self.html = read_file(BASE_HTML_PATH)

    def test_banner_triggered_at_30_messages(self):
        """Performance banner must appear at the 30th message (soft limit)."""
        self.assertIn('this.messageCount === 30', self.js)

    def test_banner_only_shows_if_not_dismissed(self):
        """Banner must not re-show if already dismissed."""
        idx = self.js.find('this.messageCount === 30')
        condition = self.js[idx:idx + 100]
        self.assertIn('performanceBannerDismissed', condition)

    def test_show_performance_banner_method_exists(self):
        """showPerformanceBanner() must exist."""
        self.assertIn('showPerformanceBanner()', self.js)

    def test_dismiss_performance_banner_method_exists(self):
        """dismissPerformanceBanner() must exist."""
        self.assertIn('dismissPerformanceBanner()', self.js)

    def test_dismiss_saves_to_session_storage(self):
        """Dismissing banner must save flag to sessionStorage."""
        self.assertIn("sessionStorage.setItem('chatbot-perf-dismissed'", self.js)

    def test_banner_element_in_html(self):
        """base.html must include the performance banner element."""
        self.assertIn('class="chatbot-performance-banner"', self.html)

    def test_banner_starts_hidden(self):
        """Performance banner must start hidden."""
        idx = self.html.find('chatbot-performance-banner')
        surrounding = self.html[idx:idx + 200]
        self.assertIn('hidden', surrounding)

    def test_banner_has_role_status(self):
        """Banner must have role='status' for accessibility."""
        idx = self.html.find('chatbot-performance-banner')
        surrounding = self.html[idx:idx + 200]
        self.assertIn('role="status"', surrounding)

    def test_banner_dismiss_button_in_html(self):
        """Banner must include a dismiss button."""
        self.assertIn('chatbot-performance-dismiss', self.html)

    def test_banner_uses_info_colors_in_css(self):
        """Banner must use info-100 background (#DBEAFE) and info-700 text (#1E40AF)."""
        idx = self.css.find('.chatbot-performance-banner')
        self.assertGreater(idx, 0)
        rule = self.css[idx:idx + 200]
        self.assertIn('#DBEAFE', rule)

    def test_banner_text_uses_info_700_color(self):
        """Banner text must use info-700 (#1E40AF) color."""
        self.assertIn('#1E40AF', self.css)

    def test_banner_shown_again_after_clear(self):
        """After clearing conversation, messageCount resets so banner can appear at 30 again."""
        idx = self.js.find('executeClearConversation() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 800]
        # messageCount must be reset to 0
        self.assertIn('this.messageCount = 0', func_body)
        # performanceBannerDismissed must reset
        self.assertIn('this.performanceBannerDismissed = false', func_body)

    def test_banner_restored_on_page_reload_if_count_exceeded(self):
        """restoreConversation() must re-show banner if restored count >= 30 and not dismissed."""
        idx = self.js.find('restoreConversation() {')
        func_body = self.js[idx:idx + 700]
        self.assertIn('messageCount >= 30', func_body)
        self.assertIn('showPerformanceBanner()', func_body)


class TestXButtonBehavior(unittest.TestCase):
    """Verify X button closes to FAB (does not clear) the conversation."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)
        self.html = read_file(BASE_HTML_PATH)

    def test_close_button_calls_close_not_clear(self):
        """Close button (X) must call closeChatbot() (closes to FAB), not clear conversation."""
        # US-4.2.1: × now calls closeChatbot() (closes to FAB only, not minimizes to strip)
        idx = self.js.find('closeBtn.addEventListener')
        self.assertGreater(idx, 0)
        handler = self.js[idx:idx + 150]
        self.assertIn('this.closeChatbot()', handler)
        self.assertNotIn('clearConversation', handler)

    def test_close_button_in_html(self):
        """base.html must include the close button with chatbot-close class."""
        self.assertIn('class="chatbot-close"', self.html)

    def test_close_method_does_not_clear_conversation(self):
        """closeChatbot() method must not touch conversation data."""
        # US-4.2.1: close() renamed to closeChatbot() in three-state model
        idx = self.js.find('closeChatbot() {')
        self.assertGreater(idx, 0)
        # Find end of closeChatbot() method (next method definition)
        next_method = self.js.find('\n    async sendMessage', idx)
        func_body = self.js[idx:next_method]
        self.assertNotIn('this.conversation', func_body)
        self.assertNotIn('sessionStorage.removeItem', func_body)


if __name__ == '__main__':
    unittest.main()
