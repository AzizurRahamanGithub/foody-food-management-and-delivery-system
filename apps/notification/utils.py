from .models import Notification


def notify_admins(title, message, notification_type='general'):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admin_users = User.objects.filter(is_staff=True)
    for admin in admin_users:
        Notification.create_for_user(
            user=admin,
            notification_type=notification_type,
            title=title,
            message=message)


def notify_order_placed(user, order):
    Notification.create_for_user(
        user=user,
        notification_type='order_placed',
        title='Order Placed!',
        message=(
            f'Your order #{order.order_number} from '
            f'{order.merchant.business_name} has been placed.'),
        data={'order_id': order.id,
              'order_number': order.order_number})


def notify_order_confirmed(user, order):
    Notification.create_for_user(
        user=user,
        notification_type='order_confirmed',
        title='Order Confirmed!',
        message=(
            f'{order.merchant.business_name} confirmed '
            f'your order #{order.order_number}.'),
        data={'order_id': order.id,
              'order_number': order.order_number})


def notify_order_preparing(user, order):
    Notification.create_for_user(
        user=user,
        notification_type='order_preparing',
        title='Order Being Prepared',
        message=(
            f'{order.merchant.business_name} is preparing '
            f'your order #{order.order_number}.'),
        data={'order_id': order.id,
              'order_number': order.order_number})


def notify_out_for_delivery(user, order, rider_name='Your rider'):
    Notification.create_for_user(
        user=user,
        notification_type='order_out_for_delivery',
        title='Out for Delivery',
        message=(
            f'{rider_name} picked up your order '
            f'#{order.order_number}'),
        data={'order_id': order.id,
              'order_number': order.order_number,
              'rider_name': rider_name})


def notify_order_delivered(user, order):
    Notification.create_for_user(
        user=user,
        notification_type='order_delivered',
        title='Order Delivered!',
        message=(
            f'Your order from {order.merchant.business_name} '
            f'has arrived!'),
        data={'order_id': order.id,
              'order_number': order.order_number})


def notify_order_cancelled(user, order, reason=''):
    msg = (f'Your order #{order.order_number} from '
           f'{order.merchant.business_name} was cancelled.')
    if reason:
        msg += f' Reason: {reason}'
    Notification.create_for_user(
        user=user,
        notification_type='order_cancelled',
        title='Order Cancelled',
        message=msg,
        data={'order_id': order.id,
              'order_number': order.order_number,
              'reason': reason})


def notify_rate_order(user, order):
    Notification.create_for_user(
        user=user,
        notification_type='rate_order',
        title='Rate Your Order',
        message=(
            f'How was your {order.merchant.business_name} '
            f'experience?'),
        data={'order_id': order.id,
              'order_number': order.order_number,
              'merchant_name': order.merchant.business_name})


def notify_promotion(user, title, message, promo_code=None,
                     image=None):
    data = {}
    if promo_code:
        data['promo_code'] = promo_code
    Notification.create_for_user(
        user=user,
        notification_type='promotion',
        title=title,
        message=message,
        data=data,
        image=image)


def notify_deal(user, title, message, promo_code=None,
                min_order=None, image=None):
    data = {}
    if promo_code:
        data['promo_code'] = promo_code
    if min_order:
        data['min_order'] = str(min_order)
    Notification.create_for_user(
        user=user,
        notification_type='deal',
        title=title,
        message=message,
        data=data,
        image=image)
