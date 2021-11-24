from django.core.management.base import BaseCommand
from django.db.models import Q
from django_scopes import scope
from pretix.base.models.event import Event
from pretix.base.models.invoices import Invoice
from pretix.base.models.orders import Order
from pretix.base.models.organizer import Organizer
from pretix.base.services.invoices import generate_invoice, invoice_qualified


class Command(BaseCommand):
    help = "Backfills missing invoices"

    def add_arguments(self, parser):
        parser.add_argument("organizer_slug", type=str)
        parser.add_argument("event_slug", type=str)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        o_slug = options["organizer_slug"]
        e_slug = options["event_slug"]

        if dry_run := options["dry_run"]:
            self.stdout.write(self.style.WARNING("Running Dry Run"))

        o = Organizer.objects.filter(slug__iexact=o_slug).first()

        with scope(organizer=o):
            not_qualified = []
            has_invoice = []
            has_no_adress = []
            added = []

            e = Event.objects.filter(slug__iexact=e_slug).first()

            for o in Order.objects.all():

                # Has invoice
                if has_inv := o.invoices.exists() and not (
                    o.status in (Order.STATUS_PAID, Order.STATUS_PENDING)
                    and o.invoices.filter(is_cancellation=True).count()
                    >= o.invoices.filter(is_cancellation=False).count()
                ):
                    has_invoice.append(o.code)
                    self.stdout.write(
                        self.style.ERROR(f"Order {o.code}: already has an invoice.")
                    )
                    continue

                # Is qualified
                if (
                    e.settings.get("invoice_generate")
                    not in (
                        "admin",
                        "user",
                        "paid",
                        "True",
                    )
                    or not invoice_qualified(o)
                ):
                    not_qualified.append(o.code)
                    self.stdout.write(
                        self.style.ERROR(f"Order {o.code}: is not qualified.")
                    )
                    continue

                # Has no invoice adress
                if not hasattr(o, "invoice_address"):
                    has_no_adress.append(o.code)
                    self.stdout.write(
                        self.style.ERROR(f"Order {o.code}: has no invoice adress")
                    )
                    continue

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f"Order {o.code}: Invoice has been created")
                    )
                else:
                    inv = generate_invoice(o)
                    added.append(o.code)
                    o.log_action(
                        "pretix.backfill.invoice.generated",
                        data={"invoice": inv.pk},
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"Order {o.code}: Invoice has been created")
                    )

            self.stdout.write(
                self.style.SUCCESS(f"Orders with invoices: {', '.join(has_invoice)} ")
            )
            self.stdout.write(
                self.style.WARNING(f"Unqualified orders: {', '.join(not_qualified)} ")
            )
            self.stdout.write(
                self.style.SUCCESS(f"Added invoices to orders: {', '.join(added)} ")
            )
            self.stdout.write(
                self.style.ERROR(f"Orders without address: {', '.join(has_no_adress)} ")
            )
            self.stdout.write(self.style.NOTICE(f"Orders: {Order.objects.count()}"))
            self.stdout.write(
                self.style.NOTICE(f"Orders with invoices: {len(has_invoice)}")
            )
            self.stdout.write(
                self.style.NOTICE(
                    f"Orders without invoices: {Order.objects.count() - len(has_invoice)}"
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    f"Orders with errors: {len(set(not_qualified + has_no_adress))}"
                )
            )
