from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (GlobalCategoryViewSet, DeliveryZoneViewSet,
                    PricingRuleViewSet,
                    AdminOverviewView, AdminOrdersView,
                    AdminOrderDetailView,
                    AdminMerchantView, AdminMerchantVerificationView,
                    AdminRiderView, AdminCustomerView,
                    AdminAnalyticsView, AdminReportsView,
                    AdminAddRestaurantView, AdminInviteRiderView)

router = DefaultRouter()
router.register('global-categories', GlobalCategoryViewSet,
                basename='admin-global-categories')
router.register('delivery-zones', DeliveryZoneViewSet,
                basename='admin-delivery-zones')
router.register('pricing-rules', PricingRuleViewSet,
                basename='admin-pricing-rules')

urlpatterns = [
    path('overview/', AdminOverviewView.as_view(), name='admin-overview'),
    path('orders/', AdminOrdersView.as_view(), name='admin-orders'),
    path('orders/<int:pk>/', AdminOrderDetailView.as_view(),
         name='admin-order-detail'),
    path('merchants/', AdminMerchantView.as_view(),
         name='admin-merchants'),
    path('merchants/<int:pk>/', AdminMerchantView.as_view(),
         name='admin-merchant-action'),
    path('merchants/<int:pk>/verify/',
         AdminMerchantVerificationView.as_view(),
         name='admin-merchant-verify'),
    path('verifications/', AdminMerchantVerificationView.as_view(),
         name='admin-verifications'),
    path('verifications/<int:pk>/',
         AdminMerchantVerificationView.as_view(),
         name='admin-verification-detail'),
    path('riders/', AdminRiderView.as_view(), name='admin-riders'),
    path('riders/<int:pk>/', AdminRiderView.as_view(),
         name='admin-rider-action'),
    path('customers/', AdminCustomerView.as_view(),
         name='admin-customers'),
    path('customers/<int:pk>/', AdminCustomerView.as_view(),
         name='admin-customer-action'),
    path('analytics/', AdminAnalyticsView.as_view(),
         name='admin-analytics'),
    path('reports/', AdminReportsView.as_view(), name='admin-reports'),
    path('add-restaurant/', AdminAddRestaurantView.as_view(),
         name='admin-add-restaurant'),
    path('invite-rider/', AdminInviteRiderView.as_view(),
         name='admin-invite-rider'),
] + router.urls
