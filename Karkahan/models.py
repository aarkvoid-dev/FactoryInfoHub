from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from Home.models import SoftDeleteModel
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Factory(SoftDeleteModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='factories')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='factories', blank=True, null=True)
    
    # Location fields
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='factories')
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='factories')
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='factories')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='factories', blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='factories', blank=True, null=True)
    
    # Factory details
    address = models.TextField(blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    established_year = models.PositiveIntegerField(blank=True, null=True)
    employee_count = models.PositiveIntegerField(blank=True, null=True)
    annual_turnover = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Price per unit", default=0)
    
    # Factory specifications
    factory_type = models.CharField(max_length=100, blank=True, help_text="e.g., Manufacturing, Assembly, Processing")
    production_capacity = models.CharField(max_length=200, blank=True, help_text="e.g., 1000 units/month")
    working_hours = models.CharField(max_length=100, blank=True, help_text="e.g., 9:00 AM - 6:00 PM")
    holidays = models.TextField(blank=True, help_text="List of holidays observed")
    
    # Additional fields
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_factories', help_text="User who created this factory record")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    video_url = models.URLField(blank=True, null=True, help_text="Paste YouTube or Vimeo link here")

    class Meta:
        ordering = ['name']
        verbose_name = 'Factory'
        verbose_name_plural = 'Factories'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            # Ensure uniqueness
            counter = 1
            while Factory.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.city.name}, {self.state.name}"

    def get_absolute_url(self):
        return f"/karkahan/{self.slug}/"

    @property
    def full_address(self):
        """Return complete address of the factory"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.region:
            parts.append(self.region.name)
        if self.district:
            parts.append(self.district.name)
        if self.city:
            parts.append(self.city.name)
        if self.state:
            parts.append(self.state.name)
        if self.country:
            parts.append(self.country.name)
        if self.pincode:
            parts.append(self.pincode)
        return ", ".join(parts)

    def get_location_hierarchy(self):
        """Return location hierarchy as a dictionary"""
        return {
            'country': self.country.name if self.country else '',
            'state': self.state.name if self.state else '',
            'city': self.city.name if self.city else '',
            'district': self.district.name if self.district else '',
            'region': self.region.name if self.region else '',
        }

    def get_primary_image(self):
        """Return the primary image or first image"""
        primary_image = self.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            return primary_image.image.url
        
        # Fallback to first image if no primary image set
        first_image = self.images.first()
        if first_image and first_image.image:
            return first_image.image.url
        
        return None

    @property
    def embed_video_url(self):
        """Converts a standard YouTube/Vimeo link into an embeddable format."""
        if not self.video_url:
            return None
        
        video_url = self.video_url.strip()
        
        # YouTube URL handling
        if 'youtube.com' in video_url or 'youtu.be' in video_url:
            video_id = ""
            if 'v=' in video_url:
                # Extract video ID from youtube.com/watch?v=VIDEO_ID format
                video_id = video_url.split('v=')[1]
                # Remove any additional parameters
                if '&' in video_id:
                    video_id = video_id.split('&')[0]
            elif 'youtu.be/' in video_url:
                # Extract video ID from youtu.be/VIDEO_ID format
                video_id = video_url.split('youtu.be/')[1]
                # Remove any additional parameters
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
            
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}?autoplay=0&rel=0&showinfo=0"
        
        # Vimeo URL handling
        elif 'vimeo.com' in video_url:
            video_id = ""
            if 'vimeo.com/' in video_url:
                # Extract video ID from vimeo.com/VIDEO_ID format
                video_id = video_url.split('vimeo.com/')[1]
                # Remove any additional parameters
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
            
            if video_id:
                return f"https://player.vimeo.com/video/{video_id}"
        
        # If not YouTube or Vimeo, return the original URL (might be already embedded)
        return video_url

    @property
    def thumbnail_url(self):
        """Return the URL of the factory thumbnail (primary image)"""
        primary_image = self.get_primary_image()
        return primary_image

    @property
    def image_count(self):
        """Return the number of images for this factory"""
        return self.images.count()

    def get_primary_image_obj(self):
        """Return the primary image object"""
        return self.images.filter(is_primary=True).first()

    def has_user_purchased(self, user):
        """Check if a user has purchased this factory"""
        if not user.is_authenticated:
            return False
        return FactoryPurchase.objects.filter(
            factory=self,
            user=user,
            payment_status='completed'
        ).exists()


class FactoryImage(models.Model):
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='factories/', blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True, help_text="Alternative text for accessibility")
    is_primary = models.BooleanField(default=False, help_text="Set as primary image for the factory")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Factory Image'
        verbose_name_plural = 'Factory Images'
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"Image for {self.factory.name}"

    def image_tag(self):
        """Return HTML image tag for admin display"""
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="80" height="80" style="border-radius: 6px;" />')
        return "No image"
    image_tag.short_description = 'Image Preview'
    image_tag.allow_tags = True


class ShoppingCart(models.Model):
    """Shopping cart for factory purchases"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_cart')
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'factory']
        verbose_name = 'Shopping Cart Item'
        verbose_name_plural = 'Shopping Cart Items'

    def __str__(self):
        return f"{self.user.username} - {self.factory.name} x{self.quantity}"

    @property
    def total_price(self):
        """Calculate total price for this cart item"""
        return self.factory.price * self.quantity

    @classmethod
    def get_cart_total(cls, user):
        """Get total price of all items in user's cart"""
        cart_items = cls.objects.filter(user=user)
        return sum(item.total_price for item in cart_items)

    @classmethod
    def get_cart_count(cls, user):
        """Get total number of items in user's cart"""
        cart_items = cls.objects.filter(user=user)
        return sum(item.quantity for item in cart_items)


