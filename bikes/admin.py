from django.contrib import admin, messages
from django.utils import timezone

from .models import Bike, Reservation, Route


@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ("name", "name_el", "bike_type", "daily_price", "active")
    list_filter = ("active", "bike_type")
    search_fields = ("name", "name_el")


@admin.action(description="Mark selected reservations as returned")
def mark_reservations_returned(modeladmin, request, queryset):
    now = timezone.now()
    updated = 0
    for reservation in queryset:
        if reservation.returned_at is None:
            reservation.returned_at = now
            reservation.save(update_fields=["returned_at"])
            updated += 1
    modeladmin.message_user(
        request,
        f"{updated} reservation(s) marked as returned.",
        messages.SUCCESS,
    )


@admin.action(description="Mark selected deposits as refunded")
def mark_deposits_refunded(modeladmin, request, queryset):
    now = timezone.now()
    updated = 0
    for reservation in queryset:
        if not reservation.deposit_refunded:
            reservation.deposit_refunded = True
            reservation.deposit_refunded_at = now
            reservation.save(update_fields=["deposit_refunded", "deposit_refunded_at"])
            updated += 1
    modeladmin.message_user(
        request,
        f"{updated} deposit(s) marked as refunded.",
        messages.SUCCESS,
    )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "booking_reference",
        "bike",
        "full_name",
        "property_name",
        "rental_start",
        "rental_end",
        "paid",
        "returned_at",
        "deposit_refunded",
    )
    list_filter = ("paid", "bike", "property_name", "deposit_refunded")
    search_fields = ("booking_reference", "full_name", "email", "phone")
    readonly_fields = (
        "stripe_session_id",
        "paid_at",
        "created_at",
        "rental_price_display",
        "deposit_amount_display",
        "total_charged_display",
    )
    actions = [mark_reservations_returned, mark_deposits_refunded]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "booking_reference",
                    "bike",
                    "full_name",
                    "email",
                    "phone",
                    "property_name",
                )
            },
        ),
        (
            "Stay & rental",
            {
                "fields": (
                    "check_in",
                    "check_out",
                    "rental_start",
                    "rental_end",
                )
            },
        ),
        (
            "Payment",
            {
                "fields": (
                    "paid",
                    "paid_at",
                    "stripe_session_id",
                    "rental_price_display",
                    "deposit_amount_display",
                    "total_charged_display",
                )
            },
        ),
        (
            "Return & deposit",
            {
                "fields": (
                    "returned_at",
                    "deposit_refunded",
                    "deposit_refunded_at",
                )
            },
        ),
        (
            "Internal",
            {
                "fields": (
                    "admin_notes",
                    "guest_language",
                    "terms_accepted",
                    "confirmation_email_sent",
                    "created_at",
                )
            },
        ),
    )

    @admin.display(description="Rental price")
    def rental_price_display(self, obj):
        return obj.formatted_total_price

    @admin.display(description="Deposit")
    def deposit_amount_display(self, obj):
        return obj.formatted_deposit_amount

    @admin.display(description="Total charged")
    def total_charged_display(self, obj):
        return obj.formatted_total_charged


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("title", "title_el", "duration", "difficulty", "active")
    list_filter = ("active", "difficulty")
    search_fields = ("title", "title_el", "description", "description_el")
