from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from Home.models import SoftDeleteModel
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from django.utils.safestring import mark_safe
from .email_service import FactoryEmailService
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
import uuid


class Factory(SoftDeleteModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    factory_code = models.CharField(max_length=20, unique=True, blank=True, null=True, editable=True, 
                                     help_text="Auto-generated unique factory identification code. Leave blank to auto-generate.")
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
    
    # Featured features
    features = models.TextField(blank=True, help_text="Enter each feature on a new line or separate with commas (e.g., ISO Certified, 24/7 Operations, Export Quality)")
    
    # Additional fields
    is_active = models.BooleanField(default=False)
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
        
        # Auto-generate factory code if not set
        if not self.factory_code:
            self.factory_code = self._generate_factory_code()
        
        super().save(*args, **kwargs)
    
    def _generate_factory_code(self):
        """Generate a unique factory code in format FIH-XXXXXX"""
        import random
        import string
        
        prefix = "FIH"  # FactoryInfoHub prefix
        
        while True:
            # Generate 6 random alphanumeric characters
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"{prefix}-{random_part}"
            
            # Check if code is unique
            if not Factory.objects.filter(factory_code=code).exists():
                return code
        
        return code

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
        """Converts various video platform links into embeddable format."""
        if not self.video_url:
            return None
        
        video_url = self.video_url.strip()
        
        # YouTube URL handling (including Shorts)
        if 'youtube.com' in video_url or 'youtu.be' in video_url:
            video_id = ""
            
            # Handle regular YouTube videos
            if 'v=' in video_url:
                video_id = video_url.split('v=')[1]
                if '&' in video_id:
                    video_id = video_id.split('&')[0]
            
            # Handle YouTube Shorts
            elif 'shorts/' in video_url:
                video_id = video_url.split('shorts/')[1]
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
            
            # Handle youtu.be short links
            elif 'youtu.be/' in video_url:
                video_id = video_url.split('youtu.be/')[1]
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
            
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}?autoplay=0&rel=0&showinfo=0"
        
        # Facebook URL handling
        elif 'facebook.com' in video_url:
            # Facebook video embed URL format
            # Convert facebook.com/watch?v=VIDEO_ID or facebook.com/username/videos/VIDEO_ID
            # to facebook.com/plugins/video.php?href=FULL_URL&show_text=0&width=560
            encoded_url = video_url.replace(' ', '%20')
            return f"https://www.facebook.com/plugins/video.php?href={encoded_url}&show_text=0&width=560&height=315"
        
        # Instagram URL handling
        elif 'instagram.com' in video_url:
            # Instagram video embed URL format
            # Convert instagram.com/p/POST_ID/ to instagram.com/p/POST_ID/embed/
            if '/p/' in video_url or '/reel/' in video_url:
                if '?' in video_url:
                    video_url = video_url.split('?')[0]
                return f"{video_url}embed/"
        
        # Vimeo URL handling
        elif 'vimeo.com' in video_url:
            video_id = ""
            if 'vimeo.com/' in video_url:
                video_id = video_url.split('vimeo.com/')[1]
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
            
            if video_id:
                return f"https://player.vimeo.com/video/{video_id}"
        
        # Dailymotion URL handling
        elif 'dailymotion.com' in video_url:
            video_id = ""
            if 'video/' in video_url:
                video_id = video_url.split('video/')[1]
                if '?' in video_id:
                    video_id = video_id.split('?')[0]
            
            if video_id:
                return f"https://www.dailymotion.com/embed/video/{video_id}"
        
        # TikTok URL handling
        elif 'tiktok.com' in video_url:
            # TikTok embed URL format
            # Convert tiktok.com/@username/video/VIDEO_ID to tiktok.com/@username/video/VIDEO_ID?lang=en
            if '/video/' in video_url:
                if '?' in video_url:
                    video_url = video_url.split('?')[0]
                return f"{video_url}?lang=en"
        
        # If not recognized platform, return the original URL (might be already embedded)
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

    def get_features_list(self):
        """Return features as a list, splitting by newlines or commas"""
        if not self.features:
            return []
        # Split by newlines first, then by commas
        features = []
        for line in self.features.split('\n'):
            for item in line.split(','):
                item = item.strip()
                if item:
                    features.append(item)
        return features

    @property
    def total_views(self):
        """Return total view count for this factory"""
        try:
            return self.view_stats.total_views
        except FactoryViewStats.DoesNotExist:
            # Create stats if they don't exist
            stats = FactoryViewStats.objects.create(factory=self)
            return stats.total_views

    @property
    def today_views(self):
        """Return today's view count for this factory"""
        try:
            return self.view_stats.today_views
        except FactoryViewStats.DoesNotExist:
            # Create stats if they don't exist
            stats = FactoryViewStats.objects.create(factory=self)
            return stats.today_views

    @property
    def weekly_views(self):
        """Return weekly view count for this factory"""
        try:
            return self.view_stats.weekly_views
        except FactoryViewStats.DoesNotExist:
            # Create stats if they don't exist
            stats = FactoryViewStats.objects.create(factory=self)
            return stats.weekly_views

    @property
    def monthly_views(self):
        """Return monthly view count for this factory"""
        try:
            return self.view_stats.monthly_views
        except FactoryViewStats.DoesNotExist:
            # Create stats if they don't exist
            stats = FactoryViewStats.objects.create(factory=self)
            return stats.monthly_views


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


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_price(self):
        return sum(item.factory.price for item in self.items.all())

    @property
    def total_items(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    factory = models.ForeignKey('Factory', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'factory']  # Prevent duplicate factories in cart

    def __str__(self):
        return f"{self.factory.name} in cart of {self.cart.user.username}"


class PaymentGateway(models.Model):
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('razorpay', 'Razorpay'),
        # Add more as needed
    ]
    name = models.CharField(max_length=50, choices=GATEWAY_CHOICES, unique=True)
    is_active = models.BooleanField(default=False, help_text="Only one gateway can be active at a time")
    key_id = models.CharField(max_length=255, blank=True, help_text="API Key ID (e.g., publishable key)")
    key_secret = models.CharField(max_length=255, blank=True, help_text="API Secret Key")
    webhook_secret = models.CharField(max_length=255, blank=True, help_text="Webhook signing secret")
    mode = models.CharField(max_length=10, choices=[('test', 'Test'), ('live', 'Live')], default='test')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Payment Gateway"
        verbose_name_plural = "Payment Gateways"

    def save(self, *args, **kwargs):
        # Ensure only one active gateway
        if self.is_active:
            PaymentGateway.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_name_display()} ({'Active' if self.is_active else 'Inactive'})"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True, blank=True, help_text="Auto-generated order number")
    order_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')],
        default='pending'
    )
    gateway_used = models.ForeignKey(PaymentGateway, null=True, blank=True, on_delete=models.SET_NULL)
    transaction_id = models.CharField(max_length=255, blank=True, help_text="Gateway transaction ID")
    payment_method = models.CharField(max_length=50, blank=True, help_text="e.g., card, upi, netbanking")

    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    receipt_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retry', 'Retry Needed')
    ], default='pending')
    email_retry_count = models.PositiveIntegerField(default=0)
    last_email_error = models.TextField(blank=True, null=True, help_text="Last email error message for debugging")
    payment_completed = models.BooleanField(default=False, help_text="Whether payment has been successfully completed and verified")

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number in format: ORD-YYYY-MM-XXXX
            from datetime import datetime
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
            
            # Find the highest sequence number for this year-month
            last_order = Order.objects.filter(
                order_number__startswith=f"ORD-{year:04d}-{month:02d}-"
            ).order_by('-order_number').first()
            
            if last_order:
                # Extract the sequence number and increment
                sequence = int(last_order.order_number.split('-')[-1])
                new_sequence = sequence + 1
            else:
                # Start from 1 for this year-month
                new_sequence = 1
            
            self.order_number = f"ORD-{year:04d}-{month:02d}-{new_sequence:04d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    factory = models.ForeignKey('Factory', on_delete=models.CASCADE)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.factory.name} in Order #{self.order.id}"


