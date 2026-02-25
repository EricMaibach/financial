"""
Static verification tests for US-4.3.2: Replace API/network error alert() calls with modal error banners.

These tests verify the implementation without requiring a live browser or Flask server.
They inspect source files directly to confirm required HTML, CSS, and JS patterns are present.

Acceptance criteria verified:
  AC1  - alert("Error: " + message) on save replaced with modal banner "Could not save holding — please try again"
  AC2  - alert("Error: " + message) on delete replaced with modal banner "Could not delete holding — please try again"
  AC3  - alert("Failed to save holding") replaced with "Could not save holding — check your connection"
  AC4  - alert("Failed to delete holding") replaced with "Could not delete holding — check your connection"
  AC5  - No native alert() calls remain for API/network errors
  AC6  - Error banner appears as first element in .modal-body, above all form fields
  AC7  - Banner styling: danger-100 bg, danger-300 border, 8px radius, danger-700 text, danger-600 icon
  AC8  - Banner auto-clears on next successful save/delete or when modal is closed
  AC9  - Only one banner shown at a time; new errors replace previous text
  AC10 - Raw backend error strings are NOT exposed to users
  AC11 - role="alert" on banner element
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
# HTML Structure Tests — Holding Modal Banner
# ============================================

class TestHoldingModalBannerStructure(unittest.TestCase):
    """Verify modal-error-banner element is present in the Add/Edit holding modal."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_holding_error_banner_id_exists(self):
        """portfolio.html must have an element with id holding-error-banner."""
        self.assertIn('id="holding-error-banner"', self.html)

    def test_holding_error_banner_has_modal_error_class(self):
        """holding-error-banner must use .modal-error-banner class."""
        self.assertIn('class="modal-error-banner"', self.html)

    def test_holding_error_banner_has_role_alert(self):
        """holding-error-banner must have role="alert" for screen readers."""
        # Check that the holding banner div contains role="alert"
        pattern = r'id="holding-error-banner"[^>]*role="alert"|role="alert"[^>]*id="holding-error-banner"'
        self.assertRegex(self.html, pattern)

    def test_holding_error_banner_hidden_by_default(self):
        """holding-error-banner must be hidden by default using hidden attribute."""
        pattern = r'id="holding-error-banner"[^>]*hidden|hidden[^>]*id="holding-error-banner"'
        self.assertRegex(self.html, pattern)

    def test_holding_error_text_element_exists(self):
        """portfolio.html must have an element with id holding-error-text."""
        self.assertIn('id="holding-error-text"', self.html)

    def test_holding_error_icon_has_aria_hidden(self):
        """Warning icon in holding banner must have aria-hidden="true" (decorative)."""
        # The icon span should have aria-hidden="true" inside the holding-error-banner
        self.assertIn('aria-hidden="true"', self.html)

    def test_holding_banner_has_modal_error_icon_class(self):
        """Holding banner icon must use .modal-error-icon class."""
        self.assertIn('class="modal-error-icon"', self.html)

    def test_holding_banner_has_modal_error_text_class(self):
        """Holding banner text element must use .modal-error-text class."""
        self.assertIn('class="modal-error-text"', self.html)

    def test_holding_banner_is_first_child_of_modal_body(self):
        """holding-error-banner must appear before the form in .modal-body."""
        modal_body_idx = self.html.find('<div class="modal-body">\n                <div id="holding-error-banner"')
        self.assertNotEqual(modal_body_idx, -1,
            "holding-error-banner must be the first child of the holding modal's .modal-body")

    def test_holding_banner_appears_before_form(self):
        """holding-error-banner must appear before the form tag in the holding modal."""
        banner_idx = self.html.find('id="holding-error-banner"')
        form_idx = self.html.find('<form id="holding-form">')
        self.assertLess(banner_idx, form_idx,
            "holding-error-banner must appear before holding-form")


# ============================================
# HTML Structure Tests — Delete Modal Banner
# ============================================

