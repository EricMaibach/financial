"""
Tests for US-258.3: Sentence-level drill-in — desktop text selection toolbar.

Verifies:
- Toolbar DOM element exists in base.html with role="toolbar"
- Toolbar has exactly two buttons: Copy and Ask AI (standard <button> elements)
- Copy button has correct class and aria-label
- Ask AI button has correct class and aria-label, contains SVG sparkle icon
- Discoverability hints exist in index.html below briefing section
- Desktop hint has class ai-briefing-hint--desktop
- Mobile hint has class ai-briefing-hint--mobile
- ai-briefing-toolbar.css exists and has correct styles
- ai-briefing-toolbar.js exists and binds to briefing-narrative
- chatbot.js includes openWithTextDrillIn method
- base.html includes ai-briefing-toolbar.css and ai-briefing-toolbar.js
- dashboard.py passes briefing_text to system prompt
"""

import os
import re
import pytest

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers', 'templates')
STATIC_CSS = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers', 'static', 'css', 'components')
STATIC_JS = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers', 'static', 'js', 'components')
DASHBOARD_PY = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers', 'dashboard.py')

BASE_HTML = os.path.join(TEMPLATES_DIR, 'base.html')
INDEX_HTML = os.path.join(TEMPLATES_DIR, 'index.html')
TOOLBAR_CSS = os.path.join(STATIC_CSS, 'ai-briefing-toolbar.css')
TOOLBAR_JS = os.path.join(STATIC_JS, 'ai-briefing-toolbar.js')
CHATBOT_JS = os.path.join(STATIC_JS, 'chatbot.js')


@pytest.fixture(scope='module')
def base_html():
    with open(BASE_HTML) as f:
        return f.read()


@pytest.fixture(scope='module')
def index_html():
    with open(INDEX_HTML) as f:
        return f.read()


@pytest.fixture(scope='module')
def toolbar_css():
    with open(TOOLBAR_CSS) as f:
        return f.read()


@pytest.fixture(scope='module')
def toolbar_js():
    with open(TOOLBAR_JS) as f:
        return f.read()


@pytest.fixture(scope='module')
def chatbot_js():
    with open(CHATBOT_JS) as f:
        return f.read()


@pytest.fixture(scope='module')
def dashboard_py():
    with open(DASHBOARD_PY) as f:
        return f.read()


# ── Toolbar DOM structure in base.html ─────────────────────────────────────

class TestToolbarDOM:

    def test_toolbar_element_exists(self, base_html):
        """Floating toolbar element exists in DOM (hidden by default)."""
        assert 'id="ai-briefing-toolbar"' in base_html

    def test_toolbar_has_role_toolbar(self, base_html):
        """Toolbar has role="toolbar"."""
        assert 'role="toolbar"' in base_html

    def test_toolbar_has_aria_label(self, base_html):
        """Toolbar has aria-label for accessibility."""
        # Check the toolbar div has aria-label
        match = re.search(r'id="ai-briefing-toolbar"[^>]*aria-label=', base_html)
        assert match, 'Toolbar should have aria-label'

    def test_toolbar_copy_button_is_button_element(self, base_html):
        """Copy is a standard <button> element (not <a> or <div>)."""
        assert 'ai-briefing-toolbar__copy' in base_html
        # Verify the copy element uses <button> tag
        copy_match = re.search(
            r'<button[^>]*class="[^"]*ai-briefing-toolbar__btn[^"]*ai-briefing-toolbar__copy[^"]*"',
            base_html
        )
        assert copy_match, 'Copy should be a <button> element with ai-briefing-toolbar__copy class'

    def test_toolbar_ask_ai_button_is_button_element(self, base_html):
        """Ask AI is a standard <button> element."""
        assert 'ai-briefing-toolbar__ask-ai' in base_html
        ask_ai_match = re.search(
            r'<button[^>]*class="[^"]*ai-briefing-toolbar__btn[^"]*ai-briefing-toolbar__ask-ai[^"]*"',
            base_html
        )
        assert ask_ai_match, 'Ask AI should be a <button> element with ai-briefing-toolbar__ask-ai class'

    def test_toolbar_copy_button_has_aria_label(self, base_html):
        """Copy button has aria-label."""
        assert 'aria-label="Copy selected text"' in base_html

    def test_toolbar_ask_ai_button_has_aria_label(self, base_html):
        """Ask AI button has aria-label."""
        assert 'aria-label="Ask AI about selected text"' in base_html

    def test_toolbar_ask_ai_has_svg_icon(self, base_html):
        """Ask AI button contains an SVG sparkle icon."""
        # Find the toolbar section bounded by the surrounding comments
        toolbar_section = re.search(
            r'AI Briefing Toolbar.*?<!-- Chatbot',
            base_html,
            re.DOTALL
        )
        assert toolbar_section, 'Should find toolbar section in base.html'
        assert '<svg' in toolbar_section.group(), 'Toolbar should contain SVG sparkle icon'

    def test_toolbar_divider_exists(self, base_html):
        """Divider element exists between Copy and Ask AI."""
        assert 'ai-briefing-toolbar__divider' in base_html

    def test_toolbar_has_exactly_two_buttons(self, base_html):
        """Toolbar has exactly two buttons (Copy and Ask AI)."""
        toolbar_match = re.search(
            r'id="ai-briefing-toolbar"(.*?)</div>\s*\n\s*<!--',
            base_html,
            re.DOTALL
        )
        if not toolbar_match:
            # Try broader search
            toolbar_match = re.search(
                r'id="ai-briefing-toolbar"(.*?)<!-- Chatbot',
                base_html,
                re.DOTALL
            )
        assert toolbar_match, 'Should find toolbar section'
        toolbar_content = toolbar_match.group(1)
        button_count = len(re.findall(r'<button\b', toolbar_content))
        assert button_count == 2, f'Expected 2 buttons in toolbar, found {button_count}'


