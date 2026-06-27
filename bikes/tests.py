from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from bikes.models import Bike, Reservation, Route


class AvailabilityTests(TestCase):
    def setUp(self):
        self.bike = Bike.objects.create(
            name="City Bike",
            name_el="Ποδήλατο πόλης",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
        )

    def _reservation(self, start, end, paid=True):
        return Reservation.objects.create(
            bike=self.bike,
            full_name="Guest",
            email="guest@example.com",
            phone="+30",
            booking_reference="TEST-001",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=start,
            check_out=end,
            rental_start=start,
            rental_end=end,
            total_price=Decimal("10.00"),
            deposit_amount=self.bike.security_deposit,
            stripe_session_id=f"cs_test_{start.isoformat()}_{end.isoformat()}",
            terms_accepted=True,
            paid=paid,
        )

    def test_available_when_no_overlap(self):
        self._reservation(date(2026, 7, 1), date(2026, 7, 3))
        available = Reservation.bike_is_available(self.bike, date(2026, 7, 5), date(2026, 7, 7))
        self.assertTrue(available)

    def test_unavailable_when_overlap(self):
        self._reservation(date(2026, 7, 1), date(2026, 7, 5))
        available = Reservation.bike_is_available(self.bike, date(2026, 7, 4), date(2026, 7, 6))
        self.assertFalse(available)

    def test_unpaid_reservation_does_not_block(self):
        self._reservation(date(2026, 7, 1), date(2026, 7, 5), paid=False)
        available = Reservation.bike_is_available(self.bike, date(2026, 7, 4), date(2026, 7, 6))
        self.assertTrue(available)

    def test_calculate_total_price(self):
        total = Reservation.calculate_total_price(self.bike, date(2026, 7, 1), date(2026, 7, 3))
        self.assertEqual(total, Decimal("30.00"))


