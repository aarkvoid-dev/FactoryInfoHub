"""
Blog application forms module.

This module contains all the form classes for the blog application,
including blog post forms, image forms, and formsets for image management.

Classes:
    BlogPostForm: Form for creating and editing blog posts
    BlogImageForm: Form for managing individual blog images
    BlogImageFormSet: Formset for managing multiple blog images
"""

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import BlogPost, BlogImage
from location.models import Country, State, City, District, Region
from category.models import Category, SubCategory
from Karkahan.models import Factory
from .mixins import (
    LocationCascadingMixin, UserFormMixin, CategoryCascadingMixin
)
from django.forms import ClearableFileInput

# class MultipleFileInput(forms.ClearableFileInput):
#     allow_multiple_selected = True

#     def __init__(self, attrs=None):
#         super().__init__(attrs)
#         if attrs:
#             attrs.setdefault('multiple', True)
#         else:
#             attrs = {'multiple': True}
#         self.attrs = attrs

#     def value_from_datadict(self, data, files, name):
#         if hasattr(files, 'getlist'):
#             return files.getlist(name)
#         else:
#             return [files.get(name)]


# class BlogPostForm(forms.ModelForm):

#     category = forms.ModelChoiceField(queryset=Category.objects.all(), required=True, empty_label="Select Category")
#     country = forms.ModelChoiceField(queryset=Country.objects.all(), required=False, empty_label="Select Country (Optional)")

#     class Meta:
#         model = BlogPost
#         fields = [
#             'title', 'content', 'excerpt', 
#             'category', 'subcategory', 
#             'country', 'state', 'city', 'district', 'region', 
#             'is_published'
#         ]
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control'}),
#             'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
#             'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Apply form-control to all select fields dynamically
#         for field in self.fields:
#             if not isinstance(self.fields[field].widget, forms.CheckboxInput):
#                 self.fields[field].widget.attrs.update({'class': 'form-control'})

#         instance = kwargs.get('instance')
#         data = self.data or {}

#         # Handle location cascading
#         if data.get('country') or (instance and instance.region):
#             country_id = data.get('country') or (instance.region.district.city.state.country.id if instance and instance.region else None)
#             if country_id:
#                 self.fields['state'].queryset = State.objects.filter(country_id=country_id)
#             else:
#                 self.fields['state'].queryset = State.objects.none()
#         else:
#             self.fields['state'].queryset = State.objects.none()

#         if data.get('state') or (instance and instance.region):
#             state_id = data.get('state') or (instance.region.district.city.state.id if instance and instance.region else None)
#             if state_id:
#                 self.fields['city'].queryset = City.objects.filter(state_id=state_id)
#             else:
#                 self.fields['city'].queryset = City.objects.none()
#         else:
#             self.fields['city'].queryset = City.objects.none()

#         if data.get('city') or (instance and instance.region):
#             city_id = data.get('city') or (instance.region.district.city.id if instance and instance.region else None)
#             if city_id:
#                 self.fields['district'].queryset = District.objects.filter(city_id=city_id)
#             else:
#                 self.fields['district'].queryset = District.objects.none()
#         else:
#             self.fields['district'].queryset = District.objects.none()

#         if data.get('district') or (instance and instance.region):
#             district_id = data.get('district') or (instance.region.district.id if instance and instance.region else None)
#             if district_id:
#                 self.fields['region'].queryset = Region.objects.filter(district_id=district_id)
#             else:
#                 self.fields['region'].queryset = Region.objects.none()
#         else:
#             self.fields['region'].queryset = Region.objects.none()

#         # Handle category cascading
#         if data.get('category') or (instance and instance.subcategory):
#             category_id = data.get('category') or (instance.subcategory.category.id if instance and instance.subcategory else None)
#             if category_id:
#                 self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id)
#             else:
#                 self.fields['subcategory'].queryset = SubCategory.objects.none()
#         else:
#             self.fields['subcategory'].queryset = SubCategory.objects.none()


