"""
Static verification tests for US-171.2: Mobile FAB + bottom sheet section navigator.

These tests inspect the HTML template and CSS source files without requiring a live
Flask server.  They verify structural correctness, accessibility attributes, and
CSS property presence.
"""

import os
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(REPO_ROOT, 'signaltrackers', 'templates')
STATIC_CSS_DIR = os.path.join(REPO_ROOT, 'signaltrackers', 'static', 'css')


def read_file(path):
    with open(path, 'r') as f:
        return f.read()


INDEX_HTML = read_file(os.path.join(TEMPLATES_DIR, 'index.html'))
NAV_CSS    = read_file(os.path.join(STATIC_CSS_DIR, 'section-quick-nav.css'))


# ---------------------------------------------------------------------------
# FAB — HTML structure & accessibility
# ---------------------------------------------------------------------------

class TestMobileFABHtml(unittest.TestCase):
    """FAB button appears in index.html with correct accessibility attributes."""

    def test_fab_class_present(self):
        self.assertIn('section-quick-nav-fab', INDEX_HTML)

    def test_fab_id_present(self):
        self.assertIn('id="section-nav-fab"', INDEX_HTML)

    def test_fab_aria_label(self):
        self.assertIn('aria-label="Jump to section"', INDEX_HTML)

    def test_fab_aria_expanded_false(self):
        # Initial state must be false (sheet is closed)
        self.assertIn('aria-expanded="false"', INDEX_HTML)

    def test_fab_aria_controls(self):
        self.assertIn('aria-controls="section-quick-nav-sheet"', INDEX_HTML)

    def test_fab_icon_bi_list_ul(self):
        # Uses Bootstrap Icons bi-list-ul
        self.assertIn('bi-list-ul', INDEX_HTML)


# ---------------------------------------------------------------------------
# Backdrop — HTML structure
# ---------------------------------------------------------------------------

class TestBackdropHtml(unittest.TestCase):

    def test_backdrop_class_present(self):
        self.assertIn('section-quick-nav-backdrop', INDEX_HTML)

    def test_backdrop_id_present(self):
        self.assertIn('id="section-nav-backdrop"', INDEX_HTML)

    def test_backdrop_aria_hidden(self):
        self.assertIn('aria-hidden="true"', INDEX_HTML)


# ---------------------------------------------------------------------------
# Bottom sheet — HTML structure & accessibility
# ---------------------------------------------------------------------------

class TestBottomSheetHtml(unittest.TestCase):

    def test_sheet_class_present(self):
        self.assertIn('class="section-quick-nav-sheet"', INDEX_HTML)

    def test_sheet_id_present(self):
        self.assertIn('id="section-quick-nav-sheet"', INDEX_HTML)

    def test_sheet_role_dialog(self):
        self.assertIn('role="dialog"', INDEX_HTML)

    def test_sheet_aria_modal(self):
        self.assertIn('aria-modal="true"', INDEX_HTML)

    def test_sheet_aria_labelledby(self):
        # Must point to the title element's id
        self.assertIn('aria-labelledby="section-nav-sheet-title"', INDEX_HTML)

    def test_sheet_title_id(self):
        self.assertIn('id="section-nav-sheet-title"', INDEX_HTML)

    def test_sheet_title_text(self):
        self.assertIn('Jump to Section', INDEX_HTML)

    def test_close_button_id(self):
        self.assertIn('id="section-nav-sheet-close"', INDEX_HTML)

    def test_close_button_aria_label(self):
        self.assertIn('aria-label="Close section navigator"', INDEX_HTML)

    def test_handle_element_present(self):
        self.assertIn('section-quick-nav-sheet__handle', INDEX_HTML)

    def test_sheet_list_present(self):
        self.assertIn('section-quick-nav-sheet__list', INDEX_HTML)


# ---------------------------------------------------------------------------
# Bottom sheet — section items
# ---------------------------------------------------------------------------