# ── Discoverability hints in index.html ────────────────────────────────────

class TestDiscoverabilityHints:

    def test_hints_container_exists(self, index_html):
        """Discoverability hints container exists below briefing section."""
        assert 'ai-briefing-hints' in index_html

    def test_desktop_hint_exists(self, index_html):
        """Desktop hint with class ai-briefing-hint--desktop is present."""
        assert 'ai-briefing-hint--desktop' in index_html

    def test_mobile_hint_exists(self, index_html):
        """Mobile hint with class ai-briefing-hint--mobile is present."""
        assert 'ai-briefing-hint--mobile' in index_html

    def test_desktop_hint_text(self, index_html):
        """Desktop hint text references text selection."""
        assert 'Select any text to ask AI' in index_html

    def test_mobile_hint_text(self, index_html):
        """Mobile hint references tapping."""
        assert 'Tap any sentence' in index_html

    def test_hints_are_below_briefing_content(self, index_html):
        """Hints appear after the briefing-content div, before next section."""
        briefing_pos = index_html.find('id="briefing-content"')
        hints_pos = index_html.find('ai-briefing-hints')
        movers_pos = index_html.find('id="movers-section"')
        assert briefing_pos < hints_pos < movers_pos, \
            'Hints should be between briefing-content and movers-section'

    def test_hints_have_sparkle_icon(self, index_html):
        """Hints contain sparkle SVG icon."""
        # The hints section should contain SVG elements
        hints_start = index_html.find('ai-briefing-hints')
        hints_end = index_html.find('</section>', hints_start)
        hints_section = index_html[hints_start:hints_end]
        assert '<svg' in hints_section, 'Hints should contain sparkle SVG icon'


# ── CSS file ───────────────────────────────────────────────────────────────

