from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, NotFound
from rest_framework.decorators import api_view

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import authenticate

from .models import User, EditorFile

from .serializers import UserAuthSerializer, FileCreateSerializer, FilePatchSerializer, FileListSerializer

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import jwt
from jwt.exceptions import DecodeError

import datetime

import os
import requests
from dotenv import load_dotenv

from openai import OpenAI
import stripe

import logging
# To use:
# logger = logging.getLogger('defaultlogger')
# logger.info('This is a simple log message')

load_dotenv()

site_domain = 'conduits.link'

def send_mailgun_email(recipient_emails, subject, message):
    """
    recipient_emails is a list of emails.
    """

    mailgun_domain = os.getenv("MAILGUN_DOMAIN")

    if mailgun_domain is not None:
        email_response = requests.post(
        "https://api.mailgun.net/v3/" + mailgun_domain + "/messages",
        auth=("api", os.getenv("MAILGUN_API_KEY")),
        data={"from": "Conduit <admin@" + site_domain + ">",
            "to": recipient_emails,
            "subject": subject,
            "html": message})
    
    if email_response is None or email_response.status_code != 200:
        return Response({"message": "Internal server error occurred while sending email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({'message': 'Email sent successfully'}, status.HTTP_202_ACCEPTED)

# Check if input is a valid email address.
def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False
    
# Check if a user with the provided email already exists.
def is_existing_email(email):
    return User.objects.filter(email=email).first()


# TODO: Set key securely.
key = "TODO_CHANGEME_KEY"

def generate_jwt_token(username, expiry_length=datetime.timedelta(seconds=3600)):

    return jwt.encode({"username": username, "exp": datetime.datetime.now(tz=datetime.timezone.utc) + expiry_length}, key, algorithm="HS256")

def encode_jwt_token(response, username, expiry_length=datetime.timedelta(seconds=3600)):

    # Generate JWT token
    encoded_jwt = jwt.encode({"username": username, "exp": datetime.datetime.now(tz=datetime.timezone.utc) + expiry_length}, key, algorithm="HS256")

    # Set JWT token as a cookie
    response.set_cookie(
        key='jwt', 
        value=str(encoded_jwt), 
        httponly=True, 
        samesite='None', 
        domain='.conduits.link', 
        secure=True, 
        path="/"
    )

    return response

def decode_jwt_token(request):
    """
    Decode the JWT token in the request.

    Args:
        request: The request object.

    Returns:
        User object if the token is valid, None otherwise.
    """

    token = request.COOKIES.get('jwt')

    if token is None:
        return None

    try:
        decoded_token = jwt.decode(token, key, algorithms=["HS256"])
        return decoded_token.get('username')
    
    except DecodeError:
        return None
    
def get_user_from_jwt(request):
    """
    Returns the User object corresponding to the JWT, if it exists,
    or None otherwise.
    """
    username = decode_jwt_token(request)

    # Get user, or return None if it doesn't exist.
    return User.objects.filter(username=username).first()

    

def login(request, success_message, success_status):
    """
    request.data must include username and password.
    """
    # Serialize and validate the incoming login data
    serializer = UserAuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']

    # Authenticate user
    user = authenticate(request, username=username,
                        password=serializer.validated_data['password'])

    if user is not None:

        response_data = {'detail': success_message}
        response = Response(response_data, status=success_status)

        return encode_jwt_token(response, username)

    else:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

class RegistrationEmailView(APIView):
    def post(self, request):
        email = request.data.get('email')

        if not is_valid_email(email):
            return Response({'detail': 'Invalid email address.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if is_existing_email(email):
            return Response({"detail": "Account already registered with this email address."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate UID as string
        uid = urlsafe_base64_encode(force_bytes(email))

        # Create registration link with UID as string
        registration_link = "https://www.conduits.link/register/" + uid

        # Send email
        subject = 'Conduit Account Registration'
        message = f'Click the following link to create your Conduit account:<br><br><a href="{registration_link}">{registration_link}</a>'
        recipient_list = [email]

        return send_mailgun_email(recipient_list, subject, message)

    def get(self, request):
        return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
class UserRegistrationView(APIView):
    def post(self, request, pk):
        # Decode the UID to get the email address
        email = force_str(urlsafe_base64_decode(pk))

        if not is_valid_email(email):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if is_existing_email(email):
            return Response({"detail": "Account already registered with this email address."}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize and validate the incoming data
        serializer = UserAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create a new user
        User.objects.create_user(username=serializer.validated_data['username'],
                                        email=email,
                                        password=serializer.validated_data['password'])
        # Login to the account
        return login(request, "Account created successfully. You have been logged in.", status.HTTP_201_CREATED)
    

class UserLoginView(APIView):
    def post(self, request):
        return login(request, "Login successful.", status.HTTP_200_OK)
    
class UserLogoutView(APIView):
    def get(self, request):

        user = decode_jwt_token(request)

        if user is None:
            # Token authentication failed
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        response = Response({"detail": "You have been logged out."}, status=status.HTTP_200_OK)

        # Set JWT token as a cookie
        response.set_cookie(
            key='jwt', 
            value='', 
            httponly=True, 
            samesite='None', 
            domain='.conduits.link', 
            secure=True, 
            path="/"
        )

        return response


def encode_password_reset_uid(email):

    # Get time of request, so we can set URL expiry time.
    now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    return urlsafe_base64_encode(force_bytes(email + '|' + now))

def decode_password_reset_uid(uid):
    """
    Returns (email, creation date of URL).
    """
    return force_str(urlsafe_base64_decode(uid)).split('|')

class UserForgotView(APIView):
    
    def post(self, request):
        email = request.data.get('email')

        if not is_valid_email(email):
            return Response({'detail': 'Invalid email address.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if is_existing_email(email):

            uid = encode_password_reset_uid(email)

            # Create reset password link with UID as string
            reset_link = "https://www." + site_domain + "/forgot/" + uid

            # Send email
            subject = 'Conduit - Reset Password Request.'
            message = f'We received a request to reset your Conduit password. Please click the following link to reset it:<br><br><a href="{reset_link}">{reset_link}</a><br><br>If you did not make this request, please disregard this email.'
            recipient_list = [email]
            send_mailgun_email(recipient_list, subject, message)

        return Response({"detail": "If email was valid, reset password link has been sent."}, status=status.HTTP_200_OK)
         
class UserResetPasswordView(APIView):
    def post(self, request, pk):

        email, date = decode_password_reset_uid(pk)
        
        if not is_valid_email(email) or not is_existing_email(email):
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if "password" not in request.data:
            return Response({'detail': 'No password provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if date < str(datetime.datetime.now() - datetime.timedelta(days=1)):
            return Response({'detail': 'Sorry, this link has expired.'}, status=status.HTTP_410_GONE)

        user = User.objects.get(email=email)

        user.set_password(request.data["password"])
        user.save()

        return Response(status=status.HTTP_200_OK)
        

class DocsCreateRetrieveView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Handles requests for store/docs.
    GET: Retrieve all docs for the authenticated user.
    POST: Create a new document for the authenticated user.
    """
    queryset = EditorFile.objects.all()
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_serializer_class(self):
        """
        Return the serializer class based on the request method.
        """
        if self.request.method == 'POST':
            return FileCreateSerializer
        elif self.request.method == 'GET':
            return FileListSerializer
        else:
            # Use default serializer class for other request methods
            return super().get_serializer_class()

    def get_queryset(self):
        """
        Retrieve the queryset for the currently authenticated user's documents.
        """
        # Filter documents based on the currently authenticated user
        return EditorFile.objects.filter(author=self.request.user)

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve documents for the currently authenticated user.
        """

        user = decode_jwt_token(request)

        if user is None:
            # Token authentication failed
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        # Retrieve the queryset for the currently authenticated user's documents
        queryset = EditorFile.objects.filter(author=user)

        # Serialize the queryset
        serializer = FileListSerializer(queryset, many=True)

        # Return the serialized data in the desired format
        return Response({"docs": serializer.data})

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to create a new document for the currently authenticated user.
        """
        # Decode JWT token
        username = decode_jwt_token(request)
        
        if username is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        doc_data = request.data['doc']

        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        creation_data = {
                'author': username,
                'title': doc_data['title'],
                'body': doc_data['body'],
                'created': now,
                'modified': now
        }

        serializer = self.get_serializer(data=creation_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Construct the response in the specified format
        response_data = {
            "doc": {
                "uid": str(serializer.instance.uid),
                "created": now,
                "modified": now
            }
        }
        return Response(response_data, status=201)


class DocRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles requests for store/docs/:pk.
    GET: Retrieve the selected doc.
    PUT: Update the selected doc.
    DELETE: Delete the selected doc.
    """
    queryset = EditorFile.objects.all()
    serializer_class = FilePatchSerializer

    def get(self, request, *args, **kwargs):
        """
        Retrieve the selected doc.
        """
        user = decode_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()

        if instance.author != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if instance is None:
            return Response({"error": "The doc was not found."}, status=404)

        serializer = self.get_serializer(instance)
        return Response({"doc": serializer.data}, status=200)

        
    def put(self, request, *args, **kwargs):
        """
        Update the selected doc.
        """
        user = decode_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()

        if instance.author != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(instance, data=request.data.get('doc'), partial=True)

        if not serializer.is_valid():
            return Response({"error": "The client did not provide the correct data, and the doc was not updated."}, status=400)

        instance = self.get_object()

        if instance is None:
            return Response({"error": "The doc was not found."}, status=404)

        serializer.save()
        return Response({"doc": {"modified": instance.modified}}, status=200)


    def delete(self, request, *args, **kwargs):
        """
        Delete the selected doc.
        """
        user = decode_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        instance = self.get_object()

        if instance.author != user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        instance.delete()
        return Response({"detail": "The doc was removed."}, status=200)

# Performs LLM inference on text provided.
class GenerateTextView(APIView):
    """
    Handles endpoint for /generate/text : POST
    requests a generative model to generate text, given a prompt.
    """
    def post(self, request):
        # Extract data from the request
        data = request.data
        prompt_name = data.get('prompt', {}).get('name', '')
        messages = data.get('prompt', {}).get('messages', [])

        if not messages:
            return Response({"error": "Messages cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            max_tokens=200,
            stream=False, # should use instead of loading icon
            n=1
        )

        answer = completion.choices[0].message.content

        response = {
            "detail": "Text generated successfully",
            "prompt": {
                "name": prompt_name,
                "messages": [
                    {
                        "role": "user",
                        "content": answer
                    }
                ]
            }
        }

        return Response(response, status=status.HTTP_200_OK)
    
stripe.api_key = os.getenv("STRIPE_API_KEY")

class UserCreditsView(APIView):

    def __init__(self):
        # Key on our Stripe account for user to add their chosen amount of LLM credits.
        self.credit_price_id = 'price_1P5OogEkDHz9IHMxM3lo20bv'
    
    """
    Handle payment details.
    """
    def get(self, request):

        user = get_user_from_jwt(request)
        
        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=401)
        
        return Response({"credits": user.credits}, status=status.HTTP_200_OK)


    def post(self, request):

        user = get_user_from_jwt(request)

        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=401)
    
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': self.credit_price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url="https://" + site_domain + '/?success=true',
                cancel_url="https://" + site_domain + '/?canceled=true',
                metadata={"username": user.username},
            )
            return Response({'redirect_url': checkout_session.url}, status=302)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

class OrderFulfillmentWebhookView(APIView):

    def fulfill_order(self, session):
        
        username = session["metadata"]["username"]
        user = User.objects.get(username=username)
                    
        # Can only place one order at a time, so get the single order.
        purchase = session["line_items"]["data"][0]

        credits = purchase["amount_total"]

        user.credits += credits
        user.save()

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']
        event = None

        endpoint_secret='whsec_0afca699df9d7ee4e19c524b54f43fd9f717258524e23ee0e89c297841ab8419'# os.getenv("STRIPE_WEBHOOK_SECRET")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        if event['type'] == 'checkout.session.completed':
            # Retrieve the session.
            session = stripe.checkout.Session.retrieve(
                event['data']['object']['id'],
                expand=['line_items'],
            )

            # Fulfill the purchase.
            self.fulfill_order(session)

        # Passed signature verification
        return Response(status=status.HTTP_200_OK)

