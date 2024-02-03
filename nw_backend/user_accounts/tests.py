from django.test import TestCase
from django.urls import reverse
from django.core.mail import outbox
from django.core import mail

class RegistrationEmailTest(TestCase):
    def test_send_registration_email(self):
        email = 'test@example.com'

        # Create a fake request with POST data
        data = {'email': email}
        response = self.client.post(reverse('send_registration_email'), data)

        # Check if the response is successful
        self.assertEqual(response.status_code, 200)

        # Check if the email was sent
        self.assertEqual(len(outbox), 1)

        # Check the email content
        sent_email = outbox[0]
        self.assertEqual(sent_email.subject, 'Account Registration')
        self.assertIn(f'Click the following link to create your account:', sent_email.body)
        self.assertIn(reverse('register_user', kwargs={'pk': urlsafe_base64_encode(force_bytes(email)).decode('utf-8')}), sent_email.body)
        self.assertEqual(sent_email.from_email, 'your_email@example.com')
        self.assertEqual(sent_email.to, [email])

    def test_invalid_request_method(self):
        # Create a fake request with GET data
        response = self.client.get(reverse('send_registration_email'))

        # Check if the response returns an error for an invalid request method
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'error': 'Invalid request method'})
