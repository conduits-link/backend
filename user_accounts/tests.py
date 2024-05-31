from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.http.cookie import SimpleCookie

from .views import generate_jwt_token, encode_password_reset_uid, OrderFulfillmentWebhookView
import jwt, json

from .models import User, EditorFile, Prompt
import os , unittest.mock
from openai import AuthenticationError 


def validate_jwt(self, response, username):

    jwt_key = "TODO_CHANGEME_KEY"

    self.assertIn('jwt', response.cookies)

    jwt_cookie = response.cookies["jwt"]
    decoded_token = jwt.decode(jwt_cookie.value, jwt_key, algorithms=["HS256"])
    self.assertEqual(username, decoded_token['username'])

    self.assertEqual(jwt_cookie["httponly"], True)
    self.assertEqual(jwt_cookie["samesite"], 'None')
    self.assertEqual(jwt_cookie["secure"], True)
    self.assertEqual(jwt_cookie["domain"], ".conduits.link")


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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check if the response includes the expected detail message
        self.assertIn('Account already registered with this email address.', response.data['detail'])


class UserRegistrationViewTest(APITestCase):

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
            {'username': 'test_user', 'password': 'test_password'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Account created successfully.', response.data['detail'])

        # Check if the user is actually created in the database
        user = User.objects.filter(email=email).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'test_user') 

        validate_jwt(self, response, user.username)

    def test_invalid_registration_link(self):
        registration_link = self.get_register_link("invalid_email")

        # Try to register with the existing user's email
        response = self.client.post(registration_link,
            {'username': 'test_user', 'password': 'test_password'}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_registration_existing_user(self):
        # Create an existing user for testing
        email = 'test_user@example.com'
        existing_user = User.objects.create_user(username='existing_user', email=email)

        registration_link = self.get_register_link(email)

        # Try to register with the existing user's email
        response = self.client.post(registration_link,
            {'username': 'test_user', 'password': 'test_password'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Account already registered with this email address.', response.data['detail'])

        # Ensure that the existing user is not modified
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.username, 'existing_user')  # Ensure the username remains the same

class UserLoginViewTest(APITestCase):
    # Resets client between tests and creates a new user.
    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')

    def test_user_login_successful(self):
        # Send a POST request with valid login credentials
        response = self.client.post(reverse('login'), {'username': 'test_user', 'password': 'test_password'})
        
        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the response includes the expected detail message
        self.assertIn('Login successful.', response.data['detail'])

        validate_jwt(self, response, self.username)

    def test_user_login_invalid_credentials(self):
        # Send a POST request with invalid login credentials
        response = self.client.post(reverse('login'), {'username': 'test_user', 'password': 'wrong_password'})

        # Check if the response status code is HTTP 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if the response includes the expected detail message
        self.assertIn('Invalid credentials.', response.data['detail'])

class UserForgotAPIViewTestCase(TestCase):
    def test_send_forgot_email(self):

        data = {'email': 'test@example.com'}
        response = self.client.post(reverse('forgot'), data)

        # If email is valid, response should be 200.
        self.assertEqual(response.status_code, 200)

    def test_invalid_forgot_email_address(self):

        # Create a fake request with POST data, using invalid email.
        data = {'email': 'invalid_email'}
        response = self.client.post(reverse('forgot'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check if the response includes the expected detail message
        self.assertIn('Invalid email address.', response.data['detail'])

class UserResetPasswordAPIViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = 'test@example.com'
        self.user = User.objects.create_user(username='test_user', email=self.email, password='old_password')
        self.uid = encode_password_reset_uid(self.email)

    def test_user_reset_password(self):
        
        data = {'password': 'new_password'}

        # Send POST request to the view
        response = self.client.post(reverse('reset', kwargs={'pk': self.uid}), data)

        updated_user = User.objects.get(email=self.email)
        self.assertTrue(updated_user.check_password('new_password'))

        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_reset_password_no_password(self):
        # Data for the request, without required password field
        data = {}

        # Send POST request to the view without providing a password
        response = self.client.post(reverse('reset', kwargs={'pk': self.uid}), data)

        # Check if the response status code is 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], 'No password provided.')


    def test_user_reset_password_invalid_email(self):

        data = {'password': 'new_password'}

        invalid_email_uid = encode_password_reset_uid("not_an_email")

        # Send POST request to the view with an invalid email
        response = self.client.post(reverse('reset', kwargs={'pk': invalid_email_uid}), data)

        # Check if the response status code is 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_reset_password_invalid_date(self):
        invalid_date_uid = urlsafe_base64_encode(force_bytes(self.email+ '|1970-01-01 00:00:00'))

        data = {'password': 'new_password'}

        # Send POST request to the view with an invalid email
        response = self.client.post(reverse('reset', kwargs={'pk': invalid_date_uid}), data)

        # Check if the response status code is 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        self.assertEqual(response.data["detail"], "Sorry, this link has expired.")


class UserLogoutViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_logout(self):

        # Create an account and set the JWT to its value.
        self.username ='test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})

        # Log out and ensure the JWT has been cleared.
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('', response.cookies["jwt"].value)

    def test_logout_no_jwt(self):

        # Try to log out without being logged in.
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_jwt(self):

        # Try to log out with a JWT that doesn't correspond to a user.
        self.client.cookies = SimpleCookie({'jwt': "invalid_JWT"})
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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
        self.assertIn('docs', response.data)
        docs = response.data['docs']
        self.assertIsInstance(docs, list)

        # Check the structure of each file in the 'files' list
        for doc in docs:
            self.assertIsInstance(doc, dict)
            self.assertIn('uid', doc)
            self.assertIsInstance(doc['uid'], str)
            self.assertIn('title', doc)
            self.assertIsInstance(doc['title'], str)
            self.assertIn('body', doc)
            self.assertIsInstance(doc['body'], str)  
            self.assertIn('created', doc)
            self.assertIsInstance(doc['created'], str)  
            self.assertIn('modified', doc)
            self.assertIsInstance(doc['modified'], str)  

        # Most recently created document should be listed first.
        self.assertEqual(docs[0]['title'], 'Test Document 2')

        self.assertEqual(docs[1]['title'], 'Test Document')

    def test_post_create_new_doc(self):
        # Data for creating a new document
        data = {"doc": {'title': 'New Document', 'body': [{'test': 'Hello World'}]}}

        # Send a POST request to create a new document
        response = self.client.post(reverse('create-view-docs'), data, format='json')

        # Check if the response is successful (HTTP 201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the response data is stored in "doc" key.
        self.assertIsInstance(response.data, dict)
        self.assertIn('doc', response.data)

        doc_data = response.data['doc']

        # Check the structure and content of the 'doc' dictionary
        self.assertIsInstance(doc_data, dict)
        self.assertIn('uid', doc_data)
        self.assertIn('created', doc_data)
        self.assertIn('modified', doc_data)

        # Check response matches expected values
        self.assertEqual(doc_data['created'], doc_data['modified'])

        # Retrieve EditorFile object corresponding to response UID
        editor_file = EditorFile.objects.get(uid=doc_data['uid'])

        # Check if the attributes of the EditorFile object match the expected values
        self.assertEqual(editor_file.title, 'New Document')
        self.assertEqual(editor_file.body, [{'test': 'Hello World'}])

    def test_get_empty_docs_list(self):
        # Send a GET request to retrieve the list of documents for a user with no documents
        response = self.client.get(reverse('create-view-docs'))

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the response contains an empty list of docs
        self.assertEqual(response.data['docs'], [])

class DocRetrieveUpdateDestroyViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')

        # Include the token in the client's request headers
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})

        # Create a test document associated with the user
        self.doc = EditorFile.objects.create(author=self.user, title='Test Document', body='Lorem Ipsum')

        # Create another account for authorization testing
        another_username = 'another_user'
        User.objects.create_user(username=another_username, password='another_password')

        self.another_jwt = SimpleCookie({'jwt': generate_jwt_token(another_username)})

    def test_get_selected_doc(self):
        # Send a GET request to retrieve the selected document
        response = self.client.get(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the serializer used for the response is the correct one
        self.assertIsInstance(response.data, dict)

        self.assertEqual(response.data['doc']['title'], 'Test Document')
    
    def test_get_selected_doc_wrong_user(self):
        # Log into another account
        self.client.cookies = self.another_jwt

        # Send a GET request to retrieve the selected document, but it should fail due to permission denied
        response = self.client.get(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_selected_doc(self):
        # Data for updating the document
        updated_data = {'doc': {'title': 'Updated Document', 'body': 'Updated Content'}}

        # Send a PUT request to update the selected document
        response = self.client.put(reverse('edit-doc', kwargs={'pk': self.doc.pk}), updated_data, format='json')

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


        # Check if the serializer used for the response is the correct one
        self.assertIsInstance(response.data, dict)
        self.assertIn('doc', response.data)
        self.assertIn('modified', response.data['doc'])

        # Retrieve the updated document from the database
        updated_doc = EditorFile.objects.get(pk=self.doc.pk)

        # Check updates have been made
        self.assertEqual(updated_doc.title, 'Updated Document')
        self.assertEqual(updated_doc.body, 'Updated Content')

    def test_update_selected_doc_wrong_user(self):

        # Log into another account
        self.client.cookies = self.another_jwt

        updated_data = {'doc': {'title': 'Updated Document', 'body': 'Updated Content'}}

        # Send a PUT request to update the selected document, but it should fail due to permission denied
        response = self.client.put(reverse('edit-doc', kwargs={'pk': self.doc.pk}), updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Retrieve the document from the database
        doc = EditorFile.objects.get(pk=self.doc.pk)

        # Check if the document still has the original title
        self.assertEqual(doc.title, 'Test Document')
        self.assertEqual(doc.body, 'Lorem Ipsum')


    def test_delete_selected_doc(self):
        # Send a DELETE request to delete the selected document
        response = self.client.delete(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        # Check if the response is successful (HTTP 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the message indicates that the document was removed
        self.assertIn('detail', response.data)

        self.assertEqual("The doc was removed.", response.data['detail'])

        # Check if the document has been deleted
        self.assertFalse(EditorFile.objects.filter(pk=self.doc.pk).exists())

    def test_delete_selected_doc_not_logged_in(self):

        # Clear JWT
        self.client.cookies = {}

        # Send a DELETE request to delete the selected document, but it should fail due to permission denied
        response = self.client.delete(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        # Check if the response is a permission denied error (HTTP 403 Forbidden)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if the document still exists
        self.assertTrue(EditorFile.objects.filter(pk=self.doc.pk).exists())

    def test_delete_selected_doc_wrong_user(self):

        # Log into another account
        self.client.cookies = self.another_jwt

        # Send a DELETE request to delete the selected document, but it should fail due to permission denied
        response = self.client.delete(reverse('edit-doc', kwargs={'pk': self.doc.pk}))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Check if the document still exists
        self.assertTrue(EditorFile.objects.filter(pk=self.doc.pk).exists())

class PromptViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')
        self.url = reverse('prompts')

        # Include the token in the client's request headers
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})        

    def test_get_prompts_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_prompts_nonempty(self):
        prompt1 = Prompt.objects.create(user=self.user, name="Test", prompt="Test prompt")
        prompt2 = Prompt.objects.create(user=self.user, name="Test2", prompt="Test prompt 2")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {"uid": str(prompt1.uid), "name": "Test", "prompt": "Test prompt"},
            {"uid": str(prompt2.uid), "name": "Test2", "prompt": "Test prompt 2"}
        ]
        self.assertEqual(response.data, expected_data)

    def test_post_single_prompt(self):
        data = {"name": "Test", "prompt": "Test prompt"}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.prompts.count(), 1)
        self.assertEqual(self.user.prompts.first().name, "Test")
        self.assertEqual(self.user.prompts.first().prompt, "Test prompt")


    def test_post_prompts_duplicate_name(self):
        Prompt.objects.create(user=self.user, name="Test", prompt="Test prompt")

        # Try and create a prompt with a duplicate name
        data = {"name": "Test", "prompt": "Test prompt 2"}
        response = self.client.post(self.url, data, format='json')

        # Response should fail.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_prompts_unauthenticated(self):
        # Log out.
        self.client.cookies = SimpleCookie({})
        response = self.client.get(reverse('prompts'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_prompts_unauthenticated(self):
        # Log out.
        self.client.cookies = SimpleCookie({})
        response = self.client.post(reverse('prompts'), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class PromptDetailViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')
        self.prompt = Prompt.objects.create(user=self.user, name="Test", prompt="Test prompt")
        self.url_name = 'prompts-detail'
        self.url = reverse(self.url_name, kwargs={'pk': self.prompt.uid})

        # Include the token in the client's request headers
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})

    def test_get_prompt(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {"uid": str(self.prompt.uid), "name": "Test", "prompt": "Test prompt"}
        self.assertEqual(response.data, expected_data)

    def test_get_nonexistent_prompt(self):
        url = reverse(self.url_name, kwargs={'pk': 'nonexistent_id'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_prompt(self):
        data = {"name": "Updated Test", "prompt": "Updated prompt"}

        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.prompt.refresh_from_db()
        self.assertEqual(self.prompt.name, "Updated Test")
        self.assertEqual(self.prompt.prompt, "Updated prompt")

    def test_update_nonexistent_prompt(self):
        url = reverse(self.url_name, kwargs={'pk': 'nonexistent_id'})
        data = {"name": "Updated Test", "prompt": "Updated prompt"}

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_prompt(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Prompt.objects.filter(uid=self.prompt.uid).exists())

    def test_delete_nonexistent_prompt(self):
        url = reverse(self.url_name, kwargs={'pk': 'nonexistent_id'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GenerateTextTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password', credits=100)

        # Include the token in the client's request headers
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})

        self.request_data = {
            "prompt": {
                "name": "Test Prompt",
                "messages": [
                    {
                        "role": "user",
                        "content": "Please add more detail to the following text. Do not add information for the sake of it, simply add more relevant information that will enhance the value of the information. The text input is the following: 'The sky is blue.'"
                    }
                ]
            }
        }

    # Use invalid OpenAI API key to avoid spending money during tests.
    @unittest.mock.patch.dict(os.environ, {"OPENAI_API_KEY": "invalid_key"})
    def test_generate_text_success(self):

        try: # Send a POST request to the generate_text endpoint
            response = self.client.post(reverse('generate-text'), self.request_data, format='json')
        except AuthenticationError as e:
            response = e

        # Check if the response is unauthorized due to invalid key
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.code, "invalid_api_key")

    def test_generate_text_invalid_json(self):
        # Send a POST request with invalid JSON format
        response = self.client.post(reverse('generate-text'), "invalid_json", content_type='application/json')

        # Check if the response indicates invalid JSON format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Send a POST request with invalid JSON format - no "role" entry.
        response = self.client.post(reverse('generate-text'), 
            {"prompt": 
                {
                    "name": "Test Prompt",
                    "messages": [
                        {
                            "content": "Please add more detail to the following text. Do not add information for the sake of it, simply add more relevant information that will enhance the value of the information. The text input is the following: 'The sky is blue.'"
                        }
                    ]
                }
            }, content_type='application/json'
        )

        # Check if the response indicates invalid JSON format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Send a POST request with invalid JSON format - no "content" entry.
        response = self.client.post(reverse('generate-text'), 
            {"prompt": 
                {
                    "name": "Test Prompt",
                    "messages": [
                        {
                            "role": "user"
                        }
                    ]
                }
            }, content_type='application/json'
        )

        # Check if the response indicates invalid JSON format
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_text_not_logged_in(self):
        # Log out.
        self.client.cookies = SimpleCookie({})

        # Send a POST request with invalid JSON format
        response = self.client.post(reverse('generate-text'), self.request_data, content_type='application/json')

        # Check if the response indicates invalid JSON format
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # TODO: add tests for different credits scenarios.

class UserCreditsViewTest(APITestCase):
    """
    Test all aspects of UserCreditsView that do not depend on Stripe.
    """
    def setUp(self):
        # Create a user for testing
        self.client = APIClient()

        self.username ='test_user'

        self.user = User.objects.create_user(username=self.username, password='test_password', email='test@example.com')

    def login(self):
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})

    def test_get_credits_authenticated(self):

        self.login()

        response = self.client.get(reverse('credits'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['credits'], self.user.credits)

    def test_get_credits_unauthenticated(self):
        response = self.client.get(reverse('credits'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_credits_authenticated(self):
        self.login()

        response = self.client.post(reverse('credits'), {}, content_type='application/json')

        # Stripe webhook should return URL for payment input.
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_post_credits_unauthenticated(self):
        response = self.client.post(reverse('credits'), {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderFulfillmentViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')

    def test_fulfill_order(self):

        # Mock of the Stripe checkout_session data, with the fields we require.
        session = {
            "metadata": {"username": "test_user"},
            "line_items": {"data": [{"amount_total": 10}]}
        }

        # Send data to fulfill_order, bypassing Stripe webhook function.
        view = OrderFulfillmentWebhookView()
        view.fulfill_order(session)

        # Check if the user's credits have been updated.
        self.user.refresh_from_db()
        self.assertEqual(self.user.credits, 10)

class CreditsSessionIDViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.username = 'test_user'
        self.user = User.objects.create_user(username=self.username, password='test_password')
        self.client.cookies = SimpleCookie({'jwt': generate_jwt_token(self.username)})
        self.pk = "test_pk"

        self.session_data = {
            "id": self.pk,
            "metadata": {"username": self.username},
            "status": "complete",
            "amount_total": 100
        }

    @unittest.mock.patch("stripe.checkout.Session.retrieve")
    def test_successful_payment(self, mock_session_retrieve):
        mock_session_retrieve.return_value = self.session_data

        url = reverse("credits-sessionid", args=[self.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "Payment successful.")
        self.assertEqual(response.data["added_credits"], 100)

    @unittest.mock.patch("stripe.checkout.Session.retrieve")
    def test_unsuccessful_payment(self, mock_session_retrieve):
        self.session_data["status"] = "incomplete"
        mock_session_retrieve.return_value = self.session_data

        url = reverse("credits-sessionid", args=[self.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertEqual(response.data["status"], "Payment unsuccessful.")

    @unittest.mock.patch("stripe.checkout.Session.retrieve")
    def test_unauthorized_user(self, mock_session_retrieve):
        self.client.cookies = SimpleCookie({})

        mock_session_retrieve.return_value = self.session_data

        url = reverse("credits-sessionid", args=[self.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "Unauthorized")


    def test_invalid_session_id(self):

        url = reverse("credits-sessionid", args=["invalid_pk"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
