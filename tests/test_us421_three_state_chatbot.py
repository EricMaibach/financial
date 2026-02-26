"""
Static verification tests for US-144.1: Remove bottom-strip state and simplify chatbot
to binary expand/FAB model.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required HTML, CSS, and JS patterns are present.

Binary state model:
  closed   — FAB visible, panel hidden
  expanded — Panel visible, FAB hidden (mobile) or shifted (tablet/desktop)

These tests also verify the strip has been fully removed (no strip HTML, CSS, or JS).
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


# ============================================
# Strip Removal Tests — HTML
# ============================================

class TestStripRemovedFromHTML(unittest.TestCase):
    """Verify the bottom strip element has been removed from base.html."""

    def setUp(self):
        self.html = read_file(BASE_HTML_PATH)

    def test_strip_element_not_in_html(self):
        """base.html must NOT include chatbot-strip button element."""
        self.assertNotIn('id="chatbot-strip"', self.html)

    def test_strip_class_not_in_html(self):
        """base.html must NOT reference class chatbot-strip."""
        self.assertNotIn('class="chatbot-strip"', self.html)

    def test_strip_label_not_in_html(self):
        """base.html must NOT include chatbot-strip-label span."""
        self.assertNotIn('chatbot-strip-label', self.html)

    def test_strip_badge_not_in_html(self):
        """base.html must NOT include chatbot-strip-badge span."""
        self.assertNotIn('chatbot-strip-badge', self.html)

    def test_strip_chevron_not_in_html(self):
        """base.html must NOT include chatbot-strip-chevron element."""
        self.assertNotIn('chatbot-strip-chevron', self.html)

    def test_fab_still_in_html(self):
        """FAB must still be present (used in closed state)."""
        self.assertIn('id="chatbot-fab"', self.html)

    def test_panel_still_in_html(self):
        """Panel must still be present (used in expanded state)."""
        self.assertIn('id="chatbot-panel"', self.html)


# ============================================
# Single-Button Tests — HTML
# ============================================

class TestSingleButtonHTML(unittest.TestCase):
    """Verify panel header has exactly one button (the minimize/close button)."""

    def setUp(self):
        self.html = read_file(BASE_HTML_PATH)

    def test_minimize_button_still_present(self):
        """The single close button must still have class chatbot-minimize."""
        self.assertIn('class="chatbot-minimize"', self.html)

    def test_close_button_removed(self):
        """The separate × close button (chatbot-close class) must be removed."""
        self.assertNotIn('class="chatbot-close"', self.html)

    def test_single_header_button_closes_to_fab(self):
        """The single header button must have accessible label referencing close."""
        idx = self.html.find('class="chatbot-minimize"')
        self.assertGreater(idx, 0)
        surrounding = self.html[idx:idx + 200]
        self.assertIn('aria-label=', surrounding)
        # Must indicate closing, not minimizing to strip
        label_match = re.search(r'aria-label="([^"]+)"', surrounding)
        self.assertIsNotNone(label_match)
        label = label_match.group(1).lower()
        self.assertIn('close', label)


# ============================================
# Strip Removal Tests — CSS
# ============================================

class TestStripRemovedFromCSS(unittest.TestCase):
    """Verify all strip CSS has been removed from chatbot.css."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_strip_class_not_in_css(self):
        """chatbot.css must NOT contain .chatbot-strip rule."""
        self.assertNotIn('.chatbot-strip', self.css)

    def test_strip_label_not_in_css(self):
        """chatbot.css must NOT contain .chatbot-strip-label rule."""
        self.assertNotIn('.chatbot-strip-label', self.css)

    def test_strip_badge_not_in_css(self):
        """chatbot.css must NOT contain .chatbot-strip-badge rule."""
        self.assertNotIn('.chatbot-strip-badge', self.css)

    def test_strip_chevron_not_in_css(self):
        """chatbot.css must NOT contain .chatbot-strip-chevron rule."""
        self.assertNotIn('.chatbot-strip-chevron', self.css)

    def test_strip_visible_class_not_in_css(self):
        """chatbot.css must NOT contain chatbot-strip--visible class."""
        self.assertNotIn('chatbot-strip--visible', self.css)

    def test_fab_data_chatbot_hidden_not_in_css(self):
        """chatbot.css must NOT contain [data-chatbot-hidden] rule (strip-only concept)."""
        self.assertNotIn('data-chatbot-hidden', self.css)

    def test_close_class_not_in_css(self):
        """chatbot.css must NOT contain .chatbot-close rule (button removed)."""
        self.assertNotIn('.chatbot-close', self.css)


