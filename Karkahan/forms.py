from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import Factory, FactoryImage
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from django.core.exceptions import ValidationError
from decimal import Decimal


class FactoryForm(ModelForm):
    """Simplified FactoryForm without dynamic category creation"""
    
    class Meta:
        model = Factory
        fields = [
            'name', 'description', 'category', 'subcategory',
            'country', 'state', 'city', 'district', 'region',
            'address', 'pincode', 'contact_person', 'contact_phone',
            'contact_email', 'website', 'video_url', 'established_year',
            'employee_count', 'annual_turnover', 'factory_type', 'price',
            'production_capacity', 'working_hours', 'holidays', 'features',
            'is_active', 'is_verified'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40, 'class': 'form-control', 'placeholder': 'e.g., We specialize in textile manufacturing with 20 years of experience...'}),
            'address': forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'form-control', 'placeholder': 'e.g., 123 Industrial Area, Sector 5, Mumbai, Maharashtra 400001'}),
            'holidays': forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'form-control', 'placeholder': 'e.g., Diwali, Holi, Republic Day, Independence Day, weekends'}),
            'features': forms.Textarea(attrs={'rows': 4, 'cols': 40, 'class': 'form-control', 'placeholder': 'e.g., ISO 9001 Certified\n24/7 Operations\nExport Quality\nCustom Manufacturing\nOn-time Delivery'}),
            'contact_phone': forms.TextInput(attrs={'type': 'tel', 'class': 'form-control', 'placeholder': 'e.g., 9876543210', 'maxlength': '10', 'pattern': '[0-9]{10}', 'title': 'Please enter exactly 10 digits'}),
            'contact_email': forms.EmailInput(attrs={'type': 'email', 'class': 'form-control', 'placeholder': 'e.g., contact@factoryname.com'}),
            'website': forms.URLInput(attrs={'type': 'url', 'class': 'form-control', 'placeholder': 'e.g., https://factoryname.com (optional)'}),
            'video_url': forms.URLInput(attrs={
                'type': 'url', 
                'class': 'form-control',
                'placeholder': 'e.g., https://youtube.com/watch?v=dQw4w9WgXcQ (optional)',
                'pattern': 'https?://.*',
                'title': 'Please enter a valid URL starting with http:// or https://',
                'data-video-preview': 'true'
            }),
            'established_year': forms.NumberInput(attrs={'min': 1900, 'max': 2030, 'class': 'form-control', 'placeholder': 'e.g., 2015'}),
            # 'employee_count': forms.NumberInput(attrs={'min': 0, 'class': 'form-control', 'placeholder': 'e.g., 150'}),
            'employee_count': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 150',
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '')",
                'pattern': '[0-9]+(\\.[0-9]+)?',
                'title': 'Please enter only numbers (no hyphens, plus signs, or letters)'
            }),
            # 'annual_turnover': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': 'e.g., 5000000.00'}),
            'annual_turnover': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5000000',
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '')",
                'pattern': '[0-9]+(\\.[0-9]+)?',
                'title': 'Please enter only numbers (no hyphens, plus signs, or letters)'
            }),
            'factory_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Textile Manufacturing, Electronics Assembly, Food Processing'}),
            'production_capacity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bulk/Average/Small'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 9:00 AM - 6:00 PM, Monday to Saturday'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABC Textiles Pvt. Ltd.'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 400001'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mr. John Doe, Operations Manager'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': 'e.g., 1500.00'}),
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
            'video_url': 'Video Tour URL',
            'established_year': 'Established Year',
            'employee_count': 'Employee Count',
            'annual_turnover': 'Annual Turnover (in INR)',
            'factory_type': 'Factory Type',
            'production_capacity': 'Production Capacity',
            'working_hours': 'Working Hours',
            'holidays': 'Holidays',
            'features': 'Featured Features',
            'is_active': 'Is Active',
            'is_verified': 'Is Verified',
            'price': 'Amount'
        }
        help_texts = {
            'name': 'Official registered name of your factory as it appears in business documents',
            'description': 'Detailed description of your factory operations, capabilities, specialties, and what makes your factory unique',
            'category': 'Main industry category that best represents your factory type and operations',
            'subcategory': 'More specific specialization within the selected main category',
            'country': 'Select the country where your factory is located',
            'state': 'Select the state or province within the selected country',
            'city': 'Select the city or municipality where your factory is located',
            'district': 'Select the district or area within the selected city',
            'region': 'Select the specific region or locality within the selected district',
            'address': 'Complete physical address including street, building number, and nearby landmarks',
            'pincode': 'Postal code or ZIP code for your factory location',
            'contact_person': 'Name of the primary contact person at your factory for business inquiries',
            'contact_phone': 'Primary contact phone number (include country code if international)',
            'contact_email': 'Business email address for official communications and inquiries',
            'website': 'Your factory\'s official website URL (optional but recommended for credibility)',
            'video_url': 'Paste YouTube or Vimeo link for factory virtual tour to showcase your facilities',
            'established_year': 'Year your factory was established and began operations (e.g., 2015)',
            'employee_count': 'Total number of employees currently working at your factory',
            'annual_turnover': 'Your factory\'s annual revenue in Indian Rupees (approximate if confidential)',
            'factory_type': 'Type of manufacturing or processing operations (e.g., Textile, Electronics, Food Processing, Automotive)',
            'production_capacity': 'Maximum production output per time period (e.g., 5000 units/month, 10 tons/day, 1000 pieces/week)',
            'working_hours': 'Standard working hours and days (e.g., 9:00 AM - 6:00 PM, Monday to Saturday, 24/7 operations)',
            'holidays': 'List of observed holidays or non-working days throughout the year',
            'features': 'Key features and capabilities of your factory (one per line or comma-separated). Examples: ISO Certified, 24/7 Operations, Export Quality, Custom Manufacturing',
            'price': 'Cost per unit or service rate (optional for information purposes)',
            'is_active': 'Check to make your factory visible to users and searchable in listings',
            'is_verified': 'Check if your factory has been verified by administrators (usually checked by staff)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make name required
        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['price'].required = False
        self.fields['contact_person'].required = True
        self.fields['contact_email'].required = False
        self.fields['contact_phone'].required = True
        self.fields['category'].required = True
        self.fields['subcategory'].required = True
        
        # Set up initial queryset for subcategory based on selected category
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=category_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
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
        elif self.instance.pk and self.instance.country:
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
        elif self.instance.pk and self.instance.state:
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

        # Ensure proper initial values for select2 widgets
        if self.instance.pk:
            # Set initial values for select2 to show current selections
            if self.instance.category:
                self.fields['category'].initial = self.instance.category
            if self.instance.subcategory:
                self.fields['subcategory'].initial = self.instance.subcategory
            if self.instance.country:
                self.fields['country'].initial = self.instance.country
            if self.instance.state:
                self.fields['state'].initial = self.instance.state
            if self.instance.city:
                self.fields['city'].initial = self.instance.city
            if self.instance.district:
                self.fields['district'].initial = self.instance.district
            if self.instance.region:
                self.fields['region'].initial = self.instance.region


class CategoryForm(forms.ModelForm):
    """Form for creating new categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Category Description'}),
        }
        labels = {
            'name': 'Category Name',
            'description': 'Description',
        }


class SubCategoryForm(forms.ModelForm):
    """Form for creating new subcategories"""
    
    class Meta:
        model = SubCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subcategory Name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Subcategory Description'}),
        }
        labels = {
            'name': 'Subcategory Name',
            'description': 'Description',
        }


class LocationForm(forms.ModelForm):
    """Base form for location creation"""
    
    class Meta:
        model = None  # Will be set in subclasses
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CountryForm(LocationForm):
    """Form for creating countries"""
    
    class Meta(LocationForm.Meta):
        model = Country
        fields = ['name', 'code']


class StateForm(LocationForm):
    """Form for creating states"""
    
    class Meta(LocationForm.Meta):
        model = State
        fields = ['name', 'code', 'country']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
        }


class CityForm(LocationForm):
    """Form for creating cities"""
    
    class Meta(LocationForm.Meta):
        model = City
        fields = ['name', 'code', 'state', 'is_capital', 'population', 'area', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'is_capital': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'population': forms.NumberInput(attrs={'class': 'form-control'}),
            'area': forms.NumberInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class DistrictForm(LocationForm):
    """Form for creating districts"""
    
    class Meta(LocationForm.Meta):
        model = District
        fields = ['name', 'code', 'city']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
        }


class RegionForm(LocationForm):
    """Form for creating regions"""
    
    class Meta(LocationForm.Meta):
        model = Region
        fields = ['name', 'code', 'district', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FactoryImageForm(ModelForm):
    """Form for individual factory images"""
    class Meta:
        model = FactoryImage
        fields = ['image', 'alt_text', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control-file',
                'data-image-id': lambda: 'image_' + str(id(self)) if hasattr(self, 'instance') and self.instance.pk else 'new_image'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Description of this image...'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-toggle-primary': 'true'
            })
        }
        labels = {
            'image': 'Image File',
            'alt_text': 'Alternative Text (for accessibility)',
            'is_primary': 'Set as Primary Image'
        }
        help_texts = {
            'alt_text': 'Describe what this image shows for screen readers and SEO',
            'is_primary': 'This image will be shown as the main preview image'
        }


# Formset for handling multiple FactoryImage objects
FactoryImageFormSet = inlineformset_factory(
    Factory,
    FactoryImage,
    form=FactoryImageForm,
    extra=3,  # Show 3 empty forms by default
    can_delete=True,
    can_order=False
)


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
    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        required=False,
        empty_label="All Districts"
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        empty_label="All Regions"
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
        
        # Update querysets based on selected values from GET parameters
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

        # Initialize subcategory queryset based on initial category value
        if self.initial.get('category'):
            try:
                category_id = self.initial.get('category').id
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=category_id, is_active=True
                ).order_by('name')
            except AttributeError:
                pass

        # Initialize state queryset based on initial country value
        if self.initial.get('country'):
            try:
                country_id = self.initial.get('country').id
                self.fields['state'].queryset = State.objects.filter(
                    country_id=country_id
                ).order_by('name')
            except AttributeError:
                pass

        # Initialize city queryset based on initial state value
        if self.initial.get('state'):
            try:
                state_id = self.initial.get('state').id
                self.fields['city'].queryset = City.objects.filter(
                    state_id=state_id
                ).order_by('name')
            except AttributeError:
                pass

        # Initialize district queryset based on initial city value
        if self.initial.get('city'):
            try:
                city_id = self.initial.get('city').id
                self.fields['district'].queryset = District.objects.filter(
                    city_id=city_id
                ).order_by('name')
            except AttributeError:
                pass

        # Initialize region queryset based on initial district value
        if self.initial.get('district'):
            try:
                district_id = self.initial.get('district').id
                self.fields['region'].queryset = Region.objects.filter(
                    district_id=district_id
                ).order_by('name')
            except AttributeError:
                pass