#     def save(self, commit=True, author=None):
#         instance = super().save(commit=False)
#         if author:
#             instance.author = author
#         if instance.is_published and not instance.published_at:
#             instance.published_at = timezone.now()
#         elif not instance.is_published:
#             instance.published_at = None
#         if commit:
#             instance.save()
#         return instance


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class BlogPostForm(LocationCascadingMixin, CategoryCascadingMixin, UserFormMixin, forms.ModelForm):
    """
    Form for creating and editing blog posts with hierarchical data support.
    
    This form includes support for category and location hierarchies,
    as well as multiple image uploads with proper validation.
    """
    
    # Using ModelChoiceField for proper cascading functionality
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), 
        required=True, 
        empty_label=_("Select Category"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_category'})
    )
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.none(), 
        required=False, 
        empty_label=_("Select Sub-Category"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_subcategory'})
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(), 
        required=False, 
        empty_label=_("Select Country"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_country'})
    )
    state = forms.ModelChoiceField(
        queryset=State.objects.none(), 
        required=False, 
        empty_label=_("Select State"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_state'})
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.none(), 
        required=False, 
        empty_label=_("Select City"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_city'})
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.none(), 
        required=False, 
        empty_label=_("Select District"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_district'})
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(), 
        required=False, 
        empty_label=_("Select Region"),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_region'})
    )

    # Use the custom MultipleFileField
    images = MultipleFileField(
        required=False,
        label=_('Upload Images'),
        help_text=_('Select multiple images to upload. The first image will be set as featured.')
    )
    
    # Related factories field
    related_factories = forms.ModelMultipleChoiceField(
        queryset=Factory.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text=_('Select factories related to this blog post')
    )

    class Meta:
        model = BlogPost
        fields = [
            'title', 'content', 'excerpt', 'category', 'subcategory', 
            'country', 'state', 'city', 'district', 'region', 
            'related_factories', 'is_published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Blog Title')
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 10, 
                'placeholder': _('Write your blog post content here...')
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': _('Brief summary of your blog post...')
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. Populate querysets if we are editing an existing post
        if self.instance and self.instance.pk:
            # Category Hierarchy
            if self.instance.category:
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category=self.instance.category
                )
            
            # Location Hierarchy
            if self.instance.country:
                self.fields['state'].queryset = State.objects.filter(country=self.instance.country)
            if self.instance.state:
                self.fields['city'].queryset = City.objects.filter(state=self.instance.state)
            if self.instance.city:
                self.fields['district'].queryset = District.objects.filter(city=self.instance.city)
            if self.instance.district:
                self.fields['region'].queryset = Region.objects.filter(district=self.instance.district)

        # 2. Maintain support for POST data (if validation fails, keep selections)
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        
        # Set up initial values for edit mode
        if self.instance.pk:
            initial_values = self.get_category_initial_values()
            initial_values.update(self.get_location_initial_values())
            for field, value in initial_values.items():
                if field in self.fields:
                    self.fields[field].initial = value

        # Set up dynamic querysets based on form data
        self.setup_category_fields()
        self.setup_location_fields()

    def save(self, commit=True, author=None):
        """
        Save the form instance with user association and proper field assignment.
        
        Args:
            commit (bool): Whether to save to database immediately
            author (User): User to associate with the instance
        
        Returns:
            BlogPost: The saved blog post instance
        """
        instance = super().save(commit=False)
        data = self.cleaned_data

        # Assign the selected instances directly since we're using ModelChoiceField
        instance.category = data.get('category')
        instance.subcategory = data.get('subcategory')
        instance.country = data.get('country')
        instance.state = data.get('state')
        instance.city = data.get('city')
        instance.district = data.get('district')
        instance.region = data.get('region')

        # Set the author if provided
        if author:
            instance.author = author

        if commit:
            instance.save()

            self.save_m2m()
            
            # Handle multiple images
            images = data.get('images', [])
            if images:
                # Clear existing images if this is an edit
                if self.instance.pk:
                    self.instance.images.all().delete()
                
                # Create new image entries
                for i, image in enumerate(images):
                    BlogImage.objects.create(
                        blog_post=instance,
                        image=image,
                        order=i,
                        is_featured=(i == 0)  # First image is featured by default
                    )
        
        return instance


class BlogImageForm(forms.ModelForm):
    """
    Form for managing individual blog images.
    
    This form handles the upload and management of individual images
    associated with blog posts, including captions and ordering.
    """
    
    class Meta:
        model = BlogImage
        fields = ['image', 'caption', 'is_featured', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Image caption (optional)')
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BlogImageFormSet(forms.BaseInlineFormSet):
    """
    Formset for managing multiple blog images.
    
    This formset provides a way to manage multiple BlogImage forms
    in a single interface, typically used in the admin or inline forms.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False


class BlogPostFilterForm(forms.Form):
    """Form for filtering blog posts similar to factory filter"""
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
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
    is_published = forms.BooleanField(
        required=False,
        initial=False,
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