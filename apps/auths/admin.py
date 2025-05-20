from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, HelpUsImprove, ContactMessage
from django.utils import timezone

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _



class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('full_name','first_name', 'last_name', 'role', 'phone_number', 'address', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'is_active')}
        ),
    )

    def get_queryset(self, request):
        """Show all users normally"""
        return super().get_queryset(request)

    # --- Custom Admin URLs ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("admins/", self.admin_site.admin_view(self.view_admins), name="customuser_admins"),
            path("staff/", self.admin_site.admin_view(self.view_staff), name="customuser_staff"),
            path("users/", self.admin_site.admin_view(self.view_users), name="customuser_users"),
        ]
        return custom_urls + urls

    def view_admins(self, request):
        qs = self.model.objects.filter(is_superuser=True)
        context = dict(
            self.admin_site.each_context(request),
            title=_("Admin Users"),
            users=qs,
            section="Admins",
        )
        return render(request, "customuser_list.html", context)

    def view_staff(self, request):
        qs = self.model.objects.filter(is_staff=True, is_superuser=False)
        context = dict(
            self.admin_site.each_context(request),
            title=_("Staff Members"),
            users=qs,
            section="Staff",
        )
        return render(request, "customuser_list.html", context)

    def view_users(self, request):
        qs = self.model.objects.filter(is_staff=False, is_superuser=False)
        context = dict(
            self.admin_site.each_context(request),
            title=_("Regular Users"),
            users=qs,
            section="Users",
        )
        return render(request, "customuser_list.html", context)

# Register models
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "subject", "created_at")
    search_fields = ("full_name", "email", "subject", "message")
    list_filter = ("created_at",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    list_per_page = 25

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "User Contact Messages"


# ---------------- Help Us Improve ---------------- #
@admin.register(HelpUsImprove)
class HelpUsImproveAdmin(admin.ModelAdmin):
    list_display = ( "user", "short_message")
    search_fields = ("user__email", "improve_message")
    ordering = ("-id",)
    list_per_page = 25

    def short_message(self, obj):
        """Show first 50 chars of feedback message"""
        return (obj.improve_message[:50] + "...") if len(obj.improve_message) > 50 else obj.improve_message
    short_message.short_description = "Feedback Message"

    class Meta:
        verbose_name = "Help Us Improve"
        verbose_name_plural = "User Feedback"

# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'otp', 'otp_created_at', 'reset_token', 'reset_token_expires')
#     search_fields = ('user__email', 'user__username')




