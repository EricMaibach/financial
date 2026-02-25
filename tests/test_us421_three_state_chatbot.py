"""
Static verification tests for US-4.2.1: Implement three-state chatbot model with bottom strip.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required HTML, CSS, and JS patterns are present.

Three-state model:
  closed    — FAB visible, panel hidden, strip hidden
  expanded  — Panel visible, FAB hidden (mobile) or shifted (tablet/desktop), strip hidden
  minimized — Strip visible, FAB hidden, panel hidden
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
# HTML Structure Tests
# ============================================

class TestStripHTML(unittest.TestCase):
    """Verify the bottom strip element is present in base.html."""

    def setUp(self):
        self.html = read_file(BASE_HTML_PATH)

    def test_strip_element_in_html(self):
        """base.html must include the chatbot-strip button element."""
        self.assertIn('id="chatbot-strip"', self.html)

    def test_strip_has_chatbot_strip_class(self):
        """Strip button must have class chatbot-strip."""
        self.assertIn('class="chatbot-strip"', self.html)

    def test_strip_has_aria_label(self):
        """Strip button must have an accessible aria-label."""
        idx = self.html.find('id="chatbot-strip"')
        self.assertGreater(idx, 0)
        surrounding = self.html[idx:idx + 300]
        self.assertIn('aria-label=', surrounding)
        self.assertIn('expand', surrounding.lower())

    def test_strip_has_aria_expanded_false(self):
        """Strip button must start with aria-expanded='false'."""
        idx = self.html.find('id="chatbot-strip"')
        surrounding = self.html[idx:idx + 300]
        self.assertIn('aria-expanded="false"', surrounding)

    def test_strip_starts_hidden(self):
        """Strip button must start hidden (minimized state not active on load)."""
        idx = self.html.find('id="chatbot-strip"')
        surrounding = self.html[idx:idx + 300]
        self.assertIn('hidden', surrounding)

    def test_strip_has_label_span(self):
        """Strip must contain chatbot-strip-label span."""
        self.assertIn('chatbot-strip-label', self.html)

    def test_strip_has_badge_span(self):
        """Strip must contain chatbot-strip-badge span for unread notifications."""
        self.assertIn('chatbot-strip-badge', self.html)

    def test_strip_badge_starts_hidden(self):
        """Strip badge must start hidden (no unread messages on load)."""
        idx = self.html.find('chatbot-strip-badge')
        self.assertGreater(idx, 0)
        surrounding = self.html[idx:idx + 100]
        self.assertIn('hidden', surrounding)

    def test_strip_has_chevron(self):
        """Strip must contain chatbot-strip-chevron for expand affordance."""
        self.assertIn('chatbot-strip-chevron', self.html)

    def test_fab_element_still_in_html(self):
        """FAB must still be present (used in closed state)."""
        self.assertIn('id="chatbot-fab"', self.html)

    def test_panel_element_still_in_html(self):
        """Panel must still be present (used in expanded state)."""
        self.assertIn('id="chatbot-panel"', self.html)


# ============================================
# CSS Tests — Bottom Strip Styles
# ============================================

class TestStripCSS(unittest.TestCase):
    """Verify chatbot-strip CSS is correct per spec."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_strip_class_declared(self):
        """.chatbot-strip CSS rule must be declared."""
        self.assertIn('.chatbot-strip', self.css)

    def test_strip_is_fixed_positioned(self):
        """Strip must use fixed positioning (stays at viewport bottom)."""
        idx = self.css.find('.chatbot-strip {')
        self.assertGreater(idx, 0)
        rule = self.css[idx:idx + 500]
        self.assertIn('position: fixed', rule)

    def test_strip_anchors_to_bottom(self):
        """Strip must be anchored to viewport bottom."""
        idx = self.css.find('.chatbot-strip {')
        rule = self.css[idx:idx + 500]
        self.assertIn('bottom: 0', rule)

    def test_strip_height_48px(self):
        """Strip must be exactly 48px (touch-safe per spec)."""
        idx = self.css.find('.chatbot-strip {')
        rule = self.css[idx:idx + 500]
        self.assertIn('height: 48px', rule)

    def test_strip_background_neutral_800(self):
        """Strip must use neutral-800 (#1F2937) background."""
        idx = self.css.find('.chatbot-strip {')
        rule = self.css[idx:idx + 500]
        self.assertIn('#1F2937', rule)

    def test_strip_top_border_neutral_600(self):
        """Strip must have neutral-600 (#4B5563) top border."""
        idx = self.css.find('.chatbot-strip {')
        rule = self.css[idx:idx + 500]
        self.assertIn('#4B5563', rule)

    def test_strip_full_width_mobile(self):
        """Strip must span full width on mobile (left:0, right:0)."""
        idx = self.css.find('.chatbot-strip {')
        rule = self.css[idx:idx + 500]
        self.assertIn('left: 0', rule)
        self.assertIn('right: 0', rule)

    def test_strip_hidden_attribute_display_none(self):
        """Strip [hidden] must be display:none."""
        self.assertIn('.chatbot-strip[hidden]', self.css)
        idx = self.css.find('.chatbot-strip[hidden]')
        rule = self.css[idx:idx + 80]
        self.assertIn('none', rule)

    def test_strip_visible_class_opacity_1(self):
        """chatbot-strip--visible class must set opacity:1 to enable fade-in."""
        self.assertIn('chatbot-strip--visible', self.css)
        idx = self.css.find('chatbot-strip--visible')
        rule = self.css[idx:idx + 80]
        self.assertIn('opacity: 1', rule)

    def test_strip_fade_in_transition(self):
        """Strip must have an opacity transition for fade-in animation."""
        idx = self.css.find('.chatbot-strip {')
        rule = self.css[idx:idx + 800]
        self.assertIn('transition:', rule)
        self.assertIn('opacity', rule)

    def test_strip_label_text_sm(self):
        """Strip label must be 14px (text-sm) per spec."""
        self.assertIn('.chatbot-strip-label', self.css)
        idx = self.css.find('.chatbot-strip-label')
        rule = self.css[idx:idx + 200]
        self.assertIn('14px', rule)

    def test_strip_label_weight_500(self):
        """Strip label must be font-weight 500 per spec."""
        idx = self.css.find('.chatbot-strip-label')
        rule = self.css[idx:idx + 200]
        self.assertIn('font-weight: 500', rule)

    def test_strip_badge_danger_600(self):
        """Strip badge must use danger-600 (#DC2626) background (same as FAB badge)."""
        self.assertIn('.chatbot-strip-badge', self.css)
        idx = self.css.find('.chatbot-strip-badge')
        rule = self.css[idx:idx + 200]
        self.assertIn('#DC2626', rule)

    def test_strip_badge_hidden_attribute(self):
        """Strip badge [hidden] must be display:none."""
        self.assertIn('.chatbot-strip-badge[hidden]', self.css)
        idx = self.css.find('.chatbot-strip-badge[hidden]')
        rule = self.css[idx:idx + 80]
        self.assertIn('none', rule)

    def test_strip_tablet_width_360px(self):
        """Strip must be 360px wide on tablet (aligns with panel)."""
        # Use rfind to get the LAST 768px block (strip's block, not panel's block)
        idx = self.css.rfind('@media (min-width: 768px)')
        self.assertGreater(idx, 0)
        last_tablet_block = self.css[idx:]
        self.assertIn('.chatbot-strip', last_tablet_block)
        self.assertIn('width: 360px', last_tablet_block)

    def test_strip_desktop_width_440px(self):
        """Strip must be 440px wide on desktop (aligns with panel)."""
        idx = self.css.find('@media (min-width: 1024px)')
        self.assertGreater(idx, 0)
        remaining = self.css[idx:]
        strip_440_idx = remaining.find('width: 440px')
        self.assertGreater(strip_440_idx, 0)

    def test_strip_tablet_right_aligned(self):
        """Strip must be right-aligned on tablet (left: auto)."""
        # Use rfind to get the LAST 768px block (strip's block, not panel's block)
        idx = self.css.rfind('@media (min-width: 768px)')
        last_tablet_block = self.css[idx:]
        chatbot_strip_idx = last_tablet_block.find('.chatbot-strip')
        self.assertGreater(chatbot_strip_idx, 0)
        block = last_tablet_block[chatbot_strip_idx:chatbot_strip_idx + 200]
        self.assertIn('left: auto', block)


