from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.utils.translation import gettext as _
import logging

from .models import Reservation

logger = logging.getLogger(__name__)


def send_payment_confirmation_emails(reservation, language_code):
    if not reservation.paid or reservation.confirmation_email_sent:
        return False

    admin_delivered = _deliver_admin_notification(reservation)

    if not settings.DEFAULT_FROM_EMAIL:
        return False

    guest_sent = _send_guest_confirmation_email(reservation, language_code)

    if guest_sent and admin_delivered:
        reservation.confirmation_email_sent = True
        reservation.save(update_fields=["confirmation_email_sent"])
        return True
    return False


def confirm_reservation_payment(reservation, language_code):
    with transaction.atomic():
        reservation = Reservation.objects.select_for_update().get(pk=reservation.pk)
        if reservation.paid and not reservation.confirmation_email_sent:
            send_payment_confirmation_emails(reservation, language_code)
    return reservation


def complete_paid_reservation_local_fallback(reservation, language_code):
    with transaction.atomic():
        reservation = Reservation.objects.select_for_update().get(pk=reservation.pk)

        if not reservation.paid:
            reservation.paid = True
            reservation.paid_at = timezone.now()
            reservation.guest_language = language_code
            reservation.save(update_fields=["paid", "paid_at", "guest_language"])

        confirm_reservation_payment(reservation, language_code)
    return reservation


def _send_guest_confirmation_email(reservation, language_code):
    with translation.override(language_code):
        subject = _("Your bike rental is confirmed")
        context = {
            "reservation": reservation,
            "LANGUAGE_CODE": language_code,
        }
        text_body = render_to_string("bikes/emails/guest_confirmation.txt", context)
        html_body = render_to_string("bikes/emails/guest_confirmation.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[reservation.email],
    )
    message.attach_alternative(html_body, "text/html")
    return message.send() == 1


def _render_admin_notification_text(reservation):
    return render_to_string(
        "bikes/emails/admin_notification.txt",
        {"reservation": reservation},
    )


def _log_admin_notification(reservation, reason):
    logger.warning(
        "Vilfredo Bikes admin booking notification (%s):\n%s",
        reason,
        _render_admin_notification_text(reservation),
    )


def _deliver_admin_notification(reservation):
    if not settings.ADMIN_NOTIFICATION_EMAIL:
        _log_admin_notification(
            reservation,
            "ADMIN_NOTIFICATION_EMAIL is not set; logging instead of email",
        )
        return True

    if not settings.DEFAULT_FROM_EMAIL:
        _log_admin_notification(
            reservation,
            "DEFAULT_FROM_EMAIL is not set; logging instead of email",
        )
        return True

    sent = _send_admin_notification_email(reservation)
    if not sent:
        _log_admin_notification(
            reservation,
            "admin email could not be sent; logging notification content",
        )
    return sent


def _send_admin_notification_email(reservation):
    subject = f"New paid bike booking – {reservation.booking_reference}"
    context = {"reservation": reservation}
    text_body = _render_admin_notification_text(reservation)
    html_body = render_to_string("bikes/emails/admin_notification.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_NOTIFICATION_EMAIL],
    )
    message.attach_alternative(html_body, "text/html")
    return message.send() == 1