class BookingFlowTests(TestCase):
    def setUp(self):
        self.bike = Bike.objects.create(
            name="Electric Bike",
            name_el="Ηλεκτρικό ποδήλατο",
            bike_type=Bike.BikeType.ELECTRIC,
            daily_price=Decimal("20.00"),
            active=True,
        )

    def _form_data(self, **overrides):
        data = {
            "full_name": "Jane Guest",
            "email": "jane@example.com",
            "phone": "+30 6900000000",
            "booking_reference": "OH2-12345",
            "property_name": Reservation.PropertyName.OFFICE_HOME_2,
            "check_in": "2026-07-01",
            "check_out": "2026-07-10",
            "rental_start": "2026-07-02",
            "rental_end": "2026-07-04",
            "accept_terms": "on",
        }
        data.update(overrides)
        return data

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake")
    @patch("bikes.views.create_checkout_session")
    def test_successful_booking_creates_unpaid_reservation_and_redirects_to_stripe(
        self, mock_create_checkout_session
    ):
        mock_create_checkout_session.return_value = MagicMock(
            id="cs_test_123",
            url="https://checkout.stripe.com/test",
        )
        response = self.client.post(
            reverse("bike_detail", args=[self.bike.pk]),
            self._form_data(),
        )
        reservation = Reservation.objects.get()
        self.assertFalse(reservation.paid)
        self.assertTrue(reservation.terms_accepted)
        self.assertEqual(reservation.booking_reference, "OH2-12345")
        self.assertEqual(reservation.total_price, Decimal("60.00"))
        self.assertEqual(reservation.deposit_amount, Decimal("400.00"))
        self.assertEqual(reservation.total_charged, Decimal("460.00"))
        self.assertEqual(reservation.stripe_session_id, "cs_test_123")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://checkout.stripe.com/test")
        mock_create_checkout_session.assert_called_once()

    def test_booking_requires_accept_terms(self):
        response = self.client.post(
            reverse("bike_detail", args=[self.bike.pk]),
            self._form_data(accept_terms=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 0)
        self.assertContains(response, "You must accept the rental terms to continue.")

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake")
    @patch("bikes.views.create_checkout_session")
    def test_unavailable_bike_shows_error(self, mock_create_checkout_session):
        Reservation.objects.create(
            bike=self.bike,
            full_name="Other Guest",
            email="other@example.com",
            phone="+30",
            booking_reference="OH3-99999",
            property_name=Reservation.PropertyName.OFFICE_HOME_3,
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 10),
            rental_start=date(2026, 7, 2),
            rental_end=date(2026, 7, 5),
            total_price=Decimal("80.00"),
            deposit_amount=Decimal("400.00"),
            stripe_session_id="cs_test_overlap",
            terms_accepted=True,
            paid=True,
        )
        response = self.client.post(
            reverse("bike_detail", args=[self.bike.pk]),
            self._form_data(rental_start="2026-07-04", rental_end="2026-07-06"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertContains(
            response,
            "Sorry, this bike is not available for the selected rental dates",
        )
        mock_create_checkout_session.assert_not_called()

    def test_rental_start_before_check_in_is_rejected(self):
        response = self.client.post(
            reverse("bike_detail", args=[self.bike.pk]),
            self._form_data(rental_start="2026-06-30"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rental start must be on or after check-in")
        self.assertEqual(Reservation.objects.count(), 0)


class StripePaymentTests(TestCase):
    def setUp(self):
        self.bike = Bike.objects.create(
            name="Electric Bike",
            name_el="Ηλεκτρικό ποδήλατο",
            bike_type=Bike.BikeType.ELECTRIC,
            daily_price=Decimal("20.00"),
            active=True,
        )
        self.reservation = Reservation.objects.create(
            bike=self.bike,
            full_name="Jane Guest",
            email="jane@example.com",
            phone="+30",
            booking_reference="OH2-12345",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 10),
            rental_start=date(2026, 7, 2),
            rental_end=date(2026, 7, 4),
            total_price=Decimal("60.00"),
            deposit_amount=Decimal("400.00"),
            stripe_session_id="cs_test_123",
            guest_language="en",
            terms_accepted=True,
            paid=False,
        )

    @override_settings(LOCAL_STRIPE_SUCCESS_FALLBACK=False)
    def test_success_page_without_fallback_shows_processing(self):
        response = self.client.get(
            reverse("booking_payment_success", args=[self.reservation.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.reservation.refresh_from_db()
        self.assertFalse(self.reservation.paid)
        self.assertContains(response, "Payment processing")

    @override_settings(
        LOCAL_STRIPE_SUCCESS_FALLBACK=True,
        DEFAULT_FROM_EMAIL="bikes@test.example",
        ADMIN_NOTIFICATION_EMAIL="owner@test.example",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_success_page_with_fallback_marks_paid(self):
        response = self.client.get(
            reverse("booking_payment_success", args=[self.reservation.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.paid)
        self.assertIsNotNone(self.reservation.paid_at)
        self.assertContains(response, "Booking confirmed")
        self.assertContains(response, "Payment completed successfully")

    @override_settings(
        LOCAL_STRIPE_SUCCESS_FALLBACK=True,
        DEFAULT_FROM_EMAIL="bikes@test.example",
        ADMIN_NOTIFICATION_EMAIL="owner@test.example",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_success_page_fallback_sends_emails_once(self):
        from django.core import mail

        url = reverse("booking_payment_success", args=[self.reservation.pk])
        self.client.get(url)
        self.client.get(url)
        self.reservation.refresh_from_db()

        self.assertTrue(self.reservation.confirmation_email_sent)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(
        DEFAULT_FROM_EMAIL="bikes@test.example",
        ADMIN_NOTIFICATION_EMAIL="owner@test.example",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_webhook_marks_reservation_paid_and_sends_emails(self):
        from django.core import mail

        from bikes.stripe_utils import mark_reservation_paid_from_session

        session = {
            "id": "cs_test_123",
            "metadata": {"reservation_id": str(self.reservation.pk)},
        }
        mark_reservation_paid_from_session(session)
        self.reservation.refresh_from_db()

        self.assertTrue(self.reservation.paid)
        self.assertIsNotNone(self.reservation.paid_at)
        self.assertTrue(self.reservation.confirmation_email_sent)
        self.assertEqual(len(mail.outbox), 2)

        mark_reservation_paid_from_session(session)
        self.assertEqual(len(mail.outbox), 2)

    @override_settings(
        DEFAULT_FROM_EMAIL="bikes@test.example",
        ADMIN_NOTIFICATION_EMAIL="owner@test.example",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_webhook_guest_email_uses_stored_language(self):
        from django.core import mail

        from bikes.stripe_utils import mark_reservation_paid_from_session

        self.reservation.guest_language = "el"
        self.reservation.save(update_fields=["guest_language"])

        mark_reservation_paid_from_session(
            {"id": "cs_test_123", "metadata": {"reservation_id": str(self.reservation.pk)}}
        )

        self.assertIn("Η ενοικίαση ποδηλάτου σας επιβεβαιώθηκε", mail.outbox[0].subject)

    def test_cancel_page_keeps_reservation_unpaid(self):
        response = self.client.get(
            reverse("booking_payment_cancel", args=[self.reservation.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.reservation.refresh_from_db()
        self.assertFalse(self.reservation.paid)
        self.assertFalse(self.reservation.confirmation_email_sent)
        self.assertContains(response, "Payment was cancelled")


class BilingualTests(TestCase):
    def setUp(self):
        self.bike = Bike.objects.create(
            name="Electric Bike",
            name_el="Ηλεκτρικό ποδήλατο",
            bike_type=Bike.BikeType.ELECTRIC,
            daily_price=Decimal("20.00"),
            active=True,
        )
        Route.objects.create(
            title="Thessaloniki Waterfront",
            title_el="Παραλία Θεσσαλονίκης",
            duration="45 min",
            duration_el="45 λεπτά",
            difficulty=Route.Difficulty.EASY,
            description="A relaxed ride along the promenade.",
            description_el="Ήρεμη βόλτα κατά μήκος του παραλιακού.",
            active=True,
        )

    def test_homepage_english(self):
        with translation.override("en"):
            response = self.client.get(reverse("home"))
            self.assertContains(response, "Rent a bike during your stay")
            self.assertContains(response, "Electric Bike")
            self.assertNotContains(response, "Νοικιάστε ποδήλατο")

    def test_homepage_greek(self):
        with translation.override("el"):
            response = self.client.get(reverse("home"))
            self.assertContains(response, "Νοικιάστε ποδήλατο κατά τη διάρκεια της διαμονής σας")
            self.assertContains(response, "Ηλεκτρικό ποδήλατο")
            self.assertNotContains(response, "Rent a bike during your stay")

    def test_routes_page_greek(self):
        with translation.override("el"):
            response = self.client.get(reverse("routes"))
            self.assertContains(response, "Παραλία Θεσσαλονίκης")
            self.assertContains(response, "45 λεπτά")
            self.assertNotContains(response, "Thessaloniki Waterfront")

    def test_validation_message_greek(self):
        with translation.override("el"):
            response = self.client.post(
                reverse("bike_detail", args=[self.bike.pk]),
                {
                    "full_name": "Jane Guest",
                    "email": "jane@example.com",
                    "phone": "+30",
                    "booking_reference": "OH2-1",
                    "property_name": Reservation.PropertyName.OFFICE_HOME_2,
                    "check_in": "2026-07-01",
                    "check_out": "2026-07-10",
                    "rental_start": "2026-06-30",
                    "rental_end": "2026-07-04",
                },
            )
            self.assertContains(response, "Η έναρξη ενοικίασης πρέπει να είναι")


class SecurityDepositTests(TestCase):
    def test_city_bike_deposit_is_150(self):
        bike = Bike.objects.create(
            name="City Bike",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
        )
        self.assertEqual(bike.security_deposit, Decimal("150.00"))

    def test_electric_bike_deposit_is_400(self):
        bike = Bike.objects.create(
            name="Electric Bike",
            bike_type=Bike.BikeType.ELECTRIC,
            daily_price=Decimal("20.00"),
        )
        self.assertEqual(bike.security_deposit, Decimal("400.00"))

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake")
    @patch("bikes.stripe_utils.stripe.checkout.Session.create")
    def test_stripe_checkout_charges_rental_and_deposit(self, mock_create):
        bike = Bike.objects.create(
            name="City Bike",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
            active=True,
        )
        mock_create.return_value = MagicMock(
            id="cs_test_deposit",
            url="https://checkout.stripe.com/test",
        )
        response = self.client.post(
            reverse("bike_detail", args=[bike.pk]),
            {
                "full_name": "Jane Guest",
                "email": "jane@example.com",
                "phone": "+30",
                "booking_reference": "OH2-1",
                "property_name": Reservation.PropertyName.OFFICE_HOME_2,
                "check_in": "2026-07-01",
                "check_out": "2026-07-10",
                "rental_start": "2026-07-02",
                "rental_end": "2026-07-04",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        reservation = Reservation.objects.get()
        self.assertEqual(reservation.deposit_amount, Decimal("150.00"))
        self.assertEqual(reservation.total_charged, Decimal("180.00"))

        line_items = mock_create.call_args.kwargs["line_items"]
        self.assertEqual(len(line_items), 2)
        self.assertEqual(line_items[0]["price_data"]["unit_amount"], 3000)
        self.assertEqual(line_items[1]["price_data"]["unit_amount"], 15000)

    def test_bike_detail_shows_deposit_notice_in_greek(self):
        bike = Bike.objects.create(
            name="City Bike",
            name_el="Ποδήλατο πόλης",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
            active=True,
        )
        with translation.override("el"):
            response = self.client.get(reverse("bike_detail", args=[bike.pk]))
            self.assertContains(response, "150,00 €")
            self.assertContains(
                response,
                "Η εγγύηση επιστρέφεται μετά την επιστροφή του ποδηλάτου χωρίς φθορά, απώλεια ή κλοπή.",
            )

    def test_success_page_shows_payment_breakdown(self):
        bike = Bike.objects.create(
            name="Electric Bike",
            bike_type=Bike.BikeType.ELECTRIC,
            daily_price=Decimal("20.00"),
        )
        reservation = Reservation.objects.create(
            bike=bike,
            full_name="Jane Guest",
            email="jane@example.com",
            phone="+30",
            booking_reference="OH2-1",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 10),
            rental_start=date(2026, 7, 2),
            rental_end=date(2026, 7, 4),
            total_price=Decimal("60.00"),
            deposit_amount=Decimal("400.00"),
            stripe_session_id="cs_test_breakdown",
            terms_accepted=True,
            paid=False,
        )
        response = self.client.get(reverse("booking_payment_success", args=[reservation.pk]))
        self.assertContains(response, "Rental price")
        self.assertContains(response, "Security deposit")
        self.assertContains(response, "Total charged today")
        self.assertContains(response, "460,00 €")


class ReservationAdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.bike = Bike.objects.create(
            name="City Bike",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
        )
        self.reservation = Reservation.objects.create(
            bike=self.bike,
            full_name="Jane Guest",
            email="jane@example.com",
            phone="+30 6900000000",
            booking_reference="OH2-ADMIN",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 10),
            rental_start=date(2026, 7, 2),
            rental_end=date(2026, 7, 4),
            total_price=Decimal("30.00"),
            deposit_amount=Decimal("150.00"),
            stripe_session_id="cs_test_admin",
            terms_accepted=True,
            paid=True,
        )
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.example",
            password="pass",
        )
        self.client.login(username="admin", password="pass")

    def test_admin_changelist_shows_return_and_deposit_columns(self):
        response = self.client.get(reverse("admin:bikes_reservation_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OH2-ADMIN")
        self.assertContains(response, "Deposit refunded")

    def test_admin_detail_shows_payment_amounts(self):
        response = self.client.get(
            reverse("admin:bikes_reservation_change", args=[self.reservation.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "30,00 €")
        self.assertContains(response, "150,00 €")
        self.assertContains(response, "180,00 €")

    def test_mark_returned_action(self):
        url = reverse("admin:bikes_reservation_changelist")
        response = self.client.post(
            url,
            {
                "action": "mark_reservations_returned",
                "_selected_action": [self.reservation.pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.reservation.refresh_from_db()
        self.assertIsNotNone(self.reservation.returned_at)

    def test_mark_returned_action_is_idempotent(self):
        self.reservation.returned_at = timezone.now()
        self.reservation.save(update_fields=["returned_at"])
        original = self.reservation.returned_at

        self.client.post(
            reverse("admin:bikes_reservation_changelist"),
            {
                "action": "mark_reservations_returned",
                "_selected_action": [self.reservation.pk],
            },
        )
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.returned_at, original)

    def test_mark_deposit_refunded_action(self):
        self.client.post(
            reverse("admin:bikes_reservation_changelist"),
            {
                "action": "mark_deposits_refunded",
                "_selected_action": [self.reservation.pk],
            },
        )
        self.reservation.refresh_from_db()
        self.assertTrue(self.reservation.deposit_refunded)
        self.assertIsNotNone(self.reservation.deposit_refunded_at)

    def test_mark_deposit_refunded_action_is_idempotent(self):
        self.reservation.deposit_refunded = True
        self.reservation.deposit_refunded_at = timezone.now()
        self.reservation.save(update_fields=["deposit_refunded", "deposit_refunded_at"])
        original = self.reservation.deposit_refunded_at

        self.client.post(
            reverse("admin:bikes_reservation_changelist"),
            {
                "action": "mark_deposits_refunded",
                "_selected_action": [self.reservation.pk],
            },
        )
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.deposit_refunded_at, original)


class PickupReturnInstructionsTests(TestCase):
    def setUp(self):
        self.bike = Bike.objects.create(
            name="City Bike",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
        )
        self.reservation = Reservation.objects.create(
            bike=self.bike,
            full_name="Jane Guest",
            email="jane@example.com",
            phone="+30",
            booking_reference="OH2-PICKUP",
            property_name=Reservation.PropertyName.OFFICE_HOME_2,
            check_in=date(2026, 7, 1),
            check_out=date(2026, 7, 10),
            rental_start=date(2026, 7, 2),
            rental_end=date(2026, 7, 4),
            total_price=Decimal("30.00"),
            deposit_amount=Decimal("150.00"),
            stripe_session_id="cs_test_pickup",
            terms_accepted=True,
            paid=False,
        )

    @override_settings(LOCAL_STRIPE_SUCCESS_FALLBACK=True)
    def test_paid_success_page_shows_pickup_instructions_in_english(self):
        response = self.client.get(
            reverse("booking_payment_success", args=[self.reservation.pk])
        )
        self.assertContains(response, "Pickup instructions:")
        self.assertContains(
            response,
            "The bike is available at your accommodation from the first rental day.",
        )
        self.assertContains(response, "Return instructions:")
        self.assertContains(
            response,
            "Late return may affect the refundable security deposit.",
        )

    @override_settings(LOCAL_STRIPE_SUCCESS_FALLBACK=False)
    def test_processing_success_page_hides_pickup_instructions(self):
        response = self.client.get(
            reverse("booking_payment_success", args=[self.reservation.pk])
        )
        self.assertNotContains(response, "Pickup instructions:")
        self.assertNotContains(response, "Return instructions:")

    @override_settings(LOCAL_STRIPE_SUCCESS_FALLBACK=True)
    def test_paid_success_page_shows_pickup_instructions_in_greek(self):
        with translation.override("el"):
            response = self.client.get(
                reverse("booking_payment_success", args=[self.reservation.pk])
            )
            self.assertContains(response, "Οδηγίες παραλαβής:")
            self.assertContains(
                response,
                "Το ποδήλατο είναι διαθέσιμο στο κατάλυμά σας από την πρώτη ημέρα ενοικίασης.",
            )
            self.assertContains(response, "Οδηγίες επιστροφής:")
            self.assertNotContains(response, "Pickup instructions:")

    @override_settings(
        DEFAULT_FROM_EMAIL="bikes@test.example",
        ADMIN_NOTIFICATION_EMAIL="owner@test.example",
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    def test_guest_email_includes_pickup_instructions_in_stored_language(self):
        from django.core import mail

        from bikes.stripe_utils import mark_reservation_paid_from_session

        self.reservation.guest_language = "el"
        self.reservation.save(update_fields=["guest_language"])

        mark_reservation_paid_from_session(
            {"id": "cs_test_pickup", "metadata": {"reservation_id": str(self.reservation.pk)}}
        )

        guest_email = mail.outbox[0]
        self.assertIn("Οδηγίες παραλαβής:", guest_email.body)
        self.assertIn("Οδηγίες επιστροφής:", guest_email.body)
        self.assertNotIn("Pickup instructions:", guest_email.body)


class PropertyLandingTests(TestCase):
    def setUp(self):
        self.bike = Bike.objects.create(
            name="City Bike",
            name_el="Ποδήλατο πόλης",
            bike_type=Bike.BikeType.CITY,
            daily_price=Decimal("10.00"),
            active=True,
        )

    def test_office_home_2_landing_english(self):
        response = self.client.get(reverse("property_office_home_2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rent a bike during your stay at Office Home 2.")
        self.assertContains(response, "Choose a bike")
        self.assertContains(response, "Book now")

    def test_office_home_3_landing_greek(self):
        with translation.override("el"):
            response = self.client.get(reverse("property_office_home_3"))
            self.assertEqual(response.status_code, 200)
            self.assertContains(
                response,
                "Ενοικιάστε ποδήλατο κατά τη διαμονή σας στο Office Home 3.",
            )
            self.assertContains(response, "Επιλέξτε ποδήλατο")
            self.assertContains(response, "Κράτηση")

    def test_property_bike_detail_preselects_property(self):
        response = self.client.get(
            reverse("property_bike_detail_oh2", args=[self.bike.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="property_name"')
        self.assertContains(response, 'value="Office Home 2"')
        self.assertNotContains(response, '<select name="property_name"')

    @override_settings(STRIPE_SECRET_KEY="sk_test_fake")
    @patch("bikes.views.create_checkout_session")
    def test_property_booking_uses_preselected_property(self, mock_create_checkout_session):
        mock_create_checkout_session.return_value = MagicMock(
            id="cs_test_property",
            url="https://checkout.stripe.com/test",
        )
        response = self.client.post(
            reverse("property_bike_detail_oh3", args=[self.bike.pk]),
            {
                "full_name": "Jane Guest",
                "email": "jane@example.com",
                "phone": "+30",
                "booking_reference": "OH3-1",
                "property_name": Reservation.PropertyName.OFFICE_HOME_2,
                "check_in": "2026-07-01",
                "check_out": "2026-07-10",
                "rental_start": "2026-07-02",
                "rental_end": "2026-07-04",
                "accept_terms": "on",
            },
        )
        reservation = Reservation.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(reservation.property_name, Reservation.PropertyName.OFFICE_HOME_3)

    def test_unknown_property_slug_returns_404(self):
        response = self.client.get("/en/unknown-property/")
        self.assertEqual(response.status_code, 404)



