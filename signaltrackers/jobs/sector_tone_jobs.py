import logging

logger = logging.getLogger(__name__)


def run_sector_tone_pipeline():
    """
    Background job to run the SEC EDGAR + FinBERT sector tone pipeline.

    This is a quarterly batch job (~30–60 minutes). Results are stored in
    data/sector_tone_cache.json and served by the Flask context processor.

    Catches all exceptions so the scheduler remains healthy if the pipeline
    fails (e.g. EDGAR rate limits, transformers unavailable in test env).
    """
    logger.info("Sector tone pipeline: starting")
    try:
        # Lazy import — keeps module importable without transformers/torch
        from sector_tone_pipeline import update_sector_management_tone
        update_sector_management_tone()
        logger.info("Sector tone pipeline: completed successfully")
    except ImportError as exc:
        logger.error(
            "Sector tone pipeline: 'transformers' package not installed — %s", exc
        )
    except Exception as exc:
        logger.error("Sector tone pipeline: failed — %s", exc, exc_info=True)


def run_sector_tone_pipeline_wrapper():
    """Wrapper to run the sector tone pipeline job with Flask app context."""
    # Import here to avoid circular imports
    from dashboard import app

    with app.app_context():
        run_sector_tone_pipeline()
