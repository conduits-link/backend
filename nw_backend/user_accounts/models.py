from django.db import models
from django.contrib.auth.models import AbstractUser

class EditorFile(models.Model):

    title = models.CharField(max_length=50, help_text='Title of file')

    # 25000 chars ≈ 5000 words. Temporary length limit.
    file_text = models.CharField(max_length=25000, help_text='Text stored in file')

    date_created = models.DateTimeField()

    class Meta:
        # Order files from most recent to oldest.
        ordering = ['-date_created']

    def __str__(self):
        return self.title
    

class User(AbstractUser):
    pass
