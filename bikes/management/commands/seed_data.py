from decimal import Decimal

from django.core.management.base import BaseCommand

from bikes.models import Bike, Route


BIKES = [
    {
        "name": "Electric Bike",
        "name_el": "Ηλεκτρικό ποδήλατο",
        "bike_type": Bike.BikeType.ELECTRIC,
        "daily_price": Decimal("20.00"),
    },
    {
        "name": "City Bike",
        "name_el": "Ποδήλατο πόλης",
        "bike_type": Bike.BikeType.CITY,
        "daily_price": Decimal("10.00"),
    },
]

ROUTES = [
    {
        "title": "Thessaloniki Waterfront",
        "title_el": "Παραλία Θεσσαλονίκης",
        "duration": "45 min",
        "duration_el": "45 λεπτά",
        "difficulty": Route.Difficulty.EASY,
        "description": "A relaxed ride along the Thermaic Gulf promenade with sea views.",
        "description_el": "Ήρεμη βόλτα κατά μήκος του παραλιακού με θέα στη θάλασσα.",
        "google_maps_url": "https://maps.google.com/?q=Thessaloniki+Waterfront",
    },
    {
        "title": "White Tower Route",
        "title_el": "Διαδρομή Λευκού Πύργου",
        "duration": "1 hour",
        "duration_el": "1 ώρα",
        "difficulty": Route.Difficulty.MODERATE,
        "description": "Circle the city centre landmarks from the White Tower to Aristotelous Square.",
        "description_el": "Κυκλική διαδρομή στα κεντρικά αξιοθέατα, από τον Λευκό Πύργο μέχρι την πλατεία Αριστοτέλους.",
        "google_maps_url": "https://maps.google.com/?q=White+Tower+Thessaloniki",
    },
    {
        "title": "Kalamaria Ride",
        "title_el": "Βόλτα στην Καλαμαριά",
        "duration": "1.5 hours",
        "duration_el": "1,5 ώρα",
        "difficulty": Route.Difficulty.MODERATE,
        "description": "Coastal ride through Kalamaria with cafés and quiet side streets.",
        "description_el": "Παραλιακή διαδρομή στην Καλαμαριά με καφέ και ήσυχους δρόμους.",
        "google_maps_url": "https://maps.google.com/?q=Kalamaria+Thessaloniki",
    },
]


CANONICAL_BIKE_NAMES = {bike["name"] for bike in BIKES}


class Command(BaseCommand):
    help = "Seed initial bikes and suggested routes."

    def handle(self, *args, **options):
        for bike_data in BIKES:
            bike, created = Bike.objects.update_or_create(
                name=bike_data["name"],
                defaults={
                    "name_el": bike_data["name_el"],
                    "bike_type": bike_data["bike_type"],
                    "daily_price": bike_data["daily_price"],
                    "active": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} bike: {bike.name}")

        for bike in Bike.objects.exclude(name__in=CANONICAL_BIKE_NAMES):
            if bike.reservations.exists():
                bike.active = False
                bike.save(update_fields=["active"])
                self.stdout.write(f"Deactivated non-seed bike: {bike.name}")
            else:
                bike.delete()
                self.stdout.write(f"Removed non-seed bike: {bike.name}")

        for route_data in ROUTES:
            route, created = Route.objects.update_or_create(
                title=route_data["title"],
                defaults={
                    "title_el": route_data["title_el"],
                    "duration": route_data["duration"],
                    "duration_el": route_data["duration_el"],
                    "difficulty": route_data["difficulty"],
                    "description": route_data["description"],
                    "description_el": route_data["description_el"],
                    "google_maps_url": route_data["google_maps_url"],
                    "active": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} route: {route.title}")

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
