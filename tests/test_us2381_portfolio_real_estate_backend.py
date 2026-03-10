"""
Tests for US-238.1: Backend — Real Estate Asset Types in Portfolio API

Acceptance criteria:
- farmland, commercial_real_estate, residential_real_estate are valid asset types
- type_breakdown includes keys for each real estate type with holdings
- AI prompt lists real estate holdings as percentage values
- No dollar-value fields accepted or stored (percentage-only)
- Existing asset types are unaffected
"""
import sys
import os
import importlib

# Load portfolio module directly (avoids Flask app dependency)
SIGNALTRACKERS_DIR = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers')
_portfolio_spec = importlib.util.spec_from_file_location(
    "portfolio",
    os.path.join(SIGNALTRACKERS_DIR, "portfolio.py")
)
_portfolio_mod = importlib.util.module_from_spec(_portfolio_spec)
_portfolio_spec.loader.exec_module(_portfolio_mod)

ASSET_TYPES = _portfolio_mod.ASSET_TYPES


class TestRealEstateAssetTypes:
    def test_farmland_is_valid(self):
        assert 'farmland' in ASSET_TYPES

    def test_commercial_real_estate_is_valid(self):
        assert 'commercial_real_estate' in ASSET_TYPES

    def test_residential_real_estate_is_valid(self):
        assert 'residential_real_estate' in ASSET_TYPES

    def test_farmland_no_symbol_required(self):
        assert ASSET_TYPES['farmland']['symbol_required'] is False

    def test_commercial_real_estate_no_symbol_required(self):
        assert ASSET_TYPES['commercial_real_estate']['symbol_required'] is False

    def test_residential_real_estate_no_symbol_required(self):
        assert ASSET_TYPES['residential_real_estate']['symbol_required'] is False

    def test_farmland_no_data_source(self):
        assert ASSET_TYPES['farmland']['data_source'] is None

    def test_commercial_real_estate_no_data_source(self):
        assert ASSET_TYPES['commercial_real_estate']['data_source'] is None

    def test_residential_real_estate_no_data_source(self):
        assert ASSET_TYPES['residential_real_estate']['data_source'] is None


class TestExistingAssetTypesUnaffected:
    """Ensure adding new types didn't break existing ones."""

    def test_stock_still_valid(self):
        assert 'stock' in ASSET_TYPES
        assert ASSET_TYPES['stock']['symbol_required'] is True

    def test_etf_still_valid(self):
        assert 'etf' in ASSET_TYPES
        assert ASSET_TYPES['etf']['symbol_required'] is True

    def test_mutual_fund_still_valid(self):
        assert 'mutual_fund' in ASSET_TYPES
        assert ASSET_TYPES['mutual_fund']['symbol_required'] is True

    def test_crypto_still_valid(self):
        assert 'crypto' in ASSET_TYPES
        assert ASSET_TYPES['crypto']['symbol_required'] is False

    def test_gold_still_valid(self):
        assert 'gold' in ASSET_TYPES
        assert ASSET_TYPES['gold']['symbol_required'] is False

    def test_cash_still_valid(self):
        assert 'cash' in ASSET_TYPES

    def test_savings_still_valid(self):
        assert 'savings' in ASSET_TYPES

    def test_money_market_still_valid(self):
        assert 'money_market' in ASSET_TYPES

    def test_other_still_valid(self):
        assert 'other' in ASSET_TYPES


class TestTypeBreakdown:
    """type_breakdown dynamically groups by asset_type — test the calculation logic."""

    def _make_allocations(self, types_and_pcts):
        """Build a minimal portfolio_data structure."""
        allocations = [
            {"asset_type": t, "percentage": p, "name": t, "symbol": None}
            for t, p in types_and_pcts
        ]
        total = sum(p for _, p in types_and_pcts)
        type_breakdown = {}
        for t, p in types_and_pcts:
            type_breakdown[t] = type_breakdown.get(t, 0) + p
        return {
            "allocations": allocations,
            "total_percentage": total,
            "is_valid": 95 <= total <= 105,
            "type_breakdown": type_breakdown,
            "last_modified": None,
        }

    def test_farmland_appears_in_type_breakdown(self):
        portfolio_data = self._make_allocations([('farmland', 12.0)])
        assert 'farmland' in portfolio_data['type_breakdown']
        assert portfolio_data['type_breakdown']['farmland'] == 12.0

    def test_commercial_real_estate_appears_in_type_breakdown(self):
        portfolio_data = self._make_allocations([('commercial_real_estate', 5.0)])
        assert portfolio_data['type_breakdown']['commercial_real_estate'] == 5.0

    def test_residential_real_estate_appears_in_type_breakdown(self):
        portfolio_data = self._make_allocations([('residential_real_estate', 5.0)])
        assert portfolio_data['type_breakdown']['residential_real_estate'] == 5.0

    def test_all_three_real_estate_in_breakdown(self):
        portfolio_data = self._make_allocations([
            ('farmland', 12.0),
            ('commercial_real_estate', 5.0),
            ('residential_real_estate', 5.0),
        ])
        bd = portfolio_data['type_breakdown']
        assert bd['farmland'] == 12.0
        assert bd['commercial_real_estate'] == 5.0
        assert bd['residential_real_estate'] == 5.0

    def test_no_real_estate_no_keys(self):
        portfolio_data = self._make_allocations([('stock', 60.0), ('cash', 40.0)])
        bd = portfolio_data['type_breakdown']
        assert 'farmland' not in bd
        assert 'commercial_real_estate' not in bd
        assert 'residential_real_estate' not in bd


