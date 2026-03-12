"""
US-256.1: Extract alert severity design tokens and fix card header color

Tests verify:
- alert-severity.css exists with correct tokens and badge classes
- settings_alerts.html uses new badge classes (not inline hex)
- settings_alerts.html card header uses alert-settings-header (not bg-danger)
- base.html links alert-severity.css
- docs/design-system.md documents the tokens
"""
import pathlib
import re

_REPO_ROOT = pathlib.Path(__file__).parent.parent
_CSS_FILE = _REPO_ROOT / 'signaltrackers' / 'static' / 'css' / 'components' / 'alert-severity.css'
_SETTINGS_TEMPLATE = _REPO_ROOT / 'signaltrackers' / 'templates' / 'settings_alerts.html'
_BASE_TEMPLATE = _REPO_ROOT / 'signaltrackers' / 'templates' / 'base.html'
_DESIGN_SYSTEM = _REPO_ROOT / 'docs' / 'design-system.md'


class TestAlertSeverityCSSFile:
    """AC1: New CSS file exists with all four tokens."""

    def test_css_file_exists(self):
        assert _CSS_FILE.exists(), "alert-severity.css must exist"

    def test_token_l1_defined(self):
        content = _CSS_FILE.read_text()
        assert '--alert-l1-color' in content
        assert '#6f42c1' in content

    def test_token_l2_defined(self):
        content = _CSS_FILE.read_text()
        assert '--alert-l2-color' in content
        assert '#fd7e14' in content

    def test_token_l3_defined(self):
        content = _CSS_FILE.read_text()
        assert '--alert-l3-color' in content
        assert '#dc3545' in content

    def test_token_header_bg_defined(self):
        content = _CSS_FILE.read_text()
        assert '--alert-header-bg' in content
        assert '#4F46E5' in content

    def test_tokens_on_root(self):
        content = _CSS_FILE.read_text()
        assert ':root' in content

    def test_base_badge_class_exists(self):
        content = _CSS_FILE.read_text()
        assert '.alert-severity-badge {' in content or '.alert-severity-badge\n{' in content or '.alert-severity-badge ' in content

    def test_l1_modifier_class_exists(self):
        content = _CSS_FILE.read_text()
        assert '.alert-severity-badge--l1' in content

    def test_l2_modifier_class_exists(self):
        content = _CSS_FILE.read_text()
        assert '.alert-severity-badge--l2' in content

    def test_l3_modifier_class_exists(self):
        content = _CSS_FILE.read_text()
        assert '.alert-severity-badge--l3' in content

    def test_alert_settings_header_class_exists(self):
        content = _CSS_FILE.read_text()
        assert '.alert-settings-header' in content

    def test_l1_references_token(self):
        content = _CSS_FILE.read_text()
        assert 'var(--alert-l1-color)' in content

    def test_l2_references_token(self):
        content = _CSS_FILE.read_text()
        assert 'var(--alert-l2-color)' in content

    def test_l3_references_token(self):
        content = _CSS_FILE.read_text()
        assert 'var(--alert-l3-color)' in content

    def test_header_references_token(self):
        content = _CSS_FILE.read_text()
        assert 'var(--alert-header-bg)' in content


class TestSettingsAlertTemplate:
    """AC2-4: settings_alerts.html uses new classes, not inline hex."""

    def test_no_bg_danger_on_card_header(self):
        content = _SETTINGS_TEMPLATE.read_text()
        # bg-danger should not appear on the Smart Market Alerts card header
        # (it may appear elsewhere in comments or unrelated elements)
        # Check the card-header line specifically
        for line in content.splitlines():
            if 'card-header' in line:
                assert 'bg-danger' not in line, (
                    f"card-header line still uses bg-danger: {line.strip()}"
                )

    def test_alert_settings_header_on_card(self):
        content = _SETTINGS_TEMPLATE.read_text()
        assert 'alert-settings-header' in content

    def test_badge_uses_new_class_l1(self):
        content = _SETTINGS_TEMPLATE.read_text()
        assert 'alert-severity-badge--l1' in content

    def test_badge_uses_new_class_l2(self):
        content = _SETTINGS_TEMPLATE.read_text()
        assert 'alert-severity-badge--l2' in content

    def test_badge_uses_new_class_l3(self):
        content = _SETTINGS_TEMPLATE.read_text()
        assert 'alert-severity-badge--l3' in content

    def test_no_inline_hex_l1(self):
        content = _SETTINGS_TEMPLATE.read_text()
        assert '#6f42c1' not in content, "Inline hex #6f42c1 should be removed"

    def test_no_inline_hex_l2(self):
        content = _SETTINGS_TEMPLATE.read_text()
        assert '#fd7e14' not in content, "Inline hex #fd7e14 should be removed"

    def test_no_inline_hex_l3(self):
        content = _SETTINGS_TEMPLATE.read_text()
        assert '#dc3545' not in content, "Inline hex #dc3545 should be removed"

    def test_no_layer_badge_inline_style_block(self):
        content = _SETTINGS_TEMPLATE.read_text()
        # The old inline <style> block with layer-badge definitions should be gone
        assert '.layer-1 {' not in content
        assert '.layer-2 {' not in content
        assert '.layer-3 {' not in content


class TestBaseTemplateLinks:
    """AC7: CSS file is linked so templates render correctly."""

    def test_alert_severity_css_linked_in_base(self):
        content = _BASE_TEMPLATE.read_text()
        assert 'alert-severity.css' in content


class TestDesignSystemDocumentation:
    """AC6: design-system.md updated with token table."""

    def test_alert_severity_section_exists(self):
        content = _DESIGN_SYSTEM.read_text()
        assert 'Alert Severity' in content

    def test_l1_token_documented(self):
        content = _DESIGN_SYSTEM.read_text()
        assert '--alert-l1-color' in content

    def test_l2_token_documented(self):
        content = _DESIGN_SYSTEM.read_text()
        assert '--alert-l2-color' in content

    def test_l3_token_documented(self):
        content = _DESIGN_SYSTEM.read_text()
        assert '--alert-l3-color' in content

    def test_header_token_documented(self):
        content = _DESIGN_SYSTEM.read_text()
        assert '--alert-header-bg' in content

    def test_css_file_path_referenced(self):
        content = _DESIGN_SYSTEM.read_text()
        assert 'alert-severity.css' in content
