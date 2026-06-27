"""Acceptance checklist tests — run with: python manage.py test bikes.tests_acceptance"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from bikes.models import Bike, Reservation
from bikes.stripe_utils import mark_reservation_paid_from_session


class AcceptanceChecklistTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.city = Bike.objects.create(
            name="City Bike",
            name_el="Ποδήλατο πόλης",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
            active=True,
        )
        self.electric = Bike.objects.create(
            name="Electric Bike",
            name_el="Ηλεκτρικό ποδήλατο",
            bike_type=Bike.BikeType.ELECTRIC,
            daily_price=Decimal("20.00"),
            active=True,
        )
        self.form_data = {
            "full_name": "Test Guest",
            "email": "test@example.com",
            "phone": "+30",
            "booking_reference": "T-001",
            "property_name": Reservation.PropertyName.OFFICE_HOME_2,
            "check_in": "2026-08-01",
            "check_out": "2026-08-10",
            "rental_start": "2026-08-02",
            "rental_end": "2026-08-04",
            "accept_terms": "on",
        }

    def test_english_homepage_no_greek_leak(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Rent a bike during your stay")
        self.assertNotContains(response, "Νοικιάστε ποδήλατο")

    def test_greek_homepage_no_english_leak_in_body(self):
        with translation.override("el"):
            response = self.client.get(reverse("home"))
            self.assertContains(response, "Νοικιάστε ποδήλατο")
            self.assertNotContains(response, "Rent a bike during your stay")

    def test_greek_property_landing_intro(self):
        with translation.override("el"):
            response = self.client.get(reverse("property_office_home_2"))
            self.assertContains(
                response,
                "Ενοικιάστε ποδήλατο κατά τη διαμονή σας στο Office Home 2.",
            )

    def test_greek_property_page_title_translated(self):
        with translation.override("el"):
            response = self.client.get(reverse("property_office_home_2"))
            title = response.content.decode().split("<title>")[1].split("</title>")[0]
            self.assertIn("Ενοικιάστε ποδήλατο", title)
            self.assertNotIn("Rent a bike during your stay", title)

    def test_invalid_form_does_not_create_reservation(self):
        response = self.client.post(
            reverse("bike_detail", args=[self.city.pk]),
            {"full_name": "", "email": "not-an-email"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_rental_dates_outside_stay_rejected(self):
        response = self.client.post(
            reverse("bike_detail", args=[self.city.pk]),
            {**self.form_data, "rental_start": "2026-07-31"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_greek_form_validation_messages(self):
        with translation.override("el"):
            response = self.client.post(
                reverse("bike_detail", args=[self.city.pk]),
                {"full_name": "", "email": "bad", "accept_terms": ""},
            )
        self.assertContains(response, "Αυτό το πεδίο είναι υποχρεωτικό")
        self.assertNotContains(response, "This field is required.")

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake")
    @patch("bikes.views.create_checkout_session")
    def test_city_deposit_and_total_on_booking(self, mock_stripe):
        mock_stripe.return_value = MagicMock(
            id="cs_acc_1", url="https://checkout.stripe.com/test"
        )
        response = self.client.post(
            reverse("bike_detail", args=[self.city.pk]), self.form_data
        )
        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.total_price, Decimal("30.00"))
        self.assertEqual(reservation.deposit_amount, Decimal("150.00"))
        self.assertEqual(reservation.total_charged, Decimal("180.00"))

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake")
    @patch("bikes.views.create_checkout_session")
    def test_paid_reservation_blocks_overlap(self, mock_stripe):
        mock_stripe.return_value = MagicMock(
            id="cs_acc_1", url="https://checkout.stripe.com/test"
        )
        self.client.post(reverse("bike_detail", args=[self.city.pk]), self.form_data)
        Reservation.objects.update(paid=True)

        mock_stripe.return_value = MagicMock(
            id="cs_acc_2", url="https://checkout.stripe.com/test"
        )
        response = self.client.post(
            reverse("bike_detail", args=[self.city.pk]),
            {**self.form_data, "rental_start": "2026-08-03", "rental_end": "2026-08-05"},
        )
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertContains(
            response,
            "Sorry, this bike is not available for the selected rental dates",
        )

    def test_unpaid_reservation_does_not_block(self):
        Reservation.objects.create(
            bike=self.electric,
            full_name="Unpaid",
            email="u@example.com",
            phone="+30",
            booking_reference="U-1",
            property_name=Reservation.PropertyName.OFFICE_HOME_3,
            check_in=date(2026, 9, 1),
            check_out=date(2026, 9, 10),
            rental_start=date(2026, 9, 2),
            rental_end=date(2026, 9, 4),
            total_price=Decimal("60.00"),
            deposit_amount=Decimal("400.00"),
            stripe_session_id="cs_unpaid_1",
            paid=False,
            terms_accepted=True,
        )
        self.assertTrue(
            Reservation.bike_is_available(self.electric, date(2026, 9, 3), date(2026, 9, 5))
        )

    def test_cancel_page_shows_payment_breakdown(self):
        reservation = Reservation.objects.create(
            bike=self.city,
            full_name="Cancel",
            email="c@example.com",
            phone="+30",
            booking_reference="C-1",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=date(2026, 10, 1),
            check_out=date(2026, 10, 10),
            rental_start=date(2026, 10, 2),
            rental_end=date(2026, 10, 4),
            total_price=Decimal("30.00"),
            deposit_amount=Decimal("150.00"),
            stripe_session_id="cs_cancel_1",
            paid=False,
            terms_accepted=True,
        )
        response = self.client.get(
            reverse("booking_payment_cancel", args=[reservation.pk])
        )
        self.assertContains(response, "180,00 €")
        self.assertFalse(reservation.paid)

    @override_settings(
        LOCAL_STRIPE_SUCCESS_FALLBACK=False,
        DEFAULT_FROM_EMAIL="bikes@test.example",
        ADMIN_NOTIFICATION_EMAIL="owner@test.example",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_webhook_paid_flow_and_no_duplicate_emails(self):
        reservation = Reservation.objects.create(
            bike=self.electric,
            full_name="Webhook",
            email="w@example.com",
            phone="+30",
            booking_reference="W-1",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=date(2026, 11, 1),
            check_out=date(2026, 11, 10),
            rental_start=date(2026, 11, 2),
            rental_end=date(2026, 11, 4),
            total_price=Decimal("60.00"),
            deposit_amount=Decimal("400.00"),
            stripe_session_id="cs_webhook_1",
            guest_language="en",
            paid=False,
            terms_accepted=True,
        )
        session = {"id": "cs_webhook_1", "metadata": {"reservation_id": str(reservation.pk)}}
        mark_reservation_paid_from_session(session)
        mark_reservation_paid_from_session(session)
        self.assertEqual(len(mail.outbox), 2)

        response = self.client.get(
            reverse("booking_payment_success", args=[reservation.pk])
        )
        self.assertContains(response, "Booking confirmed")
        self.assertContains(response, "460,00 €")

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake")
    @patch("bikes.stripe_utils.stripe.checkout.Session.create")
    def test_stripe_checkout_line_items_and_locale(self, mock_create):
        mock_create.return_value = MagicMock(
            id="cs_locale", url="https://checkout.stripe.com/test"
        )
        with translation.override("el"):
            self.client.post(
                reverse("property_bike_detail_oh2", args=[self.city.pk]),
                self.form_data,
            )
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.guest_language, "el")
        kwargs = mock_create.call_args.kwargs
        self.assertEqual(kwargs["locale"], "el")
        self.assertEqual(len(kwargs["line_items"]), 2)
        self.assertEqual(kwargs["line_items"][0]["price_data"]["unit_amount"], 3000)
        self.assertEqual(kwargs["line_items"][1]["price_data"]["unit_amount"], 15000)

    def test_admin_shows_payment_amounts(self):
        reservation = Reservation.objects.create(
            bike=self.electric,
            full_name="Admin",
            email="a@example.com",
            phone="+30",
            booking_reference="A-1",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=date(2026, 12, 1),
            check_out=date(2026, 12, 10),
            rental_start=date(2026, 12, 2),
            rental_end=date(2026, 12, 4),
            total_price=Decimal("60.00"),
            deposit_amount=Decimal("400.00"),
            stripe_session_id="cs_admin_1",
            paid=True,
            terms_accepted=True,
        )
        User.objects.create_superuser("accadmin", "a@test.example", "pass")
        self.client.login(username="accadmin", password="pass")
        response = self.client.get(
            reverse("admin:bikes_reservation_change", args=[reservation.pk])
        )
        self.assertContains(response, "460,00 €")
        self.assertContains(response, "Rental price")
