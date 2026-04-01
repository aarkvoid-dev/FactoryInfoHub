from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from Karkahan.models import Order, Cart, OrderItem
from Karkahan.views import send_order_receipt

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix payment system issues and clean up stuck orders'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Process orders older than this many days (default: 7)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        
        self.stdout.write(
            self.style.SUCCESS(f'Payment System Fix Tool')
        )
        self.stdout.write(f'Dry run: {dry_run}')
        self.stdout.write(f'Days threshold: {days}')
        self.stdout.write('-' * 50)

        # Find stuck pending orders
        cutoff_date = timezone.now() - timedelta(days=days)
        stuck_orders = Order.objects.filter(
            payment_status='pending',
            order_date__lt=cutoff_date
        )

        self.stdout.write(f'Found {stuck_orders.count()} stuck pending orders')

        if stuck_orders.exists():
            for order in stuck_orders:
                self.stdout.write(f'  Order #{order.id}: {order.user.username} - {order.total_amount}')
                
                if not dry_run:
                    try:
                        with transaction.atomic():
                            # Mark as failed
                            order.payment_status = 'failed'
                            order.save()
                            
                            self.stdout.write(
                                self.style.WARNING(f'  Marked order #{order.id} as failed')
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  Error processing order #{order.id}: {e}')
                        )

        # Find completed orders without receipts
        completed_without_receipt = Order.objects.filter(
            payment_status='completed',
            receipt_sent=False
        )

        self.stdout.write(f'Found {completed_without_receipt.count()} completed orders without receipts')

        if completed_without_receipt.exists():
            for order in completed_without_receipt:
                self.stdout.write(f'  Order #{order.id}: {order.user.username}')
                
                if not dry_run:
                    try:
                        factories = [item.factory for item in order.items.all()]
                        if send_order_receipt(order.user, order, factories):
                            self.stdout.write(
                                self.style.SUCCESS(f'  Sent receipt for order #{order.id}')
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'  Failed to send receipt for order #{order.id}')
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  Error sending receipt for order #{order.id}: {e}')
                        )

        # Find carts with completed orders still in them
        orders_with_items = Order.objects.filter(
            payment_status='completed'
        ).values_list('id', flat=True)

        carts_to_clean = Cart.objects.filter(
            items__order__in=orders_with_items
        ).distinct()

        self.stdout.write(f'Found {carts_to_clean.count()} carts with completed order items')

        if carts_to_clean.exists():
            for cart in carts_to_clean:
                items_to_remove = cart.items.filter(
                    factory__in=OrderItem.objects.filter(
                        order__in=orders_with_items
                    ).values_list('factory_id', flat=True)
                )
                
                self.stdout.write(f'  Cart for {cart.user.username}: {items_to_remove.count()} items')
                
                if not dry_run:
                    try:
                        items_to_remove.delete()
                        self.stdout.write(
                            self.style.SUCCESS(f'  Cleaned cart for {cart.user.username}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  Error cleaning cart for {cart.user.username}: {e}')
                        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Dry run completed - no changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Payment system fix completed')
            )