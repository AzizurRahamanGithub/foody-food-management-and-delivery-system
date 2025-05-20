from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (MerchantProfileView, CategoryViewSet, MenuItemViewSet,
                    AddonGroupViewSet, AddonViewSet, OfferViewSet,
                    MerchantDashboardView, MerchantOrdersView,
                    MerchantOrderDetailView, MerchantOrderStatusView)

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='merchant-categories')
router.register('items', MenuItemViewSet, basename='merchant-items')
router.register('addon-groups', AddonGroupViewSet, basename='merchant-addon-groups')
router.register('addons', AddonViewSet, basename='merchant-addons')
router.register('offers', OfferViewSet, basename='merchant-offers')

urlpatterns = [
    path('profile/', MerchantProfileView.as_view(), name='merchant-profile'),
    path('dashboard/', MerchantDashboardView.as_view(), name='merchant-dashboard'),
    path('orders/', MerchantOrdersView.as_view(), name='merchant-orders'),
    path('orders/<int:pk>/', MerchantOrderDetailView.as_view(), name='merchant-order-detail'),
    path('orders/<int:pk>/status/', MerchantOrderStatusView.as_view(), name='merchant-order-status'),
] + router.urls
