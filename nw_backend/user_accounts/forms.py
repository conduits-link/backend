from django import forms
from .models import User, EditorFile

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

class NewEditorFile(forms.ModelForm):

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
