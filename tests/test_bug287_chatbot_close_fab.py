"""
Tests for Bug #287: Chatbot close button and FAB visibility.

Verifies that:
- Close (X) button is visible on all viewports (desktop, tablet, mobile)
- FAB is hidden when chatbot is open on all viewports
- Behavior is consistent across breakpoints
"""

import os
import re
import pytest
from bs4 import BeautifulSoup


CHATBOT_CSS_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'signaltrackers', 'static', 'css', 'components', 'chatbot.css'
)

CHATBOT_JS_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'signaltrackers', 'static', 'js', 'components', 'chatbot.js'
)

BASE_HTML_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'signaltrackers', 'templates', 'base.html'
)


@pytest.fixture(scope='module')
def chatbot_css():
    with open(CHATBOT_CSS_PATH) as f:
        return f.read()


@pytest.fixture(scope='module')
def chatbot_js():
    with open(CHATBOT_JS_PATH) as f:
        return f.read()


@pytest.fixture(scope='module')
def base_html():
    with open(BASE_HTML_PATH) as f:
        return f.read()


@pytest.fixture(scope='module')
def base_soup(base_html):
    return BeautifulSoup(base_html, 'html.parser')


# ============================================
# Close Button Visibility Tests
# ============================================

class TestCloseButtonVisibility:
    """Close (X) button must be visible and functional on all viewports."""

    def test_close_button_exists_in_html(self, base_soup):
        """chatbot-minimize button exists in the DOM."""
        btn = base_soup.find('button', class_='chatbot-minimize')
        assert btn is not None, 'Close button (.chatbot-minimize) must exist in base.html'

    def test_close_button_has_aria_label(self, base_soup):
        """Close button has aria-label='Close chatbot'."""
        btn = base_soup.find('button', class_='chatbot-minimize')
        assert btn.get('aria-label') == 'Close chatbot', \
            'Close button must have aria-label="Close chatbot"'

    def test_close_button_has_aria_controls(self, base_soup):
        """Close button has aria-controls pointing to chatbot-panel."""
        btn = base_soup.find('button', class_='chatbot-minimize')
        assert btn.get('aria-controls') == 'chatbot-panel', \
            'Close button must have aria-controls="chatbot-panel"'

    def test_close_button_contains_x_symbol(self, base_soup):
        """Close button contains × symbol."""
        btn = base_soup.find('button', class_='chatbot-minimize')
        assert '×' in btn.get_text(), 'Close button must contain × symbol'

    def test_close_button_not_hidden_by_css(self, chatbot_css):
        """No CSS rule hides .chatbot-minimize at any breakpoint."""
        # Check that chatbot-minimize is never set to display:none or visibility:hidden
        minimize_blocks = re.findall(
            r'\.chatbot-minimize[^{]*\{([^}]+)\}', chatbot_css
        )
        for block in minimize_blocks:
            assert 'display: none' not in block and 'display:none' not in block, \
                '.chatbot-minimize must never have display:none'
            assert 'visibility: hidden' not in block and 'visibility:hidden' not in block, \
                '.chatbot-minimize must never have visibility:hidden'

    def test_close_button_is_keyboard_focusable(self, chatbot_css):
        """Close button has focus styles (keyboard accessible)."""
        assert '.chatbot-minimize:focus' in chatbot_css, \
            '.chatbot-minimize must have :focus styles for keyboard accessibility'


# ============================================
# FAB Hidden When Chatbot Open Tests
# ============================================

class TestFabHiddenWhenOpen:
    """FAB must be hidden when chatbot is open on ALL viewports."""

    def test_fab_hidden_base_rule(self, chatbot_css):
        """Base rule hides FAB when aria-expanded='true' (opacity:0, pointer-events:none)."""
        # Find the base (non-media-query) rule for .chatbot-fab[aria-expanded="true"]
        match = re.search(
            r'\.chatbot-fab\[aria-expanded="true"\]\s*\{([^}]+)\}',
            chatbot_css
        )
        assert match, 'Base rule for .chatbot-fab[aria-expanded="true"] must exist'
        rule_body = match.group(1)
        assert 'opacity' in rule_body and '0' in rule_body, \
            'FAB must have opacity:0 when expanded'
        assert 'pointer-events' in rule_body and 'none' in rule_body, \
            'FAB must have pointer-events:none when expanded'

    def test_no_desktop_fab_visible_override(self, chatbot_css):
        """No media query overrides FAB to be visible when expanded."""
        # Extract all media query blocks
        media_blocks = re.findall(
            r'@media[^{]+\{((?:[^{}]|\{[^}]*\})*)\}',
            chatbot_css
        )
        for block in media_blocks:
            # Check if any rule re-enables FAB when expanded
            fab_expanded = re.findall(
                r'\.chatbot-fab\[aria-expanded="true"\]\s*\{([^}]+)\}',
                block
            )
            for rule_body in fab_expanded:
                assert 'opacity: 1' not in rule_body and 'opacity:1' not in rule_body, \
                    'No media query should override FAB opacity to 1 when expanded'
                assert 'pointer-events: auto' not in rule_body and 'pointer-events:auto' not in rule_body, \
                    'No media query should override FAB pointer-events to auto when expanded'

    def test_no_fab_shift_right_when_expanded(self, chatbot_css):
        """FAB should not shift position when expanded (old behavior removed)."""
        media_blocks = re.findall(
            r'@media[^{]+\{((?:[^{}]|\{[^}]*\})*)\}',
            chatbot_css
        )
        for block in media_blocks:
            fab_expanded = re.findall(
                r'\.chatbot-fab\[aria-expanded="true"\]\s*\{([^}]+)\}',
                block
            )
            for rule_body in fab_expanded:
                assert 'right: 376px' not in rule_body, \
                    'FAB should not shift to right:376px when expanded (old tablet behavior)'
                assert 'right: 456px' not in rule_body, \
                    'FAB should not shift to right:456px when expanded (old desktop behavior)'


