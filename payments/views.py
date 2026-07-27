from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from courses.models import Course
from .models import Order
from .utils import generate_signature, verify_signature


@login_required
def initiate_payment_view(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug, is_published=True)

    # Guard clauses first — fail fast on states that shouldn't reach payment at all.
    if course.price == 0:
        messages.info(request, "This course is free — enroll directly.")
        return redirect('courses:course_detail', slug=course.slug)

    if course.enrollments.filter(student=request.user).exists():
        messages.info(request, "You're already enrolled in this course.")
        return redirect('courses:course_detail', slug=course.slug)

    amount = course.price
    tax_amount = Decimal('0')
    total_amount = amount + tax_amount

    order = Order.objects.create(
        student=request.user,
        course=course,
        amount=amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )

    payment_data = {
        "amount": str(amount),
        "tax_amount": str(tax_amount),
        "total_amount": str(total_amount),
        "transaction_uuid": str(order.transaction_uuid),
        "product_code": settings.ESEWA_PRODUCT_CODE,
        "product_service_charge": "0",
        "product_delivery_charge": "0",
        "success_url": request.build_absolute_uri('/payments/success/'),
        "failure_url": request.build_absolute_uri('/payments/failure/'),
        "signed_field_names": "total_amount,transaction_uuid,product_code",
    }
    payment_data["signature"] = generate_signature(payment_data, settings.ESEWA_SECRET_KEY)

    return render(request, 'payments/redirect_to_esewa.html', {
        'payment_data': payment_data,
        'esewa_form_url': settings.ESEWA_FORM_URL,
    })