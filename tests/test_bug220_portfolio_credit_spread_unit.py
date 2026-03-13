"""
Tests for Bug #220: Portfolio AI credit spread unit conversion missing.

generate_portfolio_market_context() was reading raw FRED values (e.g. 2.8)
and formatting them as basis points without the required * 100 conversion.
This caused the portfolio AI to see HY spread as ~3 bp instead of ~280 bp.
Fix: add * 100 to hy_val and ig_val inside generate_portfolio_market_context().
"""

import os
import sys
import re
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


def extract_function_body(src, func_name, chars=3000):
    """Return the first `chars` characters of a named function."""
    start = src.find(f'def {func_name}(')
    if start == -1:
        raise AssertionError(f'{func_name} not found in source')
    return src[start:start + chars]


# ---------------------------------------------------------------------------
# 1. Bug fix present — * 100 conversion inside the function
# ---------------------------------------------------------------------------

class TestPortfolioContextCreditSpreadSourceCode(unittest.TestCase):
    """Static verification that the * 100 conversion is present in generate_portfolio_market_context()."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')
        cls.func_body = extract_function_body(cls.src, 'generate_portfolio_market_context')

    def test_hy_val_multiplied_by_100(self):
        self.assertIn(
            'hy_val = hy_df.iloc[-1][hy_df.columns[1]] * 100',
            self.func_body,
            'hy_val must be multiplied by 100 inside generate_portfolio_market_context()'
        )

    def test_ig_val_multiplied_by_100(self):
        self.assertIn(
            'ig_val = ig_df.iloc[-1][ig_df.columns[1]] * 100',
            self.func_body,
            'ig_val must be multiplied by 100 inside generate_portfolio_market_context()'
        )

    def test_hy_spread_formatted_as_bp(self):
        """HY spread must be formatted as integer bp in the output."""
        self.assertIn('HY Spread: {hy_val:.0f} bp', self.func_body)

    def test_ig_spread_formatted_as_bp(self):
        """IG spread must be formatted as integer bp in the output."""
        self.assertIn('IG Spread: {ig_val:.0f} bp', self.func_body)

    def test_broken_raw_assignment_absent(self):
        """Confirm the pre-fix raw assignment (without * 100) is not present."""
        # The exact broken pattern: assignment without * 100
        self.assertNotIn(
            'hy_val = hy_df.iloc[-1][hy_df.columns[1]]\n',
            self.func_body,
            'Pre-fix broken hy_val assignment (missing * 100) must not exist'
        )
        self.assertNotIn(
            'ig_val = ig_df.iloc[-1][ig_df.columns[1]]\n',
            self.func_body,
            'Pre-fix broken ig_val assignment (missing * 100) must not exist'
        )


# ---------------------------------------------------------------------------
# 2. Scope boundaries — all other call sites remain correct
# ---------------------------------------------------------------------------

class TestAllCreditSpreadCallSitesConsistent(unittest.TestCase):
    """Every hy_df.iloc[-1] and ig_df.iloc[-1] assignment in dashboard.py applies * 100."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')
        cls.lines = cls.src.splitlines()

    def _find_bad_assignments(self, pattern):
        """
        Return list of (lineno, line) where pattern matches but * 100 is absent.
        Excludes multi-expression lines for change calculations.
        """
        bad = []
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if re.search(pattern, stripped):
                # Skip comments
                if stripped.startswith('#'):
                    continue
                # Skip lines that are computing change (they do subtraction first, then * 100)
                if 'hy_df.iloc[-1]' in stripped and 'hy_df.iloc[' in stripped and '-' in stripped:
                    continue
                if '* 100' not in stripped:
                    bad.append((i + 1, stripped))
        return bad

    def test_all_hy_df_iloc_last_row_assignments_have_multiplication(self):
        """Every `hy_val = hy_df.iloc[-1]...` or `hy_current = hy_df.iloc[-1]...` line has * 100."""
        bad = self._find_bad_assignments(r'(hy_val|hy_current)\s*=\s*hy_df\.iloc\[-1\]')
        self.assertEqual(bad, [], f'hy_df.iloc[-1] assignments without * 100: {bad}')

    def test_all_ig_df_iloc_last_row_assignments_have_multiplication(self):
        """Every `ig_val = ig_df.iloc[-1]...` or `ig_current = ig_df.iloc[-1]...` line has * 100."""
        bad = self._find_bad_assignments(r'(ig_val|ig_current)\s*=\s*ig_df\.iloc\[-1\]')
        self.assertEqual(bad, [], f'ig_df.iloc[-1] assignments without * 100: {bad}')


# ---------------------------------------------------------------------------
# 3. No other functions modified
# ---------------------------------------------------------------------------

class TestScopeBoundaries(unittest.TestCase):
    """The fix must touch only generate_portfolio_market_context()."""

    @classmethod
    def setUpClass(cls):
        cls.src = read_source('dashboard.py')

    def _assert_line_contains(self, lineno, expected_snippet):
        lines = self.src.splitlines()
        actual = lines[lineno - 1].strip() if lineno <= len(lines) else ''
        self.assertIn(expected_snippet, actual,
                      f'Line {lineno} expected to contain {expected_snippet!r}, got: {actual!r}')

    def test_line_907_still_correct(self):
        self._assert_line_contains(907, '* 100')

    def test_line_916_still_correct(self):
        self._assert_line_contains(916, '* 100')

    def test_line_937_still_correct(self):
        self._assert_line_contains(937, '* 100')

    def test_line_1008_still_correct(self):
        self._assert_line_contains(1008, '* 100')

    def test_line_1048_still_correct(self):
        self._assert_line_contains(1048, '* 100')

    def test_line_1109_still_correct(self):
        self._assert_line_contains(1109, '* 100')


# ---------------------------------------------------------------------------
# 4. Output value range documentation (static assertion on formula)
# ---------------------------------------------------------------------------

class TestCreditSpreadOutputValueDocumentation(unittest.TestCase):
    """
    Document the expected output ranges as static assertions.
    Raw FRED value * 100 must produce realistic basis-point values.
    """

    def test_normal_market_hy_formula(self):
        """Raw FRED 2.80 * 100 = 280 bp (normal market)."""
        self.assertEqual(int(2.80 * 100), 280)

    def test_stressed_market_hy_formula(self):
        """Raw FRED 5.50 * 100 = 550 bp (stressed market)."""
        self.assertEqual(int(5.50 * 100), 550)

    def test_normal_market_ig_formula(self):
        """Raw FRED 0.95 * 100 = 95 bp (normal market)."""
        self.assertEqual(int(0.95 * 100), 95)

    def test_tight_market_ig_formula(self):
        """Raw FRED 0.80 * 100 = 80 bp (very tight)."""
        self.assertEqual(int(0.80 * 100), 80)

    def test_broken_formula_would_produce_wrong_value(self):
        """Pre-fix: int(2.80) = 2 or 3 — confirm this is wrong."""
        broken_result = int(2.80)
        self.assertLess(broken_result, 10, 'Pre-fix value is single-digit (wrong scale)')
        self.assertNotEqual(broken_result, 280, 'Pre-fix value is not the correct bp value')


if __name__ == '__main__':
    unittest.main()
