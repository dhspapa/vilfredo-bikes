import stripe
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils import translation
from django.utils.translation import gettext as _

from .emails import confirm_reservation_payment
from .models import Reservation


def create_checkout_session(reservation, request):
    stripe.api_key = settings.STRIPE_SECRET_KEY

    success_path = reverse("booking_payment_success", args=[reservation.pk])
    cancel_path = reverse("booking_payment_cancel", args=[reservation.pk])
    success_url = request.build_absolute_uri(success_path)
    cancel_url = request.build_absolute_uri(cancel_path)

    language_code = reservation.guest_language or "en"
    checkout_locale = language_code if language_code in ("en", "el") else "auto"

    with translation.override(language_code):
        rental_name = _("%(bike)s rental") % {"bike": reservation.bike.display_name}
        deposit_name = _("Refundable security deposit")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        customer_email=reservation.email,
        locale=checkout_locale,
        line_items=[
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": rental_name,
                    },
                    "unit_amount": int(reservation.total_price * 100),
                },
                "quantity": 1,
            },
            {
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": deposit_name,
                    },
                    "unit_amount": int(reservation.deposit_amount * 100),
                },
                "quantity": 1,
            },
        ],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "reservation_id": str(reservation.pk),
        },
    )
    return session


def mark_reservation_paid_from_session(session):
    session_id = session.get("id")
    if not session_id:
        return None

    with transaction.atomic():
        reservation = (
            Reservation.objects.select_for_update()
            .filter(stripe_session_id=session_id)
            .first()
        )

        if reservation is None:
            reservation_id = session.get("metadata", {}).get("reservation_id")
            if reservation_id:
                reservation = (
                    Reservation.objects.select_for_update()
                    .filter(pk=reservation_id)
                    .first()
                )

        if reservation is None:
            return None

        update_fields = []
        if not reservation.paid:
            reservation.paid = True
            reservation.paid_at = timezone.now()
            update_fields.extend(["paid", "paid_at"])
        if reservation.stripe_session_id != session_id:
            reservation.stripe_session_id = session_id
            update_fields.append("stripe_session_id")
        if update_fields:
            reservation.save(update_fields=update_fields)

        confirm_reservation_payment(reservation, reservation.guest_language)
        return reservation
