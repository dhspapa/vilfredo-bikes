from pathlib import Path

import polib
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compile django.po translation files to django.mo (uses polib)."

    def handle(self, *args, **options):
        locale_root = Path(settings.BASE_DIR) / "locale"
        compiled = 0

        for po_path in locale_root.glob("**/LC_MESSAGES/django.po"):
            mo_path = po_path.with_suffix(".mo")
            po = polib.pofile(str(po_path))
            po.save_as_mofile(str(mo_path))
            compiled += 1
            self.stdout.write(self.style.SUCCESS(f"Compiled {mo_path}"))

        if compiled == 0:
            self.stdout.write(self.style.WARNING("No django.po files found."))
