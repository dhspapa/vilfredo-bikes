from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

import stripe

from .emails import complete_paid_reservation_local_fallback
from .forms import ReservationForm
from .models import Bike, Reservation, Route
from .stripe_utils import create_checkout_session, mark_reservation_paid_from_session

PROPERTY_PAGES = {
    "office-home-2": {
        "property_name": Reservation.PropertyName.OFFICE_HOME_2,
        "landing_name": "property_office_home_2",
        "bike_detail_name": "property_bike_detail_oh2",
    },
    "office-home-3": {
        "property_name": Reservation.PropertyName.OFFICE_HOME_3,
        "landing_name": "property_office_home_3",
        "bike_detail_name": "property_bike_detail_oh3",
    },
}


def _get_property_config(property_slug):
    config = PROPERTY_PAGES.get(property_slug)
    if config is None:
        raise Http404
    return config


def _property_display(property_name):
    return Reservation(property_name=property_name).get_property_name_display()


def home(request):
    bikes = Bike.objects.filter(active=True)
    return render(request, "bikes/home.html", {"bikes": bikes})


def property_landing(request, property_slug):
    config = _get_property_config(property_slug)
    property_name = config["property_name"]
    bikes = Bike.objects.filter(active=True)
    return render(
        request,
        "bikes/property_landing.html",
        {
            "property_slug": property_slug,
            "property_name": property_name,
            "property_display": _property_display(property_name),
            "property_bike_detail_name": config["bike_detail_name"],
            "bikes": bikes,
        },
    )


def bike_detail(request, pk, property_slug=None):
    bike = get_object_or_404(Bike, pk=pk, active=True)
    fixed_property_name = None
    property_landing_url = None
    property_display = None

    if property_slug:
        config = _get_property_config(property_slug)
        fixed_property_name = config["property_name"]
        property_landing_url = reverse(config["landing_name"])
        property_display = _property_display(fixed_property_name)

    form = ReservationForm(request.POST or None, property_name=fixed_property_name)

    if request.method == "POST" and form.is_valid():
        rental_start = form.cleaned_data["rental_start"]
        rental_end = form.cleaned_data["rental_end"]

        if not Reservation.bike_is_available(bike, rental_start, rental_end):
            messages.error(
                request,
                _(
                    "Sorry, this bike is not available for the selected rental dates. "
                    "Please choose different dates or another bike."
                ),
            )
        elif not settings.STRIPE_SECRET_KEY:
            messages.error(request, _("Online payments are not configured yet."))
        else:
            total_price = Reservation.calculate_total_price(bike, rental_start, rental_end)
            reservation = Reservation.objects.create(
                bike=bike,
                full_name=form.cleaned_data["full_name"],
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                booking_reference=form.cleaned_data["booking_reference"],
                property_name=form.cleaned_data["property_name"],
                check_in=form.cleaned_data["check_in"],
                check_out=form.cleaned_data["check_out"],
                rental_start=rental_start,
                rental_end=rental_end,
                total_price=total_price,
                deposit_amount=bike.security_deposit,
                guest_language=request.LANGUAGE_CODE,
                terms_accepted=True,
                paid=False,
            )
            try:
                session = create_checkout_session(reservation, request)
            except stripe.error.StripeError:
                reservation.delete()
                messages.error(
                    request,
                    _("Payment could not be started. Please try again."),
                )
            else:
                reservation.stripe_session_id = session.id
                reservation.save(update_fields=["stripe_session_id"])
                return redirect(session.url, code=303)

    return render(
        request,
        "bikes/bike_detail.html",
        {
            "bike": bike,
            "form": form,
            "property_preselected": fixed_property_name is not None,
            "property_landing_url": property_landing_url,
            "property_display": property_display,
        },
    )


@require_GET
def booking_payment_success(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    total_days = (reservation.rental_end - reservation.rental_start).days + 1

    if settings.LOCAL_STRIPE_SUCCESS_FALLBACK and not reservation.paid:
        reservation = complete_paid_reservation_local_fallback(
            reservation,
            request.LANGUAGE_CODE,
        )
    else:
        reservation.refresh_from_db()

    payment_status = "paid" if reservation.paid else "processing"

    return render(
        request,
        "bikes/booking_payment_success.html",
        {
            "reservation": reservation,
            "total_days": total_days,
            "payment_status": payment_status,
        },
    )


@require_GET
def booking_payment_cancel(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    return render(
        request,
        "bikes/booking_payment_cancel.html",
        {"reservation": reservation},
    )


def routes_page(request):
    routes = Route.objects.filter(active=True)
    return render(request, "bikes/routes.html", {"routes": routes})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponseBadRequest("Webhook secret not configured")

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponseBadRequest("Invalid payload")
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest("Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        mark_reservation_paid_from_session(session)

    return HttpResponse(status=200)
