"""
Management command to ensure all factories have FactoryViewStats objects
"""

from django.core.management.base import BaseCommand
from Karkahan.models import Factory, FactoryViewStats


class Command(BaseCommand):
    help = 'Ensure all factories have FactoryViewStats objects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Checking for factories without view stats...')
        )
        
        # Find factories without view stats
        factories_without_stats = Factory.objects.filter(
            is_deleted=False
        ).exclude(
            view_stats__isnull=False
        )
        
        count = factories_without_stats.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('All factories already have view stats!')
            )
            return
        
        self.stdout.write(f'Found {count} factories without view stats')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
            for factory in factories_without_stats[:10]:  # Show first 10
                self.stdout.write(f'  - {factory.name}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
            return

        # Create view stats for factories without them
        created_count = 0
        for factory in factories_without_stats:
            try:
                FactoryViewStats.objects.create(factory=factory)
                created_count += 1
                self.stdout.write(f'  Created view stats for: {factory.name}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Failed to create view stats for {factory.name}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created view stats for {created_count} factories'
            )
        )