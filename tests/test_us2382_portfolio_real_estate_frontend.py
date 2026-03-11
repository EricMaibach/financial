"""
Tests for US-238.2: Frontend — Asset Type Picker, Chart Colors, and Display Labels
Verifies all HTML/JS changes in portfolio.html for real estate asset types.
"""
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'templates', 'portfolio.html')


def _read_template():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


class TestAssetTypePicker:
    def test_optgroup_real_estate_exists(self):
        html = _read_template()
        assert '<optgroup label="Real Estate">' in html

    def test_farmland_option_exists(self):
        html = _read_template()
        assert 'value="farmland"' in html
        assert '>Farmland<' in html

    def test_commercial_real_estate_option_exists(self):
        html = _read_template()
        assert 'value="commercial_real_estate"' in html
        assert '>Commercial Real Estate<' in html

    def test_residential_real_estate_option_exists(self):
        html = _read_template()
        assert 'value="residential_real_estate"' in html
        assert '>Residential Real Estate<' in html

    def test_optgroup_appears_after_money_market(self):
        html = _read_template()
        money_market_pos = html.index('value="money_market"')
        optgroup_pos = html.index('<optgroup label="Real Estate">')
        assert optgroup_pos > money_market_pos

    def test_optgroup_appears_before_other(self):
        html = _read_template()
        optgroup_pos = html.index('<optgroup label="Real Estate">')
        # Find the "Other" option (not inside the optgroup)
        other_pos = html.index('value="other"')
        assert optgroup_pos < other_pos

    def test_real_estate_options_inside_optgroup(self):
        html = _read_template()
        # Extract optgroup block
        match = re.search(
            r'<optgroup label="Real Estate">(.*?)</optgroup>',
            html,
            re.DOTALL
        )
        assert match is not None, "Real Estate optgroup not found"
        optgroup_content = match.group(1)
        assert 'value="farmland"' in optgroup_content
        assert 'value="commercial_real_estate"' in optgroup_content
        assert 'value="residential_real_estate"' in optgroup_content

    def test_exactly_three_options_in_optgroup(self):
        html = _read_template()
        match = re.search(
            r'<optgroup label="Real Estate">(.*?)</optgroup>',
            html,
            re.DOTALL
        )
        assert match is not None
        options = re.findall(r'<option\s', match.group(1))
        assert len(options) == 3


class TestNameAutoPopulate:
    def test_farmland_auto_populates(self):
        html = _read_template()
        assert "this.value === 'farmland'" in html
        assert "nameInput.value = 'Farmland'" in html

    def test_commercial_real_estate_auto_populates(self):
        html = _read_template()
        assert "this.value === 'commercial_real_estate'" in html
        assert "nameInput.value = 'Commercial Real Estate'" in html

    def test_residential_real_estate_auto_populates(self):
        html = _read_template()
        assert "this.value === 'residential_real_estate'" in html
        assert "nameInput.value = 'Residential Real Estate'" in html

    def test_auto_populate_in_change_handler(self):
        html = _read_template()
        # All three must appear in the asset-type change handler block
        change_handler_start = html.index("asset-type').addEventListener('change'")
        change_handler_end = html.index('});', change_handler_start)
        handler_block = html[change_handler_start:change_handler_end]
        assert "farmland" in handler_block
        assert "commercial_real_estate" in handler_block
        assert "residential_real_estate" in handler_block


class TestTypeColors:
    def test_farmland_color(self):
        html = _read_template()
        assert "'farmland': '#7B9E5A'" in html

    def test_commercial_real_estate_color(self):
        html = _read_template()
        assert "'commercial_real_estate': '#607D8B'" in html

    def test_residential_real_estate_color(self):
        html = _read_template()
        assert "'residential_real_estate': '#E07B39'" in html

    def test_colors_in_type_colors_object(self):
        html = _read_template()
        # typeColors object starts with 'stock'
        type_colors_start = html.index("const typeColors = {")
        type_colors_end = html.index("};", type_colors_start)
        type_colors_block = html[type_colors_start:type_colors_end]
        assert "'farmland': '#7B9E5A'" in type_colors_block
        assert "'commercial_real_estate': '#607D8B'" in type_colors_block
        assert "'residential_real_estate': '#E07B39'" in type_colors_block

    def test_real_estate_colors_distinct_from_existing(self):
        # Verify new colors don't duplicate existing ones
        existing_colors = {
            '#0d6efd', '#198754', '#20c997', '#ffc107', '#fd7e14',
            '#6c757d', '#0dcaf0', '#17a2b8', '#6610f2'
        }
        new_colors = {'#7B9E5A', '#607D8B', '#E07B39'}
        # Normalize case for comparison
        existing_lower = {c.lower() for c in existing_colors}
        new_lower = {c.lower() for c in new_colors}
        assert not new_lower.intersection(existing_lower), \
            f"New colors overlap with existing: {new_lower.intersection(existing_lower)}"


class TestFormatAssetType:
    def test_farmland_label(self):
        html = _read_template()
        assert "'farmland': 'Farmland'" in html

    def test_commercial_real_estate_label(self):
        html = _read_template()
        assert "'commercial_real_estate': 'Comm. RE'" in html

    def test_residential_real_estate_label(self):
        html = _read_template()
        assert "'residential_real_estate': 'Residential RE'" in html

    def test_labels_in_format_function(self):
        html = _read_template()
        format_func_start = html.index("function formatAssetType(type)")
        format_func_end = html.index("}", format_func_start + 1)
        # Get the full function including nested braces
        # Find the labels object and closing brace
        func_block = html[format_func_start:format_func_start + 600]
        assert "'farmland': 'Farmland'" in func_block
        assert "'commercial_real_estate': 'Comm. RE'" in func_block
        assert "'residential_real_estate': 'Residential RE'" in func_block


class TestSymbolFieldBehavior:
    def test_symbol_required_does_not_include_real_estate(self):
        html = _read_template()
        # Find SYMBOL_REQUIRED declaration
        match = re.search(r"const SYMBOL_REQUIRED = \[([^\]]+)\]", html)
        assert match is not None, "SYMBOL_REQUIRED not found"
        symbol_required_content = match.group(1)
        assert 'farmland' not in symbol_required_content
        assert 'commercial_real_estate' not in symbol_required_content
        assert 'residential_real_estate' not in symbol_required_content
