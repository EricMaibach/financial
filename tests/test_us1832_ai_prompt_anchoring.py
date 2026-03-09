"""
Tests for US-183.2: Homepage Narrative Cohesion — AI Prompt Anchoring (§1 + §2)

Verifies that:
1. generate_market_conditions_synthesis() (dashboard.py §1) injects a regime-anchoring
   prefix into its user_prompt when macro_regime is available and not 'unknown'.
2. generate_daily_summary() (ai_summary.py §2) injects a regime-anchoring prefix into
   its user_prompt when macro_regime is available and not 'unknown'.
3. Both functions fall back gracefully (no prefix, no crash) when macro_regime is None
   or state is 'unknown' / 'Unknown'.
4. No HTML template containers are modified — regime reference is in generated text only.

Tests are primarily static (source-code analysis) supplemented by functional tests
with mocking for generate_daily_summary() which can be tested without Flask.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# =============================================================================
# Static tests — source code structure
# =============================================================================

class TestStaticDashboardRegimePrefix(unittest.TestCase):
    """generate_market_conditions_synthesis() must have regime prefix logic."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def test_regime_prefix_market_variable_present(self):
        self.assertIn('regime_prefix_market', self.src,
                      'regime_prefix_market variable not found in dashboard.py')

    def test_regime_prefix_market_injected_in_user_prompt(self):
        # The user_prompt f-string must include the regime prefix variable
        self.assertIn('{regime_prefix_market}', self.src,
                      'regime_prefix_market not interpolated in user_prompt in dashboard.py')

    def test_regime_prefix_market_names_regime(self):
        self.assertIn('explicitly naming the current macro regime', self.src,
                      'Expected regime-naming instruction not found in dashboard.py')

    def test_regime_prefix_market_includes_consistent_or_diverging(self):
        # Phrase may span two adjacent string literals; check for both words
        self.assertIn('consistent with', self.src,
                      '"consistent with" language not found in dashboard.py')
        self.assertIn('diverging from', self.src,
                      '"diverging from" language not found in dashboard.py')

    def test_regime_prefix_market_includes_proceed_instruction(self):
        self.assertIn('Then proceed with your standard market conditions summary', self.src,
                      'Expected proceed instruction not found in dashboard.py')

    def test_regime_prefix_market_fallback_empty_string(self):
        # When regime is unavailable, prefix must be empty string (no crash)
        self.assertIn('regime_prefix_market = ""', self.src,
                      'Empty string fallback for regime_prefix_market not found in dashboard.py')

    def test_regime_prefix_market_case_insensitive_guard(self):
        # Must use .lower() != 'unknown' for case-insensitive guard
        self.assertIn(".lower() != 'unknown'", self.src,
                      'Case-insensitive unknown guard (.lower() != unknown) not found in dashboard.py')

    def test_regime_state_interpolated_in_market_prefix(self):
        # The f-string for regime_prefix_market must interpolate regime_state
        self.assertIn('regime_state', self.src,
                      'regime_state variable not found in dashboard.py')


