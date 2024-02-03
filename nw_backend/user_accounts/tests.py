from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.db import models
from rest_framework import status
from rest_framework.test import APIClient

from .models import User, EditorFile
from .serializers import FileListSerializer, FileCreateSerializer

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

    # Resets the state of the client between tests
    def setUp(self):
        self.client = APIClient()

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

class UserLoginAPIViewTest(TestCase):
    # Resets client between tests and creates a new user.
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test_user', password='test_password')

    def test_user_login_successful(self):
        # Send a POST request with valid login credentials
        response = self.client.post(reverse('login'), {'username': 'test_user', 'password': 'test_password'})
        
        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the response includes the expected detail message
        self.assertIn('Login successful.', response.data['detail'])

    def test_user_login_invalid_credentials(self):
        # Send a POST request with invalid login credentials
        response = self.client.post(reverse('login'), {'username': 'test_user', 'password': 'wrong_password'})

        # Check if the response status code is HTTP 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if the response includes the expected detail message
        self.assertIn('Invalid credentials.', response.data['detail'])

class DocsCreateRetrieveViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test_user', password='test_password')
        self.client.force_authenticate(user=self.user)

    def test_get_docs_list(self):
        # Create a document associated with the authenticated user
        EditorFile.objects.create(author=self.user, title='Test Document', body='Lorem Ipsum')

        # Send a GET request to retrieve the list of documents
        response = self.client.get(reverse('create-view-docs'))

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the serializer used for the response is the correct one
        self.assertIsInstance(response.data, list)
        self.assertEqual(response.data[0]['title'], 'Test Document')

    def test_post_create_new_doc(self):
        # Data for creating a new document
        data = {'title': 'New Document', 'body': 'Hello World'}

        # Send a POST request to create a new document
        response = self.client.post(reverse('create-view-docs'), data)

        # Check if the response is successful (HTTP 201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the serializer used for the response is the correct one
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['title'], 'New Document')

    def test_get_empty_docs_list(self):
        # Send a GET request to retrieve the list of documents for a user with no documents
        response = self.client.get(reverse('create-view-docs'))

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the response contains an empty list
        self.assertEqual(response.data, [])