class TestFABHiddenState(unittest.TestCase):
    """Verify FAB can be hidden in minimized state via data-chatbot-hidden attribute."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_fab_hidden_attribute_rule_exists(self):
        """CSS must include rule to hide FAB via data-chatbot-hidden attribute."""
        self.assertIn('.chatbot-fab[data-chatbot-hidden]', self.css)

    def test_fab_hidden_sets_opacity_zero(self):
        """FAB [data-chatbot-hidden] must set opacity:0."""
        idx = self.css.find('.chatbot-fab[data-chatbot-hidden]')
        rule = self.css[idx:idx + 150]
        self.assertIn('opacity: 0', rule)

    def test_fab_hidden_sets_pointer_events_none(self):
        """FAB [data-chatbot-hidden] must prevent pointer events."""
        idx = self.css.find('.chatbot-fab[data-chatbot-hidden]')
        rule = self.css[idx:idx + 150]
        self.assertIn('pointer-events: none', rule)


# ============================================
# JS State Machine Tests
# ============================================

class TestThreeStateModel(unittest.TestCase):
    """Verify three-state model is implemented in chatbot.js."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def test_state_property_initialized_closed(self):
        """Widget must initialize with state = 'closed'."""
        self.assertIn("this.state = 'closed'", self.js)

    def test_expand_method_exists(self):
        """expand() method must exist (replaces binary open())."""
        self.assertIn('expand() {', self.js)

    def test_minimize_method_exists(self):
        """minimize() method must exist (new state: collapsed to bottom strip)."""
        self.assertIn('minimize() {', self.js)

    def test_close_chatbot_method_exists(self):
        """closeChatbot() method must exist (× button → FAB only)."""
        self.assertIn('closeChatbot() {', self.js)

    def test_fab_click_calls_expand(self):
        """FAB click must call expand() to open from closed state."""
        idx = self.js.find('this.fab.addEventListener')
        self.assertGreater(idx, 0)
        handler = self.js[idx:idx + 100]
        self.assertIn('this.expand()', handler)

    def test_minimize_btn_calls_minimize(self):
        """Minimize button (−) must call minimize() → bottom strip state."""
        idx = self.js.find('minimizeBtn.addEventListener')
        self.assertGreater(idx, 0)
        handler = self.js[idx:idx + 100]
        self.assertIn('this.minimize()', handler)

    def test_close_btn_calls_close_chatbot(self):
        """Close button (×) must call closeChatbot() → FAB only state."""
        idx = self.js.find('closeBtn.addEventListener')
        self.assertGreater(idx, 0)
        handler = self.js[idx:idx + 100]
        self.assertIn('this.closeChatbot()', handler)

    def test_strip_click_calls_expand(self):
        """Strip tap must call expand() to reopen from minimized state."""
        idx = self.js.find('this.strip.addEventListener')
        self.assertGreater(idx, 0)
        handler = self.js[idx:idx + 100]
        self.assertIn('this.expand()', handler)

    def test_strip_referenced_in_constructor(self):
        """Widget constructor must reference chatbot-strip element."""
        self.assertIn("'chatbot-strip'", self.js)

    def test_strip_badge_referenced_in_constructor(self):
        """Widget constructor must reference .chatbot-strip-badge element."""
        self.assertIn('chatbot-strip-badge', self.js)


