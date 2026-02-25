from django.contrib import admin
from .models import Country, State, City, District, Region

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    list_filter = []
    search_fields = ['name', 'code']
    readonly_fields = ['slug']

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'code']
    list_filter = ['country']
    search_fields = ['name', 'country__name', 'code']
    readonly_fields = ['slug']
    autocomplete_fields = ['country']

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'state']
    list_filter = ['state']
    search_fields = ['name', 'state__name']
    readonly_fields = ['slug']
    autocomplete_fields = ['state']

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'city']
    list_filter = ['city']
    search_fields = ['name', 'city__name']
    readonly_fields = ['slug']
    autocomplete_fields = ['city']

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'district']
    list_filter = ['district']
    search_fields = ['name', 'district__name']
    readonly_fields = ['slug']
    autocomplete_fields = ['district']