# ============================================
# FAB Reappears After Close Tests
# ============================================

class TestFabReappearsAfterClose:
    """FAB must reappear when chatbot is closed."""

    def test_close_sets_aria_expanded_false(self, chatbot_js):
        """closeChatbot() sets aria-expanded='false' on FAB."""
        close_match = re.search(
            r'closeChatbot\s*\(\)\s*\{([\s\S]*?)\n    \}',
            chatbot_js
        )
        assert close_match, 'closeChatbot method must exist'
        body = close_match.group(1)
        assert "aria-expanded" in body and "'false'" in body, \
            'closeChatbot must set aria-expanded to false'

    def test_close_hides_panel(self, chatbot_js):
        """closeChatbot() sets aria-hidden='true' on panel."""
        close_match = re.search(
            r'closeChatbot\s*\(\)\s*\{([\s\S]*?)\n    \}',
            chatbot_js
        )
        body = close_match.group(1)
        assert "aria-hidden" in body and "'true'" in body, \
            'closeChatbot must set panel aria-hidden to true'

    def test_close_returns_focus_to_fab(self, chatbot_js):
        """closeChatbot() returns focus to FAB."""
        close_match = re.search(
            r'closeChatbot\s*\(\)\s*\{([\s\S]*?)\n    \}',
            chatbot_js
        )
        body = close_match.group(1)
        assert 'this.fab.focus()' in body, \
            'closeChatbot must return focus to FAB'


# ============================================
# Re-opening After Close Tests
# ============================================

class TestReopenAfterClose:
    """Clicking FAB after closing chatbot must re-open the panel."""

    def test_expand_sets_aria_expanded_true(self, chatbot_js):
        """expand() sets aria-expanded='true' on FAB."""
        expand_match = re.search(
            r'expand\s*\(\)\s*\{([\s\S]*?)\n    \}',
            chatbot_js
        )
        assert expand_match, 'expand method must exist'
        body = expand_match.group(1)
        assert "aria-expanded" in body and "'true'" in body, \
            'expand must set aria-expanded to true'

    def test_expand_shows_panel(self, chatbot_js):
        """expand() sets aria-hidden='false' on panel."""
        expand_match = re.search(
            r'expand\s*\(\)\s*\{([\s\S]*?)\n    \}',
            chatbot_js
        )
        body = expand_match.group(1)
        assert "aria-hidden" in body and "'false'" in body, \
            'expand must set panel aria-hidden to false'


# ============================================
# Keyboard Dismiss Tests
# ============================================

class TestKeyboardDismiss:
    """Escape key must close the chatbot."""

    def test_escape_key_handler_exists(self, chatbot_js):
        """Document keydown listener checks for Escape when expanded."""
        assert "'Escape'" in chatbot_js or '"Escape"' in chatbot_js, \
            'Escape key handler must exist'
        assert 'closeChatbot' in chatbot_js, \
            'Escape handler must call closeChatbot'


# ============================================
# Consistency Tests
# ============================================

class TestConsistentBehavior:
    """Behavior must be consistent across mobile, tablet, and desktop."""

    def test_no_viewport_specific_fab_expanded_overrides(self, chatbot_css):
        """No breakpoint-specific overrides for FAB expanded state exist."""
        # The only .chatbot-fab[aria-expanded="true"] rule should be the base one
        all_fab_expanded = re.findall(
            r'\.chatbot-fab\[aria-expanded="true"\]',
            chatbot_css
        )
        # Count occurrences — should be exactly 1 (the base rule)
        assert len(all_fab_expanded) == 1, \
            f'Expected exactly 1 .chatbot-fab[aria-expanded="true"] rule (base), found {len(all_fab_expanded)}'

    def test_minimize_button_wired_to_close(self, chatbot_js):
        """Minimize button click handler calls closeChatbot()."""
        assert 'this.minimizeBtn.addEventListener' in chatbot_js, \
            'minimizeBtn must have event listener'
        assert 'closeChatbot' in chatbot_js, \
            'minimizeBtn click must call closeChatbot'


# ============================================
# Security Tests
# ============================================

class TestSecurity:
    """No unsafe template filters added."""

    def test_no_safe_filter_in_chatbot_html(self, base_html):
        """No | safe filter on dynamic content near chatbot markup."""
        # Find chatbot section in base.html
        chatbot_start = base_html.find('id="chatbot-fab"')
        chatbot_end = base_html.find('</aside>', chatbot_start) if chatbot_start != -1 else -1
        if chatbot_start != -1 and chatbot_end != -1:
            chatbot_section = base_html[chatbot_start:chatbot_end]
            assert '| safe' not in chatbot_section, \
                'No | safe filter should be used in chatbot HTML section'


# ============================================
# CSS No Inline Styles Tests
# ============================================

class TestNoInlineStyles:
    """All hiding/showing must use CSS classes or aria attributes, not inline styles."""

    def test_js_does_not_inline_style_fab_display(self, chatbot_js):
        """JS does not set fab.style.display or fab.style.visibility."""
        assert 'this.fab.style.display' not in chatbot_js, \
            'FAB visibility must be controlled via aria attributes and CSS, not inline styles'
        assert 'this.fab.style.visibility' not in chatbot_js, \
            'FAB visibility must not use inline visibility style'
        assert 'this.fab.style.opacity' not in chatbot_js, \
            'FAB visibility must not use inline opacity style'