class FactoryPurchase(models.Model):
    """Track individual factory purchases"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='factory_purchases')
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name='purchases')
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-purchased_at']
        verbose_name = 'Factory Purchase'
        verbose_name_plural = 'Factory Purchases'

    def __str__(self):
        return f"{self.user.username} - {self.factory.name} - {self.payment_status}"

    @property
    def total_amount(self):
        """Calculate total amount for this purchase"""
        return self.price_at_purchase * self.quantity

    def mark_as_completed(self):
        """Mark purchase as completed and send email"""
        self.payment_status = 'completed'
        self.save()
        self.send_factory_details_email()

    def send_factory_details_email(self):
        """Send factory details to user via email"""
        if self.email_sent:
            return

        try:
            # Create email content using template
            from django.template.loader import render_to_string

            # Prepare context for template
            context = {
                'user': self.user,
                'factories': [self.factory],  # Single factory in list for template compatibility
            }

            # Render HTML email template
            html_content = render_to_string('karkahan/factory_details_email.html', context)

            # Create plain text version (fallback)
            text_content = f"""
            Dear {self.user.username},

            Thank you for your purchase! Here are the details for the factory you requested:

            Factory Name: {self.factory.name}
            Category: {self.factory.category.name}
            Location: {self.factory.full_address}
            Type: {self.factory.factory_type}
            Production Capacity: {self.factory.production_capacity}
            Employee Count: {self.factory.employee_count}
            Established: {self.factory.established_year}
            Annual Turnover: {self.factory.annual_turnover}

            Contact Information:
            Contact Person: {self.factory.contact_person}
            Phone: {self.factory.contact_phone}
            Email: {self.factory.contact_email}
            Website: {self.factory.website}

            Address: {self.factory.address}
            {self.factory.city.name}, {self.factory.state.name} - {self.factory.pincode}
            {self.factory.country.name}

            This information is confidential and intended solely for your use.

            Best regards,
            Factory InfoHub Team
            """

            # Send email with SSL context that bypasses certificate verification
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Factory Details: {self.factory.name}"
            msg['From'] = settings.DEFAULT_FROM_EMAIL
            msg['To'] = self.user.email

            # Add text content (for email clients that don't support HTML)
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email with SSL context that bypasses certificate verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls(context=ssl_context)
                if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(msg)

            # Update FactoryPurchase record
            self.email_sent = True
            self.email_sent_at = timezone.now()
            self.save()

            # Update corresponding PurchaseHistory record
            try:
                purchase_history = PurchaseHistory.objects.filter(
                    user=self.user,
                    factory_slug=self.factory.slug,
                    purchase_date=self.purchased_at
                ).first()

                if purchase_history:
                    purchase_history.email_delivered = True
                    purchase_history.email_delivered_at = self.email_sent_at
                    purchase_history.save()
            except Exception as history_error:
                print(f"⚠️  Warning: Could not update PurchaseHistory record: {history_error}")

            print(f"✅ Email sent successfully to {self.user.email} for purchase {self.id}")
        except Exception as e:
            import traceback
            error_msg = f"❌ Failed to send email for purchase {self.id}: {str(e)}"
            error_details = f"Error details: {traceback.format_exc()}"
            print(error_msg)
            print(error_details)

            # Also log to Django's logging system
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Email sending failed for purchase {self.id}: {str(e)}")
            logger.error(f"User: {self.user.email}, Factory: {self.factory.name}")
            logger.error(f"Error details: {traceback.format_exc()}")


class PurchaseHistory(models.Model):
    """Comprehensive purchase history with factory details snapshot"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_history')
    factory_name = models.CharField(max_length=200)
    factory_slug = models.CharField(max_length=200)
    factory_category = models.CharField(max_length=100)
    factory_location = models.CharField(max_length=500)
    factory_contact_person = models.CharField(max_length=100, blank=True)
    factory_contact_phone = models.CharField(max_length=20, blank=True)
    factory_contact_email = models.EmailField(blank=True)
    factory_address = models.TextField(blank=True)
    factory_website = models.URLField(blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_quantity = models.PositiveIntegerField(default=1)
    purchase_date = models.DateTimeField()
    email_delivered = models.BooleanField(default=False)
    email_delivered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-purchase_date']
        verbose_name = 'Purchase History'
        verbose_name_plural = 'Purchase History'

    def __str__(self):
        return f"{self.user.username} - {self.factory_name} - {self.purchase_date.strftime('%Y-%m-%d')}"

    @classmethod
    def create_from_purchase(cls, purchase):
        """Create a purchase history record from a FactoryPurchase"""
        factory = purchase.factory
        return cls.objects.create(
            user=purchase.user,
            factory_name=factory.name,
            factory_slug=factory.slug,
            factory_category=factory.category.name,
            factory_location=factory.full_address,
            factory_contact_person=factory.contact_person,
            factory_contact_phone=factory.contact_phone,
            factory_contact_email=factory.contact_email,
            factory_address=factory.address,
            factory_website=factory.website,
            purchase_price=purchase.price_at_purchase,
            purchase_quantity=purchase.quantity,
            purchase_date=purchase.purchased_at,
            email_delivered=purchase.email_sent,
            email_delivered_at=purchase.email_sent_at,
        )

    def get_factory_absolute_url(self):
        """Get the URL for the factory"""
        return reverse('karkahan:factory_detail', kwargs={'slug': self.factory_slug})