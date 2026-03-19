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


class TestStaticAiSummaryConditionsContext(unittest.TestCase):
    """generate_daily_summary() must use market conditions context (US-325.1)."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('ai_summary.py')

    def test_get_market_conditions_imported(self):
        self.assertIn('get_market_conditions', self.src,
                      'get_market_conditions not imported in ai_summary.py')

    def test_get_conditions_history_imported(self):
        self.assertIn('get_conditions_history', self.src,
                      'get_conditions_history not imported in ai_summary.py')

    def test_import_has_fallback(self):
        self.assertIn('except ImportError', self.src,
                      'ImportError fallback not found in ai_summary.py')

    def test_conditions_context_built(self):
        self.assertIn('_build_conditions_context', self.src,
                      'conditions context builder not found in ai_summary.py')

    def test_conditions_history_built(self):
        self.assertIn('_build_conditions_history_context', self.src,
                      'conditions history builder not found in ai_summary.py')

    def test_conditions_context_in_prompt(self):
        self.assertIn('{conditions_context}', self.src,
                      'conditions_context not interpolated in user_prompt in ai_summary.py')

    def test_conditions_history_in_prompt(self):
        self.assertIn('{conditions_history}', self.src,
                      'conditions_history not interpolated in user_prompt in ai_summary.py')

    def test_quadrant_naming_instruction(self):
        self.assertIn('naming the current macro quadrant', self.src,
                      'Quadrant-naming instruction not found in ai_summary.py')

    def test_three_paragraph_structure(self):
        self.assertIn('3 paragraphs', self.src,
                      'Three-paragraph instruction not found in ai_summary.py')

    def test_old_regime_prefix_removed(self):
        self.assertNotIn('regime_prefix_briefing', self.src,
                         'Old regime_prefix_briefing should be removed from ai_summary.py')


class TestNoTemplateChanges(unittest.TestCase):
    """HTML containers must NOT be modified — regime reference in generated text only."""

    @classmethod
    def setUpClass(cls):
        cls.index_src = read_source('templates/index.html')

    def test_briefing_narrative_container_unchanged(self):
        # The div#briefing-narrative must still exist
        self.assertIn('id="briefing-narrative"', self.index_src,
                      '#briefing-narrative container missing from index.html')


# =============================================================================
# Functional tests — generate_daily_summary() with mocking
# =============================================================================

class TestGenerateDailySummaryConditionsContext(unittest.TestCase):
    """
    Functional tests for conditions context injection in generate_daily_summary().
    Mocks get_market_conditions() and call_ai_with_tools() to verify prompt construction.
    """

    MOCK_CONDITIONS = {
        'quadrant': 'Goldilocks',
        'dimensions': {
            'quadrant': {'state': 'Goldilocks', 'growth_composite': 0.6, 'inflation_composite': -0.4},
            'liquidity': {'state': 'Expanding', 'score': 0.82},
            'risk': {'state': 'Calm', 'score': 1, 'vix_level': 14.8},
            'policy': {'stance': 'Neutral', 'direction': 'Easing', 'taylor_gap': -0.3},
        },
        'asset_expectations': [
            {'asset': 'S&P 500', 'direction': 'positive', 'magnitude': 'strong'},
        ],
    }

    MOCK_HISTORY = {
        '2026-02-18': {
            'quadrant': 'Reflation',
            'dimensions': {
                'liquidity': {'state': 'Neutral', 'score': 0.1},
                'risk': {'state': 'Normal'},
                'policy': {'stance': 'Neutral', 'direction': 'Paused'},
            },
        },
        '2026-03-18': {
            'quadrant': 'Goldilocks',
            'dimensions': {
                'liquidity': {'state': 'Expanding', 'score': 0.82},
                'risk': {'state': 'Calm'},
                'policy': {'stance': 'Neutral', 'direction': 'Easing'},
            },
        },
    }

    def _call_with_mocked_conditions(self, conditions, history=None):
        """Helper: call generate_daily_summary() with mocked conditions and capture prompt."""
        import ai_summary as ai_mod

        captured = {}

        def mock_call_ai(client, system_prompt, user_prompt, **kwargs):
            captured['user_prompt'] = user_prompt
            captured['system_prompt'] = system_prompt
            return {'success': True, 'content': 'Mock briefing text.'}

        with patch.object(ai_mod, 'get_market_conditions', return_value=conditions), \
             patch.object(ai_mod, 'get_conditions_history', return_value=history or {}), \
             patch.object(ai_mod, 'call_ai_with_tools', side_effect=mock_call_ai), \
             patch.object(ai_mod, 'get_ai_client', return_value=(MagicMock(), 'openai')), \
             patch.object(ai_mod, 'get_recent_summaries', return_value=[]), \
             patch.object(ai_mod, '_get_stored_news_context', return_value=None), \
             patch.object(ai_mod, 'get_latest_crypto_summary', return_value=None), \
             patch.object(ai_mod, 'get_latest_equity_summary', return_value=None), \
             patch.object(ai_mod, 'get_latest_rates_summary', return_value=None), \
             patch.object(ai_mod, 'get_latest_dollar_summary', return_value=None), \
             patch.object(ai_mod, 'get_latest_credit_summary', return_value=None), \
             patch.object(ai_mod, 'save_summary', return_value=None):
            result = ai_mod.generate_daily_summary('## MARKET DATA\nTest data.', [])

        return result, captured

    def test_conditions_context_in_prompt(self):
        result, captured = self._call_with_mocked_conditions(self.MOCK_CONDITIONS)
        self.assertTrue(result['success'])
        self.assertIn('CURRENT MARKET CONDITIONS', captured['user_prompt'])
        self.assertIn('Goldilocks', captured['user_prompt'])

    def test_conditions_dimensions_in_prompt(self):
        result, captured = self._call_with_mocked_conditions(self.MOCK_CONDITIONS)
        prompt = captured['user_prompt']
        self.assertIn('Expanding', prompt)
        self.assertIn('Calm', prompt)
        self.assertIn('Easing', prompt)

    def test_conditions_history_in_prompt(self):
        result, captured = self._call_with_mocked_conditions(self.MOCK_CONDITIONS, self.MOCK_HISTORY)
        self.assertIn('CONDITIONS HISTORY', captured['user_prompt'])

    def test_none_conditions_graceful(self):
        result, captured = self._call_with_mocked_conditions(None)
        self.assertTrue(result['success'])
        # Should not crash, just have empty conditions context
        self.assertNotIn('CURRENT MARKET CONDITIONS', captured['user_prompt'])

    def test_no_old_regime_prefix_in_prompt(self):
        result, captured = self._call_with_mocked_conditions(self.MOCK_CONDITIONS)
        self.assertNotIn('Open your briefing by naming the current macro regime',
                         captured['user_prompt'])

    def test_three_paragraph_instruction(self):
        result, captured = self._call_with_mocked_conditions(self.MOCK_CONDITIONS)
        self.assertIn('3 paragraphs', captured['system_prompt'])

    def test_market_data_preserved(self):
        result, captured = self._call_with_mocked_conditions(self.MOCK_CONDITIONS)
        self.assertIn('## MARKET DATA', captured['user_prompt'])

    def test_today_date_in_prompt(self):
        result, captured = self._call_with_mocked_conditions(self.MOCK_CONDITIONS)
        self.assertIn('Today is', captured['user_prompt'])


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
