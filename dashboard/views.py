from django.db.models import Sum, Count
from django.utils import timezone
from django.views.generic import TemplateView

from .mixins import AdminRequiredMixin
from courses.models import Course
from accounts.models import CustomUser
from payments.models import Order


class DashboardOverviewView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_students'] = CustomUser.objects.filter(role='student').count()
        context['total_instructors'] = CustomUser.objects.filter(role='instructor').count()
        context['total_courses'] = Course.objects.count()
        context['published_courses'] = Course.objects.filter(is_published=True).count()

        # Revenue: only count COMPLETED orders. A pending or failed Order
        # was never actually paid, so summing all Orders would overstate
        # revenue — this is the same "don't trust unverified state" instinct
        # as the ownership/signature checks in Phase 5.
        revenue_data = Order.objects.filter(status='completed').aggregate(
            total=Sum('total_amount')
        )
        context['total_revenue'] = revenue_data['total'] or 0

        context['pending_orders'] = Order.objects.filter(status='pending').count()
        context['completed_orders'] = Order.objects.filter(status='completed').count()

        return context