class TestToolbarCSS:

    def test_css_file_exists(self):
        """ai-briefing-toolbar.css exists."""
        assert os.path.exists(TOOLBAR_CSS)

    def test_toolbar_default_hidden(self, toolbar_css):
        """.ai-briefing-toolbar has display: none by default."""
        assert 'display: none' in toolbar_css

    def test_toolbar_visible_state(self, toolbar_css):
        """.ai-briefing-toolbar.is-visible sets display: flex."""
        assert '.ai-briefing-toolbar.is-visible' in toolbar_css
        assert 'display: flex' in toolbar_css

    def test_toolbar_hidden_on_coarse_pointer(self, toolbar_css):
        """Toolbar is hidden on pointer:coarse devices."""
        assert '@media (pointer: coarse)' in toolbar_css
        # The coarse media query should hide the toolbar
        coarse_match = re.search(
            r'@media \(pointer: coarse\)\s*\{[^}]*\.ai-briefing-toolbar[^}]*display: none',
            toolbar_css,
            re.DOTALL
        )
        assert coarse_match, 'Toolbar should be display:none on pointer:coarse'

    def test_desktop_hint_visible_by_default(self, toolbar_css):
        """.ai-briefing-hint--desktop is visible by default."""
        match = re.search(
            r'\.ai-briefing-hint--desktop\s*\{[^}]*display:\s*(flex|block)',
            toolbar_css
        )
        assert match, 'Desktop hint should be display:flex/block by default'

    def test_mobile_hint_hidden_by_default(self, toolbar_css):
        """.ai-briefing-hint--mobile is hidden by default."""
        match = re.search(
            r'\.ai-briefing-hint--mobile\s*\{[^}]*display:\s*none',
            toolbar_css
        )
        assert match, 'Mobile hint should be display:none by default'

    def test_desktop_hint_hidden_on_coarse(self, toolbar_css):
        """Desktop hint hidden on pointer:coarse."""
        # Find all content within @media (pointer: coarse) blocks
        coarse_content = ' '.join(re.findall(
            r'@media \(pointer: coarse\)\s*\{(.*?)\}(?!\s*\S)',
            toolbar_css,
            re.DOTALL
        ))
        if not coarse_content:
            # Fallback: grab everything after @media (pointer: coarse) until outer closing brace
            match = re.search(r'@media \(pointer: coarse\)(.*)', toolbar_css, re.DOTALL)
            coarse_content = match.group(1) if match else ''
        assert 'ai-briefing-hint--desktop' in coarse_content

    def test_mobile_hint_shown_on_coarse(self, toolbar_css):
        """Mobile hint shown on pointer:coarse."""
        coarse_content = ' '.join(re.findall(
            r'@media \(pointer: coarse\)\s*\{(.*?)\}(?!\s*\S)',
            toolbar_css,
            re.DOTALL
        ))
        if not coarse_content:
            match = re.search(r'@media \(pointer: coarse\)(.*)', toolbar_css, re.DOTALL)
            coarse_content = match.group(1) if match else ''
        assert 'ai-briefing-hint--mobile' in coarse_content

    def test_toolbar_border_radius(self, toolbar_css):
        """Toolbar has 4px border-radius."""
        assert 'border-radius: 4px' in toolbar_css

    def test_toolbar_has_shadow(self, toolbar_css):
        """Toolbar has box-shadow."""
        assert 'box-shadow' in toolbar_css

    def test_ask_ai_btn_uses_ai_color(self, toolbar_css):
        """Ask AI button uses --ai-color token."""
        assert 'ai-briefing-toolbar__ask-ai' in toolbar_css
        assert '--ai-color' in toolbar_css


# ── JS file ────────────────────────────────────────────────────────────────

class TestToolbarJS:

    def test_js_file_exists(self):
        """ai-briefing-toolbar.js exists."""
        assert os.path.exists(TOOLBAR_JS)

    def test_binds_to_briefing_narrative(self, toolbar_js):
        """JS listens for events on #briefing-narrative."""
        assert 'briefing-narrative' in toolbar_js

    def test_uses_mouseup_event(self, toolbar_js):
        """JS uses mouseup event for selection detection."""
        assert 'mouseup' in toolbar_js

    def test_checks_selection_within_briefing(self, toolbar_js):
        """JS verifies selection is within the briefing block."""
        assert 'isSelectionWithin' in toolbar_js or 'contains' in toolbar_js

    def test_hides_on_scroll(self, toolbar_js):
        """JS hides toolbar on scroll."""
        assert 'scroll' in toolbar_js

    def test_hides_on_escape(self, toolbar_js):
        """JS hides toolbar on Escape key."""
        assert 'Escape' in toolbar_js

    def test_copy_button_handler(self, toolbar_js):
        """JS handles Copy button click."""
        assert 'ai-briefing-toolbar__copy' in toolbar_js
        assert 'clipboard' in toolbar_js or 'execCommand' in toolbar_js

    def test_ask_ai_button_handler(self, toolbar_js):
        """JS handles Ask AI button click."""
        assert 'ai-briefing-toolbar__ask-ai' in toolbar_js
        assert 'openWithTextDrillIn' in toolbar_js

    def test_gets_full_briefing_text(self, toolbar_js):
        """JS reads full briefing text for context."""
        assert 'briefing-narrative' in toolbar_js
        assert 'innerText' in toolbar_js or 'textContent' in toolbar_js

    def test_empty_selection_does_not_show_toolbar(self, toolbar_js):
        """JS does not show toolbar for empty selection."""
        # JS should check that selected text is non-empty
        assert "selectedText" in toolbar_js or "toString" in toolbar_js

    def test_positions_above_selection(self, toolbar_js):
        """JS positions toolbar above selection (not below)."""
        assert 'getBoundingClientRect' in toolbar_js
        # Should subtract from top (placing above)
        assert 'rect.top' in toolbar_js

    def test_clamps_to_viewport(self, toolbar_js):
        """JS clamps toolbar position to stay within viewport."""
        assert 'viewport' in toolbar_js.lower() or 'innerWidth' in toolbar_js

    def test_uses_is_visible_class(self, toolbar_js):
        """JS shows toolbar by adding is-visible class."""
        assert 'is-visible' in toolbar_js

    def test_passes_briefing_text_to_widget(self, toolbar_js):
        """JS passes briefing text to chatbot widget."""
        assert 'briefingText' in toolbar_js or 'briefing_text' in toolbar_js

    def test_handles_missing_chatbot_widget(self, toolbar_js):
        """JS handles case where chatbotWidget is unavailable."""
        assert 'chatbotWidget' in toolbar_js
        assert 'console.warn' in toolbar_js


