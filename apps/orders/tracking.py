from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

ADMIN_GROUP = 'admin_live'


def broadcast_to_order(order, event_type, payload):
    """Send event to order_{id} group (customer + rider listening)."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f"order_{order.id}",
        {'type': 'status_update', 'event_type': event_type, **payload},
    )


def broadcast_to_admin(event_type, payload):
    """Send event to admin_live group."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        ADMIN_GROUP,
        {'type': 'admin_event', 'event_type': event_type, **payload},
    )


def broadcast_order_update(order, event_type='status_change'):
    from .serializers import OrderSerializer
    payload = {
        'order_id': order.id,
        'order_number': order.order_number,
        'status': order.status,
        'order': OrderSerializer(order).data,
    }
    broadcast_to_order(order, event_type, payload)
    broadcast_to_admin(event_type, payload)