# ============================================
# Binary State Model Tests — CSS
# ============================================

class TestBinaryModelCSS(unittest.TestCase):
    """Verify CSS correctly supports binary closed/expanded state."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_fab_hidden_on_mobile_when_expanded(self):
        """FAB [aria-expanded='true'] must hide on mobile (opacity:0, pointer-events:none)."""
        idx = self.css.find('.chatbot-fab[aria-expanded="true"]')
        self.assertGreater(idx, 0)
        rule = self.css[idx:idx + 200]
        self.assertIn('opacity: 0', rule)
        self.assertIn('pointer-events: none', rule)

    def test_fab_shifts_right_on_tablet(self):
        """FAB [aria-expanded='true'] on tablet must shift left to accommodate panel."""
        idx = self.css.find('@media (min-width: 768px)')
        self.assertGreater(idx, 0)
        block = self.css[idx:idx + 2000]
        self.assertIn('.chatbot-fab[aria-expanded="true"]', block)
        fab_expanded_idx = block.find('.chatbot-fab[aria-expanded="true"]')
        rule = block[fab_expanded_idx:fab_expanded_idx + 200]
        self.assertIn('opacity: 1', rule)
        self.assertIn('pointer-events: auto', rule)

    def test_panel_slides_down_when_hidden(self):
        """Panel must start with translateY(100%) to be hidden below viewport."""
        idx = self.css.find('.chatbot-panel {')
        self.assertGreater(idx, 0)
        rule = self.css[idx:idx + 600]
        self.assertIn('translateY(100%)', rule)

    def test_panel_visible_when_aria_hidden_false(self):
        """Panel [aria-hidden='false'] must translate to 0 (visible)."""
        self.assertIn('.chatbot-panel[aria-hidden="false"]', self.css)
        idx = self.css.find('.chatbot-panel[aria-hidden="false"]')
        rule = self.css[idx:idx + 100]
        self.assertIn('translateY(0)', rule)

    def test_single_minimize_button_style_exists(self):
        """chatbot.css must still have .chatbot-minimize style rule."""
        self.assertIn('.chatbot-minimize', self.css)

    def test_tablet_panel_uses_translatex(self):
        """Tablet side-panel must use translateX(100%) to slide from right."""
        idx = self.css.find('@media (min-width: 768px)')
        self.assertGreater(idx, 0)
        block = self.css[idx:idx + 2000]
        self.assertIn('translateX(100%)', block)

    def test_desktop_panel_width_440px(self):
        """Desktop panel must still be 440px wide."""
        idx = self.css.find('@media (min-width: 1024px)')
        self.assertGreater(idx, 0)
        block = self.css[idx:idx + 2000]
        panel_idx = block.find('.chatbot-panel')
        self.assertGreater(panel_idx, 0)
        panel_rule = block[panel_idx:panel_idx + 100]
        self.assertIn('width: 440px', panel_rule)


# ============================================
# Binary State Model Tests — JS
# ============================================

class TestBinaryStateModelJS(unittest.TestCase):
    """Verify binary state model is implemented in chatbot.js."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def test_state_property_initialized_closed(self):
        """Widget must initialize with state = 'closed'."""
        self.assertIn("this.state = 'closed'", self.js)

    def test_no_minimized_state_in_js(self):
        """JS must not reference 'minimized' state (strip removed)."""
        self.assertNotIn("this.state = 'minimized'", self.js)

    def test_expand_method_exists(self):
        """expand() method must exist (open from closed state)."""
        self.assertIn('expand() {', self.js)

    def test_close_chatbot_method_exists(self):
        """closeChatbot() method must exist (single close transition → FAB)."""
        self.assertIn('closeChatbot() {', self.js)

    def test_minimize_method_removed(self):
        """minimize() method must be removed (three-state model gone)."""
        self.assertNotIn('minimize() {', self.js)

    def test_fab_click_calls_expand(self):
        """FAB click must call expand() to open from closed state."""
        idx = self.js.find('this.fab.addEventListener')
        self.assertGreater(idx, 0)
        handler = self.js[idx:idx + 100]
        self.assertIn('this.expand()', handler)

    def test_minimize_btn_calls_close_chatbot(self):
        """Single header button must call closeChatbot() to collapse to FAB."""
        idx = self.js.find('minimizeBtn.addEventListener')
        self.assertGreater(idx, 0)
        handler = self.js[idx:idx + 100]
        self.assertIn('this.closeChatbot()', handler)

    def test_no_close_btn_listener(self):
        """closeBtn event listener must be removed (no second button)."""
        self.assertNotIn('closeBtn.addEventListener', self.js)

    def test_no_strip_reference_in_constructor(self):
        """Constructor must not reference chatbot-strip element."""
        self.assertNotIn("'chatbot-strip'", self.js)

    def test_no_strip_badge_reference_in_constructor(self):
        """Constructor must not reference .chatbot-strip-badge element."""
        self.assertNotIn('chatbot-strip-badge', self.js)

    def test_no_data_chatbot_hidden_in_js(self):
        """JS must not use data-chatbot-hidden attribute (strip-only concept)."""
        self.assertNotIn('data-chatbot-hidden', self.js)