class TestStateTransitions(unittest.TestCase):
    """Verify correct DOM manipulation in each state transition."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def _get_method_body(self, method_name, char_limit=1200):
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
        """expand() must set fab aria-expanded='true' (mobile hides, tablet/desktop shifts)."""
        body = self._get_method_body('expand')
        self.assertIn("aria-expanded', 'true'", body)

    def test_expand_removes_fab_data_hidden(self):
        """expand() must remove data-chatbot-hidden from FAB."""
        body = self._get_method_body('expand')
        self.assertIn("removeAttribute('data-chatbot-hidden')", body)

    def test_expand_clears_badge(self):
        """expand() must clear badges (user is now viewing messages)."""
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

    def test_minimize_sets_state_to_minimized(self):
        """minimize() must set state to 'minimized'."""
        body = self._get_method_body('minimize')
        self.assertIn("this.state = 'minimized'", body)

    def test_minimize_hides_panel(self):
        """minimize() must set panel aria-hidden='true'."""
        body = self._get_method_body('minimize')
        self.assertIn("aria-hidden', 'true'", body)

    def test_minimize_sets_fab_data_hidden(self):
        """minimize() must set data-chatbot-hidden on FAB to hide it."""
        body = self._get_method_body('minimize')
        self.assertIn("setAttribute('data-chatbot-hidden', '')", body)

    def test_minimize_removes_hidden_from_strip(self):
        """minimize() must remove hidden attribute from strip."""
        body = self._get_method_body('minimize')
        self.assertIn("removeAttribute('hidden')", body)

    def test_minimize_adds_visible_class_to_strip(self):
        """minimize() must add chatbot-strip--visible class for fade-in animation."""
        body = self._get_method_body('minimize')
        self.assertIn('chatbot-strip--visible', body)

    def test_minimize_announces_minimized(self):
        """minimize() must announce 'AI Chatbot minimized' to screen readers."""
        body = self._get_method_body('minimize')
        self.assertIn('AI Chatbot minimized', body)

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

    def test_close_chatbot_removes_fab_data_hidden(self):
        """closeChatbot() must remove data-chatbot-hidden so FAB becomes visible."""
        body = self._get_method_body('closeChatbot')
        self.assertIn("removeAttribute('data-chatbot-hidden')", body)

    def test_close_chatbot_keeps_strip_hidden(self):
        """closeChatbot() must ensure strip stays hidden (add hidden attribute)."""
        body = self._get_method_body('closeChatbot')
        self.assertIn("setAttribute('hidden', '')", body)

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


class TestEscapeKeyBehavior(unittest.TestCase):
    """Verify Escape key goes to minimized (bottom strip) state per spec."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def test_escape_calls_minimize_when_expanded(self):
        """Escape key when expanded must call minimize() (→ bottom strip), not close()."""
        # Find the global keydown handler
        idx = self.js.find("'Escape'")
        self.assertGreater(idx, 0)
        # Look near the global Escape handler (document.addEventListener)
        # The escape handler for the panel should call minimize()
        # Find the document.addEventListener('keydown') block
        doc_keydown_idx = self.js.find("document.addEventListener('keydown'")
        self.assertGreater(doc_keydown_idx, 0)
        handler_block = self.js[doc_keydown_idx:doc_keydown_idx + 300]
        self.assertIn('this.minimize()', handler_block)

    def test_escape_checks_expanded_state(self):
        """Escape handler must check state === 'expanded' before minimizing."""
        doc_keydown_idx = self.js.find("document.addEventListener('keydown'")
        handler_block = self.js[doc_keydown_idx:doc_keydown_idx + 300]
        self.assertIn("this.state === 'expanded'", handler_block)