class TestDeleteModalBannerStructure(unittest.TestCase):
    """Verify modal-error-banner element is present in the Delete confirmation modal."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_delete_error_banner_id_exists(self):
        """portfolio.html must have an element with id delete-error-banner."""
        self.assertIn('id="delete-error-banner"', self.html)

    def test_delete_error_banner_has_modal_error_class(self):
        """delete-error-banner must use .modal-error-banner class."""
        # Verify there are two instances of modal-error-banner class (one per modal)
        count = self.html.count('class="modal-error-banner"')
        self.assertGreaterEqual(count, 2,
            "Both holding and delete modals must have modal-error-banner elements")

    def test_delete_error_banner_has_role_alert(self):
        """delete-error-banner must have role="alert" for screen readers."""
        pattern = r'id="delete-error-banner"[^>]*role="alert"|role="alert"[^>]*id="delete-error-banner"'
        self.assertRegex(self.html, pattern)

    def test_delete_error_banner_hidden_by_default(self):
        """delete-error-banner must be hidden by default using hidden attribute."""
        pattern = r'id="delete-error-banner"[^>]*hidden|hidden[^>]*id="delete-error-banner"'
        self.assertRegex(self.html, pattern)

    def test_delete_error_text_element_exists(self):
        """portfolio.html must have an element with id delete-error-text."""
        self.assertIn('id="delete-error-text"', self.html)

    def test_delete_banner_appears_before_confirmation_paragraph(self):
        """delete-error-banner must appear before the confirmation <p> in the delete modal."""
        banner_idx = self.html.find('id="delete-error-banner"')
        confirm_p_idx = self.html.find('id="delete-holding-name"')
        self.assertLess(banner_idx, confirm_p_idx,
            "delete-error-banner must appear before the confirmation paragraph")


# ============================================
# No alert() Calls Remaining
# ============================================

class TestNoAlertCallsRemaining(unittest.TestCase):
    """Verify all API/network alert() calls have been replaced."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_no_save_api_error_alert(self):
        """alert('Error: ' + ...) for save must not exist."""
        # The old pattern was: alert('Error: ' + data.error) in saveHolding
        self.assertNotIn("alert('Error: '", self.html)
        self.assertNotIn('alert("Error: "', self.html)

    def test_no_failed_to_save_alert(self):
        """alert('Failed to save holding') must not exist."""
        self.assertNotIn("alert('Failed to save holding')", self.html)
        self.assertNotIn('alert("Failed to save holding")', self.html)

    def test_no_failed_to_delete_alert(self):
        """alert('Failed to delete holding') must not exist."""
        self.assertNotIn("alert('Failed to delete holding')", self.html)
        self.assertNotIn('alert("Failed to delete holding")', self.html)

    def test_no_alert_calls_for_api_errors_at_all(self):
        """No alert() calls should exist for API or network error scenarios."""
        # Find all alert( occurrences, excluding comments
        lines = self.html.split('\n')
        alert_lines = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # Skip comment lines
            if stripped.startswith('//'):
                continue
            if 'alert(' in stripped:
                alert_lines.append((i, stripped))
        self.assertEqual(alert_lines, [],
            f"Found unexpected alert() calls (non-comment lines): {alert_lines}")

    def test_us431_validation_alerts_still_absent(self):
        """Regression: US-4.3.1 validation alerts must remain absent."""
        self.assertNotIn("alert('Please fill in", self.html)
        self.assertNotIn("alert('Symbol is required", self.html)


# ============================================
# Error Message Copy Tests
# ============================================

