"""
Tests for US-218.2: Recession Probability Panel — Consolidate Explanation Elements

Acceptance criteria:
- recession-divergence-alert HTML block is removed
- recession-footer receives recession-footer--diverging class when divergence_pp >= 15
- --diverging state has correct CSS (4px left border #D97706, #FEF3C7 bg)
- WHY THREE MODELS callout wrapped in progressive disclosure (collapsed by default)
- Toggle follows established pattern with aria-expanded="false" by default
- Dead code cleanup: no orphaned recession-divergence-alert references
"""
import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
INDEX_HTML = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
RECESSION_CSS = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components', 'recession-panel.css')


def get_index_html():
    with open(INDEX_HTML, 'r') as f:
        return f.read()


def get_recession_css():
    with open(RECESSION_CSS, 'r') as f:
        return f.read()


def get_panel_section(html):
    """Return the portion of index.html inside #recession-panel-content."""
    start = html.find('id="recession-panel-content"')
    assert start != -1, "#recession-panel-content not found"
    end = html.find('</div>{# /.recession-panel #}', start)
    assert end != -1, "recession-panel closing comment not found"
    return html[start:end]


class TestDivergenceAlertRemoved(unittest.TestCase):
    """recession-divergence-alert must not appear anywhere."""

    def test_alert_class_not_in_template(self):
        html = get_index_html()
        self.assertNotIn('recession-divergence-alert', html,
                         "recession-divergence-alert still present in index.html")

    def test_alert_class_not_in_css(self):
        css = get_recession_css()
        self.assertNotIn('recession-divergence-alert', css,
                         "recession-divergence-alert CSS rule not removed from recession-panel.css")

    def test_alert_icon_not_in_template(self):
        """The exclamation-triangle icon was part of the removed alert block."""
        html = get_index_html()
        self.assertNotIn('bi-exclamation-triangle-fill', html,
                         "Alert icon still present — alert block not fully removed")


class TestRecessionFooterDivergingClass(unittest.TestCase):
    """recession-footer--diverging class applied conditionally via Jinja2."""

    def test_diverging_class_applied_when_divergence_gte_15(self):
        html = get_index_html()
        panel = get_panel_section(html)
        # Jinja2 conditional: divergence_pp >= 15 -> adds class
        self.assertIn('recession-footer--diverging', panel,
                      "recession-footer--diverging modifier class not found in panel")

    def test_diverging_class_inside_recession_footer_div(self):
        html = get_index_html()
        panel = get_panel_section(html)
        # The div opening tag should have both classes conditionally
        pattern = r'<div class="recession-footer[^"]*recession-footer--diverging[^"]*"'
        # Check using Jinja2 syntax (conditional insertion)
        jinja_pattern = r'recession-footer\{%.*?divergence_pp.*?%\}.*?recession-footer--diverging'
        # Either static class or Jinja2 conditional is acceptable
        has_static = bool(re.search(r'class="[^"]*recession-footer--diverging', panel))
        has_jinja = ('recession-footer--diverging' in panel and 'divergence_pp' in panel)
        self.assertTrue(has_static or has_jinja,
                        "recession-footer--diverging not properly applied in template")

    def test_divergence_condition_uses_gte_15(self):
        html = get_index_html()
        panel = get_panel_section(html)
        # Should check >= 15 for the diverging class
        self.assertIn('divergence_pp >= 15', panel,
                      "Boundary condition divergence_pp >= 15 not found in panel")

    def test_no_safe_filter_on_interpretation(self):
        """interpretation must NOT use | safe filter (security guard)."""
        html = get_index_html()
        panel = get_panel_section(html)
        interp_idx = panel.find('recession_probability.interpretation')
        self.assertNotEqual(interp_idx, -1, "interpretation not found in panel")
        # Check the 50 chars after interpretation for | safe
        snippet = panel[interp_idx:interp_idx + 60]
        self.assertNotIn('| safe', snippet,
                         "| safe filter used on interpretation — XSS risk")


