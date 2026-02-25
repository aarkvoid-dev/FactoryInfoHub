from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from location.models import Country, State, City, District, Region
from category.models import Category, SubCategory
from Home.models import SoftDeleteModel

class Worker(SoftDeleteModel):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    AVAILABILITY_CHOICES = [
        ('FT', 'Full-time'),
        ('PT', 'Part-time'),
        ('C', 'Contract'),
        ('T', 'Temporary'),
        ('A', 'Available immediately'),
    ]
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='N')
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    
    # Professional Information with Category/Subcategory
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='workers')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='workers', null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    skills = models.TextField(blank=True, help_text="List of skills and competencies")
    availability = models.CharField(max_length=2, choices=AVAILABILITY_CHOICES, default='A')
    expected_daily_wage = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    
    # Location Information
    country = models.ForeignKey(Country, on_delete=models.CASCADE, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True, blank=True)
    address = models.TextField(blank=True)
    
    # System Fields
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_workers', help_text="User who created this worker record")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.full_name}-{self.id or ''}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.full_name
    
    def get_absolute_url(self):
        return reverse('workers:worker_detail', kwargs={'slug': self.slug})
    
    def get_full_location(self):
        """Return formatted location string"""
        parts = []
        if self.city:
            parts.append(self.city.name)
        if self.state:
            parts.append(self.state.name)
        if self.country:
            parts.append(self.country.name)
        return ', '.join(parts) if parts else 'Location not specified'
    
    def get_experience_display(self):
        """Return formatted experience string"""
        if self.years_of_experience == 1:
            return f"{self.years_of_experience} year"
        return f"{self.years_of_experience} years"
    
    def get_wage_display(self):
        """Return formatted wage string"""
        return f"₹{self.expected_daily_wage:,}/day"
    
    def soft_delete(self):
        """Soft delete the worker"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    @property
    def is_available(self):
        """Check if worker is available for work"""
        return self.is_active and not self.is_deleted and self.availability != 'N'

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Worker'
        verbose_name_plural = 'Workers'

class WorkExperience(models.Model):
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='experiences')
    company_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Work Experience'
        verbose_name_plural = 'Work Experiences'
    
    def clean(self):
        """Validate work experience data"""
        from django.core.exceptions import ValidationError
        from datetime import date
        
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError('End date cannot be before start date.')
        
        if self.is_current and self.end_date:
            raise ValidationError('Cannot have an end date for a current position.')
        
        # Check for overlapping experiences
        if self.start_date:
            overlapping = WorkExperience.objects.filter(
                worker=self.worker,
                start_date__lte=self.start_date,
                end_date__gte=self.start_date
            ).exclude(pk=self.pk)
            
            if self.end_date:
                overlapping = overlapping.filter(
                    end_date__gte=self.end_date
                )
            
            if overlapping.exists():
                raise ValidationError('Work experience dates overlap with existing experience.')
    
    def save(self, *args, **kwargs):
        """Override save to include validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
    
    def get_duration(self):
        """Calculate and return job duration"""
        if self.end_date and self.start_date:
            duration = self.end_date - self.start_date
            months = duration.days // 30
            years = months // 12
            remaining_months = months % 12
            
            if years > 0:
                if remaining_months > 0:
                    return f"{years} years, {remaining_months} months"
                return f"{years} years"
            else:
                return f"{months} months"
        return "Ongoing" if self.is_current else "Duration not specified"
