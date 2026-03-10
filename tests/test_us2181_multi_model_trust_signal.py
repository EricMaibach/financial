"""
Tests for US-218.1: Add multi-model trust signal callout to Recession Probability panel
"""
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
INDEX_HTML = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')


def get_index_html():
    with open(INDEX_HTML, 'r') as f:
        return f.read()


class TestMultiModelTrustSignalCallout(unittest.TestCase):
    """Callout block appears inside recession panel, after recession-source div."""

    def setUp(self):
        self.html = get_index_html()

    def _recession_panel_content(self):
        start = self.html.find('id="recession-panel-content"')
        self.assertNotEqual(start, -1, "#recession-panel-content not found")
        # Grab from here to the closing panel div
        end = self.html.find('</div>{# /.recession-panel #}', start)
        self.assertNotEqual(end, -1, "recession-panel closing div not found")
        return self.html[start:end]

    def test_callout_present_in_panel(self):
        panel = self._recession_panel_content()
        self.assertIn('Why three models?', panel)

    def test_callout_after_recession_source(self):
        panel = self._recession_panel_content()
        source_idx = panel.find('recession-source')
        callout_idx = panel.find('Why three models?')
        self.assertNotEqual(source_idx, -1, ".recession-source not found in panel")
        self.assertNotEqual(callout_idx, -1, "callout not found in panel")
        self.assertGreater(callout_idx, source_idx,
                           "callout must appear after .recession-source")

    def test_callout_separated_by_toggle(self):
        # US-218.2: callout now in progressive disclosure; toggle button separates source from content
        panel = self._recession_panel_content()
        source_idx = panel.find('recession-source')
        callout_idx = panel.find('Why three models?')
        between = panel[source_idx:callout_idx]
        self.assertIn('recession-why-toggle', between,
                      "recession-why-toggle must appear between source and callout")

    def test_callout_uses_info_circle_icon(self):
        # US-218.2: info-circle is in the collapsible content (second occurrence of "Why three models?")
        panel = self._recession_panel_content()
        content_idx = panel.find('id="recession-why-content"')
        self.assertNotEqual(content_idx, -1, "recession-why-content not found")
        content_block = panel[content_idx:content_idx + 600]
        self.assertIn('bi-info-circle', content_block)
        self.assertIn('aria-hidden="true"', content_block)

    def test_callout_uses_bootstrap_utilities_only(self):
        panel = self._recession_panel_content()
        callout_idx = panel.find('Why three models?')
        block = panel[max(0, callout_idx - 500):callout_idx + 500]
        self.assertIn('bg-light', block)
        self.assertIn('border-start', block)
        self.assertIn('border-secondary', block)
        self.assertIn('rounded-2', block)
        self.assertIn('p-3', block)
        self.assertIn('mt-2', block)

    def test_callout_body_copy_exact(self):
        expected_fragment = (
            "Single indicators fail in practice. The yield curve inverted in 2022 and held through"
        )
        self.assertIn(expected_fragment, self.html)

    def test_callout_body_ends_correctly(self):
        # US-218.2: indentation updated to match progressive disclosure wrapper
        expected_fragment = (
            "and when they diverge,\n"
            "                  the disagreement is itself the signal."
        )
        self.assertIn(expected_fragment, self.html)

    def test_no_new_css_file_created(self):
        """Callout must use no new CSS — confirm no new CSS file references were added."""
        css_dir = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components')
        css_files = os.listdir(css_dir)
        # Ensure no file referencing us218 or trust-signal was introduced
        new_files = [f for f in css_files if 'us218' in f or 'trust-signal' in f]
        self.assertEqual(new_files, [],
                         f"No new CSS file should have been created for this story: {new_files}")

    def test_no_template_variable_required(self):
        """Callout must be static — no new Jinja2 variable references."""
        panel = self._recession_panel_content()
        callout_idx = panel.find('Why three models?')
        block = panel[callout_idx:callout_idx + 600]
        # Should contain no {{ }} template expressions
        self.assertNotIn('{{', block,
                         "Callout must be static — no template variables allowed")

    def test_callout_always_rendered(self):
        """Callout must not be wrapped in any conditional block."""
        callout_idx = self.html.find('Why three models?')
        self.assertNotEqual(callout_idx, -1)
        # Check 200 chars before the callout for any {% if %} without matching recession_probability block
        before = self.html[max(0, callout_idx - 200):callout_idx]
        # The only {% if %} allowed nearby would be the outer recession_probability guard (far above)
        # Immediately before should NOT have a standalone {% if %} for the callout itself
        import re
        # Strip comments and find if-blocks
        if_matches = re.findall(r'\{%-?\s*if\b', before)
        # Allow 0 or 1 (the panel's own recession_probability guard is far above, not in 200-char window)
        self.assertLessEqual(len(if_matches), 0,
                             f"Callout should not be inside any conditional: found {if_matches}")


class TestMultiModelTrustSignalLabelText(unittest.TestCase):
    """Label text must match spec exactly."""

    def setUp(self):
        self.html = get_index_html()

    def test_label_text_exact(self):
        self.assertIn('Why three models?', self.html)

    def test_label_style_classes(self):
        # US-218.2: callout heading is inside collapsible content; find via recession-why-content
        content_idx = self.html.find('id="recession-why-content"')
        self.assertNotEqual(content_idx, -1, "recession-why-content not found")
        block = self.html[content_idx:content_idx + 400]
        self.assertIn('text-xs', block)
        self.assertIn('text-uppercase', block)
        self.assertIn('fw-semibold', block)
        self.assertIn('text-secondary', block)

    def test_body_style_classes(self):
        # US-218.2: callout body is inside collapsible content
        content_idx = self.html.find('id="recession-why-content"')
        self.assertNotEqual(content_idx, -1, "recession-why-content not found")
        block = self.html[content_idx:content_idx + 600]
        self.assertIn('small text-muted mb-0', block)


if __name__ == '__main__':
    unittest.main()