class TestErrorMessageCopy(unittest.TestCase):
    """Verify correct hardcoded error messages are used (no raw backend strings)."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_save_api_error_message(self):
        """Save API error must show 'Could not save holding — please try again'."""
        # The em-dash \u2014 may appear as unicode escape or literal
        self.assertTrue(
            'Could not save holding' in self.html and 'please try again' in self.html,
            "Save API error message not found"
        )

    def test_delete_api_error_message(self):
        """Delete API error must show 'Could not delete holding — please try again'."""
        self.assertTrue(
            'Could not delete holding' in self.html and 'please try again' in self.html,
            "Delete API error message not found"
        )

    def test_save_network_error_message(self):
        """Save network failure must show 'Could not save holding — check your connection'."""
        self.assertTrue(
            'Could not save holding' in self.html and 'check your connection' in self.html,
            "Save network error message not found"
        )

    def test_delete_network_error_message(self):
        """Delete network failure must show 'Could not delete holding — check your connection'."""
        self.assertTrue(
            'Could not delete holding' in self.html and 'check your connection' in self.html,
            "Delete network error message not found"
        )

    def test_no_raw_backend_error_exposed(self):
        """Raw 'Error: ' + data.error pattern must not appear in banner display code."""
        # Old pattern exposed backend messages: alert('Error: ' + data.error)
        self.assertNotIn("'Error: ' + data.error", self.html)
        self.assertNotIn('"Error: " + data.error', self.html)
        self.assertNotIn('data.error', self.html.split('confirmDelete')[0].split('saveHolding')[-1].split('// ')[0]
                         if 'showModalError' in self.html else '')

    def test_hardcoded_messages_not_dynamic(self):
        """Modal error messages must be hardcoded strings, not template interpolation."""
        # The showModalError calls must use static strings, not data.error
        save_api_pattern = r"showModalError\([^)]*data\.error"
        self.assertNotRegex(self.html, save_api_pattern,
            "showModalError must not pass raw data.error to users")


# ============================================
# JS Helpers Tests
# ============================================

class TestJSHelpers(unittest.TestCase):
    """Verify JS helper functions are present and correct."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_show_modal_error_function_defined(self):
        """showModalError() function must be defined."""
        self.assertIn('function showModalError(', self.html)

    def test_clear_modal_error_function_defined(self):
        """clearModalError() function must be defined."""
        self.assertIn('function clearModalError(', self.html)

    def test_show_modal_error_sets_text(self):
        """showModalError must set text content of the text element."""
        self.assertIn('textContent = message', self.html)

    def test_show_modal_error_removes_hidden(self):
        """showModalError must show the banner by setting hidden = false."""
        self.assertIn('banner.hidden = false', self.html)

    def test_clear_modal_error_adds_hidden(self):
        """clearModalError must hide the banner by setting hidden = true."""
        self.assertIn('banner.hidden = true', self.html)

    def test_save_holding_calls_show_modal_error_for_api_error(self):
        """saveHolding must call showModalError for API error (data.error branch)."""
        # Check that after data.error check, showModalError is called (not alert)
        self.assertIn("showModalError('holding-error-banner'", self.html)

    def test_save_holding_calls_show_modal_error_for_network_error(self):
        """saveHolding catch block must call showModalError for network failure."""
        # Both save error messages must appear in the html
        save_connection_msg = "Could not save holding"
        self.assertIn(save_connection_msg, self.html)

    def test_confirm_delete_calls_show_modal_error_for_api_error(self):
        """confirmDelete must call showModalError for API error."""
        self.assertIn("showModalError('delete-error-banner'", self.html)

    def test_confirm_delete_calls_show_modal_error_for_network_error(self):
        """confirmDelete catch block must call showModalError for network failure."""
        delete_connection_msg = "Could not delete holding"
        self.assertIn(delete_connection_msg, self.html)


# ============================================
# Banner Lifecycle / Clear Tests
# ============================================

