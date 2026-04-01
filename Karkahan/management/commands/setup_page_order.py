from django.core.management.base import BaseCommand
from Home.models import Page


class Command(BaseCommand):
    help = 'Set up default ordering for pages'

    def handle(self, *args, **options):
        # Define the desired order for pages
        page_order = {
            'about': 1,      # About Us - First
            'terms': 2,      # Terms & Conditions - Second  
            'refund': 3,     # Refund Policy - Third
            'privacy': 4,    # Privacy Policy - Fourth
            'disclaimer': 5, # Disclaimer - Fifth
        }
        
        updated_count = 0
        created_count = 0
        
        for page_type, order in page_order.items():
            try:
                page = Page.objects.get(page_type=page_type)
                if page.order != order:
                    page.order = order
                    page.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated {page.title} order to {order}'
                        )
                    )
                else:
                    self.stdout.write(
                        f'{page.title} already has order {order}'
                    )
            except Page.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Page with type "{page_type}" not found'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} pages'
            )
        )