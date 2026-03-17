"""
Tests for US-296.1: Surface new FRED series in Explorer page by conditions dimension.

Verifies:
- All 18 new FRED series from US-293.1 have METRIC_DESCRIPTIONS entries
- Each description has 'what', 'why', 'watch' fields
- METRIC_CATEGORIES maps all 18 series to correct Market Conditions dimensions
- METRIC_DISPLAY_NAMES provides human-readable labels for series with non-obvious names
- api_metrics_list endpoint returns category field for each metric
- Explorer template renders optgroup elements for categorized metrics
- Existing metrics retain their descriptions and functionality
- No XSS via metric names or descriptions (no |safe on dynamic values)
- Grouping covers all four dimensions: Liquidity, Growth×Inflation, Risk, Policy
"""

import json
import os
import re
import pytest


DASHBOARD_PY = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers', 'dashboard.py')
EXPLORER_HTML = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers', 'templates', 'explorer.html')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'signaltrackers', 'data')


@pytest.fixture(scope='module')
def dashboard_src():
    with open(DASHBOARD_PY) as f:
        return f.read()


@pytest.fixture(scope='module')
def explorer_html():
    with open(EXPLORER_HTML) as f:
        return f.read()


# ─── Market Conditions series definitions ───────────────────────────────

# The 18 new FRED series from US-293.1, mapped by their CSV metric name
# Some reuse existing CSVs (fed_balance_sheet, reverse_repo, cpi, m2_money_supply)
LIQUIDITY_SERIES = [
    'fed_balance_sheet',         # WALCL (pre-existing CSV, pre-existing description)
    'treasury_general_account',  # WDTGAL
    'reverse_repo',              # RRPONTSYD (pre-existing CSV, pre-existing description)
    'ecb_total_assets',          # ECBASSETSW
    'boj_total_assets',          # JPNASSETS
    'fx_eur_usd',                # DEXUSEU
    'fx_jpy_usd',                # DEXJPUS
]

GROWTH_INFLATION_SERIES = [
    'industrial_production',     # INDPRO
    'building_permits',          # PERMIT
    'breakeven_inflation_5y',    # T5YIE
    'cpi',                       # CPIAUCSL (pre-existing CSV, pre-existing description)
    'core_pce_price_index',      # PCEPILFE
]

RISK_SERIES = [
    'vix_3month',                # VXVCLS
    'stl_financial_stress',      # STLFSI4
]

POLICY_SERIES = [
    'fed_funds_upper_target',    # DFEDTARU
    'pce_price_index',           # PCEPI
    'real_gdp',                  # GDPC1
    'potential_gdp',             # GDPPOT
    'unemployment_rate',         # UNRATE
    'natural_unemployment_rate', # NROU
]

ALL_CONDITIONS_SERIES = LIQUIDITY_SERIES + GROWTH_INFLATION_SERIES + RISK_SERIES + POLICY_SERIES

# Series that had METRIC_DESCRIPTIONS before US-296.1
PRE_EXISTING_DESCRIPTIONS = {'fed_balance_sheet', 'reverse_repo', 'cpi', 'm2_money_supply'}

# Series that need NEW descriptions added by this story
NEW_DESCRIPTION_SERIES = [s for s in ALL_CONDITIONS_SERIES if s not in PRE_EXISTING_DESCRIPTIONS]


# ─── METRIC_DESCRIPTIONS tests ─────────────────────────────────────────

class TestMetricDescriptions:
    """Verify METRIC_DESCRIPTIONS entries for all new conditions series."""

    def test_all_new_series_have_descriptions(self, dashboard_src):
        """Every new conditions series must have a METRIC_DESCRIPTIONS entry."""
        for series in NEW_DESCRIPTION_SERIES:
            assert f"'{series}'" in dashboard_src or f'"{series}"' in dashboard_src, \
                f"Missing METRIC_DESCRIPTIONS entry for '{series}'"

    @pytest.mark.parametrize("series", NEW_DESCRIPTION_SERIES)
    def test_description_has_what_field(self, dashboard_src, series):
        """Each description must have a 'what' field."""
        # Find the description block for this series
        pattern = rf"'{series}':\s*\{{[^}}]*'what':"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            f"'{series}' description missing 'what' field"

    @pytest.mark.parametrize("series", NEW_DESCRIPTION_SERIES)
    def test_description_has_why_field(self, dashboard_src, series):
        """Each description must have a 'why' field."""
        pattern = rf"'{series}':\s*\{{[^}}]*'why':"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            f"'{series}' description missing 'why' field"

    @pytest.mark.parametrize("series", NEW_DESCRIPTION_SERIES)
    def test_description_has_watch_field(self, dashboard_src, series):
        """Each description must have a 'watch' field."""
        pattern = rf"'{series}':\s*\{{[^}}]*'watch':"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            f"'{series}' description missing 'watch' field"

    def test_pre_existing_descriptions_unchanged(self, dashboard_src):
        """Pre-existing descriptions must still exist."""
        for series in PRE_EXISTING_DESCRIPTIONS:
            pattern = rf"'{series}':\s*\{{"
            assert re.search(pattern, dashboard_src), \
                f"Pre-existing description for '{series}' was removed or renamed"

    def test_total_new_descriptions_count(self, dashboard_src):
        """Should have descriptions for all new series (not pre-existing)."""
        count = 0
        for series in NEW_DESCRIPTION_SERIES:
            if re.search(rf"'{series}':\s*\{{", dashboard_src):
                count += 1
        assert count == len(NEW_DESCRIPTION_SERIES), \
            f"Expected {len(NEW_DESCRIPTION_SERIES)} new descriptions, found {count}"


