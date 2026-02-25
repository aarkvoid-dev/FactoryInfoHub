from django import forms
from django.forms import ModelForm
from .models import Worker, WorkExperience
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region

class WorkerForm(ModelForm):
    # Add dynamic category creation fields

    new_category = forms.CharField(required=False, widget=forms.HiddenInput())
    new_subcategory = forms.CharField(required=False, widget=forms.HiddenInput())
    new_state = forms.CharField(required=False, widget=forms.HiddenInput())
    new_city = forms.CharField(required=False, widget=forms.HiddenInput())
    new_district = forms.CharField(required=False, widget=forms.HiddenInput())
    new_region = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Worker
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'email',
            'category', 'subcategory', 'years_of_experience', 'skills', 'availability', 'expected_daily_wage',
            'country', 'state', 'city', 'district', 'region', 'address',
            'is_active', 'is_verified'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'availability': forms.Select(attrs={'class': 'form-control'}),
            'expected_daily_wage': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'full_name': 'Full Name',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'phone_number': 'Phone Number',
            'email': 'Email Address',
            'category': 'Primary Trade/Skill',
            'subcategory': 'Specialization',
            'years_of_experience': 'Years of Experience',
            'skills': 'Core Competencies',
            'availability': 'Work Availability',
            'expected_daily_wage': 'Expected Daily Rate (INR)',
            'country': 'Country',
            'state': 'State/Province',
            'city': 'City/Municipality',
            'district': 'District/Area',
            'region': 'Region',
            'address': 'Complete Address',
            'is_active': 'Profile Active',
            'is_verified': 'Verified Worker',
        }
        help_texts = {
            'skills': 'List your skills separated by commas (e.g., Sewing, Embroidery, Pattern Making)',
            'availability': 'e.g., Full-time, Part-time, Contract, Available immediately',
            'expected_daily_wage': 'Your expected daily wage in Indian Rupees',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make name required
        self.fields['full_name'].required = True
        
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
            # If editing existing worker, show subcategories for its current category
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

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category = cleaned_data.get('new_category')
        subcategory = cleaned_data.get('subcategory')
        new_subcategory = cleaned_data.get('new_subcategory')

        def handle_location(field, new_field_name, model_class, parent_field):
            val = cleaned_data.get(field)
            new_val = cleaned_data.get(new_field_name)
            parent = cleaned_data.get(parent_field)

            if new_val and not val:
                if not parent:
                    self.add_error(field, f"Please select a {parent_field} first.")
                else:
                    obj, _ = model_class.objects.get_or_create(
                        name=new_val.strip(),
                        **{parent_field: parent}
                    )
                    cleaned_data[field] = obj

        # Process location chain
        handle_location('state', 'new_state', State, 'country')
        handle_location('city', 'new_city', City, 'state')
        handle_location('district', 'new_district', District, 'city')
        handle_location('region', 'new_region', Region, 'district')

        # Handle dynamic category creation
        if new_category and not category:
            # Create new category
            category, created = Category.objects.get_or_create(
                name=new_category.strip(),
                defaults={'description': f'Auto-created category: {new_category.strip()}'}
            )
            cleaned_data['category'] = category

        # Handle dynamic subcategory creation
        if new_subcategory and not subcategory:
            parent_category = cleaned_data.get('category')
            if not parent_category:
                self.add_error('new_subcategory', 'Please select or create a category first.')
            else:
                # Create new subcategory
                subcategory, created = SubCategory.objects.get_or_create(
                    name=new_subcategory.strip(),
                    category=parent_category,
                    defaults={'description': f'Auto-created subcategory: {new_subcategory.strip()}'}
                )
                cleaned_data['subcategory'] = subcategory

        return cleaned_data

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['company_name', 'job_title', 'start_date', 'end_date', 'description', 'is_current']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'company_name': 'Company Name',
            'job_title': 'Job Title',
            'start_date': 'Start Date',
            'end_date': 'End Date (leave blank if current)',
            'description': 'Job Description',
            'is_current': 'Currently Employed Here',
        }
        help_texts = {
            'description': 'Brief description of your role and responsibilities',
            'is_current': 'Check if this is your current job',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current = cleaned_data.get('is_current')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date.")

        if is_current and end_date:
            raise forms.ValidationError("If this is your current job, please leave end date blank.")

        return cleaned_data

class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = [
            'full_name', 'date_of_birth', 'gender', 'phone_number', 'email',
            'category', 'subcategory', 'years_of_experience', 'skills', 'availability', 'expected_daily_wage',
            'country', 'state', 'city', 'district', 'region', 'address',
            'is_active', 'is_verified'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'subcategory': forms.Select(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'skills': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'availability': forms.Select(attrs={'class': 'form-control'}),
            'expected_daily_wage': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'district': forms.Select(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        labels = {
            'full_name': 'Full Name',
            'date_of_birth': 'Date of Birth',
            'gender': 'Gender',
            'phone_number': 'Phone Number',
            'email': 'Email Address',
            'category': 'Primary Trade/Skill',
            'subcategory': 'Specialization',
            'years_of_experience': 'Years of Experience',
            'skills': 'Core Competencies',
            'availability': 'Work Availability',
            'expected_daily_wage': 'Expected Daily Rate (INR)',
            'country': 'Country',
            'state': 'State/Province',
            'city': 'City/Municipality',
            'district': 'District/Area',
            'region': 'Region',
            'address': 'Complete Address',
            'is_active': 'Profile Active',
            'is_verified': 'Verified Worker',
        }

class WorkerFilterForm(forms.Form):
    """Form for filtering workers"""
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories"
    )
    subcategory = forms.ModelChoiceField(
        queryset=SubCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Specializations"
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
    availability = forms.ChoiceField(
        choices=[('', 'All Availability')] + Worker.AVAILABILITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_experience = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min years'}),
        label='Min Experience'
    )
    max_wage = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max daily rate'}),
        label='Max Daily Rate'
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
