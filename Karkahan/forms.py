from django import forms
from django.forms import ModelForm
from .models import Factory
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region


class FactoryForm(ModelForm):
    class Meta:
        model = Factory
        fields = [
            'name', 'description', 'category', 'subcategory',
            'country', 'state', 'city', 'district', 'region',
            'address', 'pincode', 'contact_person', 'contact_phone',
            'contact_email', 'website', 'established_year',
            'employee_count', 'annual_turnover', 'factory_type',
            'production_capacity', 'working_hours', 'holidays',
            'is_active', 'is_verified'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'address': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
            'holidays': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
            'contact_phone': forms.TextInput(attrs={'type': 'tel'}),
            'contact_email': forms.EmailInput(attrs={'type': 'email'}),
            'website': forms.URLInput(attrs={'type': 'url'}),
            'established_year': forms.NumberInput(attrs={'min': 1900, 'max': 2030}),
            'employee_count': forms.NumberInput(attrs={'min': 0}),
            'annual_turnover': forms.NumberInput(attrs={'step': '0.01'}),
        }
        labels = {
            'name': 'Factory Name',
            'description': 'Description',
            'category': 'Category',
            'subcategory': 'Sub Category',
            'country': 'Country',
            'state': 'State',
            'city': 'City',
            'district': 'District',
            'region': 'Region',
            'address': 'Address',
            'pincode': 'Pincode',
            'contact_person': 'Contact Person',
            'contact_phone': 'Contact Phone',
            'contact_email': 'Contact Email',
            'website': 'Website',
            'established_year': 'Established Year',
            'employee_count': 'Employee Count',
            'annual_turnover': 'Annual Turnover (in INR)',
            'factory_type': 'Factory Type',
            'production_capacity': 'Production Capacity',
            'working_hours': 'Working Hours',
            'holidays': 'Holidays',
            'is_active': 'Is Active',
            'is_verified': 'Is Verified',
        }
        help_texts = {
            'factory_type': 'e.g., Manufacturing, Assembly, Processing',
            'production_capacity': 'e.g., 1000 units/month',
            'working_hours': 'e.g., 9:00 AM - 6:00 PM',
            'holidays': 'List of holidays observed',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make name required
        self.fields['name'].required = True
        
        # Set up initial queryset for subcategory based on selected category
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=category_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            # If editing existing factory, show subcategories for its current category
            self.fields['subcategory'].queryset = self.instance.category.subcategories.filter(
                is_active=True
            ).order_by('name')
        else:
            self.fields['subcategory'].queryset = SubCategory.objects.none()

        # Set up initial queryset for state based on selected country
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['state'].queryset = State.objects.filter(
                    country_id=country_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['state'].queryset = self.instance.country.states.all().order_by('name')
        else:
            self.fields['state'].queryset = State.objects.none()

        # Set up initial queryset for city based on selected state
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(
                    state_id=state_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['city'].queryset = self.instance.state.cities.all().order_by('name')
        else:
            self.fields['city'].queryset = City.objects.none()

        # Set up initial queryset for district based on selected city
        if 'city' in self.data:
            try:
                city_id = int(self.data.get('city'))
                self.fields['district'].queryset = District.objects.filter(
                    city_id=city_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.city:
            self.fields['district'].queryset = self.instance.city.districts.all().order_by('name')
        else:
            self.fields['district'].queryset = District.objects.none()

        # Set up initial queryset for region based on selected district
        if 'district' in self.data:
            try:
                district_id = int(self.data.get('district'))
                self.fields['region'].queryset = Region.objects.filter(
                    district_id=district_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.district:
            self.fields['region'].queryset = self.instance.district.regions.all().order_by('name')
        else:
            self.fields['region'].queryset = Region.objects.none()

        # Add CSS classes for styling
        for field_name, field in self.fields.items():
            if field_name in ['description', 'address', 'holidays']:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class FactoryFilterForm(forms.Form):
    """Form for filtering factories"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories"
    )
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Subcategories"
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        empty_label="All Countries"
    )
    state = forms.ModelChoiceField(
        queryset=State.objects.all(),
        required=False,
        empty_label="All States"
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        required=False,
        empty_label="All Cities"
    )
    factory_type = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Factory type...'})
    )
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update querysets based on selected values
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=category_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['state'].queryset = State.objects.filter(
                    country_id=country_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass

        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(
                    state_id=state_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass