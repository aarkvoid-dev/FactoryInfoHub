from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from Home.models import SoftDeleteModel


class Country(SoftDeleteModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True, help_text="ISO 3166-1 alpha-3 country code")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('location:country_detail', kwargs={'slug': self.slug})


class State(SoftDeleteModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True, help_text="State code (e.g., MH for Maharashtra)")
    slug = models.SlugField(max_length=100, blank=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'country']
        ordering = ['country', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.country.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.country.name}"

    def get_absolute_url(self):
        return reverse('location:state_detail', kwargs={'slug': self.slug})

class City(SoftDeleteModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True, help_text="City code")
    slug = models.SlugField(max_length=100, blank=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    is_capital = models.BooleanField(default=False, help_text="Is this the capital city of the state?")
    population = models.PositiveIntegerField(blank=True, null=True, help_text="Population in numbers")
    area = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Area in square kilometers")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'state']
        ordering = ['state', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.state.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.state.name}"

    def get_absolute_url(self):
        return reverse('location:city_detail', kwargs={'slug': self.slug})

    @property
    def country(self):
        return self.state.country
    
class District(SoftDeleteModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True, help_text="District code")
    slug = models.SlugField(max_length=100, blank=True)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='districts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'city']
        ordering = ['city', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.city.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.city.name}"
    def get_absolute_url(self):
        return reverse('location:district_detail', kwargs={'slug': self.slug})




class Region(SoftDeleteModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True, help_text="Region/area code")
    slug = models.SlugField(max_length=100, blank=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='regions')
    description = models.TextField(blank=True, help_text="Description of the region/area")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'district']
        ordering = ['district', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.district.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}, {self.district.name}"
    def get_absolute_url(self):
        return reverse('location:region_detail', kwargs={'slug': self.slug})

    @property
    def city(self):
        return self.district.city

    @property
    def state(self):
        return self.district.city.state

    @property
    def country(self):
        return self.district.city.state.country
