from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("bikes", "0007_reservation_deposit_required"),
    ]

    operations = [
        migrations.AddField(
            model_name="reservation",
            name="admin_notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="reservation",
            name="deposit_refunded",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="reservation",
            name="deposit_refunded_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="reservation",
            name="returned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
