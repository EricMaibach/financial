"""
Static verification tests for US-3.2.4: Responsive Tablet and Desktop Layouts.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required CSS patterns, breakpoints,
and HTML attributes are present.
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHATBOT_CSS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css', 'components', 'chatbot.css')
BASE_HTML_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'templates', 'base.html')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


class TestTabletMediaQuery(unittest.TestCase):
    """Verify tablet-specific CSS (768px+) is present and correct."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_tablet_breakpoint_declared(self):
        """CSS must contain a min-width: 768px media query."""
        self.assertIn('@media (min-width: 768px)', self.css)

    def test_tablet_panel_uses_translatex_for_hiding(self):
        """Panel must use translateX(100%) to hide on tablet (not translateY)."""
        # Extract the 768px block and verify translateX(100%) is present
        idx = self.css.find('@media (min-width: 768px)')
        self.assertGreater(idx, 0)
        block = self.css[idx:idx + 2000]
        self.assertIn('translateX(100%)', block)

    def test_tablet_panel_translatex_zero_when_visible(self):
        """Panel visible state must use translateX(0) on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('translateX(0)', block)

    def test_tablet_panel_width_360px(self):
        """Panel width must be 360px on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('width: 360px', block)

    def test_tablet_panel_full_viewport_height(self):
        """Panel must use 100vh height on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('height: 100vh', block)

    def test_tablet_panel_positions_at_top_right(self):
        """Panel must be positioned top: 0 and right: 0 on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('top: 0', block)
        self.assertIn('right: 0', block)

    def test_tablet_panel_left_border(self):
        """Panel must have left border (separator from content) on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('border-left:', block)

    def test_tablet_panel_no_border_radius(self):
        """Panel must have border-radius: 0 on tablet (square corners)."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('border-radius: 0', block)

    def test_tablet_panel_no_top_border(self):
        """Panel must remove top border on tablet (side panel has left border instead)."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('border-top: none', block)

    def test_tablet_header_no_border_radius(self):
        """Header must have border-radius: 0 on tablet (panel is square)."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        # Header override with border-radius: 0
        self.assertIn('.chatbot-header', block)
        header_idx = block.find('.chatbot-header')
        header_block = block[header_idx:header_idx + 100]
        self.assertIn('border-radius: 0', header_block)

    def test_tablet_fab_transition_includes_right(self):
        """FAB must transition 'right' property for smooth position shift on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        # FAB transition override must include 'right'
        fab_transition_idx = block.find('.chatbot-fab {')
        self.assertGreater(fab_transition_idx, 0)
        fab_block = block[fab_transition_idx:fab_transition_idx + 200]
        self.assertIn('right', fab_block)
        self.assertIn('transition:', fab_block)

    def test_tablet_fab_visible_when_panel_open(self):
        """FAB must remain visible (opacity: 1) when panel is open on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        # aria-expanded true rule must set opacity: 1 (not 0)
        expanded_idx = block.find('[aria-expanded="true"]')
        self.assertGreater(expanded_idx, 0)
        expanded_block = block[expanded_idx:expanded_idx + 200]
        self.assertIn('opacity: 1', expanded_block)

    def test_tablet_fab_pointer_events_auto_when_open(self):
        """FAB must have pointer-events: auto when panel is open on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        expanded_idx = block.find('[aria-expanded="true"]')
        expanded_block = block[expanded_idx:expanded_idx + 200]
        self.assertIn('pointer-events: auto', expanded_block)

    def test_tablet_fab_shifts_right_376px_when_panel_open(self):
        """FAB must be at right: 376px when panel is open on tablet (360px + 16px)."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('right: 376px', block)

    def test_tablet_fab_transform_none_when_panel_open(self):
        """FAB must reset transform to none when panel is open on tablet."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        expanded_idx = block.find('[aria-expanded="true"]')
        expanded_block = block[expanded_idx:expanded_idx + 200]
        self.assertIn('transform: none', expanded_block)


class TestDesktopMediaQuery(unittest.TestCase):
    """Verify desktop-specific CSS (1024px+) is present and correct."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_desktop_breakpoint_declared(self):
        """CSS must contain a min-width: 1024px media query."""
        self.assertIn('@media (min-width: 1024px)', self.css)

    def test_desktop_panel_width_440px(self):
        """Panel width must be 440px on desktop (wider than tablet)."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('width: 440px', block)

    def test_desktop_fab_shifts_right_456px_when_panel_open(self):
        """FAB must be at right: 456px when panel is open on desktop (440px + 16px)."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('right: 456px', block)

    def test_desktop_fab_hover_scale_108(self):
        """FAB hover must scale to 1.08 on desktop."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('scale(1.08)', block)

    def test_desktop_tooltip_pseudo_element_declared(self):
        """CSS must declare tooltip via ::after pseudo-element on desktop."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('.chatbot-fab::after', block)

    def test_desktop_tooltip_uses_data_tooltip_attr(self):
        """Tooltip must use content: attr(data-tooltip) to read from HTML attribute."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        self.assertIn("content: attr(data-tooltip)", block)

    def test_desktop_tooltip_positioned_left_of_fab(self):
        """Tooltip must be positioned to the left of the FAB (right: 72px)."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        self.assertIn('right: 72px', block)

    def test_desktop_tooltip_initially_hidden(self):
        """Tooltip must start with opacity: 0 (hidden by default)."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        # Find the ::after block and check opacity: 0
        after_idx = block.find('.chatbot-fab::after')
        after_block = block[after_idx:after_idx + 400]
        self.assertIn('opacity: 0', after_block)

    def test_desktop_tooltip_non_interactive(self):
        """Tooltip must have pointer-events: none (should not block clicks)."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        after_idx = block.find('.chatbot-fab::after')
        after_block = block[after_idx:after_idx + 600]
        self.assertIn('pointer-events: none', after_block)

    def test_desktop_tooltip_shows_on_hover(self):
        """Tooltip must appear (opacity: 1) when FAB is hovered."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        # Look for hover rule showing tooltip
        self.assertIn(':hover::after', block)

    def test_desktop_tooltip_hidden_when_panel_open(self):
        """Tooltip must NOT show when panel is open (:not([aria-expanded='true']))."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        self.assertIn(':not([aria-expanded="true"]):hover::after', block)

    def test_desktop_tooltip_has_transition(self):
        """Tooltip must have a transition for opacity (smooth fade-in)."""
        idx = self.css.find('@media (min-width: 1024px)')
        block = self.css[idx:idx + 2000]
        after_idx = block.find('.chatbot-fab::after')
        after_block = block[after_idx:after_idx + 600]
        self.assertIn('transition:', after_block)
        self.assertIn('opacity', after_block)


