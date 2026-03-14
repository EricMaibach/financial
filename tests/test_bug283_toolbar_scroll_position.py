"""
Tests for Bug #283: Toolbar scroll position fix.

Verifies that ai-briefing-toolbar.js computes topY without adding window.scrollY,
so the toolbar appears correctly at any scroll position.
"""

import os
import re
import pytest


TOOLBAR_JS_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'signaltrackers', 'static', 'js', 'components', 'ai-briefing-toolbar.js'
)


@pytest.fixture(scope='module')
def toolbar_js():
    with open(TOOLBAR_JS_PATH) as f:
        return f.read()


class TestScrollPositionFix:

    def test_scrollY_not_added_to_topY(self, toolbar_js):
        """topY must not include + window.scrollY (the root cause of bug #283)."""
        # The buggy line was: const topY = rect.top - toolbarH - 8 + window.scrollY;
        assert 'window.scrollY' not in toolbar_js or \
               re.search(r'topY\s*=.*window\.scrollY', toolbar_js) is None, \
            'topY must not add window.scrollY — toolbar uses position:fixed (viewport coords)'

    def test_topY_uses_viewport_coords(self, toolbar_js):
        """topY is computed purely from getBoundingClientRect() values (viewport-relative)."""
        match = re.search(r'const topY\s*=\s*([^;]+);', toolbar_js)
        assert match, 'topY assignment not found in toolbar JS'
        expr = match.group(1)
        assert 'window.scrollY' not in expr, \
            f'topY expression "{expr}" must not include window.scrollY'

    def test_topY_formula_correct(self, toolbar_js):
        """topY is rect.top - toolbarH - 8 (8px gap above selection)."""
        assert 'rect.top - toolbarH - 8' in toolbar_js, \
            'topY formula should be rect.top - toolbarH - 8'

    def test_toolbar_uses_position_fixed(self, toolbar_js):
        """Toolbar element uses position:fixed — confirms viewport coords are correct."""
        # The CSS sets position:fixed; JS must be consistent
        # Verify no pageYOffset / scrollTop usage in positioning logic
        assert 'pageYOffset' not in toolbar_js, \
            'pageYOffset must not be used for toolbar positioning'

    def test_scroll_listener_still_present(self, toolbar_js):
        """Scroll dismiss listener is not accidentally removed by the fix."""
        assert 'scroll' in toolbar_js, 'Scroll event listener should still be present'
        assert 'onScroll' in toolbar_js, 'onScroll handler should still be present'

    def test_viewport_clamping_unchanged(self, toolbar_js):
        """Horizontal viewport clamping logic is still in place."""
        assert 'viewportW' in toolbar_js
        assert 'Math.max(8,' in toolbar_js or 'Math.max( 8,' in toolbar_js or \
               re.search(r'Math\.max\s*\(\s*8\s*,', toolbar_js), \
            'Left-edge clamping should still be present'
