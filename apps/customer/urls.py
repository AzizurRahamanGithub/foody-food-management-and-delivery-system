from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (CustomerProfileView, SavedAddressViewSet,
                    PaymentMethodViewSet, HomeView, RestaurantListView,
                    RestaurantDetailView, MenuItemDetailView, SearchView,
                    CartView, CartAddItemView, CartUpdateItemView,
                    CartRemoveItemView, CartClearView, CheckoutView,
                    MyOrdersView, OrderDetailView, CancelOrderView,
                    TrackOrderView, ReviewCreateView, PaystackInitializeView,
                    PaystackVerifyView)

router = DefaultRouter()
router.register('addresses', SavedAddressViewSet, basename='addresses')
router.register('payment-methods', PaymentMethodViewSet, basename='payment-methods')

urlpatterns = [
    path('profile/', CustomerProfileView.as_view(), name='customer-profile'),
    path('home/', HomeView.as_view(), name='home'),
    path('restaurants/', RestaurantListView.as_view(), name='restaurants'),
    path('restaurants/<int:pk>/', RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('items/<int:pk>/', MenuItemDetailView.as_view(), name='item-detail'),
    path('search/', SearchView.as_view(), name='search'),

    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', CartAddItemView.as_view(), name='cart-add'),
    path('cart/update/<int:pk>/', CartUpdateItemView.as_view(), name='cart-update'),
    path('cart/remove/<int:pk>/', CartRemoveItemView.as_view(), name='cart-remove'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),

    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', MyOrdersView.as_view(), name='my-orders'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('orders/<int:pk>/track/', TrackOrderView.as_view(), name='track-order'),
    path('review/', ReviewCreateView.as_view(), name='create-review'),
    path('payment/initialize/', PaystackInitializeView.as_view(), name='paystack-init'),
    path('payment/verify/', PaystackVerifyView.as_view(), name='paystack-verify'),
] + router.urls