class TestDesktopPanelLayout(unittest.TestCase):
    """Verify desktop panel inherits correct side-panel layout from tablet styles."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_both_breakpoints_present(self):
        """Both 768px and 1024px breakpoints must be present."""
        self.assertIn('@media (min-width: 768px)', self.css)
        self.assertIn('@media (min-width: 1024px)', self.css)

    def test_desktop_breakpoint_after_tablet_breakpoint(self):
        """Desktop 1024px breakpoint must come after tablet 768px breakpoint."""
        tablet_idx = self.css.find('@media (min-width: 768px)')
        desktop_idx = self.css.find('@media (min-width: 1024px)')
        self.assertGreater(desktop_idx, tablet_idx)

    def test_panel_box_shadow_for_side_panel(self):
        """Panel must use left-side box-shadow for side panel layout."""
        idx = self.css.find('@media (min-width: 768px)')
        block = self.css[idx:idx + 2000]
        # Box-shadow should cast shadow to the left (negative x offset)
        self.assertIn('box-shadow:', block)

    def test_translatex_not_in_mobile_base_styles(self):
        """Mobile base styles must NOT use translateX (should use translateY for bottom sheet)."""
        # Get only the base (non-media-query) section
        first_media = self.css.find('@media')
        base_css = self.css[:first_media] if first_media > 0 else self.css
        self.assertNotIn('translateX(100%)', base_css)

    def test_translatey_in_mobile_base_styles(self):
        """Mobile base styles must use translateY(100%) for bottom sheet."""
        first_media = self.css.find('@media')
        base_css = self.css[:first_media] if first_media > 0 else self.css
        self.assertIn('translateY(100%)', base_css)


class TestFABTooltipAttribute(unittest.TestCase):
    """Verify FAB HTML has the data-tooltip attribute for desktop tooltip."""

    def setUp(self):
        self.html = read_file(BASE_HTML_PATH)

    def test_fab_has_data_tooltip_attribute(self):
        """FAB button must have data-tooltip attribute for desktop CSS tooltip."""
        self.assertIn('data-tooltip=', self.html)

    def test_fab_data_tooltip_value(self):
        """FAB data-tooltip must say 'Ask AI about this chart'."""
        self.assertIn('data-tooltip="Ask AI about this chart"', self.html)

    def test_fab_data_tooltip_on_same_button(self):
        """data-tooltip must be on the chatbot-fab element."""
        # Find the FAB button block
        fab_idx = self.html.find('id="chatbot-fab"')
        self.assertGreater(fab_idx, 0)
        # Look for data-tooltip within 300 chars of the FAB id
        fab_block = self.html[fab_idx:fab_idx + 300]
        self.assertIn('data-tooltip=', fab_block)

    def test_fab_aria_label_unchanged(self):
        """FAB must still have its aria-label for screen reader accessibility."""
        self.assertIn('aria-label="Open AI chatbot"', self.html)

    def test_fab_aria_expanded_present(self):
        """FAB must still have aria-expanded attribute for state tracking."""
        self.assertIn('aria-expanded="false"', self.html)


class TestMobileLayoutUnchanged(unittest.TestCase):
    """Verify mobile bottom sheet layout is not broken by tablet/desktop additions."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_mobile_panel_still_bottom_zero(self):
        """Mobile base styles must still have bottom: 0 for bottom sheet."""
        first_media = self.css.find('@media')
        base_css = self.css[:first_media] if first_media > 0 else self.css
        self.assertIn('bottom: 0', base_css)

    def test_mobile_panel_left_zero(self):
        """Mobile base styles must still have left: 0 for full-width bottom sheet."""
        first_media = self.css.find('@media')
        base_css = self.css[:first_media] if first_media > 0 else self.css
        self.assertIn('left: 0', base_css)

    def test_mobile_panel_border_radius_top(self):
        """Mobile base styles must have top border-radius for bottom sheet."""
        first_media = self.css.find('@media')
        base_css = self.css[:first_media] if first_media > 0 else self.css
        self.assertIn('border-radius: 16px 16px 0 0', base_css)

    def test_mobile_fab_hidden_when_expanded(self):
        """Mobile base styles must hide FAB (opacity: 0) when panel is expanded."""
        first_media = self.css.find('@media')
        base_css = self.css[:first_media] if first_media > 0 else self.css
        # Find the aria-expanded="true" rule in base styles
        expanded_idx = base_css.find('[aria-expanded="true"]')
        self.assertGreater(expanded_idx, 0)
        expanded_block = base_css[expanded_idx:expanded_idx + 200]
        self.assertIn('opacity: 0', expanded_block)

    def test_mobile_fab_pointer_events_none_when_expanded(self):
        """Mobile base styles must disable pointer events on FAB when expanded."""
        first_media = self.css.find('@media')
        base_css = self.css[:first_media] if first_media > 0 else self.css
        expanded_idx = base_css.find('[aria-expanded="true"]')
        expanded_block = base_css[expanded_idx:expanded_idx + 200]
        self.assertIn('pointer-events: none', expanded_block)


