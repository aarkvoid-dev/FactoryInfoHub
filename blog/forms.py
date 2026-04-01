"""
Blog application forms module.

This module contains all the form classes for the blog application,
including blog post forms, image forms, and formsets for image management.

Classes:
    BlogPostForm: Form for creating and editing blog posts
    BlogImageForm: Form for managing individual blog images
    BlogImageFormSet: Formset for managing multiple blog images
"""

import hashlib
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
from tinymce.widgets import TinyMCE

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
    
    # Using ModelChoiceField for proper cascading functionality with Select2 tags support
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), 
        required=True, 
        empty_label=_("Select Category"),
        widget=forms.Select(attrs={'class': 'form-control select2-searchable', 'id': 'id_category'})
    )
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.none(), 
        required=False, 
        empty_label=_("Select Sub-Category"),
        widget=forms.Select(attrs={'class': 'form-control select2-searchable', 'id': 'id_subcategory'})
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(), 
        required=False, 
        empty_label=_("Select Country"),
        widget=forms.Select(attrs={'class': 'form-control select2-searchable', 'id': 'id_country'})
    )
    state = forms.ModelChoiceField(
        queryset=State.objects.none(), 
        required=False, 
        empty_label=_("Select State"),
        widget=forms.Select(attrs={'class': 'form-control select2-searchable', 'id': 'id_state'})
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.none(), 
        required=False, 
        empty_label=_("Select City"),
        widget=forms.Select(attrs={'class': 'form-control select2-searchable', 'id': 'id_city'})
    )
    district = forms.ModelChoiceField(
        queryset=District.objects.none(), 
        required=False, 
        empty_label=_("Select District"),
        widget=forms.Select(attrs={'class': 'form-control select2-searchable', 'id': 'id_district'})
    )
    region = forms.ModelChoiceField(
        queryset=Region.objects.none(), 
        required=False, 
        empty_label=_("Select Region"),
        widget=forms.Select(attrs={'class': 'form-control select2-searchable', 'id': 'id_region'})
    )

    # Use the custom MultipleFileField
    images = MultipleFileField(
        required=False,
        label=_('Upload Images'),
        help_text=_('Select multiple images to upload. The first image will be set as featured. Recommended: High-quality images in JPG/PNG format, minimum 800x600 pixels')
    )
    
    # Related factories field
    related_factories = forms.ModelMultipleChoiceField(
        queryset=Factory.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text=_('Select factories that are relevant to your blog post content. This helps readers discover related businesses')
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
                'placeholder': _('e.g., "Top 10 Textile Manufacturing Trends in 2024"')
            }),
            'content': TinyMCE(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': _('e.g., Share your insights about the industry, include statistics, examples, and practical tips...')
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': _('e.g., Discover the latest trends shaping the textile industry in 2024...')
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'title': 'Catchy and descriptive title for your blog post (max 200 characters). Make it engaging to attract readers.',
            'content': 'Main content of your blog post. Use paragraphs, bullet points, and formatting to make it engaging and easy to read. Include relevant keywords for better search visibility.',
            'excerpt': 'Brief summary of your blog post that appears in search results and listings (150-200 characters recommended). This is what users will see before clicking to read more.',
            'category': 'Main category that best represents your blog post topic and industry focus.',
            'subcategory': 'More specific subcategory within the selected main category to help with content organization and discovery.',
            'country': 'Country related to your blog post content (optional). Select if your content is location-specific.',
            'state': 'State or province related to your blog post content (optional). Select if your content is region-specific.',
            'city': 'City or municipality related to your blog post content (optional). Select if your content is city-specific.',
            'district': 'District or area related to your blog post content (optional). Select for more specific location targeting.',
            'region': 'Specific region or locality related to your blog post content (optional). Use for hyper-local content.',
            'related_factories': 'Select factories that are relevant to your blog post content. This helps readers discover related businesses and improves content relevance.',
            'is_published': 'Check to publish your blog post immediately and make it visible to all users. Uncheck to save as draft for later publishing.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set all required fields
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['excerpt'].required = True
        self.fields['category'].required = True
        self.fields['subcategory'].required = True
        self.fields['state'].required = True
        self.fields['city'].required = True
        self.fields['district'].required = True
        self.fields['region'].required = True

        # For edit mode, set initial values but keep querysets unrestricted
        # This allows JavaScript to handle the cascading properly
        if self.instance.pk:
            if self.instance.region:
                region = self.instance.region
                district = region.district
                city = district.city
                state = city.state
                country = state.country
                
                # Set initial values explicitly
                self.fields['country'].initial = country
                self.fields['state'].initial = state
                self.fields['city'].initial = city
                self.fields['district'].initial = district
                self.fields['region'].initial = region
            elif self.instance.district:
                district = self.instance.district
                city = district.city
                state = city.state
                country = state.country
                
                self.fields['country'].initial = country
                self.fields['state'].initial = state
                self.fields['city'].initial = city
                self.fields['district'].initial = district
            elif self.instance.city:
                city = self.instance.city
                state = city.state
                country = state.country
                
                self.fields['country'].initial = country
                self.fields['state'].initial = state
                self.fields['city'].initial = city
            elif self.instance.state:
                state = self.instance.state
                country = state.country
                
                self.fields['country'].initial = country
                self.fields['state'].initial = state
            elif self.instance.country:
                self.fields['country'].initial = self.instance.country

        # Keep all querysets unrestricted to allow JavaScript cascading
        # The JavaScript will handle loading the correct options via AJAX
        self.fields['country'].queryset = Country.objects.all()
        self.fields['state'].queryset = State.objects.all()
        self.fields['city'].queryset = City.objects.all()
        self.fields['district'].queryset = District.objects.all()
        self.fields['region'].queryset = Region.objects.all()
        self.fields['subcategory'].queryset = SubCategory.objects.filter(is_active=True)


    def save(self, commit=True, author=None):
        instance = super().save(commit=False)
        if author:
            instance.author = author

        if commit:
            instance.save()
            self.save_m2m()

            # Handle new images - only if images were uploaded
            images = self.cleaned_data.get('images', [])
            if images:
                # Use content-based deduplication to prevent duplicates
                # This works even when Django generates unique filenames
                
                # Get existing image content hashes from database
                existing_hashes = set()
                for blog_image in instance.images.all():
                    try:
                        with blog_image.image.open('rb') as f:
                            content = f.read()
                            file_hash = hashlib.md5(content).hexdigest()
                            existing_hashes.add(file_hash)
                    except Exception as e:
                        print(f"Error reading existing image {blog_image.image.name}: {e}")
                        continue
                
                # Log image processing for debugging
                print(f"Processing {len(images)} images for blog post: {instance.title}")
                print(f"Existing image hashes: {existing_hashes}")
                
                # Filter out images that already exist based on content hash
                new_images = []
                for image in images:
                    try:
                        # Read image content and calculate hash
                        image.seek(0)  # Reset file pointer to beginning
                        content = image.read()
                        file_hash = hashlib.md5(content).hexdigest()
                        
                        if file_hash not in existing_hashes:
                            new_images.append((image, file_hash))
                            print(f"New image to save: {image.name} (hash: {file_hash})")
                            existing_hashes.add(file_hash)  # Add to set to prevent processing same file multiple times in this request
                        else:
                            print(f"Image content already exists, skipping: {image.name} (hash: {file_hash})")
                    except Exception as e:
                        print(f"Error processing image {image.name}: {e}")
                        continue
                
                if not new_images:
                    print("No new images to save")
                    return instance
                
                # For new blog posts, create images starting from order 0
                if not instance.pk:
                    for i, (image, file_hash) in enumerate(new_images):
                        BlogImage.objects.create(
                            blog_post=instance,
                            image=image,
                            order=i,
                            is_featured=(i == 0)  # First image is featured by default
                        )
                # For existing blog posts, append new images to existing ones
                else:
                    # Get the next order number after existing images
                    next_order = instance.images.count()
                    print(f"Appending {len(new_images)} new images to existing blog post. Next order: {next_order}")
                    for i, (image, file_hash) in enumerate(new_images):
                        BlogImage.objects.create(
                            blog_post=instance,
                            image=image,
                            order=next_order + i,
                            is_featured=False  # Don't set as featured when appending to existing images
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