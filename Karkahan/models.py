from django.db import models
from django.utils.text import slugify
from Home.models import SoftDeleteModel
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region

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
    
    # Factory specifications
    factory_type = models.CharField(max_length=100, blank=True, help_text="e.g., Manufacturing, Assembly, Processing")
    production_capacity = models.CharField(max_length=200, blank=True, help_text="e.g., 1000 units/month")
    working_hours = models.CharField(max_length=100, blank=True, help_text="e.g., 9:00 AM - 6:00 PM")
    holidays = models.TextField(blank=True, help_text="List of holidays observed")
    
    # Additional fields
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
