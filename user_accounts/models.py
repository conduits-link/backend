from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser 
from django.core.validators import MinValueValidator
import uuid

class EditorFile(models.Model):
    """Class to represent a basic text file in our database."""

    uid = models.CharField(max_length=50, primary_key=True, default=uuid.uuid4, editable=False, help_text='ID of file')

    title = models.CharField(max_length=50, help_text='Title of file')

    # 25000 chars ≈ 5000 words.
    body = models.JSONField(default=list, help_text='Text stored in file')

    author = models.CharField(max_length = 20, help_text='Username of file creator')

    # Automatically set when file is made
    created = models.DateTimeField(auto_now_add=True) 

    # Automatically set when file is modified
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        # Order files from most recent to oldest.
        ordering = ['-created']

    def get_absolute_url(self):
        """Returns the URL to access a particular instance of EditorFile."""
        return reverse('file-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the EditorFile object (in Admin site etc.)."""
        return self.title

class User(AbstractUser):
    """Class to store user information in our database."""

    # Store LLM API credits.
    # Float field to we can subtract fractions of a credit for small prompts.
    # Negative credits are permitted to allow for Tiktoken price estimation errors.
    credits = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.username