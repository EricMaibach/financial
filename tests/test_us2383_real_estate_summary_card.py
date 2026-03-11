"""
Tests for US-238.3: UI — Real Estate Summary Card
Verifies HTML structure and JS logic in portfolio.html.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'templates', 'portfolio.html')


def _read_template():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


class TestRealEstateSummaryCardHTML:
    def test_card_label_real_estate(self):
        html = _read_template()
        assert '>REAL ESTATE<' in html

    def test_real_estate_pct_id_exists(self):
        html = _read_template()
        assert 'id="real-estate-pct"' in html

    def test_real_estate_breakdown_id_exists(self):
        html = _read_template()
        assert 'id="real-estate-breakdown"' in html

    def test_default_pct_value(self):
        html = _read_template()
        # The h2 with id real-estate-pct should have 0% as default
        assert re.search(r'id="real-estate-pct"[^>]*>\s*0%', html)

    def test_default_breakdown_text(self):
        html = _read_template()
        assert 'No real estate holdings' in html

    def test_card_uses_metric_card_class(self):
        html = _read_template()
        # Find the real estate card block
        re_section = html[html.index('REAL ESTATE'):]
        # Walk back to find the card div
        card_section = html[max(0, html.index('REAL ESTATE') - 200):html.index('REAL ESTATE') + 200]
        assert 'metric-card' in card_section

    def test_card_uses_col_xl_3_col_md_6(self):
        html = _read_template()
        re_idx = html.index('real-estate-pct')
        surrounding = html[re_idx - 300:re_idx]
        assert 'col-xl-3' in surrounding
        assert 'col-md-6' in surrounding

    def test_card_uses_col_mb_3(self):
        html = _read_template()
        re_idx = html.index('real-estate-pct')
        surrounding = html[re_idx - 300:re_idx]
        assert 'mb-3' in surrounding

    def test_card_structure_h6_h2_small(self):
        html = _read_template()
        re_idx = html.index('REAL ESTATE')
        block = html[max(0, re_idx - 100):re_idx + 300]
        assert '<h6' in block
        assert '<h2' in block
        assert '<small' in block

    def test_card_appears_after_alternatives(self):
        html = _read_template()
        alt_pos = html.index('id="alternatives-pct"')
        re_pos = html.index('id="real-estate-pct"')
        assert re_pos > alt_pos

    def test_alternatives_subtitle_unchanged(self):
        html = _read_template()
        assert 'Gold, Crypto' in html

    def test_alternatives_subtitle_no_real_estate(self):
        # Real estate must NOT appear in the Alternatives card subtitle
        html = _read_template()
        alt_idx = html.index('id="alternatives-pct"')
        # Look at the small tag after alternatives-pct
        after = html[alt_idx:alt_idx + 200]
        small_match = re.search(r'<small[^>]*>(.*?)</small>', after, re.DOTALL)
        assert small_match is not None
        subtitle = small_match.group(1)
        assert 'Real Estate' not in subtitle
        assert 'farmland' not in subtitle.lower()


class TestRealEstateUpdateUIJS:
    def test_real_estate_pct_calculation_exists(self):
        html = _read_template()
        assert 'realEstatePct' in html

    def test_farmland_included_in_calculation(self):
        html = _read_template()
        assert 'breakdown.farmland' in html

    def test_commercial_re_included_in_calculation(self):
        html = _read_template()
        assert 'breakdown.commercial_real_estate' in html

    def test_residential_re_included_in_calculation(self):
        html = _read_template()
        assert 'breakdown.residential_real_estate' in html

    def test_real_estate_pct_element_updated(self):
        html = _read_template()
        assert "getElementById('real-estate-pct')" in html

    def test_real_estate_breakdown_element_updated(self):
        html = _read_template()
        assert "getElementById('real-estate-breakdown')" in html

    def test_middle_dot_separator_used(self):
        html = _read_template()
        # Middle dot U+00B7 or its unicode escape
        assert '\u00B7' in html or '\\u00B7' in html

    def test_no_holdings_fallback_text_in_js(self):
        html = _read_template()
        assert 'No real estate holdings' in html

    def test_full_label_for_single_type_farmland(self):
        html = _read_template()
        assert 'Farmland' in html

    def test_full_label_for_single_type_commercial(self):
        html = _read_template()
        assert 'Commercial RE' in html

    def test_full_label_for_single_type_residential(self):
        html = _read_template()
        assert 'Residential RE' in html

    def test_abbreviation_farm_used(self):
        html = _read_template()
        assert "'Farm'" in html or '"Farm"' in html

    def test_abbreviation_comm_used(self):
        html = _read_template()
        assert "'Comm'" in html or '"Comm"' in html

    def test_abbreviation_resid_used(self):
        html = _read_template()
        assert "'Resid'" in html or '"Resid"' in html

    def test_real_estate_pct_uses_to_fixed_1(self):
        html = _read_template()
        # realEstatePct.toFixed(1) should appear somewhere in the JS
        idx = html.index("getElementById('real-estate-pct')")
        block = html[idx:idx + 100]
        assert 'toFixed(1)' in block

    def test_real_estate_calculated_before_dom_update(self):
        html = _read_template()
        calc_idx = html.index('realEstatePct =')
        dom_idx = html.index("getElementById('real-estate-pct')")
        assert calc_idx < dom_idx