class TestDivergingCSSRules(unittest.TestCase):
    """CSS for recession-footer--diverging matches spec."""

    def test_diverging_left_border_color(self):
        css = get_recession_css()
        # Should have D97706 (warning-600)
        self.assertIn('#D97706', css,
                      "warning-600 (#D97706) not found in recession-panel.css")

    def test_diverging_background_color(self):
        css = get_recession_css()
        # Should have FEF3C7 (warning-100)
        self.assertIn('#FEF3C7', css,
                      "warning-100 (#FEF3C7) not found in recession-panel.css")

    def test_diverging_border_left_width(self):
        css = get_recession_css()
        # Find the --diverging block
        idx = css.find('recession-footer--diverging')
        self.assertNotEqual(idx, -1, ".recession-footer--diverging not found in CSS")
        block = css[idx:idx + 200]
        self.assertIn('border-left', block,
                      "border-left not in .recession-footer--diverging block")

    def test_diverging_rule_exists(self):
        css = get_recession_css()
        self.assertIn('.recession-footer--diverging', css,
                      ".recession-footer--diverging rule missing from recession-panel.css")


class TestWhyThreeModelsProgressiveDisclosure(unittest.TestCase):
    """WHY THREE MODELS callout is wrapped in progressive disclosure, collapsed by default."""

    def test_toggle_button_present(self):
        html = get_index_html()
        panel = get_panel_section(html)
        self.assertIn('recession-why-toggle', panel,
                      "recession-why-toggle button not found in recession panel")

    def test_toggle_is_button_element(self):
        html = get_index_html()
        panel = get_panel_section(html)
        # Should be a <button> with the toggle class
        self.assertIn('<button', panel, "<button> element not found in panel")
        btn_idx = panel.find('recession-why-toggle')
        # Walk back to find opening tag
        tag_start = panel.rfind('<', 0, btn_idx)
        tag_end = panel.find('>', btn_idx)
        tag = panel[tag_start:tag_end + 1]
        self.assertTrue(tag.startswith('<button'), f"recession-why-toggle is not a <button>: {tag[:60]}")

    def test_toggle_aria_expanded_false_by_default(self):
        html = get_index_html()
        panel = get_panel_section(html)
        idx = panel.find('recession-why-toggle')
        # Get the button tag
        tag_start = panel.rfind('<', 0, idx)
        tag_end = panel.find('>', idx)
        tag = panel[tag_start:tag_end + 50]  # include a bit more
        # aria-expanded="false" should be in the button attributes
        self.assertIn('aria-expanded="false"', tag,
                      'aria-expanded="false" not set on toggle button by default')

    def test_toggle_has_aria_controls(self):
        html = get_index_html()
        panel = get_panel_section(html)
        idx = panel.find('recession-why-toggle')
        tag_start = panel.rfind('<', 0, idx)
        # Find the closing > of the button opening tag
        tag_end = panel.find('>', tag_start + 100)
        tag = panel[tag_start:tag_end + 1]
        self.assertIn('aria-controls', tag,
                      "aria-controls not set on toggle button")

    def test_toggle_min_height_css(self):
        css = get_recession_css()
        idx = css.find('.recession-why-toggle')
        self.assertNotEqual(idx, -1, ".recession-why-toggle not in CSS")
        block_end = css.find('}', idx)
        block = css[idx:block_end + 1]
        self.assertIn('min-height', block,
                      "min-height not set on .recession-why-toggle")
        # Extract the value
        mh_match = re.search(r'min-height:\s*(\d+)px', block)
        self.assertIsNotNone(mh_match, "min-height px value not found")
        self.assertGreaterEqual(int(mh_match.group(1)), 44,
                                f"min-height is {mh_match.group(1)}px — must be ≥ 44px")

    def test_callout_content_hidden_by_default(self):
        html = get_index_html()
        panel = get_panel_section(html)
        # Content div should have hidden attribute
        self.assertIn('id="recession-why-content"', panel,
                      "recession-why-content not found in panel")
        content_idx = panel.find('id="recession-why-content"')
        tag_start = panel.rfind('<', 0, content_idx)
        tag_end = panel.find('>', content_idx)
        tag = panel[tag_start:tag_end + 1]
        self.assertIn('hidden', tag,
                      "recession-why-content not hidden by default (missing hidden attribute)")

    def test_callout_content_after_toggle_button(self):
        html = get_index_html()
        panel = get_panel_section(html)
        toggle_idx = panel.find('recession-why-toggle')
        content_idx = panel.find('recession-why-content')
        self.assertGreater(content_idx, toggle_idx,
                           "recession-why-content appears before the toggle button")

    def test_why_three_models_text_in_panel(self):
        html = get_index_html()
        panel = get_panel_section(html)
        self.assertIn('Why three models?', panel,
                      "Why three models? text not found in panel")

    def test_toggle_chevron_present(self):
        html = get_index_html()
        panel = get_panel_section(html)
        self.assertIn('recession-why-chevron', panel,
                      "recession-why-chevron element not found in toggle button")

    def test_toggle_lines_present(self):
        html = get_index_html()
        panel = get_panel_section(html)
        self.assertIn('recession-why-toggle-line', panel,
                      "recession-why-toggle-line decorative lines not found")

    def test_toggle_css_exists(self):
        css = get_recession_css()
        self.assertIn('.recession-why-toggle', css,
                      ".recession-why-toggle CSS not found in recession-panel.css")
        self.assertIn('.recession-why-toggle-line', css,
                      ".recession-why-toggle-line CSS not found in recession-panel.css")
        self.assertIn('.recession-why-chevron', css,
                      ".recession-why-chevron CSS not found in recession-panel.css")

    def test_chevron_rotation_on_expanded_css(self):
        css = get_recession_css()
        self.assertIn('aria-expanded="true"]', css,
                      "aria-expanded true state not handled in CSS (chevron rotation)")

    def test_toggle_focus_style_in_css(self):
        css = get_recession_css()
        self.assertIn('.recession-why-toggle:focus', css,
                      ".recession-why-toggle:focus not defined in CSS")


