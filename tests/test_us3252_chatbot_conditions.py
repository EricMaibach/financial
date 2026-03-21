"""
Tests for US-325.2: Chatbot conditions context and history integration.

Verifies that:
- Chatbot system prompt includes market conditions context (all 4 dimensions)
- Chatbot system prompt includes conditions history for trend-aware answers
- Old regime labels removed from chatbot prompt construction
- Section-opening live data uses conditions instead of regime for asset sections
- Conditions framework terminology used (quadrant, not regime)
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Chatbot endpoint — structural tests on dashboard.py
# ---------------------------------------------------------------------------


class TestChatbotConditionsImports(unittest.TestCase):
    """dashboard.py must import conditions context builders from ai_summary."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def test_build_conditions_context_imported(self):
        self.assertIn('_build_conditions_context', self.src)

    def test_build_conditions_history_context_imported(self):
        self.assertIn('_build_conditions_history_context', self.src)

    def test_get_market_conditions_imported(self):
        self.assertIn('get_market_conditions', self.src)

    def test_get_conditions_history_imported(self):
        self.assertIn('get_conditions_history', self.src)


class TestChatbotSystemPrompt(unittest.TestCase):
    """Chatbot system prompt must reference conditions framework, not regime."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')
        # Extract the api_chatbot function body
        start = cls.src.find('def api_chatbot()')
        end = cls.src.find('\ndef ', start + 1)
        cls.chatbot_fn = cls.src[start:end] if end != -1 else cls.src[start:]

    def test_conditions_context_built_in_chatbot(self):
        """Chatbot function must call _build_conditions_context."""
        self.assertIn('_build_conditions_context', self.chatbot_fn)

    def test_conditions_history_built_in_chatbot(self):
        """Chatbot function must call _build_conditions_history_context."""
        self.assertIn('_build_conditions_history_context', self.chatbot_fn)

    def test_get_market_conditions_called(self):
        """Chatbot function must call get_market_conditions()."""
        self.assertIn('get_market_conditions()', self.chatbot_fn)

    def test_get_conditions_history_called(self):
        """Chatbot function must call get_conditions_history()."""
        self.assertIn('get_conditions_history()', self.chatbot_fn)

    def test_quadrant_terminology_in_prompt(self):
        """System prompt must reference the four-quadrant framework."""
        self.assertIn('quadrant', self.chatbot_fn.lower())

    def test_four_dimensions_mentioned(self):
        """System prompt must mention all four conditions dimensions."""
        self.assertIn('liquidity', self.chatbot_fn.lower())
        self.assertIn('risk', self.chatbot_fn.lower())
        self.assertIn('policy', self.chatbot_fn.lower())

    def test_no_old_regime_labels_in_prompt(self):
        """System prompt must not reference Bull, Bear, Neutral, Recession Watch."""
        # Check the system_prompt string construction area specifically
        prompt_start = self.chatbot_fn.find('system_prompt = (')
        prompt_end = self.chatbot_fn.find(')', prompt_start + 50)
        prompt_section = self.chatbot_fn[prompt_start:prompt_end]
        self.assertNotIn("'Bull'", prompt_section)
        self.assertNotIn("'Bear'", prompt_section)
        self.assertNotIn("'Neutral'", prompt_section)
        self.assertNotIn("'Recession Watch'", prompt_section)

    def test_error_handling_for_conditions(self):
        """Conditions context building must be wrapped in try/except."""
        # Find the conditions context section
        cond_start = self.chatbot_fn.find('conditions_context')
        cond_section = self.chatbot_fn[cond_start:cond_start + 900]
        self.assertIn('except', cond_section)


# ---------------------------------------------------------------------------
# Section-opening live data — no regime in asset sections
# ---------------------------------------------------------------------------


class TestSectionLiveDataConditions(unittest.TestCase):
    """_get_section_live_data must use conditions, not regime, for asset sections."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')
        start = cls.src.find('def _get_section_live_data(')
        end = cls.src.find('\ndef ', start + 1)
        cls.fn = cls.src[start:end] if end != -1 else cls.src[start:]

    def test_market_conditions_section_handler_exists(self):
        """market-conditions section must have its own handler, not generic fallback."""
        self.assertIn("section_id == 'market-conditions'", self.fn)

    def test_market_conditions_uses_build_context(self):
        """market-conditions handler must use _build_conditions_context."""
        mc_start = self.fn.find("section_id == 'market-conditions'")
        mc_section = self.fn[mc_start:mc_start + 300]
        self.assertIn('_build_conditions_context', mc_section)

    def test_asset_credit_uses_conditions(self):
        """Credit section must use conditions quadrant, not macro regime."""
        credit_start = self.fn.find("section_id == 'asset-credit'")
        credit_section = self.fn[credit_start:credit_start + 1200]
        self.assertIn('quadrant', credit_section.lower())
        self.assertNotIn("Macro regime:", credit_section)

    def test_asset_equity_uses_conditions(self):
        """Equity section must use conditions quadrant, not macro regime."""
        equity_start = self.fn.find("section_id == 'asset-equity'")
        equity_section = self.fn[equity_start:equity_start + 900]
        self.assertIn('quadrant', equity_section.lower())
        self.assertNotIn("Macro regime:", equity_section)

    def test_asset_rates_uses_conditions(self):
        """Rates section must use conditions quadrant, not macro regime."""
        rates_start = self.fn.find("section_id == 'asset-rates'")
        rates_section = self.fn[rates_start:rates_start + 900]
        self.assertIn('quadrant', rates_section.lower())
        self.assertNotIn("Macro regime:", rates_section)

    def test_asset_dollar_uses_conditions(self):
        """Dollar section must use conditions quadrant, not macro regime."""
        dollar_start = self.fn.find("section_id == 'asset-dollar'")
        dollar_section = self.fn[dollar_start:dollar_start + 900]
        self.assertIn('quadrant', dollar_section.lower())
        self.assertNotIn("Macro regime:", dollar_section)

    def test_asset_crypto_uses_conditions(self):
        """Crypto section must use conditions quadrant, not macro regime."""
        crypto_start = self.fn.find("section_id == 'asset-crypto'")
        crypto_section = self.fn[crypto_start:crypto_start + 900]
        self.assertIn('quadrant', crypto_section.lower())
        self.assertNotIn("Macro regime:", crypto_section)

    def test_asset_safe_havens_uses_conditions(self):
        """Safe havens section must use conditions quadrant, not macro regime."""
        sh_start = self.fn.find("section_id == 'asset-safe-havens'")
        sh_section = self.fn[sh_start:sh_start + 900]
        self.assertIn('quadrant', sh_section.lower())
        self.assertNotIn("Macro regime:", sh_section)

    def test_asset_property_uses_conditions(self):
        """Property section must use conditions quadrant, not macro regime."""
        prop_start = self.fn.find("section_id == 'asset-property'")
        prop_section = self.fn[prop_start:prop_start + 1800]
        self.assertIn('quadrant', prop_section.lower())
        self.assertNotIn("Macro regime:", prop_section)

    def test_trade_pulse_uses_conditions(self):
        """Trade pulse section must use conditions quadrant, not macro regime."""
        tp_start = self.fn.find("section_id == 'trade-pulse-section'")
        tp_section = self.fn[tp_start:tp_start + 900]
        self.assertIn('quadrant', tp_section.lower())
        self.assertNotIn("Macro regime:", tp_section)

    def test_generic_fallback_uses_conditions(self):
        """Generic fallback must use conditions, not regime."""
        # Find the fallback section (after all specific section_id checks)
        fallback_start = self.fn.find("# Generic fallback")
        if fallback_start == -1:
            fallback_start = self.fn.rfind("get_market_conditions()")
        fallback_section = self.fn[fallback_start:fallback_start + 300]
        self.assertIn('quadrant', fallback_section.lower())
        self.assertNotIn('get_macro_regime', fallback_section)


