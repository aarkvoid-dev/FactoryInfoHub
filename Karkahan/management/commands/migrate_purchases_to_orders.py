from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from Karkahan.models import FactoryPurchase, PurchaseHistory, Order, OrderItem, Payment
from decimal import Decimal
import uuid


class Command(BaseCommand):
    help = 'Migrate old FactoryPurchase records to new Order system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all FactoryPurchase records that haven't been migrated
        purchases = FactoryPurchase.objects.filter(
            migrated_to_order=False
        ).select_related('user', 'factory')
        
        if not purchases.exists():
            self.stdout.write(self.style.SUCCESS('No purchases to migrate'))
            return
        
        self.stdout.write(f'Found {purchases.count()} purchases to migrate')
        
        migrated_count = 0
        error_count = 0
        
        with transaction.atomic():
            for purchase in purchases:
                try:
                    # Create Order
                    order = Order.objects.create(
                        user=purchase.user,
                        order_number=f'MIGRATED-{purchase.id}',
                        customer_name=purchase.user.get_full_name() or purchase.user.username,
                        customer_email=purchase.user.email,
                        customer_phone=getattr(purchase.user.profile, 'phone', ''),
                        subtotal=purchase.purchase_price,
                        tax_amount=Decimal('0.00'),  # No tax for migrated orders
                        service_fee=Decimal('0.00'),  # No service fee for migrated orders
                        total_amount=purchase.purchase_price,
                        payment_method='manual',
                        status='completed' if purchase.payment_status == 'completed' else 'cancelled',
                        payment_status=purchase.payment_status,
                        notes=f'Migrated from FactoryPurchase ID: {purchase.id}',
                        created_at=purchase.purchased_at,
                        completed_at=purchase.purchased_at if purchase.payment_status == 'completed' else None,
                        migrated_from_purchase=True
                    )
                    
                    # Create OrderItem
                    OrderItem.objects.create(
                        order=order,
                        factory=purchase.factory,
                        quantity=purchase.purchase_quantity,
                        price_at_purchase=purchase.purchase_price / purchase.purchase_quantity if purchase.purchase_quantity > 0 else purchase.purchase_price,
                        total_price=purchase.purchase_price
                    )
                    
                    # Create Payment record
                    Payment.objects.create(
                        order=order,
                        payment_method='manual',
                        amount=purchase.purchase_price,
                        currency='INR',
                        status=purchase.payment_status,
                        transaction_id=f'MIGRATED-PURCHASE-{purchase.id}',
                        gateway_response=f'Migrated from FactoryPurchase ID: {purchase.id}',
                        completed_at=purchase.purchased_at if purchase.payment_status == 'completed' else None
                    )
                    
                    # Mark purchase as migrated
                    purchase.migrated_to_order = True
                    purchase.save()
                    
                    # Create PurchaseHistory record if it doesn't exist
                    if not PurchaseHistory.objects.filter(
                        user=purchase.user,
                        factory_name=purchase.factory.name
                    ).exists():
                        PurchaseHistory.objects.create(
                            user=purchase.user,
                            factory_name=purchase.factory.name,
                            factory_contact_email=purchase.factory.contact_email,
                            factory_contact_phone=purchase.factory.contact_phone,
                            factory_address=purchase.factory.address,
                            factory_description=purchase.factory.description,
                            purchase_price=purchase.purchase_price,
                            purchase_quantity=purchase.purchase_quantity,
                            purchase_date=purchase.purchased_at,
                            email_delivered=True,
                            email_delivered_at=purchase.email_sent_at or purchase.purchased_at
                        )
                    
                    migrated_count += 1
                    
                    if not dry_run:
                        self.stdout.write(
                            f'✓ Migrated purchase {purchase.id} to order {order.order_number}'
                        )
                    else:
                        self.stdout.write(
                            f'Would migrate purchase {purchase.id} to order MIGRATED-{purchase.id}'
                        )
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to migrate purchase {purchase.id}: {str(e)}')
                    )
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN COMPLETE: Would migrate {migrated_count} purchases'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'SUCCESS: Migrated {migrated_count} purchases, {error_count} errors'
                )
            )