from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import Factory, FactoryImage, ShoppingCart, Order, OrderItem, Payment
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
            'production_capacity', 'working_hours', 'holidays',
            'is_active', 'is_verified'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40, 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'form-control'}),
            'holidays': forms.Textarea(attrs={'rows': 3, 'cols': 40, 'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'type': 'tel', 'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'type': 'email', 'class': 'form-control'}),
            'website': forms.URLInput(attrs={'type': 'url', 'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={
                'type': 'url', 
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=...',
                'pattern': 'https://.*',
                'title': 'Please enter a valid URL starting with https://',
                'data-video-preview': 'true'
            }),
            'established_year': forms.NumberInput(attrs={'min': 1900, 'max': 2030, 'class': 'form-control'}),
            'employee_count': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'annual_turnover': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'factory_type': forms.TextInput(attrs={'class': 'form-control'}),
            'production_capacity': forms.TextInput(attrs={'class': 'form-control'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
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
            'is_active': 'Is Active',
            'is_verified': 'Is Verified',
            'price': 'Amount'
        }
        help_texts = {
            'factory_type': 'e.g., Manufacturing, Assembly, Processing',
            'production_capacity': 'e.g., 1000 units/month',
            'working_hours': 'e.g., 9:00 AM - 6:00 PM',
            'holidays': 'List of holidays observed',
            'video_url': 'Paste YouTube or Vimeo link for factory virtual tour',
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
                'class': 'form-control-file'
            }),
            'alt_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Description of this image...'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
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


# NEW FORMS FOR ENHANCED CART AND PAYMENT SYSTEM

class ShoppingCartForm(forms.ModelForm):
    """Form for managing shopping cart items"""
    class Meta:
        model = ShoppingCart
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10',
                'step': '1'
            })
        }
        labels = {
            'quantity': 'Quantity'
        }
        help_texts = {
            'quantity': 'Select quantity (1-10)'
        }

    def clean_quantity(self):
        """Validate quantity"""
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise ValidationError('Quantity must be at least 1')
        if quantity > 10:
            raise ValidationError('Maximum quantity per item is 10')
        return quantity


class CheckoutForm(forms.Form):
    """Form for checkout process"""
    customer_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        }),
        label='Full Name'
    )
    customer_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        label='Email Address'
    )
    customer_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number (optional)'
        }),
        label='Phone Number'
    )
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Payment Method'
    )
    accept_terms = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I accept the terms and conditions',
        required=True
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Pre-fill fields if user is authenticated
            if hasattr(user, 'profile') and user.profile:
                self.fields['customer_name'].initial = user.get_full_name() or user.username
                self.fields['customer_email'].initial = user.email
                if user.profile.phone_number:
                    self.fields['customer_phone'].initial = user.profile.phone_number


class OrderForm(forms.ModelForm):
    """Form for creating orders"""
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone', 'payment_method', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number (optional)'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special instructions or notes...'
            })
        }
        labels = {
            'customer_name': 'Full Name',
            'customer_email': 'Email Address',
            'customer_phone': 'Phone Number',
            'payment_method': 'Payment Method',
            'notes': 'Additional Notes'
        }


class PaymentForm(forms.ModelForm):
    """Form for payment processing"""
    class Meta:
        model = Payment
        fields = ['payment_method', 'amount']
        widgets = {
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'step': '0.01'
            })
        }
        labels = {
            'payment_method': 'Payment Method',
            'amount': 'Amount to Pay'
        }

    def __init__(self, *args, **kwargs):
        order_total = kwargs.pop('order_total', None)
        super().__init__(*args, **kwargs)
        
        if order_total:
            self.fields['amount'].initial = order_total
            self.fields['amount'].widget.attrs['readonly'] = 'readonly'


class OrderStatusForm(forms.ModelForm):
    """Form for updating order status (Admin use)"""
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'notes', 'tracking_number']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'tracking_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tracking number (if applicable)'
            })
        }
        labels = {
            'status': 'Order Status',
            'payment_status': 'Payment Status',
            'notes': 'Internal Notes',
            'tracking_number': 'Tracking Number'
        }


class RefundForm(forms.Form):
    """Form for processing refunds"""
    refund_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01'
        }),
        label='Refund Amount'
    )
    refund_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please provide reason for refund...'
        }),
        label='Refund Reason'
    )
    confirm_refund = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I confirm this refund is authorized',
        required=True
    )

    def __init__(self, *args, **kwargs):
        max_refund_amount = kwargs.pop('max_refund_amount', None)
        super().__init__(*args, **kwargs)
        
        if max_refund_amount:
            self.fields['refund_amount'].initial = max_refund_amount
            self.fields['refund_amount'].widget.attrs['max'] = str(max_refund_amount)