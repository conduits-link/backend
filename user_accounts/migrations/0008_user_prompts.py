# Generated by Django 5.0.4 on 2024-04-24 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_accounts', '0007_alter_user_credits'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='prompts',
            field=models.JSONField(default=list),
        ),
    ]