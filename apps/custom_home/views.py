from django.views.generic import TemplateView
from unfold.views import UnfoldModelAdminViewMixin
from apps.auths.models import CustomUser
from django.db.models import Sum
from apps.notification.models import Notification
import json
from datetime import datetime, timedelta
from django.core.paginator import Paginator

class AdminDashboardView(UnfoldModelAdminViewMixin, TemplateView):
    template_name = "dashboard.html"
    title = "Admin Dashboard"
    permission_required = ()  # allows all staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cards numbers
        # context["total_bookings"] = Booking.objects.filter(booking_status="completed").count()
        # context["total_users"] = CustomUser.objects.filter(role="user").count()
        # context["total_earning"] = (
        #     Booking.objects.filter(booking_status="completed").aggregate(total=Sum("final_total"))["total"] or 0
        # )
        # context["total_rental"] = Booking.objects.filter(shop_type__isnull=False).count()

        # # Tables
        # context["completed_bookings"] = Booking.objects.filter(booking_status="completed").order_by("-created_at")
        
        # context["users_table"] = CustomUser.objects.filter(role="user").order_by("-created_at")
        
        # context["rentals_table"] = Booking.objects.filter(booking_status="rent started").order_by("-created_at")
        
        # context["payments_table"] = Payment.objects.select_related("booking").order_by("-created_at")
        
        # context["notifications_table"] = Notification.objects.all()
        
         # --- Notifications with pagination ---
        notifications = Notification.objects.all().order_by('-created_at')
        paginator = Paginator(notifications, 5)  # 5 notifications per page
        page = self.request.GET.get('page')
        context['notifications_table'] = paginator.get_page(page)
       


        return context

