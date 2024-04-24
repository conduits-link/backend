# Generated by Django 5.0.4 on 2024-04-22 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_accounts', '0005_alter_user_credits'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='credits',
            field=models.DecimalField(decimal_places=5, default=0, max_digits=10),
        ),
    ]