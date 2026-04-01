"""
Management command to clean up old view tracking data.

This command helps maintain database performance by removing old view tracking records
while preserving aggregated statistics.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from ...models import FactoryViewTracker, FactoryViewStats
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up old factory view tracking data to maintain database performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days of view tracking data to keep (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days_to_keep = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days_to_keep)
        
        self.stdout.write(
            self.style.SUCCESS(f'Cleaning up view tracking data older than {days_to_keep} days...')
        )
        self.stdout.write(f'Cutoff date: {cutoff_date}')
        
        # Count records to be deleted
        old_records_count = FactoryViewTracker.objects.filter(
            viewed_at__lt=cutoff_date
        ).count()
        
        if old_records_count == 0:
            self.stdout.write(self.style.SUCCESS('No old records found to clean up.'))
            return
        
        self.stdout.write(f'Found {old_records_count} old view tracking records')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: No data was actually deleted.')
            )
            return
        
        # Perform the cleanup
        try:
            with transaction.atomic():
                deleted_count, _ = FactoryViewTracker.objects.filter(
                    viewed_at__lt=cutoff_date
                ).delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted {deleted_count} old view tracking records.'
                    )
                )
                
                # Update view statistics for affected factories
                self.stdout.write('Updating view statistics...')
                self.update_view_statistics()
                
        except Exception as e:
            logger.error(f"Error during view data cleanup: {e}")
            self.stdout.write(
                self.style.ERROR(f'Failed to clean up view data: {e}')
            )
    
    def update_view_statistics(self):
        """Update view statistics for all factories after cleanup"""
        try:
            factories = FactoryViewStats.objects.select_related('factory').all()
            
            for stats in factories:
                stats.update_all_stats()
            
            self.stdout.write(
                self.style.SUCCESS(f'Updated view statistics for {factories.count()} factories.')
            )
            
        except Exception as e:
            logger.error(f"Error updating view statistics: {e}")
            self.stdout.write(
                self.style.ERROR(f'Failed to update view statistics: {e}')
            )