# ── chatbot.js method ──────────────────────────────────────────────────────

class TestChatbotDrillIn:

    def test_open_with_text_drill_in_method_exists(self, chatbot_js):
        """chatbot.js has openWithTextDrillIn method."""
        assert 'openWithTextDrillIn' in chatbot_js

    def test_drill_in_fires_api_call(self, chatbot_js):
        """openWithTextDrillIn fires a real AI API call."""
        # Method should call fetch('/api/chatbot'...)
        assert "'/api/chatbot'" in chatbot_js or '"/api/chatbot"' in chatbot_js

    def test_drill_in_passes_briefing_text_context(self, chatbot_js):
        """openWithTextDrillIn passes briefing_text in context."""
        assert 'briefing_text' in chatbot_js

    def test_drill_in_shows_typing_indicator(self, chatbot_js):
        """openWithTextDrillIn shows typing indicator while AI responds."""
        # The method should call showTypingIndicator
        drill_in_section = chatbot_js[chatbot_js.find('openWithTextDrillIn'):]
        # Find the method body (up to next method at same level or end of class)
        assert 'showTypingIndicator' in drill_in_section

    def test_drill_in_adds_user_message(self, chatbot_js):
        """openWithTextDrillIn adds user message to chat."""
        drill_in_section = chatbot_js[chatbot_js.find('openWithTextDrillIn'):]
        assert 'addMessage' in drill_in_section

    def test_drill_in_handles_ai_unavailable_error(self, chatbot_js):
        """openWithTextDrillIn handles AI_UNAVAILABLE gracefully."""
        drill_in_section = chatbot_js[chatbot_js.find('openWithTextDrillIn'):]
        assert 'AI_UNAVAILABLE' in drill_in_section or 'showError' in drill_in_section

    def test_drill_in_expands_chatbot(self, chatbot_js):
        """openWithTextDrillIn expands the chatbot panel."""
        drill_in_section = chatbot_js[chatbot_js.find('openWithTextDrillIn'):]
        assert 'expand' in drill_in_section

    def test_drill_in_passes_section_context(self, chatbot_js):
        """openWithTextDrillIn passes briefing-section context to API."""
        drill_in_section = chatbot_js[chatbot_js.find('openWithTextDrillIn'):]
        assert 'briefing-section' in drill_in_section


# ── base.html includes ─────────────────────────────────────────────────────

class TestBaseHTMLIncludes:

    def test_css_included_in_base(self, base_html):
        """base.html includes ai-briefing-toolbar.css."""
        assert 'ai-briefing-toolbar.css' in base_html

    def test_js_included_in_base(self, base_html):
        """base.html includes ai-briefing-toolbar.js."""
        assert 'ai-briefing-toolbar.js' in base_html

    def test_toolbar_js_loaded_after_chatbot_js(self, base_html):
        """ai-briefing-toolbar.js is loaded after chatbot.js (dependency order)."""
        chatbot_pos = base_html.find('chatbot.js')
        toolbar_pos = base_html.find('ai-briefing-toolbar.js')
        assert chatbot_pos < toolbar_pos, \
            'ai-briefing-toolbar.js must be loaded after chatbot.js'


# ── Backend: dashboard.py ──────────────────────────────────────────────────

class TestBackendBriefingContext:

    def test_briefing_text_extracted_from_context(self, dashboard_py):
        """dashboard.py extracts briefing_text from context."""
        assert "briefing_text" in dashboard_py
        assert "context.get('briefing_text')" in dashboard_py

    def test_briefing_text_injected_into_system_prompt(self, dashboard_py):
        """dashboard.py injects briefing_text into system prompt when present."""
        # The api_chatbot function should use briefing_text in the system prompt
        assert 'briefing_context' in dashboard_py
        assert 'system_prompt' in dashboard_py
        # briefing_context should be referenced in the system_prompt construction
        # Find system_prompt = ... and verify briefing_context is nearby
        system_prompt_idx = dashboard_py.find('system_prompt = (')
        assert system_prompt_idx != -1, 'system_prompt construction not found'
        # briefing_context should be defined before system_prompt
        briefing_ctx_idx = dashboard_py.find('briefing_context')
        assert briefing_ctx_idx < system_prompt_idx, \
            'briefing_context should be defined before system_prompt'

    def test_briefing_text_not_required(self, dashboard_py):
        """dashboard.py handles missing briefing_text gracefully (not required)."""
        # briefing_text should use .get() with a default
        assert "context.get('briefing_text') or None" in dashboard_py or \
               "context.get('briefing_text', None)" in dashboard_py or \
               "context.get('briefing_text')" in dashboard_py
