from decimal import Decimal

from django.db import migrations, models


def backfill_deposit_amounts(apps, schema_editor):
    Reservation = apps.get_model("bikes", "Reservation")
    for reservation in Reservation.objects.filter(deposit_amount__isnull=True).select_related(
        "bike"
    ):
        if reservation.bike.bike_type == "city":
            reservation.deposit_amount = Decimal("150.00")
        else:
            reservation.deposit_amount = Decimal("400.00")
        reservation.save(update_fields=["deposit_amount"])


class Migration(migrations.Migration):
    dependencies = [
        ("bikes", "0006_reservation_guest_language_reservation_paid_at"),
    ]

    operations = [
        migrations.RunPython(backfill_deposit_amounts, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="reservation",
            name="deposit_amount",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Refundable security deposit charged with the rental payment.",
                max_digits=10,
            ),
        ),
    ]
