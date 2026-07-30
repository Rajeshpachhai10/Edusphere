from django.db.models import Sum, Count
from django.views.generic import TemplateView, ListView

from .mixins import AdminRequiredMixin
from accounts.models import CustomUser
from courses.models import Course
from payments.models import Order


class DashboardOverviewView(AdminRequiredMixin, TemplateView):
    """
    Landing page of the admin dashboard — aggregate platform stats.
    Admin-only, enforced by AdminRequiredMixin.
    """
    template_name = 'dashboard/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_students'] = CustomUser.objects.filter(role='student').count()
        context['total_instructors'] = CustomUser.objects.filter(role='instructor').count()
        context['total_courses'] = Course.objects.count()
        context['published_courses'] = Course.objects.filter(is_published=True).count()

        # Only completed Orders represent verified, actually-collected revenue.
        # A pending or failed Order is a claim, not a fact — same "don't trust
        # unverified state" reasoning as Phase 5's signature/ownership checks.
        revenue_data = Order.objects.filter(status='completed').aggregate(
            total=Sum('total_amount')
        )
        context['total_revenue'] = revenue_data['total'] or 0

        context['pending_orders'] = Order.objects.filter(status='pending').count()
        context['completed_orders'] = Order.objects.filter(status='completed').count()

        return context


class CourseOversightView(AdminRequiredMixin, ListView):
    """
    Admin-only cross-instructor course list: search, publish-status filter,
    and per-course enrollment counts.
    """
    model = Course
    template_name = 'dashboard/course_oversight.html'
    context_object_name = 'courses'
    paginate_by = 15

    def get_queryset(self):
        # select_related('instructor') joins the instructor row in the same
        # query (avoids N+1). annotate(Count('enrollments')) computes each
        # course's enrollment count at the DB level — 'enrollments' matches
        # Enrollment.course's related_name, not the default singular lookup.
        queryset = Course.objects.select_related('instructor').annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-created_at')

        status = self.request.GET.get('status')
        if status == 'published':
            queryset = queryset.filter(is_published=True)
        elif status == 'unpublished':
            queryset = queryset.filter(is_published=False)

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(title__icontains=search)

        return queryset

    def get_context_data(self, **kwargs):
        # Preserve current filter/search selections so the template can
        # re-select them in the filter UI, and so pagination links don't
        # silently drop the active filter when moving between pages.
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['current_search'] = self.request.GET.get('q', '')
        return context