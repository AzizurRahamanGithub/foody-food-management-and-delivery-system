from django.contrib import admin
from django.urls import path
from .models import DashboardDummy
from .views import AdminDashboardView

@admin.register(DashboardDummy)
class DashboardDummyAdmin(admin.ModelAdmin):
    def get_urls(self):
        custom_view = self.admin_site.admin_view(AdminDashboardView.as_view(model_admin=self))
        urls = super().get_urls()
        return [path("", custom_view, name="admin_dashboard")] + urls


