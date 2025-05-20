import os
import requests

PAYSTACK_BASE = 'https://api.paystack.co'


def _headers():
    secret = os.getenv('PAYSTACK_SECRET_KEY', '')
    return {
        'Authorization': f'Bearer {secret}',
        'Content-Type': 'application/json',
    }


def paystack_initialize(email, amount, reference, callback_url=None):
    """Initialize a Paystack transaction.

    amount is in the major unit (e.g. taka / naira); Paystack expects kobo/paisa.
    """
    try:
        amount_kobo = int(round(float(amount) * 100))
    except (TypeError, ValueError):
        return {'success': False, 'error': 'Invalid amount'}

    payload = {
        'email': email,
        'amount': amount_kobo,
        'reference': reference,
    }
    if callback_url:
        payload['callback_url'] = callback_url

    resp = requests.post(
        f'{PAYSTACK_BASE}/transaction/initialize',
        json=payload, headers=_headers(), timeout=20)
    data = resp.json()

    if not data.get('status'):
        return {'success': False, 'error': data.get('message', 'Paystack error')}

    return {
        'success': True,
        'authorization_url': data['data']['authorization_url'],
        'access_code': data['data'].get('access_code'),
        'reference': data['data']['reference'],
    }


def paystack_verify(reference):
    """Verify a transaction by reference. Returns dict with status/message."""
    resp = requests.get(
        f'{PAYSTACK_BASE}/transaction/verify/{reference}',
        headers=_headers(), timeout=20)
    data = resp.json()

    if not data.get('status'):
        return {'success': False, 'error': data.get('message', 'Verification failed')}

    txn = data.get('data', {})
    paid = txn.get('status') == 'success' and bool(txn.get('paid'))
    return {
        'success': paid,
        'status': txn.get('status'),
        'amount': txn.get('amount'),
        'reference': txn.get('reference'),
        'paid_at': txn.get('paid_at'),
    }
