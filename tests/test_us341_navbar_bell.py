"""
Static verification tests for US-3.4.1: Add bell icon with unread count badge to navbar.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required HTML structure, CSS, and
accessibility attributes are present per the design spec.
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_HTML_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'templates', 'base.html')
BELL_CSS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css', 'components', 'navbar-bell.css')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


class TestBellCSSFileExists(unittest.TestCase):
    """CSS component file for navbar bell must exist and be linked."""

    def test_bell_css_file_exists(self):
        """navbar-bell.css must exist at the expected path."""
        self.assertTrue(os.path.exists(BELL_CSS_PATH), f"Missing file: {BELL_CSS_PATH}")

    def test_bell_css_linked_in_base_html(self):
        """base.html must include a link to navbar-bell.css."""
        html = read_file(BASE_HTML_PATH)
        self.assertIn('navbar-bell.css', html)


class TestBellCSSStyles(unittest.TestCase):
    """CSS for navbar bell must meet design spec requirements."""

    def setUp(self):
        self.css = read_file(BELL_CSS_PATH)

    def test_bell_btn_class_defined(self):
        """.navbar-bell-btn class must be defined."""
        self.assertIn('.navbar-bell-btn', self.css)

    def test_bell_btn_position_relative(self):
        """Bell wrapper must use position: relative to anchor the badge."""
        self.assertIn('position: relative', self.css)

    def test_bell_btn_display_inline_flex(self):
        """Bell wrapper must use inline-flex display."""
        self.assertIn('display: inline-flex', self.css)

    def test_bell_btn_padding_for_touch_target(self):
        """Bell button must have padding to achieve ≥44px touch target."""
        self.assertIn('padding:', self.css)

    def test_bell_btn_default_opacity_75(self):
        """Bell must use 75% white opacity at rest."""
        self.assertIn('rgba(255, 255, 255, 0.75)', self.css)

    def test_bell_btn_hover_full_opacity(self):
        """Bell must transition to 100% white on hover."""
        self.assertIn('.navbar-bell-btn:hover', self.css)
        self.assertIn('#ffffff', self.css)

    def test_bell_btn_active_class(self):
        """.navbar-bell-btn.active must be styled (for /alerts page)."""
        self.assertIn('.navbar-bell-btn.active', self.css)

    def test_bell_btn_unread_class(self):
        """.navbar-bell-btn--unread must be styled (for unread > 0)."""
        self.assertIn('.navbar-bell-btn--unread', self.css)

    def test_bell_btn_transition_150ms(self):
        """Bell must have a 150ms transition for smooth hover."""
        self.assertIn('150ms', self.css)

    def test_badge_class_defined(self):
        """.navbar-bell-badge class must be defined."""
        self.assertIn('.navbar-bell-badge', self.css)

    def test_badge_position_absolute(self):
        """Badge must use position: absolute for top-right overlay."""
        self.assertIn('position: absolute', self.css)

    def test_badge_danger_color(self):
        """Badge must use danger-600 (#DC2626) background color."""
        self.assertIn('#DC2626', self.css)

    def test_badge_white_text(self):
        """Badge text must be white (#ffffff)."""
        # Check for white color in badge definition
        css = self.css
        badge_idx = css.find('.navbar-bell-badge')
        self.assertGreater(badge_idx, 0)
        badge_block = css[badge_idx:badge_idx + 500]
        self.assertIn('#ffffff', badge_block)

    def test_badge_font_size_10px(self):
        """Badge text must be 10px font size."""
        self.assertIn('font-size: 10px', self.css)

    def test_badge_font_weight_bold(self):
        """Badge text must be font-weight: 700."""
        self.assertIn('font-weight: 700', self.css)

    def test_badge_border_for_visual_separation(self):
        """Badge must have border to separate from navbar background."""
        self.assertIn('border:', self.css)

    def test_badge_border_matches_navbar_dark(self):
        """Badge border must use Bootstrap bg-dark color (#212529)."""
        self.assertIn('#212529', self.css)

    def test_badge_min_width_16px(self):
        """Badge must have min-width: 16px for circular shape."""
        self.assertIn('min-width: 16px', self.css)

    def test_badge_height_16px(self):
        """Badge must have height: 16px."""
        self.assertIn('height: 16px', self.css)

    def test_badge_border_radius(self):
        """Badge must have border-radius for circular/pill shape."""
        self.assertIn('border-radius:', self.css)


class TestBellHTMLStructure(unittest.TestCase):
    """HTML structure in base.html must match spec requirements."""

    def setUp(self):
        self.html = read_file(BASE_HTML_PATH)

    def test_bell_wrapper_outside_collapse(self):
        """Bell wrapper must appear AFTER the collapse div closing tag."""
        collapse_close_idx = self.html.rfind('</div>', 0, self.html.find('<!-- Always-visible'))
        bell_idx = self.html.find('navbar-bell-btn')
        self.assertGreater(bell_idx, collapse_close_idx,
                           "Bell must be outside (after) the collapse navbar div")

    def test_bell_is_anchor_tag(self):
        """Bell button must be an <a> tag (direct link, no JS needed)."""
        # Find the bell btn class in HTML; look back up to 200 chars for the opening <a tag
        idx = self.html.find('navbar-bell-btn')
        self.assertGreater(idx, 0)
        opener = self.html[max(0, idx - 200):idx]
        self.assertIn('<a', opener)

    def test_bell_links_to_alert_history(self):
        """Bell must link to the alert_history URL endpoint."""
        self.assertIn("url_for('alert_history')", self.html)
        # Also confirm the bell btn has this link (not just the dropdown)
        idx = self.html.find('navbar-bell-btn')
        surrounding = self.html[max(0, idx - 300):idx + 300]
        self.assertIn("url_for('alert_history')", surrounding)

    def test_bell_uses_bi_bell_icon(self):
        """Bell must use the bi bi-bell Bootstrap icon."""
        self.assertIn('bi bi-bell', self.html)

    def test_bell_icon_aria_hidden(self):
        """Bell icon element must have aria-hidden=true (count is in aria-label)."""
        idx = self.html.find('bi bi-bell')
        surrounding = self.html[max(0, idx - 50):idx + 100]
        self.assertIn('aria-hidden="true"', surrounding)

    def test_bell_has_aria_label(self):
        """Bell anchor must have aria-label for screen readers."""
        idx = self.html.find('navbar-bell-btn')
        surrounding = self.html[idx:idx + 500]
        self.assertIn('aria-label=', surrounding)

    def test_bell_aria_label_includes_alerts_text(self):
        """Bell aria-label must include 'Alerts' text."""
        idx = self.html.find('navbar-bell-btn')
        surrounding = self.html[idx:idx + 500]
        self.assertIn('Alerts', surrounding)

    def test_bell_has_title_tooltip(self):
        """Bell must have title attribute for browser tooltip."""
        idx = self.html.find('navbar-bell-btn')
        surrounding = self.html[idx:idx + 500]
        self.assertIn('title=', surrounding)

    def test_bell_active_state_on_alert_history_page(self):
        """Bell must apply active class when on alert_history endpoint."""
        self.assertIn("request.endpoint == 'alert_history'", self.html)
        # Confirm active check is near the bell btn
        idx = self.html.find('navbar-bell-btn')
        surrounding = self.html[idx:idx + 500]
        self.assertIn("request.endpoint == 'alert_history'", surrounding)

    def test_bell_authenticated_only(self):
        """Bell must only render for authenticated users."""
        # The bell should be inside a current_user.is_authenticated block
        idx = self.html.find('navbar-bell-btn')
        # Look backwards for the auth guard
        preceding = self.html[max(0, idx - 300):idx]
        self.assertIn('current_user.is_authenticated', preceding)

    def test_badge_element_present(self):
        """Badge span with navbar-bell-badge class must be in HTML."""
        self.assertIn('navbar-bell-badge', self.html)

    def test_badge_aria_hidden(self):
        """Badge must have aria-hidden=true (count is in bell's aria-label)."""
        idx = self.html.find('navbar-bell-badge')
        surrounding = self.html[max(0, idx - 10):idx + 100]
        self.assertIn('aria-hidden="true"', surrounding)

    def test_badge_conditionally_rendered_when_unread_gt_0(self):
        """Badge must only render when unread_alert_count > 0."""
        self.assertIn('unread_alert_count > 0', self.html)
        # Confirm conditional is near the badge
        idx = self.html.find('navbar-bell-badge')
        preceding = self.html[max(0, idx - 200):idx]
        self.assertIn('unread_alert_count > 0', preceding)

    def test_badge_shows_9plus_for_10_or_more(self):
        """Badge must cap display at '9+' for unread_alert_count >= 10."""
        self.assertIn("'9+' if unread_alert_count >= 10", self.html)

    def test_bell_unread_class_applied_when_unread(self):
        """Bell link must get navbar-bell-btn--unread class when unread_alert_count > 0."""
        idx = self.html.find('navbar-bell-btn')
        surrounding = self.html[idx:idx + 500]
        self.assertIn('navbar-bell-btn--unread', surrounding)

    def test_toggler_inside_always_visible_wrapper(self):
        """Hamburger toggler must be inside the always-visible wrapper div."""
        wrapper_idx = self.html.find('<!-- Always-visible')
        self.assertGreater(wrapper_idx, 0)
        toggler_after_wrapper = self.html.find('navbar-toggler', wrapper_idx)
        self.assertGreater(toggler_after_wrapper, 0,
                           "navbar-toggler must appear inside the always-visible wrapper")


class TestBellNotRenderedForAnonymousUsers(unittest.TestCase):
    """Bell must not appear for unauthenticated users."""

    def setUp(self):
        self.html = read_file(BASE_HTML_PATH)

    def test_bell_guarded_by_auth_check(self):
        """Bell must be wrapped in {% if current_user.is_authenticated %} block."""
        # Find the always-visible wrapper section
        wrapper_idx = self.html.find('<!-- Always-visible')
        self.assertGreater(wrapper_idx, 0)
        wrapper_section = self.html[wrapper_idx:wrapper_idx + 1000]
        self.assertIn('current_user.is_authenticated', wrapper_section)
        self.assertIn('navbar-bell-btn', wrapper_section)


if __name__ == '__main__':
    unittest.main()
