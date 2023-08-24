from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        required=True
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
        required=True
    )

    class Meta:
        model = User  # Assuming you're using Django's User model
        fields = ('username', 'email')