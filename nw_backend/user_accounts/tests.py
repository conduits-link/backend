from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status

from .models import User

# Tests the registration email view executes correctly.
# Doesn't test if the email sends correctly.
class RegistrationEmailTest(TestCase):
    def test_send_registration_email(self):

        # Create a fake request with POST data
        data = {'email': 'test@example.com'}
        response = self.client.post(reverse('register-email'), data)

        # Check if the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'Email sent successfully'})

class UserRegistrationAPIViewTest(TestCase):

    # Create a registration link for a test email
    def get_register_link(self, email):
        uid = urlsafe_base64_encode(force_bytes(email))
        return reverse('register-account', kwargs={'pk': uid})

    def test_user_registration_success(self):

        email = 'test_user@example.com'

        registration_link = self.get_register_link(email)

        # Simulate following the registration link for the given email address
        response = self.client.post(registration_link,
            {'username': 'test_user', 'password': 'secure_password'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Account created successfully.', response.data['detail'])

        # Check if the user is actually created in the database
        user = User.objects.filter(email=email).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'test_user')  # Assuming your serializer assigns a default username

    def test_user_registration_existing_user(self):
        # Create an existing user for testing
        email = 'test_user@example.com'
        existing_user = User.objects.create_user(username='existing_user', email=email, password='password123')

        registration_link = self.get_register_link(email)

        # Try to register with the existing user's email
        response = self.client.post(registration_link,
            {'username': 'test_user', 'password': 'test_password'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Account already exists for this email.', response.data['detail'])

        # Ensure that the existing user is not modified
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.username, 'existing_user')  # Ensure the username remains the same
