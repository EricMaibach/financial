"""
Tests for US-219.1: Add regime-thread class to Cross-Market and Prediction sections
"""
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
INDEX_HTML = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')

REGIME_THREAD_PATTERN = 'regime-thread{% if macro_regime %} {{ macro_regime.css_class }}{% endif %}'


def get_index_html():
    with open(INDEX_HTML, 'r') as f:
        return f.read()


class TestRegimeThreadClassPresence(unittest.TestCase):
    """Both new sections must have the exact regime-thread class pattern."""

    def setUp(self):
        self.html = get_index_html()

    def test_signals_section_has_regime_thread(self):
        idx = self.html.find('id="signals-section"')
        self.assertNotEqual(idx, -1, "#signals-section not found")
        section_tag = self.html[max(0, idx - 300):idx + 300]
        self.assertIn('regime-thread', section_tag)

    def test_signals_section_has_exact_pattern(self):
        self.assertIn(
            'id="signals-section"',
            self.html,
            "#signals-section not found"
        )
        idx = self.html.find('id="signals-section"')
        section_tag = self.html[max(0, idx - 300):idx + 300]
        self.assertIn(REGIME_THREAD_PATTERN, section_tag)

    def test_prediction_section_has_regime_thread(self):
        idx = self.html.find('id="prediction-section"')
        self.assertNotEqual(idx, -1, "#prediction-section not found")
        section_tag = self.html[max(0, idx - 300):idx + 300]
        self.assertIn('regime-thread', section_tag)

    def test_prediction_section_has_exact_pattern(self):
        self.assertIn(
            'id="prediction-section"',
            self.html,
            "#prediction-section not found"
        )
        idx = self.html.find('id="prediction-section"')
        section_tag = self.html[max(0, idx - 300):idx + 300]
        self.assertIn(REGIME_THREAD_PATTERN, section_tag)


class TestRegimeThreadTotalCount(unittest.TestCase):
    """Total regime-thread occurrences in index.html must be 9."""

    def setUp(self):
        self.html = get_index_html()

    def test_total_regime_thread_count_is_nine(self):
        count = self.html.count('regime-thread')
        self.assertEqual(count, 9, f"Expected 9 regime-thread occurrences, found {count}")


class TestAllRequiredSectionsHaveRegimeThread(unittest.TestCase):
    """All 9 below-§0 sections must have the regime-thread class."""

    def setUp(self):
        self.html = get_index_html()

    def _section_has_regime_thread(self, section_id):
        idx = self.html.find(f'id="{section_id}"')
        if idx == -1:
            return False
        # Search a wide window around the ID (class may appear before or after id attr)
        section_tag = self.html[max(0, idx - 300):idx + 300]
        return 'regime-thread' in section_tag

    def test_recession_panel_section_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('recession-panel-section'))

    def test_regime_implications_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('regime-implications'))

    def test_sector_tone_section_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('sector-tone-section'))

    def test_market_conditions_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('market-conditions'))

    def test_trade_pulse_section_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('trade-pulse-section'))

    def test_briefing_section_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('briefing-section'))

    def test_movers_section_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('movers-section'))

    def test_signals_section_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('signals-section'))

    def test_prediction_section_has_regime_thread(self):
        self.assertTrue(self._section_has_regime_thread('prediction-section'))


class TestNoBackendChanges(unittest.TestCase):
    """This story is template-only — no new CSS or Python files."""

    def test_no_new_css_file_for_us219(self):
        css_dir = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'components')
        css_files = os.listdir(css_dir)
        # No new CSS file should have been created for this story
        for name in css_files:
            self.assertFalse(
                'us219' in name.lower() or 'regime-thread-sections' in name.lower(),
                f"Unexpected CSS file created for US-219.1: {name}"
            )

    def test_section_ids_unchanged(self):
        """Quick-nav scroll targets must remain intact."""
        self.assertIn('id="signals-section"', self.html if hasattr(self, 'html') else get_index_html())
        self.assertIn('id="prediction-section"', get_index_html())


class TestConditionalRegimeClass(unittest.TestCase):
    """The Jinja2 conditional pattern must be present so css_class is only appended when set."""

    def setUp(self):
        self.html = get_index_html()

    def _get_context_around(self, section_id):
        idx = self.html.find(f'id="{section_id}"')
        return self.html[max(0, idx - 300):idx + 300]

    def test_signals_section_conditional_css_class(self):
        section_tag = self._get_context_around('signals-section')
        self.assertIn('{% if macro_regime %}', section_tag)
        self.assertIn('macro_regime.css_class', section_tag)
        self.assertIn('{% endif %}', section_tag)

    def test_prediction_section_conditional_css_class(self):
        section_tag = self._get_context_around('prediction-section')
        self.assertIn('{% if macro_regime %}', section_tag)
        self.assertIn('macro_regime.css_class', section_tag)
        self.assertIn('{% endif %}', section_tag)


if __name__ == '__main__':
    unittest.main()
