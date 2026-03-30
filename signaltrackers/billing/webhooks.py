"""
Stripe Webhook Event Handlers

Processes incoming Stripe webhook events to keep subscription status
in sync with payment activity.  Each handler is idempotent — processing
the same event twice produces the same result.
"""

import logging
from datetime import datetime, timezone

import stripe

from extensions import db
from models.user import User, SubscriptionStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def handle_webhook_event(event):
    """Dispatch a verified Stripe event to the appropriate handler.

    Returns a dict with 'status' and optional 'message' for the HTTP response.
    Unrecognised event types are acknowledged (200) but not processed.
    """
    handler = _EVENT_HANDLERS.get(event['type'])
    if handler is None:
        logger.debug("Unhandled Stripe event type: %s", event['type'])
        return {'status': 'ignored', 'message': f"Event type {event['type']} not handled"}

    try:
        handler(event['data']['object'])
        return {'status': 'processed'}
    except Exception:
        logger.exception("Error processing Stripe event %s (id=%s)",
                         event['type'], event.get('id'))
        raise


# ---------------------------------------------------------------------------
# Individual event handlers
# ---------------------------------------------------------------------------

def _handle_checkout_session_completed(session):
    """Activate subscription after successful Stripe Checkout.

    This is the moment a user becomes a paid subscriber.
    """
    customer_id = session.get('customer')
    customer_email = session.get('customer_email') or session.get('customer_details', {}).get('email')
    subscription_id = session.get('subscription')

    if not customer_id:
        logger.warning("checkout.session.completed missing customer ID")
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()

    # Fall back to email lookup if customer ID not yet linked
    if user is None and customer_email:
        user = User.query.filter_by(email=customer_email).first()

    if user is None:
        logger.warning(
            "checkout.session.completed for unknown user "
            "(customer=%s, email=%s)", customer_id, customer_email
        )
        return

    # Link Stripe customer if not already set
    if user.stripe_customer_id != customer_id:
        user.stripe_customer_id = customer_id

    user.subscription_status = SubscriptionStatus.ACTIVE.value

    # Fetch subscription to get current period end
    if subscription_id:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            user.subscription_end_date = datetime.fromtimestamp(
                sub['current_period_end'], tz=timezone.utc
            )
        except Exception:
            logger.exception("Failed to retrieve subscription %s", subscription_id)

    db.session.commit()
    logger.info("Subscription activated for user %s (customer=%s)",
                user.id, customer_id)


def _handle_invoice_paid(invoice):
    """Record successful renewal — keep subscription active."""
    customer_id = invoice.get('customer')
    if not customer_id:
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user is None:
        logger.debug("invoice.paid for unknown customer %s", customer_id)
        return

    user.subscription_status = SubscriptionStatus.ACTIVE.value

    # Update end date from the subscription's current period
    subscription_id = invoice.get('subscription')
    if subscription_id:
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            user.subscription_end_date = datetime.fromtimestamp(
                sub['current_period_end'], tz=timezone.utc
            )
        except Exception:
            logger.exception("Failed to retrieve subscription %s", subscription_id)

    db.session.commit()
    logger.info("Invoice paid — subscription renewed for user %s", user.id)


def _handle_invoice_payment_failed(invoice):
    """Mark subscription as past_due — access is NOT revoked."""
    customer_id = invoice.get('customer')
    if not customer_id:
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user is None:
        logger.debug("invoice.payment_failed for unknown customer %s", customer_id)
        return

    user.subscription_status = SubscriptionStatus.PAST_DUE.value
    db.session.commit()
    logger.info("Payment failed — subscription past_due for user %s", user.id)


def _handle_subscription_deleted(subscription):
    """Mark subscription as canceled — access continues until period end."""
    customer_id = subscription.get('customer')
    if not customer_id:
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user is None:
        logger.debug("customer.subscription.deleted for unknown customer %s",
                      customer_id)
        return

    user.subscription_status = SubscriptionStatus.CANCELED.value

    # Preserve access until the end of the paid period
    current_period_end = subscription.get('current_period_end')
    if current_period_end:
        user.subscription_end_date = datetime.fromtimestamp(
            current_period_end, tz=timezone.utc
        )

    db.session.commit()
    logger.info("Subscription canceled for user %s (access until %s)",
                user.id, user.subscription_end_date)


def _handle_subscription_updated(subscription):
    """Update subscription details — future-proofing for plan changes."""
    customer_id = subscription.get('customer')
    if not customer_id:
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user is None:
        logger.debug("customer.subscription.updated for unknown customer %s",
                      customer_id)
        return

    # Map Stripe status to our SubscriptionStatus
    stripe_status = subscription.get('status')
    status_map = {
        'active': SubscriptionStatus.ACTIVE.value,
        'past_due': SubscriptionStatus.PAST_DUE.value,
        'canceled': SubscriptionStatus.CANCELED.value,
        'unpaid': SubscriptionStatus.PAST_DUE.value,
        'incomplete': SubscriptionStatus.NONE.value,
        'incomplete_expired': SubscriptionStatus.NONE.value,
    }
    new_status = status_map.get(stripe_status)
    if new_status:
        user.subscription_status = new_status

    current_period_end = subscription.get('current_period_end')
    if current_period_end:
        user.subscription_end_date = datetime.fromtimestamp(
            current_period_end, tz=timezone.utc
        )

    db.session.commit()
    logger.info("Subscription updated for user %s (status=%s)",
                user.id, stripe_status)


# ---------------------------------------------------------------------------
# Handler dispatch table
# ---------------------------------------------------------------------------

_EVENT_HANDLERS = {
    'checkout.session.completed': _handle_checkout_session_completed,
    'invoice.paid': _handle_invoice_paid,
    'invoice.payment_failed': _handle_invoice_payment_failed,
    'customer.subscription.deleted': _handle_subscription_deleted,
    'customer.subscription.updated': _handle_subscription_updated,
}