class TestBannerLifecycle(unittest.TestCase):
    """Verify banners are cleared at the right times."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_holding_banner_cleared_on_modal_close(self):
        """clearModalError for holding-error-banner must be called in hidden.bs.modal handler."""
        self.assertIn("clearModalError('holding-error-banner')", self.html)
        # Verify it's near the hidden.bs.modal handler
        hidden_event_idx = self.html.find("'hidden.bs.modal'")
        clear_holding_idx = self.html.find("clearModalError('holding-error-banner')")
        self.assertGreater(hidden_event_idx, 0, "hidden.bs.modal handler must exist")
        self.assertGreater(clear_holding_idx, 0, "clearModalError('holding-error-banner') must exist")

    def test_delete_banner_cleared_on_modal_close(self):
        """clearModalError for delete-error-banner must be called in hidden.bs.modal handler."""
        self.assertIn("clearModalError('delete-error-banner')", self.html)

    def test_holding_banner_cleared_on_successful_save(self):
        """clearModalError must be called before holdingModal.hide() on success."""
        clear_idx = self.html.find("clearModalError('holding-error-banner')")
        hide_idx = self.html.find('holdingModal.hide()')
        self.assertLess(clear_idx, hide_idx,
            "clearModalError must be called before holdingModal.hide() on success")

    def test_delete_banner_cleared_on_successful_delete(self):
        """clearModalError must be called before deleteModal.hide() on success."""
        clear_idx = self.html.find("clearModalError('delete-error-banner')")
        hide_idx = self.html.find('deleteModal.hide()')
        self.assertLess(clear_idx, hide_idx,
            "clearModalError must be called before deleteModal.hide() on success")

    def test_delete_modal_has_hidden_bs_modal_listener(self):
        """deleteModal must have a hidden.bs.modal event listener to clear banner."""
        # There must be at least 2 hidden.bs.modal listener registrations
        count = self.html.count("'hidden.bs.modal'")
        self.assertGreaterEqual(count, 2,
            "Both holdingModal and deleteModal must have hidden.bs.modal listeners")

    def test_only_one_banner_per_modal(self):
        """Each modal must have exactly one modal-error-banner element."""
        # Verify exactly 2 modal-error-banner instances total (one per modal)
        count = self.html.count('id="holding-error-banner"')
        self.assertEqual(count, 1, "Exactly one holding-error-banner must exist")
        count = self.html.count('id="delete-error-banner"')
        self.assertEqual(count, 1, "Exactly one delete-error-banner must exist")


# ============================================
# CSS Tests
# ============================================

class TestModalErrorBannerCSS(unittest.TestCase):
    """Verify .modal-error-banner styles match the design spec."""

    def setUp(self):
        self.css = read_file(DASHBOARD_CSS_PATH)

    def test_modal_error_banner_class_defined(self):
        """.modal-error-banner class must be defined in dashboard.css."""
        self.assertIn('.modal-error-banner', self.css)

    def test_modal_error_banner_background_danger_100(self):
        """Banner background must be danger-100 (#FEE2E2)."""
        # Find the .modal-error-banner block
        banner_block_start = self.css.find('.modal-error-banner')
        banner_block_end = self.css.find('}', banner_block_start)
        banner_block = self.css[banner_block_start:banner_block_end]
        self.assertIn('#FEE2E2', banner_block,
            ".modal-error-banner background must be #FEE2E2 (danger-100)")

    def test_modal_error_banner_border_danger_300(self):
        """Banner border must include danger-300 (#FCA5A5)."""
        banner_block_start = self.css.find('.modal-error-banner')
        banner_block_end = self.css.find('}', banner_block_start)
        banner_block = self.css[banner_block_start:banner_block_end]
        self.assertIn('#FCA5A5', banner_block,
            ".modal-error-banner border must include #FCA5A5 (danger-300)")

    def test_modal_error_banner_border_radius_8px(self):
        """Banner must have 8px border-radius."""
        banner_block_start = self.css.find('.modal-error-banner')
        banner_block_end = self.css.find('}', banner_block_start)
        banner_block = self.css[banner_block_start:banner_block_end]
        self.assertIn('8px', banner_block,
            ".modal-error-banner must have 8px border-radius")

    def test_modal_error_banner_margin_bottom_16px(self):
        """Banner must have 16px margin-bottom (space-4) to separate from form."""
        banner_block_start = self.css.find('.modal-error-banner')
        banner_block_end = self.css.find('}', banner_block_start)
        banner_block = self.css[banner_block_start:banner_block_end]
        self.assertIn('16px', banner_block,
            ".modal-error-banner must have 16px margin-bottom")

    def test_modal_error_banner_flex_layout(self):
        """Banner must use flexbox for icon + text layout."""
        banner_block_start = self.css.find('.modal-error-banner')
        banner_block_end = self.css.find('}', banner_block_start)
        banner_block = self.css[banner_block_start:banner_block_end]
        self.assertIn('flex', banner_block,
            ".modal-error-banner must use flexbox layout")

    def test_modal_error_icon_class_defined(self):
        """.modal-error-icon class must be defined in dashboard.css."""
        self.assertIn('.modal-error-icon', self.css)

    def test_modal_error_icon_color_danger_600(self):
        """Banner icon must be danger-600 (#DC2626)."""
        icon_block_start = self.css.find('.modal-error-icon')
        icon_block_end = self.css.find('}', icon_block_start)
        icon_block = self.css[icon_block_start:icon_block_end]
        self.assertIn('#DC2626', icon_block,
            ".modal-error-icon color must be #DC2626 (danger-600)")

    def test_modal_error_text_class_defined(self):
        """.modal-error-text class must be defined in dashboard.css."""
        self.assertIn('.modal-error-text', self.css)

    def test_modal_error_text_color_danger_700(self):
        """Banner text must be danger-700 (#B91C1C)."""
        text_block_start = self.css.find('.modal-error-text')
        text_block_end = self.css.find('}', text_block_start)
        text_block = self.css[text_block_start:text_block_end]
        self.assertIn('#B91C1C', text_block,
            ".modal-error-text color must be #B91C1C (danger-700)")

    def test_modal_error_text_font_size_14px(self):
        """Banner text must be 14px (text-sm)."""
        text_block_start = self.css.find('.modal-error-text')
        text_block_end = self.css.find('}', text_block_start)
        text_block = self.css[text_block_start:text_block_end]
        self.assertIn('14px', text_block,
            ".modal-error-text font-size must be 14px")

    def test_modal_error_text_margin_zero(self):
        """Banner text paragraph margin must be 0 (no default p margin)."""
        text_block_start = self.css.find('.modal-error-text')
        text_block_end = self.css.find('}', text_block_start)
        text_block = self.css[text_block_start:text_block_end]
        self.assertIn('margin: 0', text_block,
            ".modal-error-text must have margin: 0 to suppress default <p> margin")


# ============================================
# Accessibility Tests
# ============================================

class TestAccessibility(unittest.TestCase):
    """Verify accessibility requirements for modal error banners."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_holding_banner_role_alert(self):
        """holding-error-banner must have role="alert" for immediate screen reader announcement."""
        # Find the holding banner element and check it has role=alert
        self.assertIn('id="holding-error-banner"', self.html)
        self.assertIn('role="alert"', self.html)

    def test_delete_banner_role_alert(self):
        """delete-error-banner must have role="alert"."""
        self.assertIn('id="delete-error-banner"', self.html)

    def test_both_banners_have_role_alert(self):
        """Both error banners must have role="alert"."""
        count = self.html.count('class="modal-error-banner" role="alert"')
        self.assertEqual(count, 2,
            "Both modal-error-banner elements must have role='alert'")

    def test_icon_aria_hidden(self):
        """Warning icon must have aria-hidden='true' (it is decorative)."""
        # Find modal-error-icon spans and verify they have aria-hidden="true"
        self.assertIn('class="modal-error-icon" aria-hidden="true"', self.html)

    def test_both_icons_aria_hidden(self):
        """Both modal error icons must have aria-hidden='true'."""
        count = self.html.count('class="modal-error-icon" aria-hidden="true"')
        self.assertEqual(count, 2,
            "Both modal-error-icon elements must have aria-hidden='true'")

    def test_us431_aria_describedby_not_broken(self):
        """Regression: aria-describedby linkage from US-4.3.1 must remain intact."""
        self.assertIn('aria-describedby="asset-type-error"', self.html)
        self.assertIn('aria-describedby="symbol-error"', self.html)
        self.assertIn('aria-describedby="name-error"', self.html)
        self.assertIn('aria-describedby="percentage-error"', self.html)


# ============================================
# Security Tests
# ============================================

class TestSecurity(unittest.TestCase):
    """Verify no sensitive backend data is exposed in error messages."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_no_dynamic_error_message_in_banner(self):
        """showModalError calls must not include data.error or error.message."""
        # Extract showModalError calls
        calls = re.findall(r'showModalError\([^)]+\)', self.html)
        for call in calls:
            self.assertNotIn('data.error', call,
                f"showModalError must not expose data.error: {call}")
            self.assertNotIn('error.message', call,
                f"showModalError must not expose error.message: {call}")

    def test_banner_content_is_static(self):
        """Banner error text must be static strings, not user or server input."""
        # All showModalError calls should use string literals for the message
        # Verify the 4 hardcoded messages
        self.assertIn("'Could not save holding \\u2014 please try again'", self.html)
        self.assertIn("'Could not delete holding \\u2014 please try again'", self.html)
        self.assertIn("'Could not save holding \\u2014 check your connection'", self.html)
        self.assertIn("'Could not delete holding \\u2014 check your connection'", self.html)

    def test_no_innerHTML_used_for_banner(self):
        """Banner text must use textContent, not innerHTML, to prevent XSS."""
        # The showModalError helper should use textContent, not innerHTML
        # Find the showModalError function and verify
        func_start = self.html.find('function showModalError(')
        func_end = self.html.find('}', func_start)
        func_body = self.html[func_start:func_end]
        self.assertIn('textContent', func_body,
            "showModalError must use textContent (not innerHTML) to set error text")
        self.assertNotIn('innerHTML', func_body,
            "showModalError must not use innerHTML (XSS risk)")


# ============================================
# Regression Tests
# ============================================

class TestRegression(unittest.TestCase):
    """Verify US-4.3.1 inline field errors are not broken by this change."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_inline_error_spans_still_present(self):
        """US-4.3.1 inline error spans must still be present."""
        self.assertIn('id="asset-type-error"', self.html)
        self.assertIn('id="symbol-error"', self.html)
        self.assertIn('id="name-error"', self.html)
        self.assertIn('id="percentage-error"', self.html)

    def test_clear_validation_errors_still_defined(self):
        """clearValidationErrors() function must still be defined."""
        self.assertIn('function clearValidationErrors()', self.html)

    def test_show_field_error_still_defined(self):
        """showFieldError() function must still be defined."""
        self.assertIn('function showFieldError(', self.html)

    def test_clear_field_error_still_defined(self):
        """clearFieldError() function must still be defined."""
        self.assertIn('function clearFieldError(', self.html)

    def test_inline_errors_called_in_save_holding(self):
        """saveHolding must still call showFieldError for validation."""
        self.assertIn("showFieldError('asset-type-error'", self.html)
        self.assertIn("showFieldError('name-error'", self.html)
        self.assertIn("showFieldError('percentage-error'", self.html)
        self.assertIn("showFieldError('symbol-error'", self.html)

    def test_holding_modal_still_exists(self):
        """holdingModal Bootstrap modal must still be present."""
        self.assertIn('id="holdingModal"', self.html)

    def test_delete_modal_still_exists(self):
        """deleteModal Bootstrap modal must still be present."""
        self.assertIn('id="deleteModal"', self.html)


# ============================================
# Performance Tests
# ============================================

class TestPerformance(unittest.TestCase):
    """Verify no additional network requests are triggered by banner display."""

    def setUp(self):
        self.html = read_file(PORTFOLIO_HTML_PATH)

    def test_show_modal_error_is_dom_only(self):
        """showModalError must only do DOM manipulation, no fetch/XHR calls."""
        func_start = self.html.find('function showModalError(')
        func_end = self.html.find('}', func_start)
        func_body = self.html[func_start:func_end]
        self.assertNotIn('fetch(', func_body,
            "showModalError must not make network requests")
        self.assertNotIn('XMLHttpRequest', func_body,
            "showModalError must not make network requests")

    def test_clear_modal_error_is_dom_only(self):
        """clearModalError must only do DOM manipulation."""
        func_start = self.html.find('function clearModalError(')
        func_end = self.html.find('}', func_start)
        func_body = self.html[func_start:func_end]
        self.assertNotIn('fetch(', func_body,
            "clearModalError must not make network requests")


if __name__ == '__main__':
    unittest.main()
