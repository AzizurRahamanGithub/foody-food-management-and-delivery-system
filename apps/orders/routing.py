from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/delivery/(?P<order_id>\d+)/$',
            consumers.DeliveryTrackingConsumer.as_asgi()),
    re_path(r'ws/admin/live/$',
            consumers.AdminLiveConsumer.as_asgi()),
]
