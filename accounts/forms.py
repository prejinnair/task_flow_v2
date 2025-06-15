from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from projects.models import *
from accounts.models import UserPermission, UserProfile
class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password',)

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match!')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with that email already exists.")
        return email



class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full mt-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary focus:border-primary',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        }),
        label="Email",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full mt-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-2 focus:ring-primary focus:border-primary',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
        label="Password",
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email or not password:
            raise forms.ValidationError("Both email and password are required.")
        return cleaned_data

class UserAdminForm(forms.ModelForm):
    teams = forms.ModelMultipleChoiceField(queryset=Team.objects.all(), required=False)
    projects = forms.ModelMultipleChoiceField(queryset=Project.objects.all(), required=False)
    permissions = forms.ModelMultipleChoiceField(queryset=UserPermission.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'role', 'teams', 'projects', 'permissions']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...', 'class': 'w-full p-2 border rounded'}),
        }
