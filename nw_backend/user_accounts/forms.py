from django import forms
from .models import User, EditorFile

class UserCreationForm(forms.ModelForm):
    """Default user creation form, with password confirmation."""
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
        model = User
        fields = ('username', 'email')

class CreateEditorFile(forms.ModelForm):
    """Form to allow user creation or editing of basic textual EditorFile."""

    title = forms.CharField(
        label="Title Input",
        required=True,
        max_length=50, 
        min_length=1, 
        help_text="Enter the title of your file"
    )

    file_text = forms.CharField(
        label="Text Input",
        widget=forms.Textarea, # Makes the input box large
        required=True,
        max_length=25000, 
        min_length=1, 
        help_text="Enter the text you wish to save to file"
    )

    class Meta:
        model = EditorFile
        fields = ['title', 'file_text']
