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


def check_all_alerts_for_user(user):
    """
    Run all alert detectors for a single user

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

    # Initialize all detectors
    detectors = [
        VIXSpikeDetector(25),
        VIXSpikeDetector(30),
        CreditSpreadWideningDetector(),
        YieldCurveInversionDetector(),
        EquityBreadthDetector(),
        ExtremePercentileDetector(),
    ]

    alerts_created = 0

    for detector in detectors:
        try:
            alert_data = detector.should_trigger(user, metrics)

            if alert_data:
                detector.create_alert(user.id, **alert_data)
                alerts_created += 1
                logger.info(f"Created alert '{alert_data['title']}' for user {user.id}")

        except Exception as e:
            logger.error(f"Error in detector {detector.alert_type} for user {user.id}: {str(e)}", exc_info=True)
            continue

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
