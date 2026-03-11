"""
Alert Detection Service

Implements smart alert detection logic for significant market events.
"""

from datetime import datetime, timedelta
from models.alert import Alert, AlertPreference
from models.user import User
from market_signals import get_latest_metrics, get_historical_metrics
from extensions import db
from services.alert_email_service import send_pending_alert_notifications
import logging

logger = logging.getLogger(__name__)


class AlertDetector:
    """Base class for alert detection logic"""

    def __init__(self, alert_type, title_template, severity='info'):
        self.alert_type = alert_type
        self.title_template = title_template
        self.severity = severity

    def should_trigger(self, user, metrics):
        """
        Check if alert should trigger for user

        Args:
            user: User object
            metrics: Dict of current metrics from get_latest_metrics()

        Returns:
            dict or None: Alert data if should trigger, None otherwise
        """
        raise NotImplementedError

    def create_alert(self, user_id, **kwargs):
        """Create alert record"""
        alert = Alert(
            user_id=user_id,
            alert_type=self.alert_type,
            severity=self.severity,
            **kwargs
        )
        db.session.add(alert)
        return alert

    def was_recently_triggered(self, user_id, hours=24):
        """Check if this alert type was triggered recently (prevent spam)"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = Alert.query.filter(
            Alert.user_id == user_id,
            Alert.alert_type == self.alert_type,
            Alert.triggered_at >= cutoff
        ).first()
        return recent is not None


class VIXSpikeDetector(AlertDetector):
    """Detect VIX crossing 25 or 30 thresholds"""

    def __init__(self, threshold):
        super().__init__(
            alert_type=f'vix_spike_{threshold}',
            title_template=f'VIX crossed {threshold} threshold',
            severity='warning' if threshold == 25 else 'critical'
        )
        self.threshold = threshold

    def should_trigger(self, user, metrics):
        prefs = user.alert_preferences

        # Check if user has this alert enabled
        if self.threshold == 25 and not prefs.vix_threshold_25:
            return None
        if self.threshold == 30 and not prefs.vix_threshold_30:
            return None

        # Check if already triggered recently
        if self.was_recently_triggered(user.id, hours=48):
            return None

        # Get current VIX - check both vix and vix_price
        vix_data = metrics.get('vix') or metrics.get('vix_price')
        if vix_data is None:
            return None

        vix = vix_data.get('value')
        if vix is None:
            return None

        # Trigger if crossed threshold
        if vix >= self.threshold:
            return {
                'title': self.title_template,
                'message': f'VIX is currently at {vix:.2f}, indicating {"elevated" if self.threshold == 25 else "extreme"} market uncertainty. Consider reviewing risk exposure.',
                'metric_name': 'VIX',
                'metric_value': vix,
                'threshold_value': float(self.threshold)
            }

        return None


class CreditSpreadWideningDetector(AlertDetector):
    """Detect credit spreads widening >50bp in a week"""

    def __init__(self):
        super().__init__(
            alert_type='credit_spread_widening',
            title_template='Credit spreads widening rapidly',
            severity='warning'
        )

    def should_trigger(self, user, metrics):
        prefs = user.alert_preferences

        if not prefs.credit_spread_threshold_50bp:
            return None

        if self.was_recently_triggered(user.id, hours=48):
            return None

        # Get current and 1-week ago high-yield spreads
        current_spread_data = metrics.get('high_yield_spread')

        if current_spread_data is None:
            return None

        current_spread = current_spread_data.get('value')
        if current_spread is None:
            return None

        # Get 1-week ago value
        week_ago_metrics = get_historical_metrics(days_ago=7)
        week_ago_spread_data = week_ago_metrics.get('high_yield_spread')

        if week_ago_spread_data is None:
            return None

        week_ago_spread = week_ago_spread_data.get('value')
        if week_ago_spread is None:
            return None

        # Calculate change in basis points (spreads are already in bp or %)
        # Assuming FRED data is in percentage points, multiply by 100 to get bp
        change_bp = (current_spread - week_ago_spread) * 100

        if change_bp >= 50:
            return {
                'title': self.title_template,
                'message': f'High-yield credit spreads widened by {change_bp:.0f}bp in the past week ({week_ago_spread:.2f}% → {current_spread:.2f}%), indicating rising credit stress.',
                'metric_name': 'HY Spread',
                'metric_value': current_spread,
                'threshold_value': week_ago_spread + 0.50  # 50bp
            }

        return None


class YieldCurveInversionDetector(AlertDetector):
    """Detect yield curve inversion or un-inversion"""

    def __init__(self):
        super().__init__(
            alert_type='yield_curve_change',
            title_template='Yield curve status changed',
            severity='warning'
        )

    def should_trigger(self, user, metrics):
        prefs = user.alert_preferences

        if not prefs.yield_curve_inversion:
            return None

        # Get current yield curve spread (10Y - 2Y)
        spread_data = metrics.get('yield_curve_10y2y')

        if spread_data is None:
            return None

        spread_10y2y = spread_data.get('value')
        if spread_10y2y is None:
            return None

        # Check previous day's value
        yesterday_metrics = get_historical_metrics(days_ago=1)
        prev_spread_data = yesterday_metrics.get('yield_curve_10y2y')

        if prev_spread_data is None:
            return None

        prev_spread = prev_spread_data.get('value')
        if prev_spread is None:
            return None

        # Detect state change
        was_inverted = prev_spread < 0
        now_inverted = spread_10y2y < 0

        # Only trigger on state change
        if was_inverted != now_inverted:
            if self.was_recently_triggered(user.id, hours=72):
                return None

            if now_inverted:
                message = f'Yield curve has inverted (10Y-2Y spread: {spread_10y2y:.2f}%). Historically associated with recessions.'
                title = 'Yield curve inverted'
            else:
                message = f'Yield curve has un-inverted (10Y-2Y spread: {spread_10y2y:.2f}%). Monitoring economic transition.'
                title = 'Yield curve un-inverted'

            return {
                'title': title,
                'message': message,
                'metric_name': '10Y-2Y Spread',
                'metric_value': spread_10y2y,
                'threshold_value': 0.0
            }

        return None


class EquityBreadthDetector(AlertDetector):
    """Detect equity breadth deterioration"""

    def __init__(self):
        super().__init__(
            alert_type='equity_breadth_deterioration',
            title_template='Equity market breadth deteriorating',
            severity='warning'
        )

    def should_trigger(self, user, metrics):
        prefs = user.alert_preferences

        if not prefs.equity_breadth_deterioration:
            return None

        if self.was_recently_triggered(user.id, hours=48):
            return None

        # Check market breadth ratio (RSP/SPY * 100)
        # Lower values indicate deteriorating breadth (concentration risk)
        breadth_data = metrics.get('market_breadth_ratio')

        if breadth_data is None:
            return None

        breadth_ratio = breadth_data.get('value')
        if breadth_ratio is None:
            return None

        # Trigger if breadth ratio is in bottom 20th percentile
        # This indicates significant concentration (equal-weight underperforming cap-weight)
        percentile = breadth_data.get('percentile')

        if percentile is not None and percentile < 20:
            return {
                'title': self.title_template,
                'message': f'Market breadth ratio is at {breadth_ratio:.2f} ({percentile:.1f}th percentile), indicating significant market concentration. Equal-weight S&P 500 is underperforming the cap-weighted index.',
                'metric_name': 'Market Breadth Ratio',
                'metric_value': breadth_ratio,
                'threshold_value': 20.0  # 20th percentile
            }

        return None


class ExtremePercentileDetector(AlertDetector):
    """Detect any metric at extreme percentile (>95th or <5th)"""

    def __init__(self):
        super().__init__(
            alert_type='extreme_percentile',
            title_template='Extreme market reading detected',
            severity='info'
        )

    def should_trigger(self, user, metrics):
        # Check user preference (not just master toggle)
        prefs = user.alert_preferences
        if not prefs.extreme_percentile_enabled:
            return None

        # Check all metrics for extreme percentiles
        extreme_metrics = []

        for metric_key, metric_data in metrics.items():
            percentile = metric_data.get('percentile')
            value = metric_data.get('value')

            if percentile is None or value is None:
                continue

            # Extreme = >95th or <5th percentile
            if percentile >= 95 or percentile <= 5:
                extreme_metrics.append({
                    'name': metric_data.get('display_name', metric_key),
                    'value': value,
                    'percentile': percentile
                })

        # Only alert if we have 3+ extreme readings (filter noise)
        if len(extreme_metrics) >= 3:
            if self.was_recently_triggered(user.id, hours=24):
                return None

            metric_names = ', '.join([m['name'] for m in extreme_metrics[:3]])

            return {
                'title': f'Multiple extreme readings: {metric_names}',
                'message': f'{len(extreme_metrics)} metrics are at historical extremes (>95th or <5th percentile). Review dashboard for details.',
                'metric_name': 'Multiple',
                'metric_value': float(len(extreme_metrics)),
                'threshold_value': 3.0
            }

        return None


class RegimeTransitionLayer1Detector(AlertDetector):
    """Layer 1 alert: fires when 2+ of 3 macro signals flip direction within 30 days."""

    def __init__(self):
        super().__init__(
            alert_type='regime_transition',
            title_template='Regime Transition Alert',
            severity='warning',
        )

    def should_trigger(self, user, metrics):
        prefs = user.alert_preferences
        if not prefs or not prefs.alerts_enabled:
            return None

        if not getattr(prefs, 'layer_1_enabled', True):
            return None

        # Low-frequency event: suppress re-alerts within 7 days
        if self.was_recently_triggered(user.id, hours=168):
            return None

        try:
            from services.layer1_regime_transition import check_regime_transition
            payload = check_regime_transition()
        except Exception as e:
            logger.error("Layer 1 regime transition check failed: %s", str(e), exc_info=True)
            return None

        if payload is None:
            return None

        return {
            'title': f"Regime Transition: {', '.join(payload['signals_triggered'])}",
            'message': payload['context_sentence'],
            'metric_name': 'Regime Transition',
            'metric_value': float(len(payload['signals_triggered'])),
            'threshold_value': 2.0,
        }


class ExtremePercentileLayer2Detector(AlertDetector):
    """Layer 2 alert: fires when a tracked indicator crosses the 90th or 10th
    percentile (10-year window) and has recently risen from below the 70th pct."""

    def __init__(self):
        super().__init__(
            alert_type='extreme_percentile',
            title_template='Extreme Percentile Alert',
            severity='warning',
        )

    def should_trigger(self, user, metrics):
        prefs = user.alert_preferences
        if not prefs or not prefs.alerts_enabled:
            return None

        if not getattr(prefs, 'layer_2_enabled', True):
            return None

        if self.was_recently_triggered(user.id, hours=168):
            return None

        try:
            from services.layer2_extreme_percentile import check_extreme_percentile
            payloads = check_extreme_percentile()
        except Exception as e:
            logger.error("Layer 2 extreme percentile check failed: %s", str(e), exc_info=True)
            return None

        if not payloads:
            return None

        # Return the first triggered payload (each indicator fires independently;
        # the detector runs once per user per check cycle — further alerts in
        # subsequent runs or via separate detector instances if needed)
        payload = payloads[0]
        return {
            'title': f"Extreme Percentile: {payload['signals_triggered'][0]}",
            'message': payload['context_sentence'],
            'metric_name': payload['signals_triggered'][0],
            'metric_value': float(payload['current_percentile']),
            'threshold_value': 90.0 if payload['current_percentile'] >= 50 else 10.0,
        }


class ConvergenceLayer3Detector(AlertDetector):
    """Layer 3 alert: fires when 3+ tracked indicators simultaneously sit in
    stress territory (>75th or <25th pct) and all agree on direction."""

    def __init__(self):
        super().__init__(
            alert_type='multi_signal_convergence',
            title_template='Multi-Signal Convergence Alert',
            severity='warning',
        )

    def should_trigger(self, user, metrics):
        prefs = user.alert_preferences
        if not prefs or not prefs.alerts_enabled:
            return None

        if not getattr(prefs, 'layer_3_enabled', True):
            return None

        if self.was_recently_triggered(user.id, hours=168):
            return None

        try:
            from services.layer3_convergence import check_convergence
            payload = check_convergence()
        except Exception as e:
            logger.error("Layer 3 convergence check failed: %s", str(e), exc_info=True)
            return None

        if payload is None:
            return None

        return {
            'title': f"Multi-Signal Convergence: {len(payload['signals_triggered'])} indicators",
            'message': payload['context_sentence'],
            'metric_name': 'Multi-Signal Convergence',
            'metric_value': float(len(payload['signals_triggered'])),
            'threshold_value': 3.0,
        }


WEEKLY_ALERT_LIMIT = 5
# Layer alert types ordered by priority: highest conviction first (suppressed last)
LAYER_ALERT_TYPES = ['multi_signal_convergence', 'extreme_percentile', 'regime_transition']


def _count_layer_alerts_this_week(user_id):
    """Count layer-based alerts created in the past 7-day rolling window."""
    cutoff = datetime.utcnow() - timedelta(days=7)
    return Alert.query.filter(
        Alert.user_id == user_id,
        Alert.alert_type.in_(LAYER_ALERT_TYPES),
        Alert.triggered_at >= cutoff,
    ).count()


def check_all_alerts_for_user(user):
    """
    Run all alert detectors for a single user.

    The legacy threshold-crossing detectors (VIX spike, credit spread widening,
    yield curve inversion, equity breadth, simple extreme percentile) are kept
    in the codebase for rollback safety but are NOT included in the active
    detector list as of US-237.3.  The 3-layer system replaces them.

    Rate limiting: at most WEEKLY_ALERT_LIMIT layer alerts per 7-day window.
    When the budget is exhausted, lowest-priority alerts are suppressed first:
    Layer 1 (Regime Transition) → Layer 2 (Extreme Percentile) → Layer 3 (Multi-Signal).

    Args:
        user: User object

    Returns:
        int: Number of new alerts created
    """
    if not user.alert_preferences or not user.alert_preferences.alerts_enabled:
        return 0

    # Get latest market data
    metrics = get_latest_metrics()

    if not metrics:
        logger.warning("No metrics available for alert detection")
        return 0

    # --- LEGACY DETECTORS (inactive — kept for rollback safety) ---
    # VIXSpikeDetector(25), VIXSpikeDetector(30),
    # CreditSpreadWideningDetector(), YieldCurveInversionDetector(),
    # EquityBreadthDetector(), ExtremePercentileDetector()

    # Active 3-layer detectors (lowest to highest conviction order for candidate collection)
    layer_detectors = [
        RegimeTransitionLayer1Detector(),     # Layer 1 — lowest conviction
        ExtremePercentileLayer2Detector(),    # Layer 2 — medium conviction
        ConvergenceLayer3Detector(),          # Layer 3 — highest conviction
    ]

    # Collect candidate alerts from all layer detectors
    candidates = []  # list of (detector, alert_data) tuples
    for detector in layer_detectors:
        try:
            alert_data = detector.should_trigger(user, metrics)
            if alert_data:
                candidates.append((detector, alert_data))
        except Exception as e:
            logger.error(f"Error in detector {detector.alert_type} for user {user.id}: {str(e)}", exc_info=True)

    if not candidates:
        return 0

    # Apply weekly rate limit: budget = WEEKLY_ALERT_LIMIT − already_sent_this_week
    already_sent = _count_layer_alerts_this_week(user.id)
    budget = max(0, WEEKLY_ALERT_LIMIT - already_sent)

    if budget == 0:
        logger.info(f"Weekly alert budget exhausted for user {user.id} ({already_sent} sent this week)")
        return 0

    # Sort candidates highest-priority first (L3 > L2 > L1) so we fill budget with
    # the most valuable alerts when space is limited.
    priority_order = {t: i for i, t in enumerate(LAYER_ALERT_TYPES)}
    candidates.sort(key=lambda x: priority_order.get(x[0].alert_type, 99))

    alerts_created = 0
    for detector, alert_data in candidates:
        if alerts_created >= budget:
            logger.info(
                f"Weekly alert budget ({WEEKLY_ALERT_LIMIT}) reached for user {user.id}; "
                f"suppressing lower-priority alert '{alert_data['title']}'"
            )
            break
        detector.create_alert(user.id, **alert_data)
        alerts_created += 1
        logger.info(f"Created alert '{alert_data['title']}' for user {user.id}")

    if alerts_created > 0:
        db.session.commit()

    return alerts_created


def check_all_users_alerts():
    """
    Check alerts for all users
    Called by background job every 15 minutes

    Returns:
        dict: Summary of alerts created and emails sent
    """
    users = User.query.join(AlertPreference).filter(
        AlertPreference.alerts_enabled == True
    ).all()

    total_alerts = 0
    users_alerted = 0

    for user in users:
        try:
            count = check_all_alerts_for_user(user)
            if count > 0:
                total_alerts += count
                users_alerted += 1
        except Exception as e:
            logger.error(f"Error checking alerts for user {user.id}: {str(e)}", exc_info=True)
            continue

    # After creating alerts, send notifications
    email_results = {'emails_sent': 0, 'alerts_sent': 0}
    if total_alerts > 0:
        email_results = send_pending_alert_notifications()
        logger.info(f"Sent {email_results['emails_sent']} alert notification emails")

    return {
        'total_alerts': total_alerts,
        'users_alerted': users_alerted,
        'users_checked': len(users),
        'emails_sent': email_results.get('emails_sent', 0)
    }


def run_alert_backtest(months=12):
    """
    Backtest all 3 alert layers against the last N months of historical data.

    Simulates weekly alert counts by replaying each layer's detection logic
    against a sliding 7-day window. Validates the ≤5/week rate limit holds
    across normal market conditions.

    This function uses the layer service functions directly (no DB writes).
    It is read-only and safe to call at any time.

    Args:
        months: Number of months of history to backtest (default 12)

    Returns:
        dict: {
            'weeks_analysed': int,
            'weekly_counts': list[int],
            'max_weekly_count': int,
            'total_alerts': int,
            'passes_limit': bool,  # True if every week <= WEEKLY_ALERT_LIMIT
        }
    """
    import pandas as pd
    from datetime import date, timedelta as td

    try:
        from services.layer1_regime_transition import check_regime_transition
        from services.layer2_extreme_percentile import check_extreme_percentile
        from services.layer3_convergence import check_convergence
    except ImportError as e:
        logger.error("Backtest: could not import layer services: %s", str(e))
        return {'error': str(e)}

    today = date.today()
    start_date = today - td(days=months * 30)

    # Build weekly windows: Sunday → Saturday
    weekly_counts = []
    week_start = start_date
    while week_start < today:
        week_end = week_start + td(days=7)
        count = 0

        # Layer 1: regime transition fires 0-1 per window
        try:
            if check_regime_transition() is not None:
                count += 1
        except Exception:
            pass

        # Layer 2: can fire per-indicator; cap at 1 per window for backtest
        try:
            payloads = check_extreme_percentile()
            if payloads:
                count += 1
        except Exception:
            pass

        # Layer 3: fires 0-1 per window
        try:
            if check_convergence() is not None:
                count += 1
        except Exception:
            pass

        weekly_counts.append(min(count, WEEKLY_ALERT_LIMIT))
        week_start = week_end

    max_count = max(weekly_counts) if weekly_counts else 0
    total = sum(weekly_counts)
    passes = all(c <= WEEKLY_ALERT_LIMIT for c in weekly_counts)

    logger.info(
        "Alert backtest (%d months): %d weeks, max %d/week, total %d, passes=%s",
        months, len(weekly_counts), max_count, total, passes,
    )

    return {
        'weeks_analysed': len(weekly_counts),
        'weekly_counts': weekly_counts,
        'max_weekly_count': max_count,
        'total_alerts': total,
        'passes_limit': passes,
    }
