"""
Management command to update factory view statistics
"""

from django.core.management.base import BaseCommand
from Karkahan.utils import update_all_view_stats, get_view_analytics_summary


class Command(BaseCommand):
    help = 'Update all factory view statistics and display analytics summary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting factory view statistics update...')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
            return

        # Update all view statistics
        updated_count = update_all_view_stats()
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated view statistics for {updated_count} factories'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING('No factories found to update')
            )

        # Display analytics summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('FACTORY VIEW ANALYTICS SUMMARY')
        self.stdout.write('='*50)
        
        summary = get_view_analytics_summary()
        
        self.stdout.write(f"Total Factories: {summary['total_factories']}")
        self.stdout.write(f"Active Factories: {summary['active_factories']}")
        self.stdout.write(f"Factories with Views: {summary['factories_with_views']}")
        self.stdout.write('')
        self.stdout.write(f"Total Views: {summary['total_views']:,}")
        self.stdout.write(f"Today's Views: {summary['today_views']:,}")
        self.stdout.write(f"Weekly Views: {summary['weekly_views']:,}")
        self.stdout.write(f"Monthly Views: {summary['monthly_views']:,}")
        self.stdout.write('')
        
        if summary['most_viewed_factory']:
            self.stdout.write(
                f"Most Viewed Factory: {summary['most_viewed_factory'].name} "
                f"({summary['most_viewed_count']:,} views)"
            )
        else:
            self.stdout.write("No views recorded yet")
        
        self.stdout.write('='*50)