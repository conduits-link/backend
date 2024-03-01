import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nw_backend.settings')
django.setup()

from user_accounts.models import User


def create_test_user(username, password, email):
    try:
        User.objects.create_user(username=username, password=password, email=email)
        print(f"Test user '{username}' created successfully.")
    except Exception as e:
        print(f"Error creating test user: {e}")

if __name__ == "__main__":
    create_test_user("testuser", "testpassword", "test@example.com")