# ============================================
# State Transition Tests — JS
# ============================================

class TestBinaryStateTransitions(unittest.TestCase):
    """Verify correct DOM manipulation in each binary state transition."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def _get_method_body(self, method_name, char_limit=800):
        idx = self.js.find(f'{method_name}() {{')
        self.assertGreater(idx, 0, f'{method_name}() method not found')
        return self.js[idx:idx + char_limit]

    def test_expand_sets_state_to_expanded(self):
        """expand() must set state to 'expanded'."""
        body = self._get_method_body('expand')
        self.assertIn("this.state = 'expanded'", body)

    def test_expand_shows_panel(self):
        """expand() must set panel aria-hidden='false'."""
        body = self._get_method_body('expand')
        self.assertIn("aria-hidden', 'false'", body)

    def test_expand_sets_fab_aria_expanded_true(self):
        """expand() must set fab aria-expanded='true'."""
        body = self._get_method_body('expand')
        self.assertIn("aria-expanded', 'true'", body)

    def test_expand_clears_badge(self):
        """expand() must clear badges."""
        body = self._get_method_body('expand')
        self.assertIn('clearBadge()', body)

    def test_expand_focuses_input(self):
        """expand() must focus the input field after animation."""
        body = self._get_method_body('expand')
        self.assertIn('this.input.focus()', body)

    def test_expand_announces_opened(self):
        """expand() must announce 'AI Chatbot opened' to screen readers."""
        body = self._get_method_body('expand')
        self.assertIn('AI Chatbot opened', body)

    def test_expand_does_not_reference_strip(self):
        """expand() must not reference the strip (removed)."""
        body = self._get_method_body('expand')
        self.assertNotIn('strip', body.lower().replace('chatbot-strip-badge', ''))
        # More specific: no this.strip usage
        self.assertNotIn('this.strip', body)

    def test_close_chatbot_sets_state_to_closed(self):
        """closeChatbot() must set state to 'closed'."""
        body = self._get_method_body('closeChatbot')
        self.assertIn("this.state = 'closed'", body)

    def test_close_chatbot_hides_panel(self):
        """closeChatbot() must set panel aria-hidden='true'."""
        body = self._get_method_body('closeChatbot')
        self.assertIn("aria-hidden', 'true'", body)

    def test_close_chatbot_resets_fab_aria_expanded(self):
        """closeChatbot() must set fab aria-expanded='false'."""
        body = self._get_method_body('closeChatbot')
        self.assertIn("aria-expanded', 'false'", body)

    def test_close_chatbot_focuses_fab(self):
        """closeChatbot() must return focus to FAB after animation."""
        body = self._get_method_body('closeChatbot')
        self.assertIn('this.fab.focus()', body)

    def test_close_chatbot_announces_closed(self):
        """closeChatbot() must announce 'AI Chatbot closed' to screen readers."""
        body = self._get_method_body('closeChatbot')
        self.assertIn('AI Chatbot closed', body)

    def test_close_chatbot_does_not_touch_conversation(self):
        """closeChatbot() must not clear or modify conversation data."""
        idx = self.js.find('closeChatbot() {')
        self.assertGreater(idx, 0)
        next_method = self.js.find('\n    async sendMessage', idx)
        func_body = self.js[idx:next_method]
        self.assertNotIn('this.conversation', func_body)
        self.assertNotIn('sessionStorage.removeItem', func_body)

    def test_close_chatbot_does_not_reference_strip(self):
        """closeChatbot() must not reference the strip (removed)."""
        body = self._get_method_body('closeChatbot')
        self.assertNotIn('this.strip', body)


# ============================================
# Escape Key Tests
# ============================================

class TestEscapeKeyBehavior(unittest.TestCase):
    """Verify Escape key collapses to FAB (closed state) per binary model."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def test_escape_calls_close_chatbot_when_expanded(self):
        """Escape key when expanded must call closeChatbot() (collapse to FAB)."""
        doc_keydown_idx = self.js.find("document.addEventListener('keydown'")
        self.assertGreater(doc_keydown_idx, 0)
        handler_block = self.js[doc_keydown_idx:doc_keydown_idx + 300]
        self.assertIn('this.closeChatbot()', handler_block)

    def test_escape_does_not_call_minimize(self):
        """Escape handler must NOT call minimize() (method removed)."""
        doc_keydown_idx = self.js.find("document.addEventListener('keydown'")
        handler_block = self.js[doc_keydown_idx:doc_keydown_idx + 300]
        self.assertNotIn('this.minimize()', handler_block)

    def test_escape_checks_expanded_state(self):
        """Escape handler must check state === 'expanded' before closing."""
        doc_keydown_idx = self.js.find("document.addEventListener('keydown'")
        handler_block = self.js[doc_keydown_idx:doc_keydown_idx + 300]
        self.assertIn("this.state === 'expanded'", handler_block)


