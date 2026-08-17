from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (MerchantProfileView, GlobalCategoryListView,
                    MerchantVerifyView, MerchantItemsListView,
                    CategoryViewSet, MenuItemViewSet,
                    AddonGroupViewSet, AddonViewSet,
                    ItemAddonManageView, ItemAddonDeleteView,
                    OfferViewSet,
                    MerchantDashboardView, MerchantOrdersView,
                    MerchantOrderDetailView, MerchantOrderStatusView,
                    MerchantItemReviewsView)

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='merchant-categories')
router.register('items', MenuItemViewSet, basename='merchant-items')
router.register('addon-groups', AddonGroupViewSet, basename='merchant-addon-groups')
router.register('addons', AddonViewSet, basename='merchant-addons')
router.register('offers', OfferViewSet, basename='merchant-offers')

urlpatterns = [
    path('profile/', MerchantProfileView.as_view(), name='merchant-profile'),
    path('verify/', MerchantVerifyView.as_view(), name='merchant-verify'),
    path('global-categories/', GlobalCategoryListView.as_view(),
         name='merchant-global-categories'),
    path('items-list/', MerchantItemsListView.as_view(),
         name='merchant-items-list'),
    path('items/<int:item_id>/addons/',
         ItemAddonManageView.as_view(),
         name='item-addon-manage'),
    path('items/<int:item_id>/addons/<int:group_id>/delete/',
         ItemAddonDeleteView.as_view(),
         name='item-addon-delete'),
    path('dashboard/', MerchantDashboardView.as_view(),
         name='merchant-dashboard'),
    path('orders/', MerchantOrdersView.as_view(), name='merchant-orders'),
    path('orders/<int:pk>/', MerchantOrderDetailView.as_view(),
         name='merchant-order-detail'),
    path('orders/<int:pk>/status/', MerchantOrderStatusView.as_view(),
         name='merchant-order-status'),
    path('item-reviews/', MerchantItemReviewsView.as_view(),
         name='merchant-item-reviews'),
] + router.urls
