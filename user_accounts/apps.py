from django.apps import AppConfig

# Register apps here. We may want more than just user account handling eventually.

class UserAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_accounts'
