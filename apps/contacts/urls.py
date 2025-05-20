
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ContactCreateView,RecaptchaVerifyAPIView,ContactViewSetList,ContractTest

router = DefaultRouter()
router.register(r'list', ContactViewSetList)

urlpatterns = [
    path('', include(router.urls)),
    path('send-message/', ContactCreateView.as_view(), name='send-message'),
    path('recaptcha/', RecaptchaVerifyAPIView.as_view(), name='recaptcha'),
     path('create/', ContractTest.as_view(), name='contract-create'),
]