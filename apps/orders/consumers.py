import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class DeliveryTrackingConsumer(AsyncJsonWebsocketConsumer):
    """Rider publishes live location, customer + admin listen on order group."""

    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.group_name = f"order_{self.order_id}"
        user = self.scope.get('user')

        if not (user and user.is_authenticated):
            await self.close()
            return

        is_allowed = await self._check_access(user)
        if not is_allowed:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name)

    async def _check_access(self, user):
        return await database_sync_to_async(
            self._has_access)(user)

    def _has_access(self, user):
        from .models import Order
        if user.is_staff:
            return True
        order = Order.objects.filter(id=self.order_id).first()
        if not order:
            return False
        if order.customer_id == user.id:
            return True
        if order.rider and order.rider.user_id == user.id:
            return True
        return False

    async def receive_json(self, content, **kwargs):
        msg_type = content.get('type')
        user = self.scope.get('user')
        if not (user and user.is_authenticated):
            return

        if msg_type == 'location':
            await self._handle_location(user, content)
        elif msg_type == 'request_status':
            await self._send_status(user)
        elif msg_type == 'ping':
            await self.send_json({'type': 'pong'})

    async def _handle_location(self, user, content):
        latitude = content.get('latitude')
        longitude = content.get('longitude')
        if latitude is None or longitude is None:
            return
        is_rider = await database_sync_to_async(self._is_order_rider)(user)
        if not is_rider:
            return
        await database_sync_to_async(self._save_rider_location)(user, latitude, longitude)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'location_update',
                'rider_id': user.id,
                'rider_name': user.full_name or user.username,
                'latitude': str(latitude),
                'longitude': str(longitude),
            },
        )

    def _is_order_rider(self, user):
        from .models import Order
        order = Order.objects.filter(id=self.order_id).first()
        return bool(order and order.rider and order.rider.user_id == user.id)

    def _save_rider_location(self, user, latitude, longitude):
        profile = getattr(user, 'rider_profile', None)
        if profile:
            profile.current_latitude = latitude
            profile.current_longitude = longitude
            profile.save(update_fields=['current_latitude', 'current_longitude'])

    async def _send_status(self, user):
        status = await database_sync_to_async(self._get_order_status)()
        rider_location = await database_sync_to_async(self._get_rider_location)()
        await self.send_json({
            'type': 'status',
            'order_id': int(self.order_id),
            'status': status,
            'rider_location': rider_location,
        })

    def _get_order_status(self):
        from .models import Order
        order = Order.objects.filter(id=self.order_id).first()
        return order.status if order else None

    def _get_rider_location(self):
        from .models import Order
        order = Order.objects.filter(id=self.order_id).first()
        if order and order.rider:
            return {
                'latitude': str(order.rider.current_latitude),
                'longitude': str(order.rider.current_longitude),
            }
        return None

    # Server -> client broadcasts
    async def location_update(self, event):
        await self.send_json(event)

    async def status_update(self, event):
        await self.send_json(event)


class AdminLiveConsumer(AsyncJsonWebsocketConsumer):
    """Admin dashboard live feed: new orders, status changes, deliveries."""

    async def connect(self):
        user = self.scope.get('user')
        if not (user and user.is_authenticated and user.is_staff):
            await self.close()
            return
        self.group_name = 'admin_live'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'ping':
            await self.send_json({'type': 'pong'})

    async def admin_event(self, event):
        await self.send_json(event)
