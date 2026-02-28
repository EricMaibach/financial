"""
Static and unit tests for US-123.3:
Quarterly scheduling — auto-seed on startup + cron trigger for sector tone pipeline.

Tests verify:
- sector_tone_jobs.py file and functions exist
- run_sector_tone_pipeline() calls update_sector_management_tone() and catches exceptions
- run_sector_tone_pipeline_wrapper() uses Flask app context
- scheduler.py registers sector_tone_quarterly cron job with correct trigger params
- _is_sector_tone_cache_empty() returns correct values for all cache states
- _check_and_seed_sector_tone() submits/skips seed job correctly
- Seed job uses date trigger with minimum delay (non-blocking)
- All log messages are present in source
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIGNALTRACKERS_DIR = os.path.join(REPO_ROOT, 'signaltrackers')
sys.path.insert(0, SIGNALTRACKERS_DIR)
sys.path.insert(0, os.path.join(SIGNALTRACKERS_DIR, 'jobs'))


def read_source(filename):
    path = os.path.join(SIGNALTRACKERS_DIR, filename)
    with open(path, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# sector_tone_jobs.py — file existence
# ---------------------------------------------------------------------------

class TestSectorToneJobsFileExists(unittest.TestCase):
    """jobs/sector_tone_jobs.py must exist."""

    def test_file_exists(self):
        path = os.path.join(SIGNALTRACKERS_DIR, 'jobs', 'sector_tone_jobs.py')
        self.assertTrue(os.path.isfile(path), 'jobs/sector_tone_jobs.py not found')


# ---------------------------------------------------------------------------
# sector_tone_jobs.py — module imports and exports
# ---------------------------------------------------------------------------

class TestSectorToneJobsImports(unittest.TestCase):
    """sector_tone_jobs.py must be importable and export required functions."""

    def test_module_importable(self):
        import sector_tone_jobs
        self.assertIsNotNone(sector_tone_jobs)

    def test_run_sector_tone_pipeline_exists(self):
        from sector_tone_jobs import run_sector_tone_pipeline
        self.assertTrue(callable(run_sector_tone_pipeline))

    def test_run_sector_tone_pipeline_wrapper_exists(self):
        from sector_tone_jobs import run_sector_tone_pipeline_wrapper
        self.assertTrue(callable(run_sector_tone_pipeline_wrapper))

    def test_no_transformers_at_module_level(self):
        """transformers must not be imported at module level (lazy import)."""
        src = read_source('jobs/sector_tone_jobs.py')
        lines = src.splitlines()
        module_level = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('class '):
                break
            module_level.append(stripped)
        self.assertNotIn('transformers', '\n'.join(module_level))

    def test_no_dashboard_at_module_level(self):
        """dashboard must not be imported at module level (circular import risk)."""
        src = read_source('jobs/sector_tone_jobs.py')
        lines = src.splitlines()
        module_level = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('class '):
                break
            module_level.append(stripped)
        top = '\n'.join(module_level)
        self.assertNotIn('from dashboard', top)
        self.assertNotIn('import dashboard', top)

    def test_no_torch_at_module_level(self):
        """torch must not be imported at module level."""
        src = read_source('jobs/sector_tone_jobs.py')
        lines = src.splitlines()
        module_level = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('class '):
                break
            module_level.append(stripped)
        self.assertNotIn('import torch', '\n'.join(module_level))


# ---------------------------------------------------------------------------
# sector_tone_jobs.py — source checks
# ---------------------------------------------------------------------------

class TestSectorToneJobsSourceChecks(unittest.TestCase):
    """Source-level structural checks for jobs/sector_tone_jobs.py."""

    def setUp(self):
        self.src = read_source('jobs/sector_tone_jobs.py')

    def test_lazy_import_update_function(self):
        """update_sector_management_tone must be imported inside a function."""
        self.assertIn('from sector_tone_pipeline import update_sector_management_tone', self.src)

    def test_dashboard_import_inside_wrapper(self):
        """dashboard must be imported inside the wrapper function."""
        self.assertIn('from dashboard import app', self.src)

    def test_import_error_is_caught(self):
        """ImportError must be explicitly caught."""
        self.assertIn('ImportError', self.src)

    def test_general_exception_is_caught(self):
        """General Exception must be caught to prevent scheduler crash."""
        self.assertIn('except Exception', self.src)

    def test_pipeline_start_log_message(self):
        """A log message must be emitted at pipeline start."""
        self.assertIn('Sector tone pipeline: starting', self.src)

    def test_app_context_used(self):
        """Wrapper must use app.app_context()."""
        self.assertIn('app.app_context()', self.src)

    def test_no_requests_at_module_level(self):
        """requests must not be imported at module top level."""
        lines = self.src.splitlines()
        module_level = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('class '):
                break
            module_level.append(stripped)
        self.assertNotIn('import requests', '\n'.join(module_level))

    def test_exc_info_true_for_general_exception(self):
        """General exception handler must log exc_info for debugging."""
        self.assertIn('exc_info=True', self.src)


# ---------------------------------------------------------------------------
# run_sector_tone_pipeline — runtime behaviour
# ---------------------------------------------------------------------------

class TestRunSectorTonePipelineCallsUpdate(unittest.TestCase):
    """run_sector_tone_pipeline() must delegate to update_sector_management_tone()."""

    def test_calls_update_sector_management_tone(self):
        from sector_tone_jobs import run_sector_tone_pipeline
        import sector_tone_pipeline as stp
        with patch.object(stp, 'update_sector_management_tone') as mock_update:
            run_sector_tone_pipeline()
        mock_update.assert_called_once()

    def test_catches_import_error_does_not_propagate(self):
        """ImportError from missing transformers must not propagate."""
        from sector_tone_jobs import run_sector_tone_pipeline
        import sector_tone_pipeline as stp
        original = stp.update_sector_management_tone

        def raise_import_error():
            raise ImportError("transformers not installed")

        stp.update_sector_management_tone = raise_import_error
        try:
            run_sector_tone_pipeline()  # must not raise
        except ImportError:
            self.fail("ImportError must be caught inside run_sector_tone_pipeline")
        finally:
            stp.update_sector_management_tone = original

    def test_catches_runtime_error_does_not_propagate(self):
        """RuntimeError from pipeline failure must not propagate."""
        from sector_tone_jobs import run_sector_tone_pipeline
        import sector_tone_pipeline as stp
        original = stp.update_sector_management_tone
        stp.update_sector_management_tone = MagicMock(side_effect=RuntimeError("boom"))
        try:
            run_sector_tone_pipeline()  # must not raise
        except RuntimeError:
            self.fail("RuntimeError must be caught inside run_sector_tone_pipeline")
        finally:
            stp.update_sector_management_tone = original

    def test_catches_connection_error_does_not_propagate(self):
        """ConnectionError (EDGAR down) must not propagate."""
        from sector_tone_jobs import run_sector_tone_pipeline
        import sector_tone_pipeline as stp
        original = stp.update_sector_management_tone
        stp.update_sector_management_tone = MagicMock(
            side_effect=ConnectionError("EDGAR unreachable")
        )
        try:
            run_sector_tone_pipeline()
        except ConnectionError:
            self.fail("ConnectionError must be caught inside run_sector_tone_pipeline")
        finally:
            stp.update_sector_management_tone = original


# ---------------------------------------------------------------------------
# scheduler.py — helper functions exist
# ---------------------------------------------------------------------------

class TestSchedulerHelpersExist(unittest.TestCase):
    """scheduler.py must expose _is_sector_tone_cache_empty and _check_and_seed_sector_tone."""

    def test_is_sector_tone_cache_empty_exists(self):
        import scheduler as sched_module
        self.assertTrue(
            hasattr(sched_module, '_is_sector_tone_cache_empty'),
            '_is_sector_tone_cache_empty not found in scheduler module'
        )

    def test_is_sector_tone_cache_empty_callable(self):
        import scheduler as sched_module
        self.assertTrue(callable(sched_module._is_sector_tone_cache_empty))

    def test_check_and_seed_sector_tone_exists(self):
        import scheduler as sched_module
        self.assertTrue(
            hasattr(sched_module, '_check_and_seed_sector_tone'),
            '_check_and_seed_sector_tone not found in scheduler module'
        )

    def test_check_and_seed_sector_tone_callable(self):
        import scheduler as sched_module
        self.assertTrue(callable(sched_module._check_and_seed_sector_tone))


# ---------------------------------------------------------------------------
# _is_sector_tone_cache_empty — cache state logic
# ---------------------------------------------------------------------------

class TestIsSectorToneCacheEmpty(unittest.TestCase):
    """_is_sector_tone_cache_empty() must identify all empty/absent cache states."""

    def setUp(self):
        import scheduler as sched_module
        self.fn = sched_module._is_sector_tone_cache_empty

    def _patch_get_cache(self, return_value=None, side_effect=None):
        import sector_tone_pipeline as stp
        if side_effect is not None:
            return patch.object(stp, 'get_sector_management_tone', side_effect=side_effect)
        return patch.object(stp, 'get_sector_management_tone', return_value=return_value)

    def test_returns_true_when_cache_is_none(self):
        """Cache file absent (returns None) → True."""
        with self._patch_get_cache(return_value=None):
            self.assertTrue(self.fn())

    def test_returns_true_when_cache_is_empty_dict(self):
        """Empty JSON object {} has no data_available → True."""
        with self._patch_get_cache(return_value={}):
            self.assertTrue(self.fn())

    def test_returns_true_when_data_available_false(self):
        """data_available=False → True."""
        with self._patch_get_cache(return_value={'data_available': False, 'sectors': []}):
            self.assertTrue(self.fn())

    def test_returns_true_when_data_available_missing(self):
        """data_available key absent (falsy) → True."""
        with self._patch_get_cache(return_value={'sectors': [{'name': 'Technology'}]}):
            self.assertTrue(self.fn())

    def test_returns_true_when_sectors_list_empty(self):
        """data_available=True but no sectors → True."""
        with self._patch_get_cache(return_value={'data_available': True, 'sectors': []}):
            self.assertTrue(self.fn())

    def test_returns_true_when_sectors_key_missing(self):
        """data_available=True but sectors key absent → True."""
        with self._patch_get_cache(return_value={'data_available': True}):
            self.assertTrue(self.fn())

    def test_returns_false_when_cache_has_valid_data(self):
        """Valid cache with data_available=True and non-empty sectors → False."""
        valid = {
            'data_available': True,
            'quarter': 'Q4',
            'year': 2025,
            'sectors': [{'name': 'Technology', 'current_tone': 'positive'}],
        }
        with self._patch_get_cache(return_value=valid):
            self.assertFalse(self.fn())

    def test_returns_false_when_cache_has_multiple_sectors(self):
        """Multiple sectors, valid cache → False."""
        valid = {
            'data_available': True,
            'sectors': [
                {'name': 'Technology'},
                {'name': 'Financials'},
                {'name': 'Energy'},
            ],
        }
        with self._patch_get_cache(return_value=valid):
            self.assertFalse(self.fn())

    def test_returns_true_on_exception(self):
        """If get_sector_management_tone raises, defaults to True (safe)."""
        with self._patch_get_cache(side_effect=OSError("disk error")):
            self.assertTrue(self.fn())

    def test_returns_true_on_value_error(self):
        """ValueError from corrupt cache → True."""
        with self._patch_get_cache(side_effect=ValueError("bad json")):
            self.assertTrue(self.fn())


# ---------------------------------------------------------------------------
# _check_and_seed_sector_tone — seed job submission behaviour
# ---------------------------------------------------------------------------

class TestCheckAndSeedSectorTone(unittest.TestCase):
    """_check_and_seed_sector_tone() must submit or skip the seed job correctly."""

    def setUp(self):
        import scheduler as sched_module
        self.sched_module = sched_module
        self.mock_scheduler = MagicMock()
        self.original_scheduler = sched_module.scheduler
        sched_module.scheduler = self.mock_scheduler

    def tearDown(self):
        self.sched_module.scheduler = self.original_scheduler

    def _call_seed(self, cache_empty):
        mock_wrapper = MagicMock()
        with patch.object(
            self.sched_module, '_is_sector_tone_cache_empty', return_value=cache_empty
        ):
            self.sched_module._check_and_seed_sector_tone(mock_wrapper)
        return mock_wrapper

    def test_submits_seed_job_when_cache_empty(self):
        """Cache empty → add_job called."""
        self._call_seed(cache_empty=True)
        self.mock_scheduler.add_job.assert_called_once()

    def test_does_not_submit_seed_job_when_cache_populated(self):
        """Cache populated → add_job NOT called."""
        self._call_seed(cache_empty=False)
        self.mock_scheduler.add_job.assert_not_called()

    def test_seed_job_id_is_correct(self):
        """Seed job id must be 'sector_tone_seed'."""
        self._call_seed(cache_empty=True)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        self.assertEqual(call_kwargs['id'], 'sector_tone_seed')

    def test_seed_job_uses_date_trigger(self):
        """Seed job must use 'date' trigger for one-time deferred execution."""
        self._call_seed(cache_empty=True)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        self.assertEqual(call_kwargs['trigger'], 'date')

    def test_seed_job_trigger_is_not_cron(self):
        """Seed job must NOT use 'cron' trigger."""
        self._call_seed(cache_empty=True)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        self.assertNotEqual(call_kwargs['trigger'], 'cron')

    def test_seed_job_trigger_is_not_interval(self):
        """Seed job must NOT use 'interval' trigger."""
        self._call_seed(cache_empty=True)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        self.assertNotEqual(call_kwargs['trigger'], 'interval')

    def test_seed_job_run_date_is_in_future(self):
        """Seed job run_date must be in the future (not immediate)."""
        before = datetime.utcnow()
        self._call_seed(cache_empty=True)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        run_date = call_kwargs['run_date']
        self.assertGreater(run_date, before)

    def test_seed_job_has_minimum_5_second_delay(self):
        """Seed job run_date must be at least 5 seconds after call time."""
        before = datetime.utcnow()
        self._call_seed(cache_empty=True)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        run_date = call_kwargs['run_date']
        self.assertGreaterEqual(
            run_date, before + timedelta(seconds=4),
            "Seed job must start at least ~5 seconds after app startup"
        )

    def test_seed_job_has_replace_existing_true(self):
        """Seed job replace_existing=True prevents duplicate on double-init."""
        self._call_seed(cache_empty=True)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        self.assertTrue(call_kwargs.get('replace_existing'))

    def test_seed_job_passes_wrapper_func_as_func(self):
        """Seed job must be registered with the provided wrapper function."""
        mock_wrapper = MagicMock()
        with patch.object(
            self.sched_module, '_is_sector_tone_cache_empty', return_value=True
        ):
            self.sched_module._check_and_seed_sector_tone(mock_wrapper)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        self.assertEqual(call_kwargs['func'], mock_wrapper)

    def test_wrapper_not_called_synchronously(self):
        """Wrapper function must NOT be called directly during seed check."""
        mock_wrapper = MagicMock()
        with patch.object(
            self.sched_module, '_is_sector_tone_cache_empty', return_value=True
        ):
            self.sched_module._check_and_seed_sector_tone(mock_wrapper)
        mock_wrapper.assert_not_called()


# ---------------------------------------------------------------------------
# scheduler.py — quarterly cron job registration
# ---------------------------------------------------------------------------

class TestQuarterlyJobRegistration(unittest.TestCase):
    """register_jobs() must register sector_tone_quarterly with correct cron params."""

    def setUp(self):
        import scheduler as sched_module
        self.sched_module = sched_module
        self.mock_scheduler = MagicMock()
        self.original_scheduler = sched_module.scheduler
        sched_module.scheduler = self.mock_scheduler

    def tearDown(self):
        self.sched_module.scheduler = self.original_scheduler

    def _call_register_jobs(self):
        """Call register_jobs() with cache reporting populated (skip seed job)."""
        import sector_tone_pipeline as stp
        valid_cache = {
            'data_available': True,
            'sectors': [{'name': 'Technology', 'current_tone': 'positive'}],
        }
        with patch.object(stp, 'get_sector_management_tone', return_value=valid_cache):
            self.sched_module.register_jobs(None)

    def _get_job_call(self, job_id):
        """Return add_job kwargs for the given job id, or None if not found."""
        for c in self.mock_scheduler.add_job.call_args_list:
            kwargs = c[1]
            if kwargs.get('id') == job_id:
                return kwargs
        return None

    def test_quarterly_job_is_registered(self):
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertIsNotNone(job, "sector_tone_quarterly job was not registered")

    def test_quarterly_job_trigger_is_cron(self):
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertEqual(job['trigger'], 'cron')

    def test_quarterly_job_month_targets_all_four_quarters(self):
        """Month parameter must be '1,4,7,10'."""
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertEqual(str(job['month']), '1,4,7,10')

    def test_quarterly_job_day_is_first(self):
        """Job must fire on the 1st of the month."""
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertEqual(job['day'], 1)

    def test_quarterly_job_hour_is_2(self):
        """Job must fire at hour 2 (02:00 UTC)."""
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertEqual(job['hour'], 2)

    def test_quarterly_job_minute_is_0(self):
        """Job must fire at minute 0."""
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertEqual(job['minute'], 0)

    def test_quarterly_job_replace_existing_true(self):
        """replace_existing=True prevents duplicate registration on restart."""
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertTrue(job.get('replace_existing'))

    def test_quarterly_job_id_exact(self):
        """Job id must be exactly 'sector_tone_quarterly'."""
        self._call_register_jobs()
        job = self._get_job_call('sector_tone_quarterly')
        self.assertEqual(job['id'], 'sector_tone_quarterly')

    def test_existing_jobs_still_registered(self):
        """Existing check_alerts and daily_briefings jobs must still be registered."""
        self._call_register_jobs()
        alerts_job = self._get_job_call('check_alerts')
        briefings_job = self._get_job_call('daily_briefings')
        self.assertIsNotNone(alerts_job, "check_alerts job must still be registered")
        self.assertIsNotNone(briefings_job, "daily_briefings job must still be registered")

    def test_seed_job_not_submitted_when_cache_populated(self):
        """When cache is populated, seed job must NOT be registered."""
        self._call_register_jobs()
        seed_job = self._get_job_call('sector_tone_seed')
        self.assertIsNone(seed_job, "Seed job must NOT be registered when cache is populated")

    def test_seed_job_submitted_when_cache_empty(self):
        """When cache is absent, seed job must be registered."""
        import sector_tone_pipeline as stp
        with patch.object(stp, 'get_sector_management_tone', return_value=None):
            self.sched_module.register_jobs(None)
        seed_job = self._get_job_call('sector_tone_seed')
        self.assertIsNotNone(seed_job, "Seed job must be registered when cache is absent")


# ---------------------------------------------------------------------------
# scheduler.py — source-level checks
# ---------------------------------------------------------------------------

class TestSchedulerSourceChecks(unittest.TestCase):
    """Source-level pattern checks for scheduler.py."""

    def setUp(self):
        self.src = read_source('scheduler.py')

    def test_imports_from_sector_tone_jobs(self):
        self.assertIn('sector_tone_jobs', self.src)

    def test_quarterly_job_id_in_source(self):
        self.assertIn("'sector_tone_quarterly'", self.src)

    def test_cron_trigger_in_source(self):
        self.assertIn("trigger='cron'", self.src)

    def test_date_trigger_in_source(self):
        self.assertIn("trigger='date'", self.src)

    def test_month_quarters_string_in_source(self):
        self.assertIn("'1,4,7,10'", self.src)

    def test_seed_job_id_in_source(self):
        self.assertIn("'sector_tone_seed'", self.src)

    def test_timedelta_5_seconds_delay_in_source(self):
        self.assertIn('timedelta(seconds=5)', self.src)

    def test_replace_existing_true_present(self):
        self.assertIn('replace_existing=True', self.src)

    def test_is_cache_empty_helper_present(self):
        self.assertIn('_is_sector_tone_cache_empty', self.src)

    def test_check_and_seed_helper_present(self):
        self.assertIn('_check_and_seed_sector_tone', self.src)

    def test_log_cache_empty_message_present(self):
        self.assertIn('Sector tone cache empty', self.src)

    def test_log_cache_populated_message_present(self):
        self.assertIn('Sector tone cache populated', self.src)

    def test_log_quarterly_registered_present(self):
        self.assertIn('sector_tone_quarterly', self.src)

    def test_coalesce_in_job_defaults(self):
        """Job defaults must include coalesce=True (already present from init)."""
        self.assertIn("'coalesce': True", self.src)

    def test_max_instances_in_job_defaults(self):
        """Job defaults must include max_instances=1."""
        self.assertIn("'max_instances': 1", self.src)

    def test_datetime_imported_for_seed_delay(self):
        """datetime must be imported to compute seed job run_date."""
        self.assertIn('from datetime import', self.src)

    def test_day_one_in_source(self):
        """day=1 must appear for quarterly job."""
        self.assertIn('day=1', self.src)

    def test_hour_two_in_source(self):
        """hour=2 must appear for quarterly job."""
        self.assertIn('hour=2', self.src)

    def test_minute_zero_in_source(self):
        """minute=0 must appear for quarterly job."""
        self.assertIn('minute=0', self.src)


# ---------------------------------------------------------------------------
# Non-blocking behaviour
# ---------------------------------------------------------------------------

class TestNonBlockingBehaviour(unittest.TestCase):
    """Startup seed must be deferred via date trigger, not run synchronously."""

    def setUp(self):
        import scheduler as sched_module
        self.sched_module = sched_module
        self.mock_scheduler = MagicMock()
        self.original_scheduler = sched_module.scheduler
        sched_module.scheduler = self.mock_scheduler

    def tearDown(self):
        self.sched_module.scheduler = self.original_scheduler

    def test_seed_trigger_is_date_not_cron_not_interval(self):
        """Seed job must use 'date' trigger (one-time deferred, not recurring)."""
        mock_wrapper = MagicMock()
        with patch.object(self.sched_module, '_is_sector_tone_cache_empty', return_value=True):
            self.sched_module._check_and_seed_sector_tone(mock_wrapper)
        call_kwargs = self.mock_scheduler.add_job.call_args[1]
        self.assertEqual(call_kwargs['trigger'], 'date')
        self.assertNotIn(call_kwargs['trigger'], ('interval', 'cron'))

    def test_wrapper_not_called_synchronously_in_seed_check(self):
        """Seed check must NOT directly invoke the pipeline wrapper."""
        mock_wrapper = MagicMock()
        with patch.object(self.sched_module, '_is_sector_tone_cache_empty', return_value=True):
            self.sched_module._check_and_seed_sector_tone(mock_wrapper)
        mock_wrapper.assert_not_called()

    def test_register_jobs_does_not_call_update_directly(self):
        """register_jobs must not call update_sector_management_tone directly."""
        import sector_tone_pipeline as stp
        with patch.object(stp, 'get_sector_management_tone', return_value=None):
            with patch.object(stp, 'update_sector_management_tone') as mock_update:
                self.sched_module.register_jobs(None)
        mock_update.assert_not_called()


if __name__ == '__main__':
    unittest.main()
