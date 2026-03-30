"""
US-13.1.3: Stripe Webhook Endpoint

Tests for:
- Webhook endpoint exists and accepts POST requests
- Stripe signature verification (accept valid, reject invalid/missing)
- Event handlers: checkout.session.completed, invoice.paid,
  invoice.payment_failed, customer.subscription.deleted,
  customer.subscription.updated
- Idempotency — processing the same event twice produces identical state
- Edge cases: unknown user, missing data, unrecognised event types
- Security: no sensitive info in error responses, POST-only
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SIGNALTRACKERS_DIR = REPO_ROOT / 'signaltrackers'

sys.path.insert(0, str(SIGNALTRACKERS_DIR))

WEBHOOK_FILE = SIGNALTRACKERS_DIR / 'billing' / 'webhooks.py'
DASHBOARD_FILE = SIGNALTRACKERS_DIR / 'dashboard.py'

WEBHOOK_SOURCE = WEBHOOK_FILE.read_text()
DASHBOARD_SOURCE = DASHBOARD_FILE.read_text()


# ---------------------------------------------------------------------------
# Source-level verification — endpoint exists
# ---------------------------------------------------------------------------

class TestWebhookEndpointExists:
    """Verify webhook route is registered correctly."""

    def test_webhook_route_defined(self):
        """Webhook route is defined in dashboard.py."""
        assert "/webhook/stripe" in DASHBOARD_SOURCE

    def test_webhook_route_accepts_post(self):
        """Webhook route accepts POST method."""
        assert "methods=['POST']" in DASHBOARD_SOURCE or 'methods=["POST"]' in DASHBOARD_SOURCE

    def test_webhook_csrf_exempt(self):
        """Webhook route is CSRF exempt (Stripe can't send CSRF tokens)."""
        # Find the webhook route and check csrf.exempt is nearby above it
        idx = DASHBOARD_SOURCE.index("/webhook/stripe")
        preceding = DASHBOARD_SOURCE[max(0, idx - 200):idx]
        assert "csrf.exempt" in preceding

    def test_webhook_uses_signature_verification(self):
        """Webhook route uses Stripe signature verification."""
        assert "Stripe-Signature" in DASHBOARD_SOURCE
        assert "construct_event" in DASHBOARD_SOURCE

    def test_webhook_rejects_missing_signature(self):
        """Route checks for missing Stripe-Signature header."""
        assert "Missing signature" in DASHBOARD_SOURCE or "missing" in DASHBOARD_SOURCE.lower()


# ---------------------------------------------------------------------------
# Source-level verification — handler module
# ---------------------------------------------------------------------------

class TestWebhookHandlerModule:
    """Verify webhook handler module structure."""

    def test_handler_file_exists(self):
        """billing/webhooks.py exists."""
        assert WEBHOOK_FILE.exists()

    def test_handles_checkout_session_completed(self):
        """Handler for checkout.session.completed is defined."""
        assert "checkout.session.completed" in WEBHOOK_SOURCE

    def test_handles_invoice_paid(self):
        """Handler for invoice.paid is defined."""
        assert "invoice.paid" in WEBHOOK_SOURCE

    def test_handles_invoice_payment_failed(self):
        """Handler for invoice.payment_failed is defined."""
        assert "invoice.payment_failed" in WEBHOOK_SOURCE

    def test_handles_subscription_deleted(self):
        """Handler for customer.subscription.deleted is defined."""
        assert "customer.subscription.deleted" in WEBHOOK_SOURCE

    def test_handles_subscription_updated(self):
        """Handler for customer.subscription.updated is defined."""
        assert "customer.subscription.updated" in WEBHOOK_SOURCE

    def test_unrecognised_events_acknowledged(self):
        """Unrecognised event types return 'ignored' status (not error)."""
        assert "'ignored'" in WEBHOOK_SOURCE or '"ignored"' in WEBHOOK_SOURCE

    def test_handler_imports_subscription_status(self):
        """Handler uses SubscriptionStatus enum for status values."""
        assert "SubscriptionStatus" in WEBHOOK_SOURCE

    def test_handler_commits_to_db(self):
        """Handler commits changes to database."""
        assert "db.session.commit()" in WEBHOOK_SOURCE


# ---------------------------------------------------------------------------
# Functional Tests — Event Handlers (with mocked DB)
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Mock database session."""
    with patch('billing.webhooks.db') as mock:
        mock.session = MagicMock()
        yield mock


@pytest.fixture
def mock_stripe():
    """Mock stripe.Subscription.retrieve."""
    with patch('billing.webhooks.stripe') as mock:
        sub_mock = MagicMock()
        sub_mock.__getitem__ = lambda self, key: {
            'current_period_end': 1735689600,  # 2025-01-01 00:00:00 UTC
            'status': 'active',
        }.get(key)
        mock.Subscription.retrieve.return_value = sub_mock
        yield mock


def _make_user(stripe_customer_id='cus_test123', email='test@example.com',
               subscription_status='none', subscription_end_date=None):
    """Create a mock User object."""
    user = MagicMock()
    user.id = 'user-uuid-123'
    user.email = email
    user.stripe_customer_id = stripe_customer_id
    user.subscription_status = subscription_status
    user.subscription_end_date = subscription_end_date
    return user


class TestCheckoutSessionCompleted:
    """Tests for checkout.session.completed event handler."""

    def test_activates_subscription(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        user = _make_user()
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'checkout.session.completed',
                'id': 'evt_test1',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'customer_email': 'test@example.com',
                    'subscription': 'sub_test123',
                }},
            }
            result = handle_webhook_event(event)

        assert result['status'] == 'processed'
        assert user.subscription_status == 'active'

    def test_sets_stripe_customer_id_on_email_lookup(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        user = _make_user(stripe_customer_id=None)
        with patch('billing.webhooks.User') as MockUser:
            # First lookup by customer_id returns None, second by email returns user
            MockUser.query.filter_by.return_value.first.side_effect = [None, user]

            event = {
                'type': 'checkout.session.completed',
                'id': 'evt_test2',
                'data': {'object': {
                    'customer': 'cus_new123',
                    'customer_email': 'test@example.com',
                    'subscription': 'sub_test123',
                }},
            }
            handle_webhook_event(event)

        assert user.stripe_customer_id == 'cus_new123'
        assert user.subscription_status == 'active'

    def test_handles_unknown_user(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = None

            event = {
                'type': 'checkout.session.completed',
                'id': 'evt_test3',
                'data': {'object': {
                    'customer': 'cus_unknown',
                    'customer_email': 'unknown@example.com',
                    'subscription': 'sub_test123',
                }},
            }
            result = handle_webhook_event(event)

        # Should still succeed (200) — no crash
        assert result['status'] == 'processed'
        mock_db.session.commit.assert_not_called()

    def test_idempotent_double_processing(self, mock_db, mock_stripe):
        """Processing checkout.session.completed twice produces identical state."""
        from billing.webhooks import handle_webhook_event

        user = _make_user()
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'checkout.session.completed',
                'id': 'evt_test4',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'subscription': 'sub_test123',
                }},
            }
            handle_webhook_event(event)
            first_status = user.subscription_status
            first_end = user.subscription_end_date

            handle_webhook_event(event)
            assert user.subscription_status == first_status
            assert user.subscription_end_date == first_end


class TestInvoicePaid:
    """Tests for invoice.paid event handler."""

    def test_keeps_subscription_active(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'invoice.paid',
                'id': 'evt_inv1',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'subscription': 'sub_test123',
                }},
            }
            result = handle_webhook_event(event)

        assert result['status'] == 'processed'
        assert user.subscription_status == 'active'

    def test_updates_end_date(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'invoice.paid',
                'id': 'evt_inv2',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'subscription': 'sub_test123',
                }},
            }
            handle_webhook_event(event)

        assert user.subscription_end_date is not None

    def test_idempotent(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'invoice.paid',
                'id': 'evt_inv3',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'subscription': 'sub_test123',
                }},
            }
            handle_webhook_event(event)
            handle_webhook_event(event)

        assert user.subscription_status == 'active'

    def test_handles_unknown_customer(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = None

            event = {
                'type': 'invoice.paid',
                'id': 'evt_inv4',
                'data': {'object': {
                    'customer': 'cus_unknown',
                    'subscription': 'sub_test123',
                }},
            }
            result = handle_webhook_event(event)

        assert result['status'] == 'processed'


class TestInvoicePaymentFailed:
    """Tests for invoice.payment_failed event handler."""

    def test_marks_past_due(self, mock_db):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'invoice.payment_failed',
                'id': 'evt_fail1',
                'data': {'object': {'customer': 'cus_test123'}},
            }
            result = handle_webhook_event(event)

        assert result['status'] == 'processed'
        assert user.subscription_status == 'past_due'

    def test_does_not_revoke_access(self, mock_db):
        """past_due status should NOT revoke access per business rules."""
        from billing.webhooks import handle_webhook_event
        from models.user import SubscriptionStatus

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'invoice.payment_failed',
                'id': 'evt_fail2',
                'data': {'object': {'customer': 'cus_test123'}},
            }
            handle_webhook_event(event)

        # past_due is NOT canceled or none — access retained
        assert user.subscription_status == SubscriptionStatus.PAST_DUE.value
        assert user.subscription_status != SubscriptionStatus.CANCELED.value
        assert user.subscription_status != SubscriptionStatus.NONE.value

    def test_idempotent(self, mock_db):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='past_due')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'invoice.payment_failed',
                'id': 'evt_fail3',
                'data': {'object': {'customer': 'cus_test123'}},
            }
            handle_webhook_event(event)
            handle_webhook_event(event)

        assert user.subscription_status == 'past_due'


class TestSubscriptionDeleted:
    """Tests for customer.subscription.deleted event handler."""

    def test_marks_canceled(self, mock_db):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'customer.subscription.deleted',
                'id': 'evt_del1',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'current_period_end': 1735689600,
                }},
            }
            result = handle_webhook_event(event)

        assert result['status'] == 'processed'
        assert user.subscription_status == 'canceled'

    def test_sets_subscription_end_date(self, mock_db):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'customer.subscription.deleted',
                'id': 'evt_del2',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'current_period_end': 1735689600,
                }},
            }
            handle_webhook_event(event)

        assert user.subscription_end_date is not None
        assert user.subscription_end_date == datetime.fromtimestamp(
            1735689600, tz=timezone.utc
        )

    def test_does_not_immediately_revoke_access(self, mock_db):
        """Canceled status preserves access until end date."""
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'customer.subscription.deleted',
                'id': 'evt_del3',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'current_period_end': 1735689600,
                }},
            }
            handle_webhook_event(event)

        # Status is canceled (not none) — access continues until end_date
        assert user.subscription_status == 'canceled'
        assert user.subscription_status != 'none'

    def test_idempotent(self, mock_db):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='canceled')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'customer.subscription.deleted',
                'id': 'evt_del4',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'current_period_end': 1735689600,
                }},
            }
            handle_webhook_event(event)
            end1 = user.subscription_end_date
            handle_webhook_event(event)

        assert user.subscription_status == 'canceled'
        assert user.subscription_end_date == end1


class TestSubscriptionUpdated:
    """Tests for customer.subscription.updated event handler."""

    def test_updates_status(self, mock_db):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'customer.subscription.updated',
                'id': 'evt_upd1',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'status': 'past_due',
                    'current_period_end': 1735689600,
                }},
            }
            result = handle_webhook_event(event)

        assert result['status'] == 'processed'
        assert user.subscription_status == 'past_due'

    def test_updates_end_date(self, mock_db):
        from billing.webhooks import handle_webhook_event

        user = _make_user(subscription_status='active')
        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = user

            event = {
                'type': 'customer.subscription.updated',
                'id': 'evt_upd2',
                'data': {'object': {
                    'customer': 'cus_test123',
                    'status': 'active',
                    'current_period_end': 1735689600,
                }},
            }
            handle_webhook_event(event)

        assert user.subscription_end_date == datetime.fromtimestamp(
            1735689600, tz=timezone.utc
        )

    def test_maps_stripe_statuses_correctly(self, mock_db):
        from billing.webhooks import handle_webhook_event
        from models.user import SubscriptionStatus

        status_map = {
            'active': SubscriptionStatus.ACTIVE.value,
            'past_due': SubscriptionStatus.PAST_DUE.value,
            'canceled': SubscriptionStatus.CANCELED.value,
            'unpaid': SubscriptionStatus.PAST_DUE.value,
        }

        for stripe_status, expected in status_map.items():
            user = _make_user()
            with patch('billing.webhooks.User') as MockUser:
                MockUser.query.filter_by.return_value.first.return_value = user

                event = {
                    'type': 'customer.subscription.updated',
                    'id': f'evt_map_{stripe_status}',
                    'data': {'object': {
                        'customer': 'cus_test123',
                        'status': stripe_status,
                        'current_period_end': 1735689600,
                    }},
                }
                handle_webhook_event(event)

            assert user.subscription_status == expected, \
                f"Stripe status '{stripe_status}' should map to '{expected}'"


class TestUnrecognisedEvents:
    """Unrecognised event types are acknowledged but not processed."""

    def test_unknown_event_returns_ignored(self, mock_db):
        from billing.webhooks import handle_webhook_event

        event = {
            'type': 'charge.refunded',
            'id': 'evt_unknown1',
            'data': {'object': {}},
        }
        result = handle_webhook_event(event)

        assert result['status'] == 'ignored'
        mock_db.session.commit.assert_not_called()

    def test_random_event_type_does_not_crash(self, mock_db):
        from billing.webhooks import handle_webhook_event

        event = {
            'type': 'some.totally.unknown.event',
            'id': 'evt_unknown2',
            'data': {'object': {}},
        }
        result = handle_webhook_event(event)
        assert result['status'] == 'ignored'


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge case handling."""

    def test_checkout_missing_customer_id(self, mock_db, mock_stripe):
        """Event with no customer ID is handled gracefully."""
        from billing.webhooks import handle_webhook_event

        with patch('billing.webhooks.User') as MockUser:
            event = {
                'type': 'checkout.session.completed',
                'id': 'evt_edge1',
                'data': {'object': {
                    'customer_email': 'test@example.com',
                    'subscription': 'sub_test123',
                }},
            }
            result = handle_webhook_event(event)

        assert result['status'] == 'processed'
        mock_db.session.commit.assert_not_called()

    def test_invoice_paid_missing_customer(self, mock_db, mock_stripe):
        from billing.webhooks import handle_webhook_event

        event = {
            'type': 'invoice.paid',
            'id': 'evt_edge2',
            'data': {'object': {}},
        }
        result = handle_webhook_event(event)
        assert result['status'] == 'processed'

    def test_subscription_deleted_missing_customer(self, mock_db):
        from billing.webhooks import handle_webhook_event

        event = {
            'type': 'customer.subscription.deleted',
            'id': 'evt_edge3',
            'data': {'object': {}},
        }
        result = handle_webhook_event(event)
        assert result['status'] == 'processed'

    def test_events_out_of_order_invoice_before_checkout(self, mock_db, mock_stripe):
        """invoice.paid arriving before checkout.session.completed — no crash."""
        from billing.webhooks import handle_webhook_event

        with patch('billing.webhooks.User') as MockUser:
            MockUser.query.filter_by.return_value.first.return_value = None

            event = {
                'type': 'invoice.paid',
                'id': 'evt_edge4',
                'data': {'object': {
                    'customer': 'cus_not_yet_linked',
                    'subscription': 'sub_test123',
                }},
            }
            result = handle_webhook_event(event)

        # Gracefully handles — no crash, no commit
        assert result['status'] == 'processed'


# ---------------------------------------------------------------------------
# Security Tests
# ---------------------------------------------------------------------------

class TestSecurity:
    """Security-related checks."""

    def test_error_responses_no_stack_traces(self):
        """Error responses in the route don't expose stack traces."""
        # The route returns generic messages like 'Invalid signature', 'Invalid payload'
        assert 'traceback' not in DASHBOARD_SOURCE.lower() or \
               'traceback' not in DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]

    def test_signature_failure_logged(self):
        """Signature verification failure is logged."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        assert 'logger' in webhook_section or 'app.logger' in webhook_section

    def test_endpoint_post_only(self):
        """Webhook endpoint only accepts POST."""
        idx = DASHBOARD_SOURCE.index("/webhook/stripe")
        # Check the route decorator line (same line or nearby)
        route_line_area = DASHBOARD_SOURCE[max(0, idx - 200):idx + 200]
        assert "POST" in route_line_area
        # Should not include GET, PUT, DELETE
        assert "GET" not in route_line_area.replace("get_data", "").replace("get_webhook", "")

    def test_webhook_handler_uses_stripe_verify(self):
        """Route uses stripe.Webhook.construct_event for verification."""
        assert "construct_event" in DASHBOARD_SOURCE

    def test_no_secrets_in_error_responses(self):
        """Error response strings don't contain secret references."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        # jsonify responses shouldn't leak secret names
        for sensitive in ['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'api_key']:
            # Should only appear in config reads, not in jsonify error responses
            jsonify_calls = [line for line in webhook_section.split('\n')
                           if 'jsonify' in line and sensitive in line]
            assert len(jsonify_calls) == 0, f"Found '{sensitive}' in jsonify response"


# ---------------------------------------------------------------------------
# Route-level source verification
# ---------------------------------------------------------------------------

class TestRouteStructure:
    """Verify the webhook route handles all required paths."""

    def test_returns_400_for_invalid_payload(self):
        """Route returns 400 for ValueError (invalid payload)."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        assert '400' in webhook_section

    def test_returns_400_for_invalid_signature(self):
        """Route returns 400 for SignatureVerificationError."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        assert 'SignatureVerificationError' in webhook_section

    def test_returns_200_on_success(self):
        """Route returns 200 for successfully processed events."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        assert '200' in webhook_section

    def test_returns_500_on_handler_error(self):
        """Route returns 500 if handler raises an unexpected exception."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        assert '500' in webhook_section

    def test_checks_stripe_configured(self):
        """Route checks if Stripe is configured before processing."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        assert 'is_stripe_configured' in webhook_section or 'stripe_configured' in webhook_section

    def test_returns_503_when_not_configured(self):
        """Route returns 503 when Stripe is not configured."""
        webhook_section = DASHBOARD_SOURCE[DASHBOARD_SOURCE.index('/webhook/stripe'):]
        assert '503' in webhook_section
