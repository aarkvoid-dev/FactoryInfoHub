"""
Accounts application forms module.

This module contains all the form classes for user authentication, registration,
profile management, and password handling with proper internationalization support.

Classes:
    CustomUserCreationForm: Form for user registration
    CustomUserChangeForm: Form for user profile editing
    CustomPasswordChangeForm: Form for password changes
    CustomPasswordResetForm: Form for password reset requests
    CustomSetPasswordForm: Form for setting new passwords
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form with enhanced validation and internationalization.
    
    This form extends Django's UserCreationForm to include email, first name,
    and last name fields with proper validation and internationalization support.
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address')
        }),
        help_text=_('We will use this email for account notifications')
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your first name')
        }),
        help_text=_('Your first name as it appears on official documents')
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your last name')
        }),
        help_text=_('Your last name as it appears on official documents')
    )

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Choose a username')
            }),
            'password1': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter a strong password')
            }),
            'password2': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': _('Confirm your password')
            }),
        }
        help_texts = {
            'username': _('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        }

    def clean_username(self):
        """
        Validate username uniqueness.
        
        Returns:
            str: The cleaned username if valid
            
        Raises:
            ValidationError: If username already exists
        """
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError(_('A user with that username already exists.'))
        return username

    def clean_email(self):
        """
        Validate email uniqueness.
        
        Returns:
            str: The cleaned email if valid
            
        Raises:
            ValidationError: If email already exists
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with that email address already exists.'))
        return email

    def clean_password2(self):
        """
        Validate that both password fields match.
        
        Returns:
            str: The cleaned password2 if valid
            
        Raises:
            ValidationError: If passwords don't match
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("The two password fields didn't match."))
        return password2

    def save(self, commit=True):
        """
        Save the user with additional profile information.
        
        Args:
            commit (bool): Whether to save to database immediately
            
        Returns:
            User: The created user instance
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    """
    Custom user profile editing form.
    
    This form allows users to edit their profile information including
    username, email, first name, and last name with proper validation.
    """
    
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Username')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Email address')
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('First name')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Last name')
            }),
        }

    def clean_email(self):
        """
        Validate email uniqueness excluding current user.
        
        Returns:
            str: The cleaned email if valid
            
        Raises:
            ValidationError: If email already exists for another user
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError(_('A user with that email address already exists.'))
        return email


class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Custom password change form with enhanced styling and internationalization.
    
    This form extends Django's PasswordChangeForm with custom styling
    and internationalization support.
    """
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Current password')
        }),
        label=_("Old password")
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('New password')
        }),
        label=_("New password")
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm new password')
        }),
        label=_("Confirm new password")
    )


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset request form.
    
    This form extends Django's PasswordResetForm with custom styling
    and internationalization support for password reset requests.
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address')
        }),
        max_length=254,
        help_text=_('Enter the email address associated with your account')
    )


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom password setting form for password reset confirmation.
    
    This form extends Django's SetPasswordForm with custom styling
    and internationalization support for setting new passwords.
    """
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter new password')
        }),
        strip=False,
        help_text=_('Your password must be at least 8 characters long.')
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm new password')
        }),
        strip=False,
        help_text=_('Enter the same password as before, for verification.')
    )