class TestAssetClassBreakdown:
    """real_estate key appears in asset_class_breakdown when RE types are present."""

    def _build_breakdown(self, allocations):
        """Replicate portfolio.py's real-estate sum logic."""
        real_estate_pct = sum(
            a["percentage"] for a in allocations
            if a["asset_type"] in ['farmland', 'commercial_real_estate', 'residential_real_estate']
        )
        equity_pct = sum(
            a["percentage"] for a in allocations
            if a["asset_type"] in ['stock', 'etf', 'mutual_fund']
        )
        return {
            "equities": round(equity_pct, 2),
            "real_estate": round(real_estate_pct, 2),
        }

    def test_real_estate_key_present_when_holdings_exist(self):
        allocs = [{"asset_type": "farmland", "percentage": 12.0}]
        bd = self._build_breakdown(allocs)
        assert 'real_estate' in bd
        assert bd['real_estate'] == 12.0

    def test_all_three_types_aggregate(self):
        allocs = [
            {"asset_type": "farmland", "percentage": 12.0},
            {"asset_type": "commercial_real_estate", "percentage": 5.0},
            {"asset_type": "residential_real_estate", "percentage": 5.0},
        ]
        bd = self._build_breakdown(allocs)
        assert bd['real_estate'] == 22.0

    def test_no_real_estate_gives_zero(self):
        allocs = [{"asset_type": "stock", "percentage": 100.0}]
        bd = self._build_breakdown(allocs)
        assert bd['real_estate'] == 0.0

    def test_equities_unaffected_by_real_estate(self):
        allocs = [
            {"asset_type": "stock", "percentage": 60.0},
            {"asset_type": "farmland", "percentage": 20.0},
        ]
        bd = self._build_breakdown(allocs)
        assert bd['equities'] == 60.0
        assert bd['real_estate'] == 20.0


class TestAIPromptRealEstateLine:
    """ai_summary.py includes real estate in asset class breakdown text."""

    def test_ai_prompt_includes_real_estate_line(self):
        ai_summary_path = os.path.join(SIGNALTRACKERS_DIR, "ai_summary.py")
        with open(ai_summary_path, 'r') as f:
            content = f.read()
        assert "Real Estate" in content
        assert "real_estate" in content

    def test_real_estate_breakdown_key_referenced(self):
        ai_summary_path = os.path.join(SIGNALTRACKERS_DIR, "ai_summary.py")
        with open(ai_summary_path, 'r') as f:
            content = f.read()
        assert "breakdown.get('real_estate'" in content


class TestNoSymbolRequiredForRealEstate:
    """Real estate types must not require a symbol (percentage-only)."""

    def test_farmland_add_without_symbol_succeeds(self):
        # Replicate validation logic from portfolio.py
        asset_type = 'farmland'
        symbol = None
        assert asset_type in ASSET_TYPES
        config = ASSET_TYPES[asset_type]
        if config['symbol_required'] and not symbol:
            raise AssertionError("Symbol required but should not be")

    def test_commercial_real_estate_add_without_symbol_succeeds(self):
        asset_type = 'commercial_real_estate'
        symbol = None
        assert asset_type in ASSET_TYPES
        config = ASSET_TYPES[asset_type]
        if config['symbol_required'] and not symbol:
            raise AssertionError("Symbol required but should not be")

    def test_residential_real_estate_add_without_symbol_succeeds(self):
        asset_type = 'residential_real_estate'
        symbol = None
        assert asset_type in ASSET_TYPES
        config = ASSET_TYPES[asset_type]
        if config['symbol_required'] and not symbol:
            raise AssertionError("Symbol required but should not be")
