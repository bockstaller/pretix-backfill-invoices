from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Backfills missing invoices"

    def handle(self, *args, **options):

        self.stdout.write(self.style.SUCCESS("Hallo Pretix"))