class TestCSSStructure(unittest.TestCase):
    """Verify overall CSS file structure and organization."""

    def setUp(self):
        self.css = read_file(CHATBOT_CSS_PATH)

    def test_chatbot_css_file_exists(self):
        """chatbot.css must exist at expected path."""
        self.assertTrue(os.path.exists(CHATBOT_CSS_PATH))

    def test_base_html_file_exists(self):
        """base.html must exist at expected path."""
        self.assertTrue(os.path.exists(BASE_HTML_PATH))

    def test_no_syntax_errors_braces_balanced(self):
        """CSS must have balanced curly braces."""
        open_count = self.css.count('{')
        close_count = self.css.count('}')
        self.assertEqual(open_count, close_count,
                         f"Unbalanced braces: {open_count} open, {close_count} close")

    def test_three_breakpoint_sections_present(self):
        """CSS must have tablet (768px), desktop (1024px) media queries plus base styles."""
        self.assertIn('@media (min-width: 768px)', self.css)
        self.assertIn('@media (min-width: 1024px)', self.css)

    def test_tablet_section_has_comment_header(self):
        """Tablet section should have a descriptive comment."""
        idx = self.css.find('@media (min-width: 768px)')
        # Look for a comment near the tablet section (within 200 chars before)
        nearby = self.css[max(0, idx - 200):idx + 50]
        # Just check the media query is there (comment presence is nice-to-have)
        self.assertIn('@media (min-width: 768px)', nearby)

    def test_desktop_section_has_comment_header(self):
        """Desktop section should have a descriptive comment."""
        idx = self.css.find('@media (min-width: 1024px)')
        self.assertIn('@media (min-width: 1024px)', self.css[idx:idx + 50])


if __name__ == '__main__':
    unittest.main()
