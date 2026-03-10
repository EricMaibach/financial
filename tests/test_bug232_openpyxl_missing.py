"""
Tests for Bug #232: Richmond Fed SOS Indicator missing — openpyxl not installed.

openpyxl must be listed in signaltrackers/requirements.txt so that
pandas.read_excel() can parse the Richmond Fed .xlsx file. Without it,
_fetch_richmond_sos() silently returns (None, None) via a bare except clause,
causing the SOS model block to be omitted from the Recession Probability panel.

Second root cause (discovered during preview image validation): the Date column
in the Richmond Fed xlsx is parsed by pandas+openpyxl as datetime64/Timestamp,
NOT as an Excel serial integer. The original code called int(last_row.iloc[0]),
which raises TypeError on a Timestamp. Fix: use pd.Timestamp(last_row.iloc[0]).

Test note: xlsx mock data MUST use datetime objects in the Date column so that
openpyxl stores them as proper date cells and pandas reads them back as Timestamps.
Passing serial integers would store them as plain numbers, masking the bug.
"""

import io
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def _read_requirements() -> str:
    path = os.path.join(SIGNALTRACKERS_DIR, 'requirements.txt')
    with open(path) as f:
        return f.read()


def _read_source(filename: str) -> str:
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# Requirements file tests
# ---------------------------------------------------------------------------


class TestOpenpyxlInRequirements(unittest.TestCase):
    """openpyxl must be listed in requirements.txt with a lower-bound pin."""

    @classmethod
    def setUpClass(cls):
        cls.reqs = _read_requirements()

    def test_openpyxl_present(self):
        """requirements.txt must contain an openpyxl entry."""
        self.assertIn('openpyxl', self.reqs, "openpyxl not found in requirements.txt")

    def test_openpyxl_has_version_pin(self):
        """openpyxl entry must have a >= version constraint, not a wildcard."""
        import re
        match = re.search(r'openpyxl\s*>=\s*[\d.]+', self.reqs)
        self.assertIsNotNone(
            match,
            "openpyxl must be pinned with >= in requirements.txt (e.g. openpyxl>=3.0.0)"
        )

    def test_openpyxl_minimum_version(self):
        """openpyxl minimum version must be >= 3.0.0."""
        import re
        match = re.search(r'openpyxl\s*>=\s*([\d.]+)', self.reqs)
        self.assertIsNotNone(match, "openpyxl version constraint not found")
        from packaging.version import Version
        min_ver = Version(match.group(1))
        self.assertGreaterEqual(min_ver, Version('3.0.0'),
                                "openpyxl must require >= 3.0.0 for xlsx support")

    def test_xlrd_still_present(self):
        """xlrd must remain in requirements.txt (used for legacy .xls support)."""
        self.assertIn('xlrd', self.reqs)


# ---------------------------------------------------------------------------
# Static source tests
# ---------------------------------------------------------------------------


class TestRichmondSOSSourceStructure(unittest.TestCase):
    """_fetch_richmond_sos() must use read_excel and handle failures gracefully."""

    @classmethod
    def setUpClass(cls):
        cls.src = _read_source('recession_probability.py')

    def test_read_excel_called(self):
        """Source must call pd.read_excel to parse the .xlsx file."""
        self.assertIn('read_excel', self.src)

    def test_graceful_none_return_on_failure(self):
        """Function must return (None, None) on failure, not raise."""
        self.assertIn('return None, None', self.src)

    def test_richmond_sos_key_in_cache(self):
        """'richmond_sos' key must appear in the cache-building section."""
        self.assertIn("'richmond_sos'", self.src)

    def test_sos_risk_label_assigned(self):
        """richmond_sos_risk must be assigned in the probability update."""
        self.assertIn('richmond_sos_risk', self.src)

    def test_timestamp_used_for_date_parsing(self):
        """Source must use pd.Timestamp() to parse the date column — not int() serial conversion.

        pandas+openpyxl automatically parse date columns as datetime64/Timestamp.
        The original code called int(last_row.iloc[0]) which raises TypeError on a Timestamp.
        The fix is: pd.Timestamp(last_row.iloc[0]).strftime('%Y-%m-%d')
        """
        self.assertIn('pd.Timestamp', self.src,
                      "pd.Timestamp not found — date parsing must use pd.Timestamp(last_row.iloc[0])")

    def test_no_serial_integer_date_conversion(self):
        """Source must NOT use the broken Excel serial integer date conversion.

        The old code: int(last_row.iloc[0]) raises TypeError on a Timestamp.
        Presence of 'date_serial' or 'datetime(1899' indicates the unfixed version.
        """
        self.assertNotIn('date_serial', self.src,
                         "date_serial found — Excel serial integer conversion must be removed")
        self.assertNotIn('datetime(1899', self.src,
                         "datetime(1899 found — Excel epoch conversion must be removed")


# ---------------------------------------------------------------------------
# Behavioural tests (mocked network)
# ---------------------------------------------------------------------------


