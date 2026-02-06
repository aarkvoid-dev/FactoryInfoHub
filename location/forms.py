from django import forms
from .models import Country, State, District, City, Region


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ISO code (e.g., IND)'}),
        }


class StateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = ['name', 'code', 'country']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state code'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
        }


class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name', 'code', 'state', 'is_capital', 'population', 'area', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city code'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'is_capital': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'population': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Population'}),
            'area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Area in sq km'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude', 'step': '0.000001'}),
        }


class DistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['name', 'code', 'city']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter district name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter district code'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
        }


class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name', 'code', 'district', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter region/area name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter region code'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe this region/area'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
