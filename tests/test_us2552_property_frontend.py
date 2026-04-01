"""Tests for US-255.2: Property macro page frontend.

Validates template rendering, collapsible sections, metric cards,
percentile bars, farmland definition list, interpretation block,
responsive behavior, accessibility attributes, and AI section button.
"""

import os
import sys
import re
import unittest

# ---------------------------------------------------------------------------
# Path setup — same pattern used across the test suite
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)

os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('OPENAI_API_KEY', 'test-key')

from dashboard import app


class PropertyPageTestCase(unittest.TestCase):
    """Base test case with Flask test client."""

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()


# ============================================================================
# 1. Basic page rendering
# ============================================================================

class TestPropertyPageBasicRendering(PropertyPageTestCase):
    """Test that /property returns 200 and has essential structure."""

    def test_property_page_returns_200(self):
        resp = self.client.get('/property')
        self.assertEqual(resp.status_code, 200)

    def test_page_title(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('<title>Property Macro — MacroClarity</title>', html)

    def test_page_header_icon(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('bi-house-door', html)

    def test_page_header_title(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('Property Macro', html)

    def test_page_header_description(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('Residential real estate and farmland macro indicators', html)

    def test_category_color_violet_in_css(self):
        css_path = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'property.css')
        with open(css_path) as f:
            css = f.read()
        self.assertIn('#8B5CF6', css)

    def test_property_css_linked(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('css/property.css', html)

    def test_asset_page_header_css_linked(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('css/components/asset-page-header.css', html)


# ============================================================================
# 2. Collapsible sections
# ============================================================================

class TestCollapsibleSections(PropertyPageTestCase):
    """Test that all three collapsible sections exist with proper attributes."""

    def test_residential_section_exists(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('id="section-residential"', html)

    def test_rental_section_exists(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('id="section-rental"', html)

    def test_farmland_section_exists(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('id="section-farmland"', html)

    def test_residential_toggle_aria_expanded(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('id="residential-toggle"', html)
        self.assertIn('aria-controls="residential-content"', html)

    def test_rental_toggle_aria_expanded(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('id="rental-toggle"', html)
        self.assertIn('aria-controls="rental-content"', html)

    def test_farmland_toggle_aria_expanded(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('id="farmland-toggle"', html)
        self.assertIn('aria-controls="farmland-content"', html)

    def test_sections_collapsed_by_default_in_html(self):
        """Sections start with aria-expanded=false and content hidden."""
        resp = self.client.get('/property')
        html = resp.data.decode()
        # All toggles start collapsed
        toggles = re.findall(r'class="property-section__toggle"[^>]*aria-expanded="([^"]*)"', html)
        for state in toggles:
            self.assertEqual(state, 'false')

    def test_section_content_has_hidden_attribute(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('id="residential-content" hidden', html)
        self.assertIn('id="rental-content" hidden', html)
        self.assertIn('id="farmland-content" hidden', html)

    def test_chevron_svg_present(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertEqual(html.count('property-section__chevron'), 3)

    def test_section_titles(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('Residential Housing', html)
        self.assertIn('Rental Market', html)
        self.assertIn('Farmland', html)


# ============================================================================
# 3. Metric cards
# ============================================================================

class TestMetricCards(PropertyPageTestCase):
    """Test metric card labels and structure."""

    def test_hpi_card_label(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('Case-Shiller HPI (National)', html)

    def test_cpi_rent_card_label(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('CPI Rent (Primary Residence)', html)

    def test_vacancy_card_label(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('Rental Vacancy Rate', html)

    def test_farmland_card_label(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('USDA Farmland ($/Acre)', html)

    def test_metric_card_class_present(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('property-metric-card', html)

    def test_metric_grid_class_present(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('property-metric-grid', html)


# ============================================================================
# 4. Percentile bars
# ============================================================================

class TestPercentileBars(unittest.TestCase):
    """Test percentile bar markup in template source."""

    def setUp(self):
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            self.tpl = f.read()

    def test_hpi_progressbar_aria_label_in_template(self):
        self.assertIn('aria-label="Case-Shiller HPI at', self.tpl)

    def test_cpi_rent_progressbar_aria_label_in_template(self):
        self.assertIn('aria-label="CPI Rent at', self.tpl)

    def test_vacancy_progressbar_aria_label_in_template(self):
        self.assertIn('aria-label="Vacancy Rate at', self.tpl)

    def test_progressbar_has_aria_values_in_template(self):
        self.assertIn('aria-valuemin="0"', self.tpl)
        self.assertIn('aria-valuemax="100"', self.tpl)

    def test_progressbar_role_in_template(self):
        self.assertIn('role="progressbar"', self.tpl)

    def test_pct_bar_css_classes_in_template(self):
        self.assertIn('property-pct-bar__track', self.tpl)
        self.assertIn('property-pct-bar__fill', self.tpl)


# ============================================================================
# 5. Farmland definition list
# ============================================================================

class TestFarmlandDefinitionList(PropertyPageTestCase):
    """Test farmland uses dl/dt/dd structure."""

    def test_farmland_uses_dl_element_in_template(self):
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            tpl = f.read()
        self.assertIn('<dl', tpl)

    def test_farmland_dt_labels_in_template(self):
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            tpl = f.read()
        self.assertIn('<dt>Farm RE:</dt>', tpl)

    def test_farmland_no_percentile_bar_in_template(self):
        """Farmland section should NOT have a percentile bar (annual frequency)."""
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            tpl = f.read()
        farmland_start = tpl.find('id="farmland-content"')
        farmland_end = tpl.find('{% endblock %}', farmland_start) if farmland_start != -1 else -1
        if farmland_start != -1 and farmland_end != -1:
            farmland_html = tpl[farmland_start:farmland_end]
            # Find the end of farmland section (next property-section or interpretation)
            next_section = farmland_html.find('property-interpretation')
            if next_section == -1:
                next_section = len(farmland_html)
            farmland_only = farmland_html[:next_section]
            self.assertNotIn('property-pct-bar__track', farmland_only)

    def test_farmland_annual_cadence_note_in_template(self):
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            tpl = f.read()
        self.assertIn('Annual', tpl)


# ============================================================================
# 6. Interpretation block
# ============================================================================

class TestInterpretationBlock(unittest.TestCase):
    """Test regime interpretation block structure in template."""

    def setUp(self):
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            self.tpl = f.read()

    def test_interpretation_class_present(self):
        self.assertIn('property-interpretation', self.tpl)

    def test_interpretation_label(self):
        self.assertIn('Property Macro Outlook', self.tpl)

    def test_interpretation_lightbulb_icon(self):
        self.assertIn('bi-lightbulb', self.tpl)


# ============================================================================
# 7. AI section button
# ============================================================================

class TestAISectionButton(PropertyPageTestCase):
    """Test AI section button for property page."""

    def test_ai_section_button_present(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('data-section-id="asset-property"', html)

    def test_ai_section_button_aria_label(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('Ask AI about Property Macro', html)


# ============================================================================
# 8. CSS file content
# ============================================================================

class TestPropertyCSS(unittest.TestCase):
    """Validate property.css content."""

    def setUp(self):
        css_path = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'property.css')
        with open(css_path) as f:
            self.css = f.read()

    def test_category_color_defined(self):
        self.assertIn('--category-color: #8B5CF6', self.css)

    def test_property_section_toggle_class(self):
        self.assertIn('.property-section__toggle', self.css)

    def test_property_metric_card_class(self):
        self.assertIn('.property-metric-card', self.css)

    def test_percentile_bar_track(self):
        self.assertIn('.property-pct-bar__track', self.css)

    def test_percentile_zone_colors(self):
        self.assertIn('.property-pct-bar__fill--danger', self.css)
        self.assertIn('.property-pct-bar__fill--warning', self.css)
        self.assertIn('.property-pct-bar__fill--neutral', self.css)
        self.assertIn('.property-pct-bar__fill--info', self.css)
        self.assertIn('.property-pct-bar__fill--success', self.css)

    def test_tablet_breakpoint(self):
        self.assertIn('min-width: 768px', self.css)

    def test_desktop_breakpoint(self):
        self.assertIn('min-width: 1024px', self.css)

    def test_reduced_motion(self):
        self.assertIn('prefers-reduced-motion', self.css)

    def test_metric_grid_responsive(self):
        self.assertIn('.property-metric-grid', self.css)

    def test_interpretation_class(self):
        self.assertIn('.property-interpretation', self.css)

    def test_badge_classes(self):
        self.assertIn('.property-badge--success', self.css)
        self.assertIn('.property-badge--danger', self.css)

    def test_farmland_dl_class(self):
        self.assertIn('.property-farmland-dl', self.css)


# ============================================================================
# 9. Dashboard CSS global token
# ============================================================================

class TestGlobalCSSToken(unittest.TestCase):
    """Validate --category-property added to dashboard.css."""

    def test_category_property_class_in_dashboard_css(self):
        css_path = os.path.join(SIGNALTRACKERS_DIR, 'static', 'css', 'dashboard.css')
        with open(css_path) as f:
            css = f.read()
        self.assertIn('.category-property', css)
        self.assertIn('#8B5CF6', css)


# ============================================================================
# 10. AI section button JS context
# ============================================================================

class TestAISectionButtonJS(unittest.TestCase):
    """Validate asset-property entry in ai-section-btn.js."""

    def setUp(self):
        js_path = os.path.join(SIGNALTRACKERS_DIR, 'static', 'js', 'components', 'ai-section-btn.js')
        with open(js_path) as f:
            self.js = f.read()

    def test_asset_property_in_context_map(self):
        self.assertIn("'asset-property'", self.js)

    def test_asset_property_name(self):
        self.assertIn("name: 'Property Macro'", self.js)

    def test_asset_property_opening_message(self):
        self.assertIn('Property Macro', self.js)
        self.assertIn('Case-Shiller HPI', self.js)


# ============================================================================
# 11. Backend section opening support
# ============================================================================

class TestSectionOpeningSupport(PropertyPageTestCase):
    """Test that asset-property is in the allowed section set."""

    def test_section_opening_rejects_unknown(self):
        resp = self.client.post('/api/chatbot/section-opening',
                                json={'section_id': 'bogus'},
                                content_type='application/json')
        # May get 400 (unknown section) or 302 (login redirect) depending on auth
        self.assertIn(resp.status_code, (400, 302))

    def test_section_opening_accepts_asset_property(self):
        """Should not get 400 for asset-property (may get 400 for missing AI key)."""
        resp = self.client.post('/api/chatbot/section-opening',
                                json={'section_id': 'asset-property'},
                                content_type='application/json')
        # 400 would mean unknown section_id — anything else is acceptable
        if resp.status_code == 400:
            data = resp.get_json()
            self.assertNotEqual(data.get('error'), 'Unknown section_id')


# ============================================================================
# 12. Navigation
# ============================================================================

class TestNavigation(PropertyPageTestCase):
    """Test property link in navbar."""

    def test_property_link_in_navbar(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('href="/property"', html)

    def test_property_active_state(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        # The dropdown-item for property should have active class
        prop_link_idx = html.find('href="/property"')
        self.assertNotEqual(prop_link_idx, -1)
        # Look backward for the class attribute
        nearby = html[max(0, prop_link_idx - 100):prop_link_idx]
        self.assertIn('active', nearby)


# ============================================================================
# 13. JavaScript collapsible behavior
# ============================================================================

class TestJavaScriptBehavior(PropertyPageTestCase):
    """Test that JS for collapsible sections is included."""

    def test_js_toggles_present(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('property-section__toggle', html)

    def test_js_tablet_expansion_logic(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn('min-width: 768px', html)
        self.assertIn('aria-expanded', html)

    def test_js_click_handler(self):
        resp = self.client.get('/property')
        html = resp.data.decode()
        self.assertIn("addEventListener('click'", html)


# ============================================================================
# 14. CPI Rent MoM direction
# ============================================================================

class TestCPIRentMoM(unittest.TestCase):
    """Test that MoM direction markup exists in template."""

    def test_mom_badge_text_in_template(self):
        """Template should contain MoM badge markup."""
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            tpl = f.read()
        self.assertIn('MoM', tpl)


# ============================================================================
# 15. Vacancy quarterly cadence
# ============================================================================

class TestVacancyCadence(unittest.TestCase):
    """Test vacancy rate quarterly cadence note."""

    def test_quarterly_cadence_in_template(self):
        tpl_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'property.html')
        with open(tpl_path) as f:
            tpl = f.read()
        self.assertIn('Quarterly', tpl)


if __name__ == '__main__':
    unittest.main()
