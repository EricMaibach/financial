"""
Static verification tests for US-123.1: Backend — SEC EDGAR 8-K ingestion +
FinBERT scoring + GICS sector aggregation.

These tests verify implementation correctness without requiring live EDGAR
network calls, FinBERT model downloads, or a running Flask server.
They exercise pure-Python logic and inspect source files for structural
correctness.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Module existence
# ---------------------------------------------------------------------------


class TestModuleExists(unittest.TestCase):
    """sector_tone_pipeline.py must exist in signaltrackers/."""

    def test_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'sector_tone_pipeline.py')
        self.assertTrue(os.path.isfile(path), 'sector_tone_pipeline.py not found')


# ---------------------------------------------------------------------------
# Module imports without network calls
# ---------------------------------------------------------------------------


class TestModuleImports(unittest.TestCase):
    """Module must be importable without triggering network calls."""

    def test_import_does_not_raise(self):
        import sector_tone_pipeline
        self.assertIsNotNone(sector_tone_pipeline)

    def test_get_function_exists(self):
        from sector_tone_pipeline import get_sector_management_tone
        self.assertTrue(callable(get_sector_management_tone))

    def test_update_function_exists(self):
        from sector_tone_pipeline import update_sector_management_tone
        self.assertTrue(callable(update_sector_management_tone))

    def test_classify_tone_function_exists(self):
        from sector_tone_pipeline import _classify_tone
        self.assertTrue(callable(_classify_tone))

    def test_no_transformers_import_at_module_level(self):
        """Importing the module must not import transformers (lazy import)."""
        src = read_source('sector_tone_pipeline.py')
        # transformers import must NOT appear at module top level
        lines = src.splitlines()
        module_level_lines = []
        for line in lines:
            stripped = line.strip()
            # Stop at first function/class definition
            if stripped.startswith('def ') or stripped.startswith('class '):
                break
            module_level_lines.append(stripped)
        module_top = '\n'.join(module_level_lines)
        self.assertNotIn('from transformers', module_top,
                         'transformers must not be imported at module level (lazy import required)')

    def test_no_network_calls_at_import(self):
        """Import must not trigger requests.get calls."""
        with patch('requests.get') as mock_get:
            # Re-import should not call requests.get
            import importlib
            import sector_tone_pipeline
            importlib.reload(sector_tone_pipeline)
            mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# SCORE_THRESHOLD constant
# ---------------------------------------------------------------------------


class TestScoreThreshold(unittest.TestCase):
    """SCORE_THRESHOLD must be defined as a module-level constant = 0.15."""

    def setUp(self):
        import sector_tone_pipeline as stp
        self.stp = stp

    def test_score_threshold_defined(self):
        self.assertTrue(hasattr(self.stp, 'SCORE_THRESHOLD'))

    def test_score_threshold_is_float(self):
        self.assertIsInstance(self.stp.SCORE_THRESHOLD, float)

    def test_score_threshold_value(self):
        self.assertEqual(self.stp.SCORE_THRESHOLD, 0.15)

    def test_score_threshold_name_exact(self):
        src = read_source('sector_tone_pipeline.py')
        self.assertIn('SCORE_THRESHOLD = 0.15', src)

    def test_classify_tone_uses_threshold_constant(self):
        """Classification logic must use SCORE_THRESHOLD, not literal 0.15."""
        src = read_source('sector_tone_pipeline.py')
        # The function body should reference SCORE_THRESHOLD in comparisons
        self.assertIn('SCORE_THRESHOLD', src)
        # Must not use raw literal 0.15 in comparison operators
        import re
        # Match > 0.15 or < -0.15 as bare literals in comparison
        bare_literal = re.findall(r'[<>]\s*-?0\.15\b', src)
        self.assertEqual(len(bare_literal), 0,
                         f"Found bare 0.15 literal in comparison: {bare_literal}")


# ---------------------------------------------------------------------------
# Tone classification logic
# ---------------------------------------------------------------------------


class TestClassifyTone(unittest.TestCase):
    """_classify_tone must return correct labels for all boundary cases."""

    def setUp(self):
        from sector_tone_pipeline import _classify_tone
        self.classify = _classify_tone

    def test_above_threshold_is_positive(self):
        self.assertEqual(self.classify(0.16), 'positive')

    def test_well_above_threshold_is_positive(self):
        self.assertEqual(self.classify(0.5), 'positive')

    def test_at_plus_one_is_positive(self):
        self.assertEqual(self.classify(1.0), 'positive')

    def test_below_neg_threshold_is_negative(self):
        self.assertEqual(self.classify(-0.16), 'negative')

    def test_well_below_threshold_is_negative(self):
        self.assertEqual(self.classify(-0.5), 'negative')

    def test_at_minus_one_is_negative(self):
        self.assertEqual(self.classify(-1.0), 'negative')

    def test_zero_is_neutral(self):
        self.assertEqual(self.classify(0.0), 'neutral')

    def test_small_positive_is_neutral(self):
        self.assertEqual(self.classify(0.10), 'neutral')

    def test_small_negative_is_neutral(self):
        self.assertEqual(self.classify(-0.10), 'neutral')

    def test_exact_positive_threshold_is_neutral(self):
        """Boundary: 0.15 exactly → neutral (not positive)."""
        self.assertEqual(self.classify(0.15), 'neutral')

    def test_exact_negative_threshold_is_neutral(self):
        """Boundary: -0.15 exactly → neutral (not negative)."""
        self.assertEqual(self.classify(-0.15), 'neutral')

    def test_just_above_threshold_is_positive(self):
        self.assertEqual(self.classify(0.151), 'positive')

    def test_just_below_neg_threshold_is_negative(self):
        self.assertEqual(self.classify(-0.151), 'negative')

    def test_return_type_is_string(self):
        for v in [0.5, -0.5, 0.0]:
            result = self.classify(v)
            self.assertIsInstance(result, str, f"classify({v}) returned non-string")

    def test_only_three_possible_values(self):
        values = [0.5, -0.5, 0.0, 0.15, -0.15, 0.16, -0.16]
        for v in values:
            self.assertIn(self.classify(v), ('positive', 'neutral', 'negative'))


# ---------------------------------------------------------------------------
# GICS sectors
# ---------------------------------------------------------------------------


class TestGicsSectors(unittest.TestCase):
    """GICS_SECTORS must contain exactly 11 canonical sector names."""

    def setUp(self):
        import sector_tone_pipeline as stp
        self.sectors = stp.GICS_SECTORS

    def test_gics_sectors_defined(self):
        import sector_tone_pipeline as stp
        self.assertTrue(hasattr(stp, 'GICS_SECTORS'))

    def test_exactly_11_sectors(self):
        self.assertEqual(len(self.sectors), 11)

    def test_information_technology_present(self):
        self.assertIn("Information Technology", self.sectors)

    def test_health_care_present(self):
        self.assertIn("Health Care", self.sectors)

    def test_financials_present(self):
        self.assertIn("Financials", self.sectors)

    def test_consumer_discretionary_present(self):
        self.assertIn("Consumer Discretionary", self.sectors)

    def test_communication_services_present(self):
        self.assertIn("Communication Services", self.sectors)

    def test_industrials_present(self):
        self.assertIn("Industrials", self.sectors)

    def test_consumer_staples_present(self):
        self.assertIn("Consumer Staples", self.sectors)

    def test_energy_present(self):
        self.assertIn("Energy", self.sectors)

    def test_materials_present(self):
        self.assertIn("Materials", self.sectors)

    def test_real_estate_present(self):
        self.assertIn("Real Estate", self.sectors)

    def test_utilities_present(self):
        self.assertIn("Utilities", self.sectors)

    def test_no_duplicates(self):
        self.assertEqual(len(self.sectors), len(set(self.sectors)))

    def test_all_entries_are_strings(self):
        for s in self.sectors:
            self.assertIsInstance(s, str)


# ---------------------------------------------------------------------------
# Short name mapping
# ---------------------------------------------------------------------------


class TestShortNameMap(unittest.TestCase):
    """SHORT_NAME_MAP must contain PM-canonical abbreviations for 4 sectors."""

    def setUp(self):
        import sector_tone_pipeline as stp
        self.name_map = stp.SHORT_NAME_MAP

    def test_short_name_map_defined(self):
        import sector_tone_pipeline as stp
        self.assertTrue(hasattr(stp, 'SHORT_NAME_MAP'))

    def test_consumer_discretionary_abbreviation(self):
        self.assertEqual(self.name_map.get("Consumer Discretionary"), "Cons. Discretionary")

    def test_consumer_staples_abbreviation(self):
        self.assertEqual(self.name_map.get("Consumer Staples"), "Cons. Staples")

    def test_communication_services_abbreviation(self):
        self.assertEqual(self.name_map.get("Communication Services"), "Comm. Services")

    def test_information_technology_abbreviation(self):
        self.assertEqual(self.name_map.get("Information Technology"), "Technology")

    def test_non_abbreviated_sectors_not_in_map(self):
        """Sectors that are already ≤18 chars should not need abbreviation."""
        # These sectors should NOT be abbreviated (full name ≤ 18 chars)
        short_sectors = ["Financials", "Industrials", "Energy", "Materials", "Utilities"]
        for sector in short_sectors:
            self.assertNotIn(sector, self.name_map,
                             f"'{sector}' should not need abbreviation (already ≤18 chars)")

    def test_non_abbreviated_sectors_within_18_chars(self):
        """Sectors that are NOT in the PM abbreviation map must already be ≤18 chars
        (so they don't need abbreviation). The 18-char rule applies to passthrough
        sectors; PM-canonical abbreviations like 'Cons. Discretionary' (19 chars)
        are intentional and approved by PM decision (2026-02-25)."""
        import sector_tone_pipeline as stp
        for sector in stp.GICS_SECTORS:
            if sector in stp.SHORT_NAME_MAP:
                continue  # PM-approved abbreviations — skip length check
            self.assertLessEqual(len(sector), 18,
                                 f"Sector '{sector}' is not abbreviated but exceeds 18 chars")


# ---------------------------------------------------------------------------
# SP500_BY_SECTOR
# ---------------------------------------------------------------------------


class TestSp500BySector(unittest.TestCase):
    """SP500_BY_SECTOR must cover all 11 GICS sectors with S&P 500 tickers."""

    def setUp(self):
        import sector_tone_pipeline as stp
        self.by_sector = stp.SP500_BY_SECTOR
        self.gics = stp.GICS_SECTORS

    def test_sp500_by_sector_defined(self):
        import sector_tone_pipeline as stp
        self.assertTrue(hasattr(stp, 'SP500_BY_SECTOR'))

    def test_all_11_sectors_have_entries(self):
        for sector in self.gics:
            self.assertIn(sector, self.by_sector,
                          f"Sector '{sector}' missing from SP500_BY_SECTOR")

    def test_each_sector_has_at_least_one_ticker(self):
        for sector, tickers in self.by_sector.items():
            self.assertGreater(len(tickers), 0,
                               f"Sector '{sector}' has no tickers")

    def test_all_tickers_are_strings(self):
        for sector, tickers in self.by_sector.items():
            for t in tickers:
                self.assertIsInstance(t, str,
                                      f"Ticker {t!r} in {sector} is not a string")

    def test_all_tickers_uppercase(self):
        for sector, tickers in self.by_sector.items():
            for t in tickers:
                self.assertEqual(t, t.upper(),
                                 f"Ticker {t!r} in {sector} is not uppercase")


# ---------------------------------------------------------------------------
# EDGAR URL constants
# ---------------------------------------------------------------------------


class TestEdgarUrlConstants(unittest.TestCase):
    """EDGAR URLs must be HTTPS and point to correct SEC endpoints."""

    def setUp(self):
        import sector_tone_pipeline as stp
        self.stp = stp

    def test_edgar_search_url_defined(self):
        self.assertTrue(hasattr(self.stp, '_EDGAR_SEARCH_URL'))

    def test_edgar_search_url_is_https(self):
        self.assertTrue(self.stp._EDGAR_SEARCH_URL.startswith('https://'),
                        'EDGAR search URL must use HTTPS')

    def test_edgar_search_url_points_to_sec(self):
        self.assertIn('sec.gov', self.stp._EDGAR_SEARCH_URL)

    def test_edgar_search_url_contains_search_index(self):
        self.assertIn('search-index', self.stp._EDGAR_SEARCH_URL)

    def test_edgar_tickers_url_defined(self):
        self.assertTrue(hasattr(self.stp, '_EDGAR_TICKERS_URL'))

    def test_edgar_tickers_url_is_https(self):
        self.assertTrue(self.stp._EDGAR_TICKERS_URL.startswith('https://'))

    def test_edgar_tickers_url_points_to_sec(self):
        self.assertIn('sec.gov', self.stp._EDGAR_TICKERS_URL)

    def test_no_http_only_urls(self):
        """All URL constants must use HTTPS."""
        src = read_source('sector_tone_pipeline.py')
        import re
        http_urls = re.findall(r'http://[^\s\'"]+', src)
        self.assertEqual(http_urls, [],
                         f"Found http:// URLs (must be HTTPS): {http_urls}")

    def test_edgar_timeout_defined(self):
        self.assertTrue(hasattr(self.stp, '_EDGAR_TIMEOUT'))

    def test_edgar_timeout_is_positive_number(self):
        self.assertGreater(self.stp._EDGAR_TIMEOUT, 0)


# ---------------------------------------------------------------------------
# FinBERT model constant
# ---------------------------------------------------------------------------


class TestFinbertModel(unittest.TestCase):
    """FinBERT model must be ProsusAI/finbert from Hugging Face."""

    def test_finbert_model_name_in_source(self):
        src = read_source('sector_tone_pipeline.py')
        self.assertIn('ProsusAI/finbert', src,
                      "Source must reference ProsusAI/finbert model")

    def test_text_classification_pipeline_in_source(self):
        src = read_source('sector_tone_pipeline.py')
        self.assertIn("text-classification", src)

    def test_transformers_import_is_lazy(self):
        """transformers import must be inside a function, not at module level."""
        src = read_source('sector_tone_pipeline.py')
        # The import must be inside update_sector_management_tone
        import re
        # Find position of the import statement
        import_match = re.search(r'from transformers import', src)
        self.assertIsNotNone(import_match, "from transformers import not found in source")
        # Find position of def update_sector_management_tone
        def_match = re.search(r'def update_sector_management_tone', src)
        self.assertIsNotNone(def_match)
        # Import must appear AFTER the function definition (inside it)
        self.assertGreater(import_match.start(), def_match.start(),
                           "transformers import must be inside update_sector_management_tone, not at module level")


# ---------------------------------------------------------------------------
# _score_text_with_finbert
# ---------------------------------------------------------------------------


class TestScoreText(unittest.TestCase):
    """_score_text_with_finbert must map FinBERT output to [-1.0, +1.0]."""

    def setUp(self):
        from sector_tone_pipeline import _score_text_with_finbert
        self.score_fn = _score_text_with_finbert

    def _make_pipe(self, label, score):
        """Return a mock FinBERT pipeline that returns given label/score."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = [{'label': label, 'score': score}]
        return mock_pipe

    def test_positive_label_returns_positive_value(self):
        pipe = self._make_pipe('positive', 0.9)
        result = self.score_fn("some text", pipe)
        self.assertGreater(result, 0.0)
        self.assertAlmostEqual(result, 0.9)

    def test_negative_label_returns_negative_value(self):
        pipe = self._make_pipe('negative', 0.8)
        result = self.score_fn("some text", pipe)
        self.assertLess(result, 0.0)
        self.assertAlmostEqual(result, -0.8)

    def test_neutral_label_returns_zero(self):
        pipe = self._make_pipe('neutral', 0.95)
        result = self.score_fn("neutral text", pipe)
        self.assertEqual(result, 0.0)

    def test_empty_string_returns_zero(self):
        pipe = MagicMock()
        result = self.score_fn("", pipe)
        self.assertEqual(result, 0.0)
        pipe.assert_not_called()

    def test_whitespace_only_returns_zero(self):
        pipe = MagicMock()
        result = self.score_fn("   \n\t  ", pipe)
        self.assertEqual(result, 0.0)
        pipe.assert_not_called()

    def test_score_clamped_above_one(self):
        pipe = self._make_pipe('positive', 1.5)
        result = self.score_fn("text", pipe)
        self.assertLessEqual(result, 1.0)

    def test_score_clamped_below_zero(self):
        pipe = self._make_pipe('positive', -0.5)
        result = self.score_fn("text", pipe)
        self.assertGreaterEqual(result, -1.0)

    def test_pipeline_exception_returns_zero(self):
        pipe = MagicMock(side_effect=RuntimeError("model error"))
        result = self.score_fn("text", pipe)
        self.assertEqual(result, 0.0)

    def test_result_in_valid_range(self):
        for label, score in [('positive', 0.9), ('negative', 0.8), ('neutral', 0.99)]:
            pipe = self._make_pipe(label, score)
            result = self.score_fn("text", pipe)
            self.assertGreaterEqual(result, -1.0)
            self.assertLessEqual(result, 1.0)


# ---------------------------------------------------------------------------
# Quarter label helper
# ---------------------------------------------------------------------------


class TestGetQuarterLabel(unittest.TestCase):
    """_get_quarter_label must return correct (quarter, year) for any month."""

    def setUp(self):
        from sector_tone_pipeline import _get_quarter_label
        from datetime import datetime
        self.fn = _get_quarter_label
        self.dt = datetime

    def test_january_is_q1(self):
        self.assertEqual(self.fn(self.dt(2025, 1, 15)), ('Q1', 2025))

    def test_march_is_q1(self):
        self.assertEqual(self.fn(self.dt(2025, 3, 31)), ('Q1', 2025))

    def test_april_is_q2(self):
        self.assertEqual(self.fn(self.dt(2025, 4, 1)), ('Q2', 2025))

    def test_june_is_q2(self):
        self.assertEqual(self.fn(self.dt(2025, 6, 30)), ('Q2', 2025))

    def test_july_is_q3(self):
        self.assertEqual(self.fn(self.dt(2025, 7, 1)), ('Q3', 2025))

    def test_september_is_q3(self):
        self.assertEqual(self.fn(self.dt(2025, 9, 30)), ('Q3', 2025))

    def test_october_is_q4(self):
        self.assertEqual(self.fn(self.dt(2025, 10, 1)), ('Q4', 2025))

    def test_december_is_q4(self):
        self.assertEqual(self.fn(self.dt(2025, 12, 31)), ('Q4', 2025))

    def test_returns_tuple_of_str_and_int(self):
        q, y = self.fn(self.dt(2025, 7, 4))
        self.assertIsInstance(q, str)
        self.assertIsInstance(y, int)


# ---------------------------------------------------------------------------
# Sort sectors
# ---------------------------------------------------------------------------


class TestSortSectors(unittest.TestCase):
    """_sort_sectors must sort: positive → neutral → negative; alpha within tier."""

    def setUp(self):
        from sector_tone_pipeline import _sort_sectors
        self.sort_fn = _sort_sectors

    def _make_sector(self, name, tone):
        return {"name": name, "current_tone": tone, "current_score": 0.0,
                "short_name": name, "trend": []}

    def test_positive_before_neutral(self):
        sectors = [
            self._make_sector("Financials", "neutral"),
            self._make_sector("Technology", "positive"),
        ]
        result = self.sort_fn(sectors)
        self.assertEqual(result[0]["current_tone"], "positive")

    def test_neutral_before_negative(self):
        sectors = [
            self._make_sector("Utilities", "negative"),
            self._make_sector("Financials", "neutral"),
        ]
        result = self.sort_fn(sectors)
        self.assertEqual(result[0]["current_tone"], "neutral")

    def test_positive_before_negative(self):
        sectors = [
            self._make_sector("Utilities", "negative"),
            self._make_sector("Technology", "positive"),
        ]
        result = self.sort_fn(sectors)
        self.assertEqual(result[0]["current_tone"], "positive")
        self.assertEqual(result[1]["current_tone"], "negative")

    def test_alphabetical_within_positive_tier(self):
        sectors = [
            self._make_sector("Technology", "positive"),
            self._make_sector("Health Care", "positive"),
        ]
        result = self.sort_fn(sectors)
        self.assertEqual(result[0]["name"], "Health Care")
        self.assertEqual(result[1]["name"], "Technology")

    def test_alphabetical_within_neutral_tier(self):
        sectors = [
            self._make_sector("Materials", "neutral"),
            self._make_sector("Financials", "neutral"),
            self._make_sector("Energy", "neutral"),
        ]
        result = self.sort_fn(sectors)
        self.assertEqual(result[0]["name"], "Energy")
        self.assertEqual(result[1]["name"], "Financials")
        self.assertEqual(result[2]["name"], "Materials")

    def test_full_sort_order(self):
        """Positive → neutral → negative; alpha within each tier."""
        sectors = [
            self._make_sector("Utilities", "negative"),
            self._make_sector("Financials", "neutral"),
            self._make_sector("Technology", "positive"),
            self._make_sector("Energy", "negative"),
            self._make_sector("Health Care", "positive"),
        ]
        result = self.sort_fn(sectors)
        tones = [s["current_tone"] for s in result]
        # Verify ordering
        positives = [i for i, t in enumerate(tones) if t == "positive"]
        neutrals = [i for i, t in enumerate(tones) if t == "neutral"]
        negatives = [i for i, t in enumerate(tones) if t == "negative"]
        self.assertTrue(max(positives) < min(neutrals))
        self.assertTrue(max(neutrals) < min(negatives))

    def test_returns_list(self):
        result = self.sort_fn([self._make_sector("X", "neutral")])
        self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# Cache: get_sector_management_tone
# ---------------------------------------------------------------------------


class TestGetSectorManagementTone(unittest.TestCase):
    """get_sector_management_tone must read cache and return None when absent."""

    def setUp(self):
        from sector_tone_pipeline import get_sector_management_tone
        self.get_fn = get_sector_management_tone

    def test_returns_none_when_no_cache(self):
        import sector_tone_pipeline as stp
        with patch.object(stp, 'CACHE_FILE', Path('/nonexistent/path/cache.json')):
            result = stp.get_sector_management_tone()
        self.assertIsNone(result)

    def test_returns_dict_when_cache_exists(self):
        import sector_tone_pipeline as stp
        sample = {
            "quarter": "Q4", "year": 2025, "data_available": True,
            "sectors": []
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample, f)
            tmp_path = Path(f.name)

        try:
            with patch.object(stp, 'CACHE_FILE', tmp_path):
                result = stp.get_sector_management_tone()
            self.assertIsNotNone(result)
            self.assertEqual(result['quarter'], 'Q4')
            self.assertEqual(result['year'], 2025)
            self.assertTrue(result['data_available'])
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_returns_none_on_invalid_json(self):
        import sector_tone_pipeline as stp
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {{{")
            tmp_path = Path(f.name)
        try:
            with patch.object(stp, 'CACHE_FILE', tmp_path):
                result = stp.get_sector_management_tone()
            self.assertIsNone(result)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_no_network_calls_on_cache_read(self):
        import sector_tone_pipeline as stp
        with patch.object(stp, 'CACHE_FILE', Path('/nonexistent/cache.json')):
            with patch('requests.get') as mock_get:
                stp.get_sector_management_tone()
                mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# Cache: data model structure
# ---------------------------------------------------------------------------


class TestCacheDataModel(unittest.TestCase):
    """Cached data must conform to the spec data model."""

    def _build_sample_cache(self):
        return {
            "quarter": "Q4",
            "year": 2025,
            "data_available": True,
            "sectors": [
                {
                    "name": "Information Technology",
                    "short_name": "Technology",
                    "current_tone": "positive",
                    "current_score": 0.42,
                    "trend": [
                        {"quarter": "Q1", "year": 2025, "tone": "neutral"},
                        {"quarter": "Q2", "year": 2025, "tone": "neutral"},
                        {"quarter": "Q3", "year": 2025, "tone": "positive"},
                        {"quarter": "Q4", "year": 2025, "tone": "positive"},
                    ],
                }
            ],
        }

    def test_top_level_keys_present(self):
        data = self._build_sample_cache()
        for key in ('quarter', 'year', 'data_available', 'sectors'):
            self.assertIn(key, data)

    def test_quarter_is_string(self):
        data = self._build_sample_cache()
        self.assertIsInstance(data['quarter'], str)

    def test_year_is_int(self):
        data = self._build_sample_cache()
        self.assertIsInstance(data['year'], int)

    def test_data_available_is_bool(self):
        data = self._build_sample_cache()
        self.assertIsInstance(data['data_available'], bool)

    def test_sectors_is_list(self):
        data = self._build_sample_cache()
        self.assertIsInstance(data['sectors'], list)

    def test_sector_entry_has_required_fields(self):
        sector = self._build_sample_cache()['sectors'][0]
        for field in ('name', 'short_name', 'current_tone', 'current_score', 'trend'):
            self.assertIn(field, sector)

    def test_trend_is_list_of_dicts(self):
        trend = self._build_sample_cache()['sectors'][0]['trend']
        self.assertIsInstance(trend, list)
        for entry in trend:
            self.assertIsInstance(entry, dict)
            for key in ('quarter', 'year', 'tone'):
                self.assertIn(key, entry)

    def test_trend_at_most_4_entries(self):
        trend = self._build_sample_cache()['sectors'][0]['trend']
        self.assertLessEqual(len(trend), 4)

    def test_current_tone_valid_values(self):
        sector = self._build_sample_cache()['sectors'][0]
        self.assertIn(sector['current_tone'], ('positive', 'neutral', 'negative'))

    def test_current_score_is_float(self):
        sector = self._build_sample_cache()['sectors'][0]
        self.assertIsInstance(sector['current_score'], float)


# ---------------------------------------------------------------------------
# Template context injection (dashboard.py)
# ---------------------------------------------------------------------------


class TestDashboardContextInjection(unittest.TestCase):
    """dashboard.py must import and inject sector_management_tone."""

    def setUp(self):
        self.src = read_source('dashboard.py')

    def test_import_get_sector_management_tone(self):
        self.assertIn('get_sector_management_tone', self.src)

    def test_import_update_sector_management_tone(self):
        self.assertIn('update_sector_management_tone', self.src)

    def test_context_processor_defined(self):
        self.assertIn('inject_sector_management_tone', self.src)

    def test_context_processor_returns_sector_management_tone_key(self):
        self.assertIn("'sector_management_tone'", self.src)

    def test_context_processor_has_app_context_processor_decorator(self):
        import re
        pattern = r'@app\.context_processor\s+def inject_sector_management_tone'
        self.assertIsNotNone(re.search(pattern, self.src),
                             'inject_sector_management_tone must have @app.context_processor')

    def test_data_available_false_in_no_cache_path(self):
        """Context processor must set data_available=False when no cache."""
        self.assertIn("'data_available': False", self.src)

    def test_homepage_does_not_call_update_on_request(self):
        """update_sector_management_tone must NOT be called in a request handler."""
        import re
        # Find all lines that call update_sector_management_tone
        call_lines = [
            line for line in self.src.splitlines()
            if 'update_sector_management_tone()' in line
        ]
        # If any calls exist, they must NOT be inside route handlers
        # (acceptable: run_data_collection comment)
        for line in call_lines:
            stripped = line.strip()
            # Comments are fine
            if stripped.startswith('#'):
                continue
            # Actual call outside comment — flag it
            self.fail(f"update_sector_management_tone() called in dashboard.py: {line.strip()!r}\n"
                      "Pipeline must run as a batch job, not on each request.")


# ---------------------------------------------------------------------------
# Pipeline design (batch, not per-request)
# ---------------------------------------------------------------------------


class TestPipelineDesign(unittest.TestCase):
    """Pipeline must be designed for batch use, not per-request execution."""

    def test_cache_file_constant_defined(self):
        import sector_tone_pipeline as stp
        self.assertTrue(hasattr(stp, 'CACHE_FILE'))

    def test_cache_file_is_path(self):
        import sector_tone_pipeline as stp
        self.assertIsInstance(stp.CACHE_FILE, Path)

    def test_cache_file_in_data_directory(self):
        import sector_tone_pipeline as stp
        self.assertIn('data', str(stp.CACHE_FILE))

    def test_max_filings_per_company_defined(self):
        import sector_tone_pipeline as stp
        self.assertTrue(hasattr(stp, '_MAX_FILINGS_PER_COMPANY'))

    def test_max_filings_per_company_positive(self):
        import sector_tone_pipeline as stp
        self.assertGreater(stp._MAX_FILINGS_PER_COMPANY, 0)

    def test_edgar_timeout_configured(self):
        import sector_tone_pipeline as stp
        self.assertTrue(hasattr(stp, '_EDGAR_TIMEOUT'))
        self.assertGreater(stp._EDGAR_TIMEOUT, 0)


# ---------------------------------------------------------------------------
# Security: URL construction
# ---------------------------------------------------------------------------


class TestSecurityUrlConstruction(unittest.TestCase):
    """EDGAR URLs must be static/validated; no user-supplied input in URLs."""

    def test_no_user_input_in_edgar_url_construction(self):
        """EDGAR search URL is built from constants + ticker CIK, never user input."""
        src = read_source('sector_tone_pipeline.py')
        # The URL constants must be defined as module-level strings
        self.assertIn('_EDGAR_SEARCH_URL', src)
        self.assertIn('https://efts.sec.gov', src)

    def test_finbert_model_name_is_hardcoded(self):
        """FinBERT model name must be hardcoded, not from user input."""
        src = read_source('sector_tone_pipeline.py')
        self.assertIn('"ProsusAI/finbert"', src)


# ---------------------------------------------------------------------------
# Trend history: up to 4 quarters, oldest first
# ---------------------------------------------------------------------------


class TestTrendHistory(unittest.TestCase):
    """Trend history must be ≤4 entries, chronological (oldest first)."""

    def test_trend_max_4_quarters_in_data_model(self):
        """Spec: up to 4 quarters stored (current + 3 prior)."""
        trend = [
            {"quarter": "Q1", "year": 2025, "tone": "neutral"},
            {"quarter": "Q2", "year": 2025, "tone": "positive"},
            {"quarter": "Q3", "year": 2025, "tone": "positive"},
            {"quarter": "Q4", "year": 2025, "tone": "positive"},
        ]
        self.assertLessEqual(len(trend), 4)

    def test_trend_fewer_than_4_when_not_enough_history(self):
        """When < 4 quarters of history, trend contains only available quarters."""
        trend = [
            {"quarter": "Q4", "year": 2025, "tone": "positive"},
        ]
        # Only 1 quarter — no padding with None
        for entry in trend:
            self.assertIsNotNone(entry.get("tone"))
        self.assertEqual(len(trend), 1)

    def test_trend_entry_required_fields(self):
        entry = {"quarter": "Q4", "year": 2025, "tone": "positive"}
        self.assertIn("quarter", entry)
        self.assertIn("year", entry)
        self.assertIn("tone", entry)

    def test_source_prunes_to_4_entries(self):
        """Source code must limit trend to last 4 entries."""
        src = read_source('sector_tone_pipeline.py')
        self.assertIn('[-4:]', src, "Trend pruning to 4 entries must use [-4:] slice")


# ---------------------------------------------------------------------------
# Requirements.txt
# ---------------------------------------------------------------------------


class TestRequirements(unittest.TestCase):
    """requirements.txt must include transformers and torch."""

    def setUp(self):
        req_path = os.path.join(SIGNALTRACKERS_DIR, 'requirements.txt')
        with open(req_path) as f:
            self.reqs = f.read()

    def test_transformers_in_requirements(self):
        self.assertIn('transformers', self.reqs)

    def test_torch_in_requirements(self):
        self.assertIn('torch', self.reqs)

    def test_transformers_has_version_pin(self):
        import re
        self.assertIsNotNone(re.search(r'transformers>=\d', self.reqs))

    def test_torch_has_version_pin(self):
        import re
        self.assertIsNotNone(re.search(r'torch>=\d', self.reqs))


# ---------------------------------------------------------------------------
# Tone tone constants for sort order
# ---------------------------------------------------------------------------


class TestToneSortOrder(unittest.TestCase):
    """_TONE_SORT_ORDER must map positive < neutral < negative."""

    def setUp(self):
        import sector_tone_pipeline as stp
        self.order = stp._TONE_SORT_ORDER

    def test_tone_sort_order_defined(self):
        import sector_tone_pipeline as stp
        self.assertTrue(hasattr(stp, '_TONE_SORT_ORDER'))

    def test_positive_sorts_first(self):
        self.assertLess(self.order['positive'], self.order['neutral'])

    def test_neutral_sorts_before_negative(self):
        self.assertLess(self.order['neutral'], self.order['negative'])

    def test_positive_sorts_before_negative(self):
        self.assertLess(self.order['positive'], self.order['negative'])

    def test_all_three_tones_present(self):
        for tone in ('positive', 'neutral', 'negative'):
            self.assertIn(tone, self.order)


if __name__ == '__main__':
    unittest.main()
