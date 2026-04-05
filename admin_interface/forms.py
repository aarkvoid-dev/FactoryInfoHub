from django import forms
from django.contrib.auth.models import User
from Karkahan.models import Factory,PaymentGateway,Order,OrderItem
from Workers.models import Worker, WorkExperience
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from Accounts.models import Profile
from blog.models import BlogPost, BlogImage
from Home.models import HomePageVideo, Page, PageSection
from faq.models import FAQQuestion
from tinymce.widgets import TinyMCE

class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['factory', 'profile_image', 'date_of_birth', 'gender', 'phone_number', 'address', 'role', 'email_notifications', 'in_app_notifications', 'user']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MultipleFileInput(forms.FileInput):
    """Custom widget that supports multiple file uploads"""
    def __init__(self, attrs=None):
        # Initialize without the multiple attribute first
        super().__init__(attrs)
        # Then add the multiple attribute directly
        self.attrs['multiple'] = 'multiple'

class AdminFactoryForm(forms.ModelForm):
    # Add image field for factory images with multiple file support
    image = forms.ImageField(required=False, widget=MultipleFileInput(attrs={
        'class': 'form-control',
        'accept': 'image/*',
    }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize dependent fields with empty choices if it's a new form (Create)
        # Or keep existing choices if it's an Edit form
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
    
    class Meta:
        model = Factory
        fields = ['name', 'slug', 'description', 'category', 'subcategory', 'country', 'state', 'city', 'district', 'region', 'address', 'pincode', 'contact_person', 'contact_phone', 'contact_email', 'website', 'established_year', 'employee_count', 'annual_turnover', 'factory_type', 'production_capacity', 'working_hours', 'holidays', 'video_url', 'created_by', 'is_active', 'is_verified']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter factory name'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated slug'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter factory description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter factory address'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter pincode'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact person name'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact phone'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter contact email'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter website URL'}),
            'established_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter established year'}),
            'employee_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter employee count'}),
            'annual_turnover': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter annual turnover'}),
            'factory_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter factory type (e.g., Manufacturing, Assembly)'}),
            'production_capacity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter production capacity'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter working hours'}),
            'holidays': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List holidays observed'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter YouTube or Vimeo link'}),
            'created_by': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AdminWorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'email',
            'category', 'subcategory', 'years_of_experience', 'skills',
            'availability', 'expected_daily_wage', 'country', 'state', 'city',
            'district', 'region', 'address', 'is_active', 'is_verified',
            'created_by'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter years of experience'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'List skills and competencies'}),
            'availability': forms.Select(attrs={'class': 'form-control'}),
            'expected_daily_wage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter expected daily wage'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'created_by': forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'}),
            'created_at': forms.DateTimeInput(attrs={'class': 'form-control', 'disabled': 'disabled', 'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Mark required fields
        self.fields['full_name'].required = True
        self.fields['category'].required = True
        self.fields['years_of_experience'].required = True

        # ---------- Category/subcategory cascading ----------
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=category_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.filter(
                is_active=True
            ).order_by('name')
        else:
            self.fields['subcategory'].queryset = SubCategory.objects.none()

        # ---------- Location cascading ----------
        # Country → State
        if 'country' in self.data:
            try:
                country_id = int(self.data.get('country'))
                self.fields['state'].queryset = State.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.country:
            self.fields['state'].queryset = self.instance.country.states.all().order_by('name')
        else:
            self.fields['state'].queryset = State.objects.none()

        # State → City
        if 'state' in self.data:
            try:
                state_id = int(self.data.get('state'))
                self.fields['city'].queryset = City.objects.filter(state_id=state_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.state:
            self.fields['city'].queryset = self.instance.state.cities.all().order_by('name')
        else:
            self.fields['city'].queryset = City.objects.none()

        # City → District
        if 'city' in self.data:
            try:
                city_id = int(self.data.get('city'))
                self.fields['district'].queryset = District.objects.filter(city_id=city_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.city:
            self.fields['district'].queryset = self.instance.city.districts.all().order_by('name')
        else:
            self.fields['district'].queryset = District.objects.none()

        # District → Region
        if 'district' in self.data:
            try:
                district_id = int(self.data.get('district'))
                self.fields['region'].queryset = Region.objects.filter(district_id=district_id).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.district:
            self.fields['region'].queryset = self.instance.district.regions.all().order_by('name')
        else:
            self.fields['region'].queryset = Region.objects.none()

class ReportForm(forms.Form):
    REPORT_TYPES = [
        ('factory', 'Factory Data Report'),
        ('worker', 'Worker Data Report'),
        ('combined', 'Combined Report'),
    ]

    FORMATS = [
        ('excel', 'Excel (.xlsx)'),
        ('csv', 'CSV (.csv)'),
        ('pdf', 'PDF (.pdf)'),
    ]

    report_type = forms.ChoiceField(choices=REPORT_TYPES, label='Report Type')
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Start Date')
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='End Date')
    format = forms.ChoiceField(choices=FORMATS, label='Format')

class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['email_notifications', 'in_app_notifications']

# Admin Forms for Location Management
class AdminLocationForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location code (optional)'
            }),
        }

class AdminCountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter country name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter country code (e.g., IN, US)'
            }),
        }

class AdminStateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = ['name', 'code', 'country']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter state code'
            }),
            'country': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

class AdminCityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name', 'code', 'state']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter city code'
            }),
            'state': forms.Select(attrs={
                'class': 'form-control'
            })
        }

class AdminDistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['name', 'code', 'city']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter district name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter district code'
            }),
            'city': forms.Select(attrs={
                'class': 'form-control'
            })
        }

class AdminRegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name', 'code', 'district']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter region name'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter region code'
            }),
            'district': forms.Select(attrs={
                'class': 'form-control'
            })
        }

# Admin Forms for Category Management
class AdminCategoryForm(forms.ModelForm):
    class Meta:
        model = Category  # Default to Category, will be overridden in views
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category description',
                'rows': 3
            }),
        }

class AdminSubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['name', 'description', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subcategory name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter subcategory description',
                'rows': 3
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

# Admin Forms for Blog Management
class AdminBlogForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(
                    category_id=category_id, is_active=True
                ).order_by('name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            # If editing existing blog post, show subcategories for its current category
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
    
    class Meta:
        model = BlogPost
        fields = ['title', 'slug', 'content', 'excerpt', 'author', 'category', 'subcategory', 'country', 'state', 'city', 'district', 'region', 'related_factories', 'is_published', 'published_at', 'is_deleted']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter blog post title'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated slug'
            }),
            'content': TinyMCE(attrs={
                'class': 'form-control',
                'placeholder': 'Enter blog post content with inline images',
                'rows': 12,
                # TinyMCE configuration for image upload and inline editing
                'width': '100%',
                'height': 500,
                'toolbar': 'undo redo | formatselect | bold italic backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | image media link | code',
                'plugins': 'advlist autolink lists link image charmap preview anchor pagebreak searchreplace wordcount visualblocks visualchars code fullscreen media table help',
                'image_title': True,
                'automatic_uploads': True,
                'file_picker_types': 'image',
                'relative_urls': False,
                'remove_script_host': False,
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter brief summary of the post',
                'rows': 3
            }),
            'author': forms.Select(attrs={
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subcategory': forms.Select(attrs={
                'class': 'form-control'
            }),
            'country': forms.Select(attrs={
                'class': 'form-control'
            }),
            'state': forms.Select(attrs={
                'class': 'form-control'
            }),
            'city': forms.Select(attrs={
                'class': 'form-control'
            }),
            'district': forms.Select(attrs={
                'class': 'form-control'
            }),
            'region': forms.Select(attrs={
                'class': 'form-control'
            }),
            'related_factories': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
            'published_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }

class AdminBlogImageForm(forms.ModelForm):
    class Meta:
        model = BlogImage
        fields = ['blog_post', 'image', 'caption', 'is_featured', 'order']
        widgets = {
            'blog_post': forms.Select(attrs={
                'class': 'form-control'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image caption (optional)'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter order number'
            }),
        }

# Admin Forms for Worker Experience Management
class AdminWorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['worker', 'company_name', 'job_title', 'start_date', 'end_date', 'description', 'is_current']
        widgets = {
            'worker': forms.Select(attrs={
                'class': 'form-control'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter company name'
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter job title'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter job description'
            }),
            'is_current': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

# Admin Forms for Home Page Management
class AdminHomePageVideoForm(forms.ModelForm):
    class Meta:
        model = HomePageVideo
        fields = ['title', 'video', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter video title'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }



class AdminFAQQuestionForm(forms.ModelForm):
    class Meta:
        model = FAQQuestion
        fields = ['title', 'question_text', 'answer_text', 'category', 'tags', 'status', 'is_featured', 'order', 'published_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter question title'}),
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter the question text'}),
            'answer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 8, 'placeholder': 'Enter the answer text'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter tags separated by commas'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Order number'}),
            'published_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['question_text'].required = True
        self.fields['answer_text'].required = True
        self.fields['category'].required = True
        if not self.instance.pk and not self.data.get('order'):
            self.fields['order'].initial = 0


# Admin Forms for Payment Management
class AdminPaymentGatewayForm(forms.ModelForm):
    class Meta:
        model = PaymentGateway
        fields = ['name', 'is_active', 'key_id', 'key_secret', 'webhook_secret', 'mode']
        widgets = {
            'name': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'key_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter API Key ID (e.g., publishable key)'
            }),
            'key_secret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter API Secret Key'
            }),
            'webhook_secret': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Webhook signing secret'
            }),
            'mode': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

class AdminOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['user', 'total_amount', 'payment_status', 'payment_method', 'gateway_used', 'transaction_id', 'receipt_sent', 'email_status', 'email_retry_count']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-control'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter total amount'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_method': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter payment method (e.g., card, upi, netbanking)'
            }),
            'gateway_used': forms.Select(attrs={
                'class': 'form-control'
            }),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter transaction ID'
            }),
            'receipt_sent': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'email_retry_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'
            }),
        }

class AdminOrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['order', 'factory', 'price_at_purchase']
        widgets = {
            'order': forms.Select(attrs={
                'class': 'form-control'
            }),
            'factory': forms.Select(attrs={
                'class': 'form-control'
            }),
            'price_at_purchase': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter price at purchase'
            }),
        }


# Admin Forms for Page Management
class AdminPageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title','order', 'slug', 'page_type', 'content', 'meta_title', 'meta_description', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter page title'
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Order number'}),

            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated slug'
            }),
            'page_type': forms.Select(choices=Page.PAGE_TYPES, attrs={
                'class': 'form-control'
            }),
            'content': TinyMCE(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Enter page content'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter meta title (optional)'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter meta description (optional)'
            }),
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if not self.instance.pk and not self.data.get('order'):
                self.fields['order'].initial = 0

class AdminPageSectionForm(forms.ModelForm):
    class Meta:
        model = PageSection
        fields = ['page', 'title', 'content', 'order']
        widgets = {
            'page': forms.Select(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter section title'
            }),
            'content': TinyMCE(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Enter section content'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter order number'
            }),
        }
