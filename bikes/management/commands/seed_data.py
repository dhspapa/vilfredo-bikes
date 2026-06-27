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
        "distance": "6 km",
        "distance_el": "6 χλμ.",
        "duration": "45 min",
        "duration_el": "45 λεπτά",
        "difficulty": Route.Difficulty.EASY,
        "description": "A relaxed ride along the Thermaic Gulf promenade with sea views.",
        "description_el": "Ήρεμη βόλτα κατά μήκος του παραλιακού με θέα στη θάλασσα.",
        "points_of_interest": "White Tower, Umbrellas sculpture, Aristotelous Square",
        "points_of_interest_el": "Λευκός Πύργος, Ομπρέλες, πλατεία Αριστοτέλους",
        "google_maps_url": "https://maps.google.com/?q=Thessaloniki+Waterfront",
    },
    {
        "title": "White Tower Loop",
        "title_el": "Βόλτα Λευκού Πύργου",
        "distance": "5 km",
        "distance_el": "5 χλμ.",
        "duration": "1 hour",
        "duration_el": "1 ώρα",
        "difficulty": Route.Difficulty.MODERATE,
        "description": "Circle the city centre landmarks from the White Tower to Aristotelous Square.",
        "description_el": "Κυκλική διαδρομή στα κεντρικά αξιοθέατα, από τον Λευκό Πύργο μέχρι την πλατεία Αριστοτέλους.",
        "points_of_interest": "White Tower, Nikis Avenue, Aristotelous Square, Ladadika",
        "points_of_interest_el": "Λευκός Πύργος, Λεωφ. Νίκης, πλατεία Αριστοτέλους, Λαδάδικα",
        "google_maps_url": "https://maps.google.com/?q=White+Tower+Thessaloniki",
    },
    {
        "title": "Kalamaria Coastal Ride",
        "title_el": "Παραλιακή διαδρομή Καλαμαριάς",
        "distance": "8 km",
        "distance_el": "8 χλμ.",
        "duration": "1.5 hours",
        "duration_el": "1,5 ώρα",
        "difficulty": Route.Difficulty.MODERATE,
        "description": "Coastal ride through Kalamaria with cafés and quiet side streets.",
        "description_el": "Παραλιακή διαδρομή στην Καλαμαριά με καφέ και ήσυχους δρόμους.",
        "points_of_interest": "Kalamaria marina, Nea Krini, Mikro Emvolo",
        "points_of_interest_el": "Μαρίνα Καλαμαριάς, Νέα Κρήνη, Μικρό Έμβολο",
        "google_maps_url": "https://maps.google.com/?q=Kalamaria+Thessaloniki",
    },
    {
        "title": "Nea Krini Seafront",
        "title_el": "Παραλία Νέας Κρήνης",
        "distance": "4 km",
        "distance_el": "4 χλμ.",
        "duration": "30 min",
        "duration_el": "30 λεπτά",
        "difficulty": Route.Difficulty.EASY,
        "description": "Short seafront loop ideal for a morning coffee ride near Kalamaria.",
        "description_el": "Σύντομη παραλιακή βόλτα, ιδανική για πρωινό καφέ κοντά στην Καλαμαριά.",
        "points_of_interest": "Nea Krini beach, coastal cafés, Aretsou marina",
        "points_of_interest_el": "Παραλία Νέας Κρήνης, παραλιακά καφέ, μαρίνα Αρέτσου",
        "google_maps_url": "https://maps.google.com/?q=Nea+Krini+Thessaloniki",
    },
    {
        "title": "Aretsou Marina Loop",
        "title_el": "Βόλτα μαρίνας Αρέτσου",
        "distance": "5 km",
        "distance_el": "5 χλμ.",
        "duration": "40 min",
        "duration_el": "40 λεπτά",
        "difficulty": Route.Difficulty.EASY,
        "description": "Flat loop around Aretsou with views of yachts and the Thermaic Gulf.",
        "description_el": "Επίπεδη διαδρομή γύρω από την Αρέτσου με θέα στα σκάφη και τον Θερμαϊκό.",
        "points_of_interest": "Aretsou marina, Mikro Emvolo, Kalamaria waterfront",
        "points_of_interest_el": "Μαρίνα Αρέτσου, Μικρό Έμβολο, παραλία Καλαμαριάς",
        "google_maps_url": "https://maps.google.com/?q=Aretsou+Marina+Thessaloniki",
    },
    {
        "title": "Mikro Emvolo Peninsula",
        "title_el": "Χερσόνησος Μικρού Εμβόλου",
        "distance": "7 km",
        "distance_el": "7 χλμ.",
        "duration": "1 hour",
        "duration_el": "1 ώρα",
        "difficulty": Route.Difficulty.MODERATE,
        "description": "Scenic ride out to Mikro Emvolo with open sea views south of Kalamaria.",
        "description_el": "Γραφική διαδρομή στο Μικρό Έμβολο με ανοιχτή θέα στη θάλασα νότια της Καλαμαριάς.",
        "points_of_interest": "Mikro Emvolo lighthouse, coastal path, fish taverns",
        "points_of_interest_el": "Φάρος Μικρού Εμβόλου, παραλιακό μονοπάτι, ψαροταβέρνες",
        "google_maps_url": "https://maps.google.com/?q=Mikro+Emvolo+Thessaloniki",
    },
    {
        "title": "Kalamaria to Karetsou Park",
        "title_el": "Καλαμαριά – πάρκο Καρέτσου",
        "distance": "6 km",
        "distance_el": "6 χλμ.",
        "duration": "50 min",
        "duration_el": "50 λεπτά",
        "difficulty": Route.Difficulty.EASY,
        "description": "Green ride through neighbourhood streets to Karetsou Park and back.",
        "description_el": "Πράσινη διαδρομή σε ήσυχους δρόμους μέχρι το πάρκο Καρέτσου και επιστροφή.",
        "points_of_interest": "Karetsou Park, Kalamaria town hall, local cafés",
        "points_of_interest_el": "Πάρκο Καρέτσου, δημαρχείο Καλαμαριάς, τοπικά καφέ",
        "google_maps_url": "https://maps.google.com/?q=Karetsou+Park+Kalamaria",
    },
    {
        "title": "Thessaloniki Port to Ladadika",
        "title_el": "Λιμάνι – Λαδάδικα",
        "distance": "4 km",
        "distance_el": "4 χλμ.",
        "duration": "35 min",
        "duration_el": "35 λεπτά",
        "difficulty": Route.Difficulty.EASY,
        "description": "Easy city ride from the passenger port area to the Ladadika district.",
        "description_el": "Εύκολη διαδρομή πόλης από την περιοχή του επιβατικού λιμένα μέχρι τα Λαδάδικα.",
        "points_of_interest": "Passenger port, Aristotelous Square, Ladadika",
        "points_of_interest_el": "Επιβατικός λιμένας, πλατεία Αριστοτέλους, Λαδάδικα",
        "google_maps_url": "https://maps.google.com/?q=Thessaloniki+Port",
    },
    {
        "title": "Ano Toumba Green Streets",
        "title_el": "Πράσινες διαδρομές Άνω Τούμπας",
        "distance": "9 km",
        "distance_el": "9 χλμ.",
        "duration": "1.5 hours",
        "duration_el": "1,5 ώρα",
        "difficulty": Route.Difficulty.MODERATE,
        "description": "Hilly neighbourhood loop east of the centre with quieter residential streets.",
        "description_el": "Λοφώδης διαδρομή ανατολικά του κέντρου με ήσυχους οικιστικούς δρόμους.",
        "points_of_interest": "Ano Toumba, Kaftanzoglou Avenue, local parks",
        "points_of_interest_el": "Άνω Τούμπα, λεωφ. Καυταντζόγλου, τοπικά πάρκα",
        "google_maps_url": "https://maps.google.com/?q=Ano+Toumba+Thessaloniki",
    },
    {
        "title": "Rotunda to Concert Hall",
        "title_el": "Ροτόντα – Μέγαρο Μουσικής",
        "distance": "5 km",
        "distance_el": "5 χλμ.",
        "duration": "45 min",
        "duration_el": "45 λεπτά",
        "difficulty": Route.Difficulty.MODERATE,
        "description": "Cultural ride linking Roman monuments and the waterfront concert hall.",
        "description_el": "Πολιτιστική διαδρομή που συνδέει ρωμαϊκά μνημεία και το παραλιακό Μέγαρο Μουσικής.",
        "points_of_interest": "Rotunda, Galerius Arch, Thessaloniki Concert Hall",
        "points_of_interest_el": "Ροτόντα, Αψίδα Γαλερίου, Μέγαρο Μουσικής",
        "google_maps_url": "https://maps.google.com/?q=Thessaloniki+Concert+Hall",
    },
]


CANONICAL_BIKE_NAMES = {bike["name"] for bike in BIKES}
CANONICAL_ROUTE_TITLES = {route["title"] for route in ROUTES}


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
                    "distance": route_data["distance"],
                    "distance_el": route_data["distance_el"],
                    "duration": route_data["duration"],
                    "duration_el": route_data["duration_el"],
                    "difficulty": route_data["difficulty"],
                    "description": route_data["description"],
                    "description_el": route_data["description_el"],
                    "points_of_interest": route_data["points_of_interest"],
                    "points_of_interest_el": route_data["points_of_interest_el"],
                    "google_maps_url": route_data["google_maps_url"],
                    "active": True,
                },
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"{action} route: {route.title}")

        for route in Route.objects.exclude(title__in=CANONICAL_ROUTE_TITLES):
            route.active = False
            route.save(update_fields=["active"])
            self.stdout.write(f"Deactivated non-seed route: {route.title}")

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