# ---------------------------------------------------------------------------
# Functional tests — conditions context builder functions
# ---------------------------------------------------------------------------

# Import at module level to avoid bound-method issues
from ai_summary import _build_conditions_context, _build_conditions_history_context


class TestBuildConditionsContextFunction(unittest.TestCase):
    """_build_conditions_context must include all 4 dimensions."""

    def test_returns_empty_for_none(self):
        self.assertEqual(_build_conditions_context(None), "")

    def test_returns_empty_for_empty_dict(self):
        self.assertEqual(_build_conditions_context({}), "")

    def test_includes_quadrant(self):
        conditions = {
            'quadrant': 'Goldilocks',
            'dimensions': {
                'quadrant': {'growth_composite': 0.5, 'inflation_composite': -0.3},
                'liquidity': {'state': 'Expanding', 'score': 0.8},
                'risk': {'state': 'Calm', 'score': 20, 'vix_level': 15.0},
                'policy': {'stance': 'Accommodative', 'direction': 'Easing', 'taylor_gap': -1.5}
            }
        }
        result = _build_conditions_context(conditions)
        self.assertIn('Goldilocks', result)
        self.assertIn('CURRENT MARKET CONDITIONS', result)

    def test_includes_all_four_dimensions(self):
        conditions = {
            'quadrant': 'Stagflation',
            'dimensions': {
                'quadrant': {'growth_composite': -0.5, 'inflation_composite': 0.8},
                'liquidity': {'state': 'Contracting', 'score': -0.5},
                'risk': {'state': 'Elevated', 'score': 65, 'vix_level': 28.0},
                'policy': {'stance': 'Restrictive', 'direction': 'Tightening', 'taylor_gap': 2.0}
            }
        }
        result = _build_conditions_context(conditions)
        self.assertIn('Liquidity: Contracting', result)
        self.assertIn('Risk: Elevated', result)
        self.assertIn('Policy: Restrictive', result)
        self.assertIn('Growth composite', result)

    def test_includes_growth_inflation_scores(self):
        conditions = {
            'quadrant': 'Reflation',
            'dimensions': {
                'quadrant': {'growth_composite': 1.2, 'inflation_composite': 0.5},
                'liquidity': {'state': 'Expanding'},
                'risk': {'state': 'Normal'},
                'policy': {'stance': 'Neutral', 'direction': 'Paused'}
            }
        }
        result = _build_conditions_context(conditions)
        self.assertIn('+1.20', result)
        self.assertIn('+0.50', result)

    def test_includes_asset_expectations(self):
        conditions = {
            'quadrant': 'Goldilocks',
            'dimensions': {
                'quadrant': {},
                'liquidity': {'state': 'Expanding'},
                'risk': {'state': 'Calm'},
                'policy': {'stance': 'Accommodative', 'direction': 'Easing'}
            },
            'asset_expectations': [
                {'asset': 'Equities', 'direction': 'Bullish', 'magnitude': 'Strong'},
                {'asset': 'Bonds', 'direction': 'Neutral', 'magnitude': 'Moderate'}
            ]
        }
        result = _build_conditions_context(conditions)
        self.assertIn('Equities: Bullish (Strong)', result)
        self.assertIn('Bonds: Neutral (Moderate)', result)


