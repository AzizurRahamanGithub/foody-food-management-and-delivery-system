from django.urls import path
from .views import (RiderProfileView, AvailabilityView, RiderDocumentView,
                    BankInfoView, AvailableOrdersView, MyDeliveryTasksView,
                    AcceptTaskView, ConfirmPickupView, MarkDeliveredView,
                    EarningsView, EarningsHistoryView)

urlpatterns = [
    path('profile/', RiderProfileView.as_view(), name='rider-profile'),
    path('availability/', AvailabilityView.as_view(), name='rider-availability'),
    path('documents/', RiderDocumentView.as_view(), name='rider-documents'),
    path('documents/<int:pk>/', RiderDocumentView.as_view(), name='rider-document-delete'),
    path('bank/', BankInfoView.as_view(), name='rider-bank'),
    path('orders/available/', AvailableOrdersView.as_view(), name='rider-available-orders'),
    path('tasks/', MyDeliveryTasksView.as_view(), name='rider-tasks'),
    path('tasks/<int:task_id>/accept/', AcceptTaskView.as_view(), name='rider-accept-task'),
    path('tasks/<int:task_id>/pickup/', ConfirmPickupView.as_view(), name='rider-confirm-pickup'),
    path('tasks/<int:task_id>/deliver/', MarkDeliveredView.as_view(), name='rider-mark-delivered'),
    path('earnings/', EarningsView.as_view(), name='rider-earnings'),
    path('earnings/history/', EarningsHistoryView.as_view(), name='rider-earnings-history'),
]