class FactoryViewTracker(models.Model):
    """Tracks individual factory view events for analytics"""
    factory = models.ForeignKey(Factory, on_delete=models.CASCADE, related_name='view_trackers')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
        verbose_name = 'Factory View Tracker'
        verbose_name_plural = 'Factory View Trackers'
    
    def __str__(self):
        return f"{self.factory.name} viewed at {self.viewed_at}"


class FactoryViewStats(models.Model):
    """Aggregated view statistics for factories"""
    factory = models.OneToOneField(Factory, on_delete=models.CASCADE, related_name='view_stats')
    total_views = models.PositiveIntegerField(default=0)
    today_views = models.PositiveIntegerField(default=0)
    weekly_views = models.PositiveIntegerField(default=0)
    monthly_views = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Factory View Statistics'
        verbose_name_plural = 'Factory View Statistics'
    
    def __str__(self):
        return f"Stats for {self.factory.name}"
    
    def update_all_stats(self):
        """Update all view statistics"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Update total views
        self.total_views = self.factory.view_trackers.count()
        
        # Update today's views
        self.today_views = self.factory.view_trackers.filter(
            viewed_at__gte=today_start
        ).count()
        
        # Update weekly views
        self.weekly_views = self.factory.view_trackers.filter(
            viewed_at__gte=week_start
        ).count()
        
        # Update monthly views
        self.monthly_views = self.factory.view_trackers.filter(
            viewed_at__gte=month_start
        ).count()
        
        self.save()
    
    def increment_views(self):
        """Increment view counts"""
        self.total_views += 1
        self.today_views += 1
        self.weekly_views += 1
        self.monthly_views += 1
        self.save()