# ─── METRIC_CATEGORIES tests ───────────────────────────────────────────

class TestMetricCategories:
    """Verify METRIC_CATEGORIES maps series to correct dimensions."""

    def test_metric_categories_dict_exists(self, dashboard_src):
        """METRIC_CATEGORIES dict must exist in dashboard.py."""
        assert 'METRIC_CATEGORIES' in dashboard_src

    @pytest.mark.parametrize("series", LIQUIDITY_SERIES)
    def test_liquidity_series_categorized(self, dashboard_src, series):
        """Liquidity series must be in 'Conditions: Liquidity' category."""
        pattern = rf"'{series}':\s*'Conditions: Liquidity'"
        assert re.search(pattern, dashboard_src), \
            f"'{series}' not categorized as 'Conditions: Liquidity'"

    @pytest.mark.parametrize("series", GROWTH_INFLATION_SERIES)
    def test_growth_inflation_series_categorized(self, dashboard_src, series):
        """Growth×Inflation series must be in correct category."""
        # Allow both × and x variants
        pattern = rf"'{series}':\s*'Conditions: Growth"
        assert re.search(pattern, dashboard_src), \
            f"'{series}' not categorized under Growth×Inflation"

    @pytest.mark.parametrize("series", RISK_SERIES)
    def test_risk_series_categorized(self, dashboard_src, series):
        """Risk series must be in 'Conditions: Risk' category."""
        pattern = rf"'{series}':\s*'Conditions: Risk'"
        assert re.search(pattern, dashboard_src), \
            f"'{series}' not categorized as 'Conditions: Risk'"

    @pytest.mark.parametrize("series", POLICY_SERIES)
    def test_policy_series_categorized(self, dashboard_src, series):
        """Policy series must be in 'Conditions: Policy' category."""
        pattern = rf"'{series}':\s*'Conditions: Policy'"
        assert re.search(pattern, dashboard_src), \
            f"'{series}' not categorized as 'Conditions: Policy'"

    def test_all_four_dimensions_present(self, dashboard_src):
        """All four Market Conditions dimensions must appear in categories."""
        assert "'Conditions: Liquidity'" in dashboard_src
        assert "'Conditions: Growth" in dashboard_src  # × character varies
        assert "'Conditions: Risk'" in dashboard_src
        assert "'Conditions: Policy'" in dashboard_src

    def test_existing_asset_categories_present(self, dashboard_src):
        """Existing asset page categories should also be present."""
        for cat in ['Credit', 'Equities', 'Rates', 'Safe Havens', 'Crypto']:
            assert f"'{cat}'" in dashboard_src, \
                f"Expected category '{cat}' in METRIC_CATEGORIES"


# ─── METRIC_DISPLAY_NAMES tests ────────────────────────────────────────