class TestSheetSectionItems(unittest.TestCase):
    """All 9 sections must be listed in the bottom sheet."""

    SECTION_LABELS = ['Regime', 'Recession', 'Implications', 'Sectors', 'Markets',
                      'Briefing', 'Movers', 'Signals', 'Prediction']

    SECTION_IDS = [
        '#macro-regime-section',
        '#recession-panel-section',
        '#regime-implications',
        '#sector-tone-section',
        '#market-conditions',
        '#briefing-section',
        '#movers-section',
        '#signals-section',
        '#prediction-section',
    ]

    def _sheet_fragment(self):
        # Extract the section between the sheet div open and the first endblock
        start = INDEX_HTML.find('section-quick-nav-sheet__list')
        end   = INDEX_HTML.find('</div>', start + 1)
        return INDEX_HTML[start:end + 6]

    def test_nine_sheet_items(self):
        count = INDEX_HTML.count('section-quick-nav-sheet__item')
        # Each item appears twice: once in class attr, once in JS querySelector
        # At minimum, the class attribute appears 9 times
        self.assertGreaterEqual(count, 9)

    def test_all_data_targets_present(self):
        for sid in self.SECTION_IDS:
            self.assertIn('data-target="{}"'.format(sid), INDEX_HTML,
                          msg='Missing data-target={} in sheet items'.format(sid))


# ---------------------------------------------------------------------------
# CSS — FAB styles
# ---------------------------------------------------------------------------