def _make_xlsx_bytes(rows: list[tuple]) -> bytes:
    """Build a minimal .xlsx file in memory using openpyxl.

    IMPORTANT: Pass datetime objects for the Date column, not Excel serial integers.
    openpyxl stores datetime objects as proper date-typed cells; pandas+openpyxl then
    reads them back as Timestamps — matching the real Richmond Fed file format.
    Passing an integer would store it as a plain number and mask the date-parsing bug.
    """
    try:
        import openpyxl
    except ImportError:
        return b''

    wb = openpyxl.Workbook()
    ws = wb.active
    # Header row
    ws.append(['Date', 'SOS Indicator', 'Recession Threshold'])
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestFetchRichmondSOSSuccess(unittest.TestCase):
    """_fetch_richmond_sos() must parse a well-formed xlsx and return (value, date).

    Mock data uses datetime objects in the Date column so openpyxl stores proper
    date cells, which pandas reads back as Timestamps — exactly as the real file does.
    """

    def setUp(self):
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl not installed — install it via requirements.txt")

    def test_returns_float_and_date_string(self):
        """Happy path: valid xlsx with datetime Date cell → (float, 'YYYY-MM-DD')."""
        from recession_probability import _fetch_richmond_sos

        target_date = datetime(2026, 2, 7)
        xlsx_bytes = _make_xlsx_bytes([(target_date, 0.35, 0.2)])

        mock_resp = MagicMock()
        mock_resp.content = xlsx_bytes
        mock_resp.raise_for_status.return_value = None

        with patch('recession_probability.requests.get', return_value=mock_resp):
            prob, date_str = _fetch_richmond_sos()

        self.assertIsNotNone(prob, "Expected float probability, got None — date parsing likely failed")
        self.assertAlmostEqual(prob, 0.35, places=5)
        self.assertEqual(date_str, '2026-02-07')

    def test_returns_latest_row(self):
        """With multiple rows, the last row's value and date are returned."""
        from recession_probability import _fetch_richmond_sos

        d1 = datetime(2026, 1, 31)
        d2 = datetime(2026, 2, 7)
        xlsx_bytes = _make_xlsx_bytes([(d1, 0.10, 0.2), (d2, 0.45, 0.2)])

        mock_resp = MagicMock()
        mock_resp.content = xlsx_bytes
        mock_resp.raise_for_status.return_value = None

        with patch('recession_probability.requests.get', return_value=mock_resp):
            prob, date_str = _fetch_richmond_sos()

        self.assertAlmostEqual(prob, 0.45, places=5)
        self.assertEqual(date_str, '2026-02-07')


class TestFetchRichmondSOSNetworkFailure(unittest.TestCase):
    """_fetch_richmond_sos() must return (None, None) on network errors."""

    def test_network_error_returns_none_tuple(self):
        """RequestException → (None, None), no crash."""
        from recession_probability import _fetch_richmond_sos
        import requests as req

        with patch('recession_probability.requests.get',
                   side_effect=req.exceptions.ConnectionError("timeout")):
            result = _fetch_richmond_sos()

        self.assertEqual(result, (None, None))

    def test_http_error_returns_none_tuple(self):
        """HTTP 404 → (None, None), no crash."""
        from recession_probability import _fetch_richmond_sos
        import requests as req

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req.exceptions.HTTPError("404")

        with patch('recession_probability.requests.get', return_value=mock_resp):
            result = _fetch_richmond_sos()

        self.assertEqual(result, (None, None))

    def test_empty_dataframe_returns_none_tuple(self):
        """Empty xlsx (header only) → (None, None), no crash."""
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl not installed")

        from recession_probability import _fetch_richmond_sos

        xlsx_bytes = _make_xlsx_bytes([])  # header row only, no data
        mock_resp = MagicMock()
        mock_resp.content = xlsx_bytes
        mock_resp.raise_for_status.return_value = None

        with patch('recession_probability.requests.get', return_value=mock_resp):
            result = _fetch_richmond_sos()

        self.assertEqual(result, (None, None))


class TestTemplateSOSConditional(unittest.TestCase):
    """index.html must guard the SOS model block on recession_probability.richmond_sos."""

    @classmethod
    def setUpClass(cls):
        template_path = os.path.join(SIGNALTRACKERS_DIR, 'templates', 'index.html')
        with open(template_path) as f:
            cls.src = f.read()

    def test_richmond_sos_referenced_in_template(self):
        """Template must reference recession_probability.richmond_sos (the SOS value)."""
        self.assertIn('richmond_sos', self.src,
                      "richmond_sos not found in index.html — SOS block may be missing")

    def test_richmond_sos_conditional_present(self):
        """Template must conditionally render the SOS block using an 'is defined' guard."""
        self.assertIn('richmond_sos is defined', self.src,
                      "SOS conditional guard 'richmond_sos is defined' not found in index.html")

    def test_richmond_sos_date_rendered(self):
        """Template must render richmond_sos_date when present."""
        self.assertIn('richmond_sos_date', self.src)

    def test_richmond_sos_risk_rendered(self):
        """Template must render richmond_sos_risk label."""
        self.assertIn('richmond_sos_risk', self.src)


if __name__ == '__main__':
    unittest.main()