class TestStaticAiSummaryRegimePrefix(unittest.TestCase):
    """generate_daily_summary() must have regime prefix logic in ai_summary.py."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('ai_summary.py')

    def test_get_macro_regime_imported(self):
        self.assertIn('get_macro_regime', self.src,
                      'get_macro_regime not imported in ai_summary.py')

    def test_import_from_regime_detection(self):
        self.assertIn('from regime_detection import get_macro_regime', self.src,
                      'Import of get_macro_regime from regime_detection not found in ai_summary.py')

    def test_import_has_fallback(self):
        # Import must be wrapped in try/except with a no-op fallback
        self.assertIn('except ImportError', self.src,
                      'ImportError fallback not found in ai_summary.py')

    def test_regime_prefix_briefing_variable_present(self):
        self.assertIn('regime_prefix_briefing', self.src,
                      'regime_prefix_briefing variable not found in ai_summary.py')

    def test_regime_prefix_briefing_injected_in_user_prompt(self):
        self.assertIn('{regime_prefix_briefing}', self.src,
                      'regime_prefix_briefing not interpolated in user_prompt in ai_summary.py')

    def test_regime_prefix_briefing_names_regime(self):
        self.assertIn('Open your briefing by naming the current macro regime', self.src,
                      'Expected briefing regime-naming instruction not found in ai_summary.py')

    def test_regime_prefix_briefing_includes_investor_implication(self):
        self.assertIn('what it means for investors today', self.src,
                      'Expected investor implication language not found in ai_summary.py')

    def test_regime_prefix_briefing_includes_proceed_instruction(self):
        self.assertIn('Then proceed with your standard briefing content', self.src,
                      'Expected proceed instruction not found in ai_summary.py')

    def test_regime_prefix_briefing_fallback_empty_string(self):
        self.assertIn('regime_prefix_briefing = ""', self.src,
                      'Empty string fallback for regime_prefix_briefing not found in ai_summary.py')

    def test_regime_prefix_briefing_case_insensitive_guard(self):
        self.assertIn(".lower() != 'unknown'", self.src,
                      'Case-insensitive unknown guard (.lower() != unknown) not found in ai_summary.py')


class TestNoTemplateChanges(unittest.TestCase):
    """HTML containers must NOT be modified — regime reference in generated text only."""

    @classmethod
    def setUpClass(cls):
        cls.index_src = read_source('templates/index.html')

    def test_market_synthesis_text_container_unchanged(self):
        # The span#market-synthesis-text must still exist
        self.assertIn('id="market-synthesis-text"', self.index_src,
                      '#market-synthesis-text container missing from index.html')

    def test_briefing_narrative_container_unchanged(self):
        # The div#briefing-narrative must still exist
        self.assertIn('id="briefing-narrative"', self.index_src,
                      '#briefing-narrative container missing from index.html')


# =============================================================================
# Functional tests — generate_daily_summary() with mocking
# =============================================================================

class TestGenerateDailySummaryRegimePrefix(unittest.TestCase):
    """
    Functional tests for regime prefix injection in generate_daily_summary().
    Mocks get_macro_regime() and call_ai_with_tools() to verify prompt construction.
    """

    def _call_with_mocked_regime(self, regime_dict):
        """Helper: call generate_daily_summary() with a mocked regime and capture prompt."""
        import ai_summary as ai_mod

        captured = {}

        def mock_call_ai(client, system_prompt, user_prompt, **kwargs):
            captured['user_prompt'] = user_prompt
            return {'success': True, 'content': 'Mock briefing text.'}

        def mock_get_ai_client():
            return (MagicMock(), 'openai')

        def mock_get_recent_summaries(days=3):
            return []

        def mock_fetch_news():
            return None

        def mock_get_latest_crypto():
            return None

        def mock_get_latest_equity():
            return None

        def mock_get_latest_rates():
            return None

        def mock_get_latest_dollar():
            return None

        def mock_save_summary(*args, **kwargs):
            pass

        with patch.object(ai_mod, 'get_macro_regime', return_value=regime_dict), \
             patch.object(ai_mod, 'call_ai_with_tools', side_effect=mock_call_ai), \
             patch.object(ai_mod, 'get_ai_client', side_effect=mock_get_ai_client), \
             patch.object(ai_mod, 'get_recent_summaries', side_effect=mock_get_recent_summaries), \
             patch.object(ai_mod, 'fetch_news_for_summary', side_effect=mock_fetch_news), \
             patch.object(ai_mod, 'get_latest_crypto_summary', side_effect=mock_get_latest_crypto), \
             patch.object(ai_mod, 'get_latest_equity_summary', side_effect=mock_get_latest_equity), \
             patch.object(ai_mod, 'get_latest_rates_summary', side_effect=mock_get_latest_rates), \
             patch.object(ai_mod, 'get_latest_dollar_summary', side_effect=mock_get_latest_dollar), \
             patch.object(ai_mod, 'save_summary', side_effect=mock_save_summary):
            result = ai_mod.generate_daily_summary('## MARKET DATA\nTest data.', [])

        return result, captured

    def test_bull_regime_prefix_injected(self):
        result, captured = self._call_with_mocked_regime({'state': 'Bull'})
        self.assertTrue(result['success'])
        self.assertIn('Open your briefing by naming the current macro regime (Bull)',
                      captured['user_prompt'])

    def test_bear_regime_prefix_injected(self):
        result, captured = self._call_with_mocked_regime({'state': 'Bear'})
        self.assertIn('Open your briefing by naming the current macro regime (Bear)',
                      captured['user_prompt'])

    def test_neutral_regime_prefix_injected(self):
        result, captured = self._call_with_mocked_regime({'state': 'Neutral'})
        self.assertIn('Open your briefing by naming the current macro regime (Neutral)',
                      captured['user_prompt'])

    def test_recession_watch_regime_prefix_injected(self):
        result, captured = self._call_with_mocked_regime({'state': 'Recession Watch'})
        self.assertIn('Open your briefing by naming the current macro regime (Recession Watch)',
                      captured['user_prompt'])

    def test_none_regime_no_prefix(self):
        result, captured = self._call_with_mocked_regime(None)
        self.assertNotIn('Open your briefing by naming the current macro regime',
                         captured.get('user_prompt', ''))

    def test_unknown_lowercase_no_prefix(self):
        result, captured = self._call_with_mocked_regime({'state': 'unknown'})
        self.assertNotIn('Open your briefing by naming the current macro regime',
                         captured.get('user_prompt', ''))

    def test_unknown_capitalized_no_prefix(self):
        result, captured = self._call_with_mocked_regime({'state': 'Unknown'})
        self.assertNotIn('Open your briefing by naming the current macro regime',
                         captured.get('user_prompt', ''))

    def test_prefix_prepended_not_appended(self):
        """Regime context must open the user prompt, not appear at the end."""
        result, captured = self._call_with_mocked_regime({'state': 'Bull'})
        prompt = captured.get('user_prompt', '')
        prefix_pos = prompt.find('Open your briefing by naming')
        today_pos = prompt.find('Today is')
        self.assertGreater(today_pos, prefix_pos,
                           'Regime prefix must come before "Today is" in user_prompt')

    def test_existing_prompt_content_preserved(self):
        """Regime prefix addition must not remove existing prompt content."""
        result, captured = self._call_with_mocked_regime({'state': 'Bull'})
        prompt = captured.get('user_prompt', '')
        self.assertIn('Today is', prompt, '"Today is" missing from user_prompt after prefix injection')
        self.assertIn('Generate today\'s market briefing', prompt,
                      'Core briefing instruction missing after prefix injection')
        self.assertIn('2 paragraphs', prompt,
                      '"2 paragraphs" reminder missing after prefix injection')

    def test_prefix_includes_regime_state_in_parens(self):
        """Regime state must be interpolated into the prefix f-string."""
        result, captured = self._call_with_mocked_regime({'state': 'Bear'})
        self.assertIn('(Bear)', captured['user_prompt'],
                      'Regime state not interpolated with parentheses in prefix')

    def test_prefix_investor_implication_present(self):
        result, captured = self._call_with_mocked_regime({'state': 'Neutral'})
        self.assertIn('what it means for investors today', captured['user_prompt'])

    def test_prefix_proceed_instruction_present(self):
        result, captured = self._call_with_mocked_regime({'state': 'Neutral'})
        self.assertIn('Then proceed with your standard briefing content', captured['user_prompt'])


# =============================================================================
# Functional tests — generate_market_conditions_synthesis() prompt structure
# via static source inspection of the exact user_prompt construction
# =============================================================================

class TestMarketConditionsSynthesisPromptStructure(unittest.TestCase):
    """
    Verify the user_prompt construction in generate_market_conditions_synthesis()
    via source code analysis. Full functional mocking of dashboard.py requires
    Flask app context; static inspection is sufficient for prompt structure.
    """

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def test_regime_prefix_built_before_user_prompt(self):
        # regime_prefix_market must be assigned before user_prompt f-string
        src = self.src
        prefix_pos = src.find('regime_prefix_market =')
        user_prompt_pos = src.find("user_prompt = f\"\"\"{regime_prefix_market}")
        self.assertGreater(prefix_pos, 0, 'regime_prefix_market assignment not found')
        self.assertGreater(user_prompt_pos, 0, 'user_prompt with regime_prefix_market not found')
        self.assertLess(prefix_pos, user_prompt_pos,
                        'regime_prefix_market must be assigned before user_prompt f-string')

    def test_regime_state_sourced_from_get_macro_regime(self):
        # regime_state must come from get_macro_regime() call
        self.assertIn("regime = get_macro_regime()", self.src,
                      'get_macro_regime() not called in generate_market_conditions_synthesis()')
        self.assertIn("regime['state']", self.src,
                      "regime['state'] access not found in dashboard.py")

    def test_none_guard_present(self):
        # Must check regime is not None before accessing state
        self.assertIn('if regime and regime.get(', self.src,
                      'None guard for regime not found in dashboard.py')

    def test_regime_prefix_market_content_correct(self):
        self.assertIn(
            'Begin your synthesis by explicitly naming the current macro regime',
            self.src,
            'Expected §1 regime prefix instruction not found in dashboard.py'
        )


if __name__ == '__main__':
    unittest.main()