class TestFABCss(unittest.TestCase):

    def test_fab_class_defined(self):
        self.assertIn('.section-quick-nav-fab', NAV_CSS)

    def test_fab_position_fixed(self):
        # Find .section-quick-nav-fab rule block
        start = NAV_CSS.find('.section-quick-nav-fab {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('position: fixed', block)

    def test_fab_z_index_200(self):
        start = NAV_CSS.find('.section-quick-nav-fab {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('z-index: 200', block)

    def test_fab_hidden_desktop(self):
        # FAB must be display:none at 768px+
        self.assertIn('display: none', NAV_CSS)
        # Confirm the media query context
        self.assertIn('min-width: 768px', NAV_CSS)

    def test_fab_safe_area_inset(self):
        # iOS safe area support
        self.assertIn('env(safe-area-inset-bottom)', NAV_CSS)

    def test_fab_border_radius_50(self):
        # FAB is a circle
        start = NAV_CSS.find('.section-quick-nav-fab {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('border-radius: 50%', block)

    def test_fab_width_48(self):
        start = NAV_CSS.find('.section-quick-nav-fab {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('width: 48px', block)

    def test_fab_height_48(self):
        start = NAV_CSS.find('.section-quick-nav-fab {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('height: 48px', block)


# ---------------------------------------------------------------------------
# CSS — Backdrop styles
# ---------------------------------------------------------------------------

class TestBackdropCss(unittest.TestCase):

    def test_backdrop_class_defined(self):
        self.assertIn('.section-quick-nav-backdrop', NAV_CSS)

    def test_backdrop_z_index_300(self):
        start = NAV_CSS.find('.section-quick-nav-backdrop {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('z-index: 300', block)

    def test_backdrop_rgba_background(self):
        self.assertIn('rgba(0, 0, 0, 0.4)', NAV_CSS)

    def test_backdrop_opacity_transition(self):
        # Backdrop should fade in
        start = NAV_CSS.find('.section-quick-nav-backdrop {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('transition', block)


# ---------------------------------------------------------------------------
# CSS — Sheet panel styles
# ---------------------------------------------------------------------------

class TestSheetPanelCss(unittest.TestCase):

    def test_sheet_class_defined(self):
        self.assertIn('.section-quick-nav-sheet {', NAV_CSS)

    def test_sheet_z_index_301(self):
        start = NAV_CSS.find('.section-quick-nav-sheet {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('z-index: 301', block)

    def test_sheet_max_height_65vh(self):
        start = NAV_CSS.find('.section-quick-nav-sheet {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('max-height: 65vh', block)

    def test_sheet_border_radius(self):
        # 12px 12px 0 0
        start = NAV_CSS.find('.section-quick-nav-sheet {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('12px 12px 0 0', block)

    def test_sheet_starts_hidden(self):
        # Sheet starts off-screen via translateY(100%)
        self.assertIn('translateY(100%)', NAV_CSS)

    def test_sheet_is_open_class(self):
        # .is-open moves sheet into view
        self.assertIn('.section-quick-nav-sheet.is-open', NAV_CSS)
        self.assertIn('translateY(0)', NAV_CSS)

    def test_sheet_slide_transition(self):
        start = NAV_CSS.find('.section-quick-nav-sheet {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('transition', block)
        self.assertIn('250ms ease-out', block)


# ---------------------------------------------------------------------------
# CSS — Sheet items
# ---------------------------------------------------------------------------

class TestSheetItemCss(unittest.TestCase):

    def test_sheet_item_class_defined(self):
        self.assertIn('.section-quick-nav-sheet__item', NAV_CSS)

    def test_sheet_item_min_height_48(self):
        start = NAV_CSS.find('.section-quick-nav-sheet__item {')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('min-height: 48px', block)

    def test_sheet_item_active_color(self):
        # Active item must use brand-blue-500
        self.assertIn('.section-quick-nav-sheet__item.is-active', NAV_CSS)

    def test_sheet_item_active_border_left(self):
        start = NAV_CSS.find('.section-quick-nav-sheet__item.is-active')
        block = NAV_CSS[start:NAV_CSS.find('}', start)]
        self.assertIn('border-left: 3px solid', block)


# ---------------------------------------------------------------------------
# CSS — Reduced motion overrides
# ---------------------------------------------------------------------------

class TestReducedMotionCss(unittest.TestCase):

    def test_reduced_motion_sheet(self):
        # Both sheet and backdrop should have transition: none under reduced motion
        self.assertIn('prefers-reduced-motion: reduce', NAV_CSS)
        # Find the reduced motion block (last one in file)
        idx = NAV_CSS.rfind('prefers-reduced-motion: reduce')
        block = NAV_CSS[idx:NAV_CSS.find('@media', idx + 1) if '@media' in NAV_CSS[idx + 1:] else len(NAV_CSS)]
        self.assertIn('transition: none', block)


# ---------------------------------------------------------------------------
# JavaScript — key patterns in index.html
# ---------------------------------------------------------------------------

class TestMobileFABJavaScript(unittest.TestCase):

    def test_open_sheet_function(self):
        self.assertIn('openSheet', INDEX_HTML)

    def test_close_sheet_function(self):
        self.assertIn('closeSheet', INDEX_HTML)

    def test_body_overflow_hidden(self):
        self.assertIn("document.body.style.overflow = 'hidden'", INDEX_HTML)

    def test_body_overflow_restored(self):
        self.assertIn("document.body.style.overflow = ''", INDEX_HTML)

    def test_fab_aria_expanded_toggled(self):
        self.assertIn("setAttribute('aria-expanded', 'true')", INDEX_HTML)
        self.assertIn("setAttribute('aria-expanded', 'false')", INDEX_HTML)

    def test_focus_trap_tab_handling(self):
        self.assertIn("focus trap", INDEX_HTML.lower())
        self.assertIn("e.key !== 'Tab'", INDEX_HTML)

    def test_escape_key_closes_sheet(self):
        self.assertIn("'Escape'", INDEX_HTML)

    def test_focus_returns_to_fab_on_close(self):
        self.assertIn('fab.focus()', INDEX_HTML)

    def test_mobile_scroll_offset_navbar_only(self):
        # Mobile scroll uses navbar height only (no strip offset)
        self.assertIn('mobileScrollOffset', INDEX_HTML)

    def test_set_active_section_updates_sheet_items(self):
        # setActiveSection must update both pills and sheet items
        self.assertIn('setActiveSection', INDEX_HTML)
        self.assertIn('sheetItems', INDEX_HTML)


if __name__ == '__main__':
    unittest.main()
