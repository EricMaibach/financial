#!/usr/bin/env python3
"""
Test script for alert email notifications

Run this in Flask shell:
    flask shell
    exec(open('test_alert_email.py').read())

Or run directly:
    python test_alert_email.py
"""

from datetime import datetime
from models.alert import Alert
from models.user import User
from services.alert_email_service import send_alert_notification, send_pending_alert_notifications
from extensions import db


def create_test_alert(user_id, severity='warning', title='Test Alert', message=None):
    """Create a test alert for testing email notifications"""
    alert = Alert(
        user_id=user_id,
        alert_type='test',
        title=title,
        message=message or f'This is a test {severity} alert notification',
        severity=severity,
        metric_name='VIX',
        metric_value=28.5,
        threshold_value=25.0,
        email_sent=False
    )
    db.session.add(alert)
    db.session.commit()
    return alert


def test_single_alert_notification():
    """Test sending a single alert notification"""
    print("=" * 60)
    print("TEST: Single Alert Notification")
    print("=" * 60)

    user = User.query.first()
    if not user:
        print("ERROR: No user found in database")
        return False

    print(f"Testing with user: {user.email}")

    # Create test alert
    alert = create_test_alert(
        user.id,
        severity='warning',
        title='VIX crossed 25 threshold',
        message='VIX is currently at 28.50, indicating elevated market uncertainty. Consider reviewing risk exposure.'
    )
    print(f"Created test alert: {alert.title}")

    # Send notification
    print("Sending notification...")
    result = send_alert_notification(user, alert)

    if result:
        print("✓ Email sent successfully")
        print(f"  - email_sent: {alert.email_sent}")
        print(f"  - email_sent_at: {alert.email_sent_at}")
        return True
    else:
        print("✗ Email failed to send")
        return False


def test_batch_alerts_notification():
    """Test sending multiple alerts in one email"""
    print("\n" + "=" * 60)
    print("TEST: Batch Alert Notification (Multiple Alerts)")
    print("=" * 60)

    user = User.query.first()
    if not user:
        print("ERROR: No user found in database")
        return False

    print(f"Testing with user: {user.email}")

    # Create multiple test alerts
    alerts = [
        create_test_alert(
            user.id,
            severity='critical',
            title='VIX crossed 30 threshold',
            message='VIX is currently at 32.10, indicating extreme market uncertainty.'
        ),
        create_test_alert(
            user.id,
            severity='warning',
            title='Credit spreads widening rapidly',
            message='High-yield credit spreads widened by 55bp in the past week, indicating rising credit stress.'
        ),
        create_test_alert(
            user.id,
            severity='info',
            title='Market breadth deteriorating',
            message='Market breadth ratio is at historical lows, indicating significant market concentration.'
        ),
    ]
    print(f"Created {len(alerts)} test alerts")

    # Send notification
    print("Sending batched notification...")
    result = send_alert_notification(user, alerts)

    if result:
        print("✓ Batch email sent successfully")
        print(f"  - Alerts sent: {len(alerts)}")
        for i, alert in enumerate(alerts, 1):
            print(f"  - Alert {i}: {alert.title} [{alert.severity}]")
        return True
    else:
        print("✗ Batch email failed to send")
        return False


def test_pending_notifications():
    """Test sending all pending alert notifications"""
    print("\n" + "=" * 60)
    print("TEST: Send Pending Notifications")
    print("=" * 60)

    user = User.query.first()
    if not user:
        print("ERROR: No user found in database")
        return False

    # Create multiple unsent alerts
    alerts = [
        create_test_alert(user.id, severity='warning', title='Test Alert 1'),
        create_test_alert(user.id, severity='info', title='Test Alert 2'),
    ]
    print(f"Created {len(alerts)} unsent alerts")

    # Send pending notifications
    print("Sending pending notifications...")
    results = send_pending_alert_notifications()

    print(f"✓ Results:")
    print(f"  - Emails sent: {results['emails_sent']}")
    print(f"  - Alerts sent: {results['alerts_sent']}")

    return results['emails_sent'] > 0


def test_severity_colors():
    """Test that different severity levels render correctly"""
    print("\n" + "=" * 60)
    print("TEST: Severity Color Rendering")
    print("=" * 60)

    from services.alert_email_service import get_severity_colors

    severities = ['info', 'warning', 'critical']
    for severity in severities:
        colors = get_severity_colors(severity)
        print(f"\n{severity.upper()}:")
        print(f"  - Header BG: {colors['header_bg']}")
        print(f"  - Header Text: {colors['header_text']}")
        print(f"  - Border: {colors['border']}")
        print(f"  - Badge BG: {colors['badge_bg']}")
        print(f"  - Badge Text: {colors['badge_text']}")

    return True


def test_metric_formatting():
    """Test metric value formatting"""
    print("\n" + "=" * 60)
    print("TEST: Metric Value Formatting")
    print("=" * 60)

    from services.alert_email_service import format_metric_value

    test_values = [
        (None, 'N/A'),
        (0.0525, '5.25%'),
        (0.5, '50.00%'),
        (28.5, '28.50'),
        (1234.56, '1,234.6'),
        (3.14159, '3.14'),
    ]

    all_passed = True
    for value, expected in test_values:
        result = format_metric_value(value)
        passed = "✓" if result == expected else "✗"
        print(f"{passed} {value} → {result} (expected: {expected})")
        if result != expected:
            all_passed = False

    return all_passed


def run_all_tests():
    """Run all alert email tests"""
    print("\n" + "=" * 80)
    print("ALERT EMAIL NOTIFICATION TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        'severity_colors': test_severity_colors(),
        'metric_formatting': test_metric_formatting(),
        'single_alert': test_single_alert_notification(),
        'batch_alerts': test_batch_alerts_notification(),
        'pending_notifications': test_pending_notifications(),
    }

    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed_count = sum(results.values())
    print(f"\nTotal: {passed_count}/{total} tests passed")

    return passed_count == total


if __name__ == '__main__':
    # If running as script, set up Flask app context
    import sys
    sys.path.insert(0, '/home/eric/Documents/repos/financial/signaltrackers')

    from dashboard import app

    with app.app_context():
        success = run_all_tests()
        sys.exit(0 if success else 1)