# ============================================
# Badge State Tests
# ============================================

class TestBadgeStateRouting(unittest.TestCase):
    """Verify badge appears on correct element based on chatbot state."""

    def setUp(self):
        self.js = read_file(CHATBOT_JS_PATH)

    def test_show_badge_checks_minimized_state(self):
        """showBadge() must check if state is 'minimized' to route to strip badge."""
        idx = self.js.find('showBadge() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 400]
        self.assertIn("this.state === 'minimized'", func_body)

    def test_show_badge_shows_strip_badge_when_minimized(self):
        """showBadge() must update stripBadge when state is minimized."""
        idx = self.js.find('showBadge() {')
        func_body = self.js[idx:idx + 400]
        self.assertIn('this.stripBadge', func_body)

    def test_show_badge_shows_fab_badge_when_closed(self):
        """showBadge() must update FAB badge when state is not minimized (closed)."""
        idx = self.js.find('showBadge() {')
        func_body = self.js[idx:idx + 700]
        self.assertIn('this.badge', func_body)

    def test_strip_badge_unhidden_in_show_badge(self):
        """showBadge() must remove hidden from strip badge to make it visible."""
        idx = self.js.find('showBadge() {')
        func_body = self.js[idx:idx + 500]
        self.assertIn("removeAttribute('hidden')", func_body)

    def test_clear_badge_clears_strip_badge(self):
        """clearBadge() must clear and re-hide the strip badge."""
        idx = self.js.find('clearBadge() {')
        self.assertGreater(idx, 0)
        func_body = self.js[idx:idx + 500]
        self.assertIn('this.stripBadge', func_body)
        # Must re-hide badge on clear
        self.assertIn("setAttribute('hidden', '')", func_body)

    def test_clear_badge_clears_both_badges(self):
        """clearBadge() must clear both FAB badge and strip badge."""
        idx = self.js.find('clearBadge() {')
        func_body = self.js[idx:idx + 500]
        self.assertIn('this.badge', func_body)
        self.assertIn('this.stripBadge', func_body)


# ============================================
# Regression Tests — Prior US-3.2.x Features
# ============================================

class TestRegressionGuards(unittest.TestCase):
    """Verify prior US-3.2.x features are not broken by the three-state model."""

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
        # Find the chatbot-panel rule in the 1024px block
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

    def test_minimize_btn_still_in_html(self):
        """Minimize (−) button must still be in base.html."""
        self.assertIn('class="chatbot-minimize"', self.html)

    def test_close_btn_still_in_html(self):
        """Close (×) button must still be in base.html."""
        self.assertIn('class="chatbot-close"', self.html)

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


if __name__ == '__main__':
    unittest.main()
