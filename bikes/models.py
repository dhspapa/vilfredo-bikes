from decimal import Decimal, InvalidOperation

from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _


def format_euro(value):
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        return str(value)
    return f"{amount:.2f}".replace(".", ",") + " €"


class Bike(models.Model):
    class BikeType(models.TextChoices):
        ELECTRIC = "electric", _("Electric")
        CITY = "city", _("City")

    CITY_SECURITY_DEPOSIT = Decimal("150.00")
    ELECTRIC_SECURITY_DEPOSIT = Decimal("400.00")

    name = models.CharField(max_length=100)
    name_el = models.CharField(max_length=100, blank=True, default="")
    bike_type = models.CharField(max_length=20, choices=BikeType.choices)
    daily_price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(
        upload_to="bikes/",
        blank=True,
        null=True,
        help_text="Optional photo shown on the homepage and booking page.",
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        if get_language() == "el" and self.name_el:
            return self.name_el
        return self.name

    @property
    def security_deposit(self):
        if self.bike_type == self.BikeType.CITY:
            return self.CITY_SECURITY_DEPOSIT
        return self.ELECTRIC_SECURITY_DEPOSIT


class Reservation(models.Model):
    class PropertyName(models.TextChoices):
        OFFICE_HOME_2 = "Office Home 2", _("Office Home 2")
        OFFICE_HOME_3 = "Office Home 3", _("Office Home 3")

    bike = models.ForeignKey(Bike, on_delete=models.PROTECT, related_name="reservations")
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    booking_reference = models.CharField(max_length=100, default="")
    property_name = models.CharField(max_length=50, choices=PropertyName.choices)
    check_in = models.DateField()
    check_out = models.DateField()
    rental_start = models.DateField()
    rental_end = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Refundable security deposit charged with the rental payment.",
    )
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    deposit_refunded = models.BooleanField(default=False)
    deposit_refunded_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, default="")
    guest_language = models.CharField(max_length=10, default="en")
    terms_accepted = models.BooleanField(default=False)
    confirmation_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} – {self.bike.name} ({self.rental_start} to {self.rental_end})"

    @property
    def formatted_total_price(self):
        return format_euro(self.total_price)

    @property
    def formatted_deposit_amount(self):
        return format_euro(self.deposit_amount)

    @property
    def total_charged(self):
        return self.total_price + self.deposit_amount

    @property
    def formatted_total_charged(self):
        return format_euro(self.total_charged)

    @classmethod
    def bike_is_available(cls, bike, rental_start, rental_end):
        overlap = cls.objects.filter(
            bike=bike,
            paid=True,
        ).filter(
            rental_start__lte=rental_end,
            rental_end__gte=rental_start,
        )
        return not overlap.exists()

    @classmethod
    def calculate_total_price(cls, bike, rental_start, rental_end):
        days = (rental_end - rental_start).days + 1
        if days < 1:
            return Decimal("0.00")
        return bike.daily_price * days


class Route(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", _("Easy")
        MODERATE = "moderate", _("Moderate")
        CHALLENGING = "challenging", _("Challenging")

    title = models.CharField(max_length=200)
    title_el = models.CharField(max_length=200, blank=True, default="")
    distance = models.CharField(max_length=50, blank=True, default="")
    distance_el = models.CharField(max_length=50, blank=True, default="")
    duration = models.CharField(max_length=50)
    duration_el = models.CharField(max_length=50, blank=True, default="")
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices)
    description = models.TextField(
        help_text="Short route summary shown on the routes page.",
    )
    description_el = models.TextField(blank=True, default="")
    points_of_interest = models.TextField(
        blank=True,
        default="",
        help_text="Comma-separated highlights (e.g. White Tower, Aristotelous Square).",
    )
    points_of_interest_el = models.TextField(blank=True, default="")
    coffee_stop = models.CharField(max_length=200, blank=True, default="")
    coffee_stop_el = models.CharField(max_length=200, blank=True, default="")
    restaurant = models.CharField(max_length=200, blank=True, default="")
    restaurant_el = models.CharField(max_length=200, blank=True, default="")
    beach_info = models.CharField(max_length=255, blank=True, default="")
    beach_info_el = models.CharField(max_length=255, blank=True, default="")
    image = models.ImageField(
        upload_to="routes/",
        blank=True,
        null=True,
        help_text="Optional cover photo for the route card.",
    )
    google_maps_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def display_title(self):
        if get_language() == "el" and self.title_el:
            return self.title_el
        return self.title

    @property
    def display_distance(self):
        if get_language() == "el" and self.distance_el:
            return self.distance_el
        return self.distance

    @property
    def display_duration(self):
        if get_language() == "el" and self.duration_el:
            return self.duration_el
        return self.duration

    @property
    def display_points_of_interest(self):
        raw = (
            self.points_of_interest_el
            if get_language() == "el" and self.points_of_interest_el
            else self.points_of_interest
        )
        return [item.strip() for item in raw.split(",") if item.strip()]

    @property
    def display_description(self):
        if get_language() == "el" and self.description_el:
            return self.description_el
        return self.description

    @property
    def display_coffee_stop(self):
        if get_language() == "el" and self.coffee_stop_el:
            return self.coffee_stop_el
        return self.coffee_stop

    @property
    def display_restaurant(self):
        if get_language() == "el" and self.restaurant_el:
            return self.restaurant_el
        return self.restaurant

    @property
    def display_beach_info(self):
        if get_language() == "el" and self.beach_info_el:
            return self.beach_info_el
        return self.beach_info

    @property
    def maps_directions_url(self):
        if not self.google_maps_url:
            return ""
        if "q=" in self.google_maps_url:
            query = self.google_maps_url.split("q=", 1)[1]
            return f"https://www.google.com/maps/dir/?api=1&destination={query}"
        return self.google_maps_url