# ============================================
# Badge Tests
# ============================================

class TestBadgeAlwaysOnFAB(unittest.TestCase):
    """Verify badge always goes to FAB (no strip badge routing)."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def test_show_badge_no_minimized_check(self):
        """showBadge() must NOT check for 'minimized' state (no strip)."""
        idx = self.js.find('showBadge() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 400]
        self.assertNotIn("this.state === 'minimized'", func_body)

    def test_show_badge_always_updates_fab_badge(self):
        """showBadge() must always update the FAB badge."""
        idx = self.js.find('showBadge() {')
        func_body = self.js[idx:idx + 400]
        self.assertIn('this.badge', func_body)

    def test_show_badge_no_strip_badge_reference(self):
        """showBadge() must not reference strip badge (removed)."""
        idx = self.js.find('showBadge() {')
        func_body = self.js[idx:idx + 400]
        self.assertNotIn('this.stripBadge', func_body)

    def test_clear_badge_no_strip_badge(self):
        """clearBadge() must not reference strip badge (removed)."""
        idx = self.js.find('clearBadge() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 300]
        self.assertNotIn('this.stripBadge', func_body)

    def test_show_badge_guards_not_expanded(self):
        """Badge display must still be guarded: only when state !== expanded."""
        idx = self.js.find('showBadge()')
        self.assertGreater(idx, 0)
        context = self.js[max(0, idx - 200):idx + 50]
        self.assertIn("this.state !== 'expanded'", context)


# ============================================
# Regression Tests — Prior Features
# ============================================

class TestRegressionGuards(unittest.TestCase):
    """Verify prior US-3.2.x features are not broken by the binary model."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)
        self.html = read_file(BASE_HTML_PATH)
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_conversation_persistence_still_works(self):
        """saveConversation() and restoreConversation() must still exist."""
        self.assertIn('saveConversation() {', self.js)
        self.assertIn('restoreConversation() {', self.js)

    def test_performance_banner_still_present(self):
        """Performance banner (30-message limit) must still work."""
        self.assertIn('this.messageCount === 30', self.js)
        self.assertIn('showPerformanceBanner()', self.js)

    def test_clear_conversation_dialog_still_works(self):
        """Clear conversation dialog flow must still exist."""
        self.assertIn('showClearDialog()', self.js)
        self.assertIn('hideClearDialog()', self.js)
        self.assertIn('executeClearConversation()', self.js)

    def test_tablet_panel_still_uses_translatex(self):
        """Tablet side-panel translateX must still be present in CSS."""
        idx = self.css.find('@media (min-width: 768px)')
        self.assertGreater(idx, 0)
        block = self.css[idx:idx + 2000]
        self.assertIn('translateX(100%)', block)

    def test_desktop_panel_width_still_440px(self):
        """Desktop panel must still be 440px wide."""
        idx = self.css.find('@media (min-width: 1024px)')
        self.assertGreater(idx, 0)
        block = self.css[idx:idx + 2000]
        panel_idx = block.find('.chatbot-panel')
        self.assertGreater(panel_idx, 0)
        panel_rule = block[panel_idx:panel_idx + 100]
        self.assertIn('width: 440px', panel_rule)

    def test_fab_still_in_html(self):
        """FAB must still be in base.html."""
        self.assertIn('id="chatbot-fab"', self.html)

    def test_panel_still_in_html(self):
        """Panel must still be in base.html."""
        self.assertIn('id="chatbot-panel"', self.html)

    def test_enter_key_handler_still_present(self):
        """Enter key to send message must still work."""
        self.assertIn("e.key === 'Enter'", self.js)
        self.assertIn('!e.shiftKey', self.js)

    def test_retry_message_still_works(self):
        """retryLastMessage() must still exist for error recovery."""
        self.assertIn('retryLastMessage()', self.js)

    def test_overscroll_behavior_still_set(self):
        """chatbot-messages must still have overscroll-behavior-y: contain."""
        self.assertIn('overscroll-behavior-y: contain', self.css)

    def test_animations_still_250ms(self):
        """Panel animation must still be 250ms ease-in-out."""
        self.assertIn('250ms', self.css)

    def test_ai_api_endpoint_still_referenced(self):
        """fetchAIResponse must still call /api/chatbot endpoint."""
        self.assertIn("'/api/chatbot'", self.js)

    def test_escape_key_in_clear_dialog_still_works(self):
        """Escape key in clear dialog must still dismiss dialog."""
        idx = self.js.find('clearDialog.addEventListener')
        self.assertGreater(idx, 0)
        block = self.js[idx:idx + 400]
        self.assertIn("'Escape'", block)
        self.assertIn('hideClearDialog()', block)


if __name__ == '__main__':
    unittest.main()
