import os
from django.core.management.base import BaseCommand

MODEL_NAME_PLACEHOLDER = "MyModel"
APP_NAME_PLACEHOLDER = "myapp"

MODEL_CODE = """from django.db import models

class {model}(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
"""

SERIALIZER_CODE = """from rest_framework import serializers
from .models import {model}

class {model}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {model}
        fields = '__all__'
"""

VIEWS_CODE = """from .models import {model}
from .serializers import {model}Serializer
from ..core.crud import DynamicModelViewSet
from ..core.pagination import CustomPagination
from ..core.permissions import IsAdminRole
from ..core.publicApi import BasePublicAPIView

class {model}ViewSet(DynamicModelViewSet):
    queryset = {model}.objects.all()
    serializer_class = {model}Serializer
    pagination_class = CustomPagination
    permission_classes = [IsAdminRole]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = {model}
        kwargs['serializer_class'] = {model}Serializer
        kwargs['item_name'] = '{model_name}'
        super().__init__(*args, **kwargs)


class {model}PublicView(BasePublicAPIView):
    def __init__(self, *args, **kwargs):
        super().__init__(model={model}, serializer_class={model}Serializer, *args, **kwargs)
"""

URLS_CODE = """from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import {model}ViewSet, {model}PublicView

router = DefaultRouter()
router.register(r'action', {model}ViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('public/', {model}PublicView.as_view(), name='{url_name}-public'),
    path('public/<int:pk>/', {model}PublicView.as_view(), name='{url_name}-public-detail'),
]
"""

APPS_CODE = """from django.apps import AppConfig

class {app_cap}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app}'
"""

ADMIN_CODE = """from django.contrib import admin
from .models import {model}

admin.site.register({model})
"""

INIT_CODE = ""
TESTS_CODE = """from django.test import TestCase

# Write your tests here.
"""

class Command(BaseCommand):
    help = "Create a new Django app with custom CRUD boilerplate using DynamicModelViewSet and BasePublicAPIView"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str, help="Name of the app to create")
        parser.add_argument("--model", type=str, default="MyModel", help="Name of the main model")

    def handle(self, *args, **kwargs):
        app = kwargs["app_name"].lower()
        model = kwargs["model"]
        model_name = model
        base_path = os.path.join("apps", app)

        if os.path.exists(base_path):
            self.stdout.write(self.style.ERROR(f"App '{app}' already exists!"))
            return

        os.makedirs(base_path)

        files_and_content = {
            "__init__.py": INIT_CODE,
            "models.py": MODEL_CODE.format(model=model),
            "serializers.py": SERIALIZER_CODE.format(model=model),
            "views.py": VIEWS_CODE.format(model=model, model_name=model_name),
            "urls.py": URLS_CODE.format(model=model, url_name=model.lower()),
            "apps.py": APPS_CODE.format(app=app, app_cap=app.capitalize()),
            "admin.py": ADMIN_CODE.format(model=model),
            "tests.py": TESTS_CODE,
        }

        for filename, content in files_and_content.items():
            with open(os.path.join(base_path, filename), "w") as f:
                f.write(content)

        self.stdout.write(self.style.SUCCESS(f"✅ App '{app}' with model '{model}' created successfully!"))
