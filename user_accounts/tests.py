from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.http.cookie import SimpleCookie

from .views import generate_jwt_token

from .models import User, EditorFile

import json


# Tests the registration email view executes correctly.
# Doesn't test if the email sends correctly.
class RegistrationEmailTest(APITestCase):        

    def test_send_registration_email(self):

        # Create a fake request with POST data
        data = {'email': 'test@example.com'}
        response = self.client.post(reverse('register-email'), data)

        # Confirm the response is unsuccessful (test@example.com 
        # is not approved as a recipient by MailGun).
        self.assertEqual(response.status_code, 500)

    def test_invalid_registration_email_address(self):

        # Create a fake request with POST data, using invalid email.
        data = {'email': 'invalid_email'}
        response = self.client.post(reverse('register-email'), data)

        # Check if the response status code is HTTP 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if the response includes the expected detail message
        self.assertIn('Invalid email address.', response.data['detail'])
    
    def test_registration_email_already_registered(self):

        # Create fake account
        email = 'test_user@example.com'
        self.client = APIClient()
        self.user = User.objects.create_user(email=email, username='test')

        # Create a fake request with POST data, 
        # using the email of the account above.
        data = {'email': email}
        response = self.client.post(reverse('register-email'), data)

        # Check if the response status code is HTTP 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if the response includes the expected detail message
        self.assertIn('Account already registered with this email address.', response.data['detail'])


class UserRegistrationAPIViewTest(APITestCase):

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

    def test_invalid_registration_link(self):
        registration_link = self.get_register_link("invalid_email")

        # Try to register with the existing user's email
        response = self.client.post(registration_link,
            {'username': 'test_user', 'password': 'test_password'}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Invalid registration link.', response.data['detail'])

    def test_user_registration_existing_user(self):
        # Create an existing user for testing
        email = 'test_user@example.com'
        existing_user = User.objects.create_user(username='existing_user', email=email)

        registration_link = self.get_register_link(email)

        # Try to register with the existing user's email
        response = self.client.post(registration_link,
            {'username': 'test_user', 'password': 'test_password'}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('Account already registered with this email address.', response.data['detail'])

        # Ensure that the existing user is not modified
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.username, 'existing_user')  # Ensure the username remains the same

class UserLoginAPIViewTest(APITestCase):
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

class DocsCreateRetrieveViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.username ='test_user'

        self.user = User.objects.create_user(username=self.username, password='test_password')

        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})

    def test_get_docs_list(self):
        # Create a document associated with the authenticated user
        EditorFile.objects.create(author=self.username, title='Test Document', body='Lorem Ipsum')
        EditorFile.objects.create(author=self.username, title='Test Document 2', body='Lorem Ipsum')

        # Send a GET request to retrieve the list of documents
        response = self.client.get(reverse('create-view-docs'))

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the response data has the expected structure
        self.assertIsInstance(response.data, dict)
        self.assertIn('files', response.data)
        files = response.data['files']
        self.assertIsInstance(files, list)

        # Check the structure of each file in the 'files' list
        for file_data in files:
            self.assertIsInstance(file_data, dict)
            self.assertIn('_id', file_data)
            self.assertIsInstance(file_data['_id'], str)
            self.assertIn('title', file_data)
            self.assertIsInstance(file_data['title'], str)
            self.assertIn('body', file_data)
            self.assertIsInstance(file_data['body'], str)  
            self.assertIn('created', file_data)
            self.assertIsInstance(file_data['created'], str)  
            self.assertIn('modified', file_data)
            self.assertIsInstance(file_data['modified'], str)  

        # Most recently created document should be listed first.
        self.assertEqual(files[0]['title'], 'Test Document 2')

        self.assertEqual(files[1]['title'], 'Test Document')

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
        self.assertEqual(response.data['files'], [])


class DocRetrieveUpdateDestroyViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')

        # Include the token in the client's request headers
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})


        # Create a test document associated with the user
        self.doc = EditorFile.objects.create(author=self.user, title='Test Document', body='Lorem Ipsum')


    def test_get_selected_doc(self):
        # Send a GET request to retrieve the selected document
        response = self.client.get(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the serializer used for the response is the correct one
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['title'], 'Test Document')

    def test_update_selected_doc(self):
        # Data for updating the document
        updated_data = {'title': 'Updated Document', 'body': 'Updated Content'}

        # Send a PUT request to update the selected document
        response = self.client.put(reverse('edit-doc', kwargs={'pk': self.doc.pk}), updated_data, format='json')

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the serializer used for the response is the correct one
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['title'], 'Updated Document')

    def test_delete_selected_doc(self):
        # Send a DELETE request to delete the selected document
        response = self.client.delete(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        # Check if the response is successful (HTTP 204 No Content)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check if the document has been deleted
        self.assertFalse(EditorFile.objects.filter(pk=self.doc.pk).exists())

    def test_delete_selected_doc_permission_denied(self):
        # Create a new user
        another_username = 'another_user'
        another_user = User.objects.create_user(username=another_username, password='another_password')

        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(another_username)})

        # Send a DELETE request to delete the selected document, but it should fail due to permission denied
        response = self.client.delete(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        # Check if the response is a permission denied error (HTTP 403 Forbidden)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Check if the document still exists
        self.assertTrue(EditorFile.objects.filter(pk=self.doc.pk).exists())

# TODO: Once calling an LLM has actually been implemented in the corresponding view, update this test accordingly.
class GenerateTextTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_generate_text_success(self):
        # Define the request data
        request_data = {
            "promptName": "Test Prompt",
            "messages": [
                {
                    "role": "User",
                    "content": "Generate text for testing"
                }
            ]
        }

        # Convert the request data to JSON format
        json_data = json.dumps(request_data)

        # Send a POST request to the generate_text endpoint
        response = self.client.post(reverse('generate-text'), json_data, content_type='application/json')

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Parse the response JSON
        response_data = json.loads(response.content)

        # Verify the content of the response
        self.assertEqual(response_data['status'], 200)
        self.assertEqual(response_data['message'], 'Text generated successfully')
        self.assertEqual(response_data['data']['promptName'], 'Test Prompt')
        self.assertEqual(response_data['data']['messages'], [{'role': 'User', 'content': 'Generate text for testing'}])

    def test_generate_text_invalid_json(self):
        # Send a POST request with invalid JSON format
        response = self.client.post(reverse('generate-text'), "invalid_json", content_type='application/json')

        # Check if the response indicates invalid JSON format (HTTP 400 Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)