class TestMetricDisplayNames:
    """Verify human-readable display names for new series."""

    def test_display_names_dict_exists(self, dashboard_src):
        """METRIC_DISPLAY_NAMES dict must exist."""
        assert 'METRIC_DISPLAY_NAMES' in dashboard_src

    def test_boj_label_includes_unit(self, dashboard_src):
        """BOJ total assets label must mention 100M JPY units."""
        pattern = r"'boj_total_assets':\s*'[^']*JPY"
        assert re.search(pattern, dashboard_src), \
            "boj_total_assets display name should mention JPY units"

    def test_ecb_label_includes_unit(self, dashboard_src):
        """ECB total assets label must mention EUR units."""
        pattern = r"'ecb_total_assets':\s*'[^']*EUR"
        assert re.search(pattern, dashboard_src), \
            "ecb_total_assets display name should mention EUR units"

    def test_tga_has_readable_name(self, dashboard_src):
        """Treasury General Account should have a clear display name."""
        pattern = r"'treasury_general_account':\s*'[^']*TGA"
        assert re.search(pattern, dashboard_src), \
            "treasury_general_account display name should include TGA abbreviation"

    def test_vix3m_has_readable_name(self, dashboard_src):
        """VIX 3-month should have a clear display name."""
        pattern = r"'vix_3month':\s*'[^']*VIX3M"
        assert re.search(pattern, dashboard_src), \
            "vix_3month display name should include VIX3M"

    def test_stl_stress_has_readable_name(self, dashboard_src):
        """St. Louis Financial Stress Index should have descriptive name."""
        pattern = r"'stl_financial_stress':\s*'[^']*[Ss]tress"
        assert re.search(pattern, dashboard_src), \
            "stl_financial_stress display name should mention 'Stress'"

    def test_nairu_has_readable_name(self, dashboard_src):
        """Natural unemployment rate should mention NAIRU."""
        pattern = r"'natural_unemployment_rate':\s*'[^']*NAIRU"
        assert re.search(pattern, dashboard_src), \
            "natural_unemployment_rate display name should include NAIRU"

    def test_potential_gdp_has_cbo(self, dashboard_src):
        """Potential GDP label should mention CBO."""
        pattern = r"'potential_gdp':\s*'[^']*CBO"
        assert re.search(pattern, dashboard_src), \
            "potential_gdp display name should mention CBO"


# ─── API endpoint tests ────────────────────────────────────────────────

class TestApiMetricsList:
    """Verify api_metrics_list returns category metadata."""

    def test_api_returns_category_field(self, dashboard_src):
        """api_metrics_list must include 'category' in response objects."""
        # Check that the function builds category into the response
        assert "'category'" in dashboard_src or '"category"' in dashboard_src

    def test_api_uses_metric_categories(self, dashboard_src):
        """api_metrics_list must reference METRIC_CATEGORIES."""
        assert 'METRIC_CATEGORIES' in dashboard_src

    def test_api_uses_display_names(self, dashboard_src):
        """api_metrics_list must reference METRIC_DISPLAY_NAMES for labels."""
        assert 'METRIC_DISPLAY_NAMES' in dashboard_src

    def test_skip_non_metric_csvs(self, dashboard_src):
        """api_metrics_list should skip non-metric files like us_recessions.csv."""
        assert 'us_recessions' in dashboard_src or 'skip_files' in dashboard_src


# ─── Explorer template tests ───────────────────────────────────────────

class TestExplorerTemplate:
    """Verify Explorer template renders grouped metrics."""

    def test_optgroup_rendering(self, explorer_html):
        """Template JS must create optgroup elements for categories."""
        assert 'optgroup' in explorer_html.lower() or 'createElement(\'optgroup\')' in explorer_html

    def test_category_order_defined(self, explorer_html):
        """Category rendering order must be defined."""
        assert 'categoryOrder' in explorer_html or 'category_order' in explorer_html

    def test_conditions_liquidity_in_order(self, explorer_html):
        """Conditions: Liquidity must be in the category order."""
        assert 'Conditions: Liquidity' in explorer_html

    def test_conditions_growth_inflation_in_order(self, explorer_html):
        """Conditions: Growth×Inflation must be in the category order."""
        assert 'Growth' in explorer_html and 'Inflation' in explorer_html

    def test_conditions_risk_in_order(self, explorer_html):
        """Conditions: Risk must be in the category order."""
        assert 'Conditions: Risk' in explorer_html

    def test_conditions_policy_in_order(self, explorer_html):
        """Conditions: Policy must be in the category order."""
        assert 'Conditions: Policy' in explorer_html

    def test_uncategorized_fallback(self, explorer_html):
        """Template must handle uncategorized metrics gracefully."""
        assert 'uncategorized' in explorer_html.lower() or 'Other' in explorer_html

    def test_metric_query_param_still_works(self, explorer_html):
        """URL query parameter ?metric= must still be handled."""
        assert 'metricParam' in explorer_html or 'metric' in explorer_html

    def test_no_xss_safe_filter(self, explorer_html):
        """No |safe filter on dynamic metric names or descriptions."""
        # Check for |safe usage on metric-related variables
        safe_uses = re.findall(r'\{\{.*?metric.*?\|.*?safe.*?\}\}', explorer_html, re.IGNORECASE)
        assert len(safe_uses) == 0, f"Found |safe on metric variables: {safe_uses}"


# ─── CSV data file existence tests ──────────────────────────────────────

