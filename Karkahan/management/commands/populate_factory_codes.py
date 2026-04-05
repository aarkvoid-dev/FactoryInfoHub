from django.core.management.base import BaseCommand
from Karkahan.models import Factory
import random
import string


class Command(BaseCommand):
    help = 'Populate factory codes for all factories that do not have one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def generate_factory_code(self):
        """Generate a unique factory code in format FIH-XXXXXX"""
        prefix = "FIH"  # FactoryInfoHub prefix
        
        while True:
            # Generate 6 random alphanumeric characters
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"{prefix}-{random_part}"
            
            # Check if code is unique (not already used)
            if not Factory.objects.filter(factory_code=code).exists():
                return code
        
        return code

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all factories without a factory_code
        factories_without_code = Factory.objects.filter(
            factory_code__isnull=True
        ) | Factory.objects.filter(factory_code='')
        
        count = factories_without_code.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All factories already have factory codes!')
            )
            return
        
        self.stdout.write(f'Found {count} factories without factory codes.')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made.'))
            for factory in factories_without_code:
                self.stdout.write(f'  - {factory.name} (ID: {factory.id})')
            return
        
        # Update each factory with a unique code
        updated = 0
        for factory in factories_without_code:
            factory.factory_code = self.generate_factory_code()
            factory.save(update_fields=['factory_code'])
            updated += 1
            self.stdout.write(f'  Updated: {factory.name} -> {factory.factory_code}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully populated {updated} factory codes!'
            )
        )