class TestBuildConditionsHistoryContext(unittest.TestCase):
    """_build_conditions_history_context must format trend data for AI."""

    def test_returns_empty_for_none(self):
        self.assertEqual(_build_conditions_history_context(None), "")

    def test_returns_empty_for_empty_dict(self):
        self.assertEqual(_build_conditions_history_context({}), "")

    def test_formats_history_entries(self):
        from datetime import datetime, timedelta
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        history = {
            yesterday: {
                'quadrant': 'Goldilocks',
                'dimensions': {
                    'liquidity': {'state': 'Expanding', 'score': 0.8},
                    'risk': {'state': 'Calm'},
                    'policy': {'stance': 'Accommodative', 'direction': 'Easing'}
                }
            },
            today: {
                'quadrant': 'Reflation',
                'dimensions': {
                    'liquidity': {'state': 'Neutral', 'score': 0.1},
                    'risk': {'state': 'Normal'},
                    'policy': {'stance': 'Neutral', 'direction': 'Paused'}
                }
            }
        }
        result = _build_conditions_history_context(history, days=90)
        self.assertIn('CONDITIONS HISTORY', result)
        self.assertIn('Goldilocks', result)
        self.assertIn('Reflation', result)

    def test_identifies_transitions(self):
        from datetime import datetime, timedelta
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        history = {
            yesterday: {
                'quadrant': 'Stagflation',
                'dimensions': {
                    'liquidity': {'state': 'Contracting'},
                    'risk': {'state': 'Elevated'},
                    'policy': {'stance': 'Restrictive', 'direction': 'Tightening'}
                }
            },
            today: {
                'quadrant': 'Deflation Risk',
                'dimensions': {
                    'liquidity': {'state': 'Contracting'},
                    'risk': {'state': 'Stressed'},
                    'policy': {'stance': 'Restrictive', 'direction': 'Paused'}
                }
            }
        }
        result = _build_conditions_history_context(history, days=90)
        self.assertIn('Stagflation', result)
        self.assertIn('Deflation Risk', result)
        self.assertIn('→', result)

    def test_includes_growth_inflation_scores(self):
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        history = {
            today: {
                'quadrant': 'Goldilocks',
                'growth_score': 0.75,
                'inflation_score': -0.30,
                'dimensions': {
                    'liquidity': {'state': 'Expanding'},
                    'risk': {'state': 'Calm'},
                    'policy': {'stance': 'Accommodative', 'direction': 'Easing'}
                }
            }
        }
        result = _build_conditions_history_context(history, days=90)
        self.assertIn('+0.75', result)
        self.assertIn('-0.30', result)


if __name__ == '__main__':
    unittest.main()
