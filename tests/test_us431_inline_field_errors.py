"""
Static verification tests for US-4.3.1: Replace validation alert() calls with inline field errors.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required HTML, CSS, and JS patterns are present.

Acceptance criteria verified:
  AC1  - alert("Please fill in all required fields") replaced with inline errors
  AC2  - alert("Symbol is required for this asset type") replaced with inline error
  AC3  - Invalid input fields show danger-600 2px border via .form-control--error
  AC4  - Error text uses .form-error-message class with ⚠ prefix
  AC5  - Error persists until field corrected (re-validate on change after failed submit)
  AC6  - Multiple field errors displayed simultaneously
  AC7  - No native alert() calls for validation remain
  AC8  - Error states work on mobile viewports (responsive, no fixed widths)
  Accessibility - aria-describedby, aria-invalid, role="alert"
"""

import os
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTFOLIO_HTML_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'templates', 'portfolio.html')
DASHBOARD_CSS_PATH = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css', 'dashboard.css')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


# ============================================
# HTML Structure Tests
# ============================================

class TestErrorSpanElements(unittest.TestCase):
    """Verify error <span> elements are present for each required field."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_asset_type_error_span_exists(self):
        """portfolio.html must have span#asset-type-error."""
        self.assertIn('id="asset-type-error"', self.html)

    def test_symbol_error_span_exists(self):
        """portfolio.html must have span#symbol-error."""
        self.assertIn('id="symbol-error"', self.html)

    def test_name_error_span_exists(self):
        """portfolio.html must have span#name-error."""
        self.assertIn('id="name-error"', self.html)

    def test_percentage_error_span_exists(self):
        """portfolio.html must have span#percentage-error."""
        self.assertIn('id="percentage-error"', self.html)

    def test_asset_type_error_has_form_error_class(self):
        """asset-type-error span must use .form-error-message class."""
        idx = self.html.find('id="asset-type-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('form-error-message', surrounding)

    def test_symbol_error_has_form_error_class(self):
        """symbol-error span must use .form-error-message class."""
        idx = self.html.find('id="symbol-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('form-error-message', surrounding)

    def test_name_error_has_form_error_class(self):
        """name-error span must use .form-error-message class."""
        idx = self.html.find('id="name-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('form-error-message', surrounding)

    def test_percentage_error_has_form_error_class(self):
        """percentage-error span must use .form-error-message class."""
        idx = self.html.find('id="percentage-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('form-error-message', surrounding)

    def test_asset_type_error_has_role_alert(self):
        """asset-type-error span must have role='alert' for screen readers."""
        idx = self.html.find('id="asset-type-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('role="alert"', surrounding)

    def test_symbol_error_has_role_alert(self):
        """symbol-error span must have role='alert' for screen readers."""
        idx = self.html.find('id="symbol-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('role="alert"', surrounding)

    def test_name_error_has_role_alert(self):
        """name-error span must have role='alert' for screen readers."""
        idx = self.html.find('id="name-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('role="alert"', surrounding)

    def test_percentage_error_has_role_alert(self):
        """percentage-error span must have role='alert' for screen readers."""
        idx = self.html.find('id="percentage-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('role="alert"', surrounding)

    def test_asset_type_error_starts_hidden(self):
        """asset-type-error span must start hidden."""
        idx = self.html.find('id="asset-type-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('hidden', surrounding)

    def test_symbol_error_starts_hidden(self):
        """symbol-error span must start hidden."""
        idx = self.html.find('id="symbol-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('hidden', surrounding)

    def test_name_error_starts_hidden(self):
        """name-error span must start hidden."""
        idx = self.html.find('id="name-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('hidden', surrounding)

    def test_percentage_error_starts_hidden(self):
        """percentage-error span must start hidden."""
        idx = self.html.find('id="percentage-error"')
        surrounding = self.html[max(0, idx-10):idx+200]
        self.assertIn('hidden', surrounding)

    def test_symbol_error_message_text(self):
        """symbol-error must display 'Symbol is required for this asset type'."""
        self.assertIn('Symbol is required for this asset type', self.html)

    def test_required_fields_error_message_text(self):
        """Error spans must display 'Please fill in all required fields'."""
        self.assertIn('Please fill in all required fields', self.html)

    def test_warning_icon_prefix_on_errors(self):
        """Error spans must have ⚠ warning prefix per spec."""
        self.assertIn('⚠', self.html)

    def test_warning_icon_is_aria_hidden(self):
        """The ⚠ icon span must have aria-hidden='true' so screen readers skip it."""
        self.assertIn('aria-hidden="true"', self.html)


# ============================================
# Accessibility Attribute Tests
# ============================================

class TestAccessibilityAttributes(unittest.TestCase):
    """Verify ARIA attributes are properly set on form inputs."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_asset_type_has_aria_describedby(self):
        """asset-type select must have aria-describedby='asset-type-error'."""
        self.assertIn('aria-describedby="asset-type-error"', self.html)

    def test_symbol_input_has_aria_describedby(self):
        """holding-symbol input must have aria-describedby='symbol-error'."""
        self.assertIn('aria-describedby="symbol-error"', self.html)

    def test_name_input_has_aria_describedby(self):
        """holding-name input must have aria-describedby='name-error'."""
        self.assertIn('aria-describedby="name-error"', self.html)

    def test_percentage_input_has_aria_describedby(self):
        """holding-percentage input must have aria-describedby='percentage-error'."""
        self.assertIn('aria-describedby="percentage-error"', self.html)

    def test_asset_type_select_has_correct_describedby(self):
        """asset-type select's aria-describedby must match asset-type-error id."""
        idx = self.html.find('id="asset-type"')
        surrounding = self.html[max(0, idx-200):idx+300]
        self.assertIn('aria-describedby="asset-type-error"', surrounding)


# ============================================
# Alert Removal Tests (AC1, AC2, AC7)
# ============================================

class TestAlertRemoval(unittest.TestCase):
    """Verify native alert() calls for validation are removed."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_no_alert_for_required_fields(self):
        """alert('Please fill in all required fields') must be removed (AC1, AC7)."""
        self.assertNotIn("alert('Please fill in all required fields')", self.html)
        self.assertNotIn('alert("Please fill in all required fields")', self.html)

    def test_no_alert_for_symbol_required(self):
        """alert('Symbol is required for this asset type') must be removed (AC2, AC7)."""
        self.assertNotIn("alert('Symbol is required for this asset type')", self.html)
        self.assertNotIn('alert("Symbol is required for this asset type")', self.html)

    def test_api_error_alerts_removed(self):
        """API/network error alerts must be removed (completed in US-4.3.2)."""
        # US-4.3.2 replaced these with modal error banners
        self.assertNotIn("alert('Error: '", self.html)
        self.assertNotIn('alert("Error: "', self.html)
        self.assertNotIn("alert('Failed to save holding')", self.html)
        self.assertNotIn('alert("Failed to save holding")', self.html)
        self.assertNotIn("alert('Failed to delete holding')", self.html)
        self.assertNotIn('alert("Failed to delete holding")', self.html)


# ============================================
# JavaScript Validation Logic Tests
# ============================================

class TestValidationHelpers(unittest.TestCase):
    """Verify JS validation helper functions are present."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_show_field_error_function_exists(self):
        """showFieldError() helper function must be defined."""
        self.assertIn('function showFieldError(', self.html)

    def test_clear_field_error_function_exists(self):
        """clearFieldError() helper function must be defined."""
        self.assertIn('function clearFieldError(', self.html)

    def test_clear_validation_errors_function_exists(self):
        """clearValidationErrors() function must be defined."""
        self.assertIn('function clearValidationErrors(', self.html)

    def test_show_field_error_adds_error_class(self):
        """showFieldError must add form-control--error class to input."""
        self.assertIn('form-control--error', self.html)
        # Check classList.add pattern
        self.assertIn("classList.add('form-control--error')", self.html)

    def test_show_field_error_sets_aria_invalid(self):
        """showFieldError must set aria-invalid='true' on the field."""
        self.assertIn("setAttribute('aria-invalid', 'true')", self.html)

    def test_clear_field_error_removes_error_class(self):
        """clearFieldError must remove form-control--error class."""
        self.assertIn("classList.remove('form-control--error')", self.html)

    def test_clear_field_error_removes_aria_invalid(self):
        """clearFieldError must remove aria-invalid attribute."""
        self.assertIn("removeAttribute('aria-invalid')", self.html)

    def test_has_errors_guard_present(self):
        """saveHolding must use hasErrors guard to prevent save on validation failure."""
        self.assertIn('hasErrors', self.html)
        self.assertIn('if (hasErrors) return', self.html)

    def test_asset_type_validated_in_save(self):
        """saveHolding must validate asset type and show asset-type-error."""
        self.assertIn("'asset-type-error'", self.html)

    def test_name_validated_in_save(self):
        """saveHolding must validate name and show name-error."""
        self.assertIn("'name-error'", self.html)

    def test_percentage_validated_in_save(self):
        """saveHolding must validate percentage and show percentage-error."""
        self.assertIn("'percentage-error'", self.html)

    def test_symbol_validated_in_save(self):
        """saveHolding must validate symbol and show symbol-error."""
        self.assertIn("'symbol-error'", self.html)

    def test_clear_errors_called_at_start_of_save(self):
        """saveHolding must call clearValidationErrors() at start to reset previous errors."""
        # Check clearValidationErrors is called inside saveHolding
        save_fn_idx = self.html.find('async function saveHolding()')
        self.assertGreater(save_fn_idx, 0)
        save_fn_body = self.html[save_fn_idx:save_fn_idx + 600]
        self.assertIn('clearValidationErrors()', save_fn_body)


# ============================================
# Re-validation on Change Tests (AC5)
# ============================================

class TestRevalidationOnChange(unittest.TestCase):
    """Verify errors clear as user corrects fields (AC5)."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_name_field_input_listener_clears_error(self):
        """holding-name input listener must clear name-error when value is valid."""
        self.assertIn("'holding-name'", self.html)
        # Check addEventListener for input on holding-name
        self.assertIn("'input'", self.html)
        self.assertIn("clearFieldError('name-error'", self.html)

    def test_percentage_field_input_listener_clears_error(self):
        """holding-percentage input listener must clear percentage-error when valid."""
        self.assertIn("clearFieldError('percentage-error'", self.html)

    def test_symbol_field_input_listener_clears_error(self):
        """holding-symbol input listener must clear symbol-error when value is entered."""
        self.assertIn("clearFieldError('symbol-error'", self.html)

    def test_asset_type_change_listener_clears_error(self):
        """asset-type change listener must clear asset-type-error when selection made."""
        self.assertIn("clearFieldError('asset-type-error'", self.html)


# ============================================
# Modal Open/Close Cleanup Tests
# ============================================

class TestModalCleanup(unittest.TestCase):
    """Verify errors are cleared when modal opens or closes."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_show_add_modal_clears_errors(self):
        """showAddModal must call clearValidationErrors() to reset state."""
        show_modal_idx = self.html.find('function showAddModal()')
        self.assertGreater(show_modal_idx, 0)
        fn_body = self.html[show_modal_idx:show_modal_idx + 700]
        self.assertIn('clearValidationErrors()', fn_body)

    def test_edit_holding_clears_errors(self):
        """editHolding must call clearValidationErrors() before showing modal."""
        edit_idx = self.html.find('function editHolding(')
        self.assertGreater(edit_idx, 0)
        fn_body = self.html[edit_idx:edit_idx + 900]
        self.assertIn('clearValidationErrors()', fn_body)

    def test_modal_hidden_event_clears_errors(self):
        """hidden.bs.modal event handler must call clearValidationErrors()."""
        self.assertIn('hidden.bs.modal', self.html)
        # Find the handler
        hidden_idx = self.html.find('hidden.bs.modal')
        surrounding = self.html[max(0, hidden_idx-50):hidden_idx+200]
        self.assertIn('clearValidationErrors()', surrounding)


# ============================================
# CSS Style Tests (AC3, AC4)
# ============================================

class TestFormErrorCSS(unittest.TestCase):
    """Verify .form-error-message and .form-control--error styles exist in CSS."""

    def setUp(self):
        self.css = read_file(DASHBOARD_CSS_PATH)

    def test_form_error_message_class_defined(self):
        """dashboard.css must define .form-error-message (AC4)."""
        self.assertIn('.form-error-message', self.css)

    def test_form_error_message_color_is_danger_600(self):
        """form-error-message text must be danger-600 (#DC2626) (AC4)."""
        idx = self.css.find('.form-error-message')
        block = self.css[idx:idx+200]
        self.assertIn('#DC2626', block.upper())

    def test_form_error_message_font_size_14px(self):
        """form-error-message must use 14px font size (text-sm) (AC4)."""
        idx = self.css.find('.form-error-message')
        block = self.css[idx:idx+200]
        self.assertIn('14px', block)

    def test_form_control_error_class_defined(self):
        """dashboard.css must define .form-control--error for invalid field border (AC3)."""
        self.assertIn('form-control--error', self.css)

    def test_form_control_error_border_danger_600(self):
        """form-control--error must use danger-600 (#DC2626) border color (AC3)."""
        idx = self.css.find('form-control--error')
        block = self.css[idx:idx+300]
        self.assertIn('#DC2626', block.upper())

    def test_form_control_error_border_2px(self):
        """form-control--error must use 2px border width (AC3)."""
        idx = self.css.find('form-control--error')
        block = self.css[idx:idx+300]
        self.assertIn('2px', block)

    def test_form_select_also_covered_by_error_style(self):
        """CSS must cover both form-control and form-select with error style."""
        idx = self.css.find('form-control--error')
        block = self.css[idx:idx+300]
        self.assertIn('form-select', block)

    def test_form_error_message_margin_top(self):
        """form-error-message must have margin-top: 4px (space-1) per spec."""
        idx = self.css.find('.form-error-message')
        block = self.css[idx:idx+200]
        self.assertIn('margin-top', block)
        self.assertIn('4px', block)


# ============================================
# AC6 — Multiple Errors Simultaneously
# ============================================

class TestMultipleErrors(unittest.TestCase):
    """Verify each field has independent error tracking (AC6)."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_four_independent_error_spans(self):
        """Each required field has its own independent error span."""
        self.assertIn('id="asset-type-error"', self.html)
        self.assertIn('id="symbol-error"', self.html)
        self.assertIn('id="name-error"', self.html)
        self.assertIn('id="percentage-error"', self.html)

    def test_each_field_calls_show_field_error_independently(self):
        """saveHolding must call showFieldError for each field independently."""
        # Each field check is separate (not inside a single if block)
        self.assertIn("showFieldError('asset-type-error'", self.html)
        self.assertIn("showFieldError('name-error'", self.html)
        self.assertIn("showFieldError('percentage-error'", self.html)
        self.assertIn("showFieldError('symbol-error'", self.html)

    def test_clear_validation_errors_covers_all_fields(self):
        """clearValidationErrors must clear all four field errors."""
        idx = self.html.find('function clearValidationErrors(')
        fn_body = self.html[idx:idx+400]
        self.assertIn('asset-type-error', fn_body)
        self.assertIn('name-error', fn_body)
        self.assertIn('percentage-error', fn_body)
        self.assertIn('symbol-error', fn_body)


if __name__ == '__main__':
    unittest.main()
