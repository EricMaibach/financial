from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
import logging
import os

logger = logging.getLogger(__name__)

# Scheduler instance (singleton)
scheduler = None

def init_scheduler(app):
    """Initialize APScheduler with Flask app context"""
    global scheduler

    if scheduler is not None:
        return scheduler

    # Executor configuration
    executors = {
        'default': ThreadPoolExecutor(max_workers=3)
    }

    # Job defaults
    job_defaults = {
        'coalesce': True,  # Combine multiple missed executions into one
        'max_instances': 1,  # Prevent concurrent execution of same job
        'misfire_grace_time': 300  # 5 minutes grace period
    }

    # Use in-memory job store (jobs won't persist across restarts, but that's okay
    # since we register them on startup anyway)
    scheduler = BackgroundScheduler(
        executors=executors,
        job_defaults=job_defaults,
        timezone='UTC'
    )

    # Register jobs
    register_jobs(app)

    # Start scheduler
    scheduler.start()
    logger.info("APScheduler started successfully")

    return scheduler


def register_jobs(app):
    """Register all scheduled jobs"""
    # Import job wrapper that will handle app context
    from jobs.alert_jobs import check_alert_thresholds_wrapper
    from jobs.email_jobs import send_daily_briefings_wrapper

    # Alert checking - every 15 minutes
    scheduler.add_job(
        func=check_alert_thresholds_wrapper,
        trigger='interval',
        minutes=15,
        id='check_alerts',
        name='Check alert thresholds',
        replace_existing=True
    )
    logger.info("Registered job: check_alerts (every 15 minutes)")

    # Daily briefings - 7 AM ET (12:00 UTC in winter, 11:00 UTC in summer)
    # Note: Will need to handle user-specific timezones in the job itself
    scheduler.add_job(
        func=send_daily_briefings_wrapper,
        trigger='cron',
        hour=12,  # 12 UTC = 7 AM ET (winter)
        minute=0,
        id='daily_briefings',
        name='Send daily briefing emails',
        replace_existing=True
    )
    logger.info("Registered job: daily_briefings (daily at 12:00 UTC)")


def shutdown_scheduler():
    """Gracefully shutdown scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shut down successfully")
