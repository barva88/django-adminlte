# Stripe helpers - safe wrappers that check for STRIPE_SECRET_KEY
import os

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')


def create_checkout_session(plan_id, success_url, cancel_url):
    # If Stripe is not configured, return a simulated session id
    if not STRIPE_SECRET_KEY:
        return {'id': 'simulated_session', 'url': success_url}
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        # Implement minimal checkout creation stub
        session = stripe.checkout.Session.create(payment_method_types=['card'], line_items=[{'price': plan_id, 'quantity': 1}], mode='subscription', success_url=success_url, cancel_url=cancel_url)
        return {'id': session.id, 'url': session.url}
    except Exception:
        return {'id': 'error', 'url': cancel_url}