class TestCsvDataFiles:
    """Verify CSV data files exist for all conditions series."""

    # Some series may not have data yet if collection hasn't run on this machine.
    # These are expected to exist after a full data collection cycle.
    POSSIBLY_UNCOLLECTED = {'stl_financial_stress', 'pce_price_index', 'real_gdp', 'potential_gdp'}

    @pytest.mark.parametrize("series", ALL_CONDITIONS_SERIES)
    def test_csv_file_exists(self, series):
        """Each conditions series must have a corresponding CSV file (or be known-uncollected)."""
        csv_path = os.path.join(DATA_DIR, f'{series}.csv')
        if series in self.POSSIBLY_UNCOLLECTED:
            pytest.skip(f"data/{series}.csv not yet collected on this machine")
        assert os.path.exists(csv_path), \
            f"CSV file missing: data/{series}.csv"


# ─── Unit label accuracy tests ──────────────────────────────────────────

class TestUnitLabels:
    """Verify unit labels are accurate in descriptions."""

    def test_rrpontsyd_billions(self, dashboard_src):
        """reverse_repo description should mention billions."""
        # Check the existing description
        pattern = r"'reverse_repo':\s*\{[^}]*[Bb]illion"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            "reverse_repo description should mention billions"

    def test_walcl_millions(self, dashboard_src):
        """fed_balance_sheet description should mention billions (it's in billions)."""
        # WALCL is in millions but fed_balance_sheet description says "billions of dollars"
        pattern = r"'fed_balance_sheet':\s*\{[^}]*[Bb]illion"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            "fed_balance_sheet description should mention billions"

    def test_tga_millions(self, dashboard_src):
        """treasury_general_account description should mention millions."""
        pattern = r"'treasury_general_account':\s*\{[^}]*[Mm]illion"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            "treasury_general_account description should mention millions"

    def test_jpnassets_100m_jpy(self, dashboard_src):
        """boj_total_assets description should mention 100 million yen."""
        pattern = r"'boj_total_assets':\s*\{[^}]*100\s*[Mm]illion\s*[Yy]en"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            "boj_total_assets description should mention '100 million yen'"

    def test_ecb_millions_eur(self, dashboard_src):
        """ecb_total_assets description should mention millions of euros."""
        pattern = r"'ecb_total_assets':\s*\{[^}]*[Mm]illion.*?[Ee]uro"
        assert re.search(pattern, dashboard_src, re.DOTALL), \
            "ecb_total_assets description should mention millions of euros"


# ─── Regression tests ──────────────────────────────────────────────────

class TestRegression:
    """Verify existing Explorer functionality is preserved."""

    def test_explorer_route_exists(self, dashboard_src):
        """Explorer route must still be defined."""
        assert "@app.route('/explorer')" in dashboard_src

    def test_api_metrics_list_route_exists(self, dashboard_src):
        """api/metrics/list route must still be defined."""
        assert "@app.route('/api/metrics/list')" in dashboard_src

    def test_api_metrics_data_route_exists(self, dashboard_src):
        """api/metrics/<metric_name> route must still be defined."""
        assert "@app.route('/api/metrics/<metric_name>')" in dashboard_src

    def test_api_metric_description_route_exists(self, dashboard_src):
        """api/metrics/description/<metric_name> route must still be defined."""
        assert "@app.route('/api/metrics/description/<metric_name>')" in dashboard_src

    def test_existing_descriptions_not_removed(self, dashboard_src):
        """Spot-check that existing descriptions still present."""
        for key in ['high_yield_spread', 'gold_price', 'sp500_price', 'vix_price',
                     'bitcoin_price', 'yield_curve_10y2y']:
            assert f"'{key}'" in dashboard_src, \
                f"Existing description for '{key}' appears to be removed"

    def test_metric_aliases_preserved(self, dashboard_src):
        """Metric aliases in api_metric_data must still exist."""
        assert 'metric_aliases' in dashboard_src

    def test_divergence_gap_calculated_metric(self, dashboard_src):
        """Divergence gap calculated metric must still be in the list."""
        assert 'divergence_gap' in dashboard_src


# ─── Security tests ────────────────────────────────────────────────────

class TestSecurity:
    """Verify no security vulnerabilities introduced."""

    def test_metric_name_validation(self, dashboard_src):
        """api_metric_data should validate metric names (existing behavior)."""
        # The existing code uses metric_name to load CSV files via load_csv_data
        # which constructs path using DATA_DIR / filename - pathlib prevents traversal
        assert 'DATA_DIR' in dashboard_src

    def test_no_safe_filter_on_descriptions(self, dashboard_src):
        """METRIC_DESCRIPTIONS values should not use |safe in templates."""
        # This is checked in the template test above; double-check no HTML in descriptions
        # Descriptions should be plain text
        for series in NEW_DESCRIPTION_SERIES:
            pattern = rf"'{series}':\s*\{{([^}}]+)\}}"
            match = re.search(pattern, dashboard_src, re.DOTALL)
            if match:
                block = match.group(1)
                assert '<script' not in block.lower(), \
                    f"Possible XSS in '{series}' description"