class TestJavaScriptToggleHandler(unittest.TestCase):
    """JS toggle handler wires up recession-why-toggle correctly."""

    def test_js_toggle_handler_present(self):
        html = get_index_html()
        self.assertIn('recession-why-toggle', html,
                      "recession-why-toggle JS handler not found")

    def test_js_toggles_aria_expanded(self):
        html = get_index_html()
        # Should flip aria-expanded
        idx = html.find('recession-why-toggle')
        # Find the JS block that references this id
        js_block_start = html.find("getElementById('recession-why-toggle')")
        self.assertNotEqual(js_block_start, -1,
                            "getElementById('recession-why-toggle') not found in JS")
        js_block = html[js_block_start:js_block_start + 400]
        self.assertIn('aria-expanded', js_block,
                      "aria-expanded not toggled in JS handler")

    def test_js_toggles_hidden_attribute(self):
        html = get_index_html()
        js_block_start = html.find("getElementById('recession-why-toggle')")
        self.assertNotEqual(js_block_start, -1,
                            "getElementById('recession-why-toggle') not found")
        js_block = html[js_block_start:js_block_start + 600]
        # Either removeAttribute('hidden') or setAttribute('hidden') pattern
        self.assertTrue(
            'hidden' in js_block,
            "hidden attribute not toggled in JS handler — content must be shown/hidden via 'hidden'"
        )


class TestDeadCodeCleanup(unittest.TestCase):
    """No orphaned references to recession-divergence-alert remain."""

    def test_no_alert_in_template(self):
        html = get_index_html()
        self.assertNotIn('recession-divergence-alert', html)

    def test_no_alert_in_css(self):
        css = get_recession_css()
        self.assertNotIn('recession-divergence-alert', css)

    def test_plain_footer_css_rule_still_exists(self):
        """Base .recession-footer rule must remain for non-diverging state."""
        css = get_recession_css()
        self.assertIn('.recession-footer', css,
                      ".recession-footer base rule removed — needed for plain state")


if __name__ == '__main__':
    unittest.main()
