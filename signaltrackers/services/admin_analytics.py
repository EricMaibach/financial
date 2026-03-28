"""
Admin Analytics Service

Aggregates AI usage data for the admin dashboard.
All queries use DB-level aggregation (GROUP BY) to avoid N+1 issues.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, case, and_

from extensions import db
from models.ai_usage import AIUsageRecord
from models.user import User


def get_today_summary():
    """Get today's usage summary with registered vs anonymous breakdown.

    Returns dict with total_calls, registered_calls, input_tokens,
    output_tokens, and estimated_cost for today (UTC).
    """
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    row = db.session.query(
        func.count(AIUsageRecord.id).label('total_calls'),
        func.coalesce(func.sum(AIUsageRecord.input_tokens), 0).label('input_tokens'),
        func.coalesce(func.sum(AIUsageRecord.output_tokens), 0).label('output_tokens'),
        func.coalesce(func.sum(AIUsageRecord.estimated_cost), 0).label('estimated_cost'),
    ).filter(
        AIUsageRecord.timestamp >= today_start
    ).one()

    return {
        'total_calls': row.total_calls,
        'input_tokens': int(row.input_tokens),
        'output_tokens': int(row.output_tokens),
        'estimated_cost': float(row.estimated_cost),
    }


def get_daily_trend(days=30):
    """Get daily aggregated usage for the past N days.

    Returns list of dicts sorted oldest-first, with zero-fill for days
    with no usage.
    """
    cutoff = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=days - 1)

    date_label = func.date(AIUsageRecord.timestamp)

    rows = db.session.query(
        date_label.label('day'),
        func.count(AIUsageRecord.id).label('calls'),
        func.coalesce(func.sum(AIUsageRecord.input_tokens), 0).label('input_tokens'),
        func.coalesce(func.sum(AIUsageRecord.output_tokens), 0).label('output_tokens'),
        func.coalesce(func.sum(AIUsageRecord.estimated_cost), 0).label('cost'),
    ).filter(
        AIUsageRecord.timestamp >= cutoff
    ).group_by(date_label).all()

    # Build a lookup from query results
    data_by_day = {}
    for r in rows:
        day_str = str(r.day)
        data_by_day[day_str] = {
            'date': day_str,
            'calls': r.calls,
            'input_tokens': int(r.input_tokens),
            'output_tokens': int(r.output_tokens),
            'cost': float(r.cost),
        }

    # Zero-fill all days in the range
    result = []
    today = datetime.now(timezone.utc).date()
    for i in range(days):
        day = (today - timedelta(days=days - 1 - i))
        day_str = day.isoformat()
        if day_str in data_by_day:
            result.append(data_by_day[day_str])
        else:
            result.append({
                'date': day_str,
                'calls': 0,
                'input_tokens': 0,
                'output_tokens': 0,
                'cost': 0.0,
            })

    return result


def get_top_users(limit=10):
    """Get top users by call count and token usage for the past 30 days.

    Returns list of dicts with username, call_count, total_tokens, and cost.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    rows = db.session.query(
        User.username,
        func.count(AIUsageRecord.id).label('call_count'),
        func.coalesce(func.sum(AIUsageRecord.input_tokens), 0).label('input_tokens'),
        func.coalesce(func.sum(AIUsageRecord.output_tokens), 0).label('output_tokens'),
        func.coalesce(func.sum(AIUsageRecord.estimated_cost), 0).label('cost'),
    ).join(
        User, AIUsageRecord.user_id == User.id
    ).filter(
        AIUsageRecord.timestamp >= cutoff
    ).group_by(
        User.username
    ).order_by(
        func.count(AIUsageRecord.id).desc()
    ).limit(limit).all()

    return [
        {
            'username': r.username,
            'call_count': r.call_count,
            'input_tokens': int(r.input_tokens),
            'output_tokens': int(r.output_tokens),
            'total_tokens': int(r.input_tokens) + int(r.output_tokens),
            'cost': float(r.cost),
        }
        for r in rows
    ]


def get_anon_cap_status():
    """Get current global anonymous cap usage.

    Returns dict with used and limit.  Reads the in-memory counter from
    the rate-limiting module (only valid for today; resets at midnight UTC).
    """
    from services import rate_limiting as rl

    today = datetime.now(timezone.utc).date()

    with rl._global_lock:
        if rl._global_date == today:
            used = rl._global_count
        else:
            used = 0

    return {
        'used': used,
        'limit': rl._get_global_daily_limit(),
    }
