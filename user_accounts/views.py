from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
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
def is_existing_user(email):
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
        
        if is_existing_user(email):
            return Response({"detail": "Account already registered with this email address."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate UID as string
        uid = urlsafe_base64_encode(force_bytes(email))

        # Create registration link with UID as string
        registration_link = "https://www.conduits.link/register/" + uid

        # Send email
        subject = 'Account Registration'
        message = f'Click the following link to create your account:\n\n<a href="{registration_link}">{registration_link}</a>'
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

        if is_existing_user(email):
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
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        response = Response({"message": "You have been logged out."}, status=status.HTTP_200_OK)

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



class UserForgotView(APIView):
    
    def post(self, request):
        email = request.data.get('email')

        if not is_valid_email(email):
            return Response({'detail': 'Invalid email address.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if is_existing_user(email):

            # Generate UID as string
            uid = urlsafe_base64_encode(force_bytes(email))

            # Create reset password link with UID as string
            reset_link = "https://www." + site_domain + "/forgot/" + uid

            # Send email
            subject = 'Conduit - Reset Password Request.'
            message = f'We received a request to reset your Conduit password. Please click the following link tp reset it:\n\n<a href="{reset_link}">{reset_link}</a>\n\nIf you did not make this request, please disregard this email.'
            recipient_list = [email]
            send_mailgun_email(recipient_list, subject, message)

        return Response({"message": "If email was valid, reset password link has been sent."}, status=status.HTTP_200_OK)
         
class UserResetPasswordView(APIView):
    def post(self, request, pk):
        # Decode the UID to get the email address
        email = force_str(urlsafe_base64_decode(pk))

        if not is_valid_email(email) or not is_existing_user(email):
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        if "password" not in request.data:
            return Response({'detail': 'No password provided.'}, status=status.HTTP_400_BAD_REQUEST)

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
    parser_classes = (MultiPartParser, FormParser)

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
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
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
        user = decode_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=401)

        # Call the create method to create and return a new document
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Associate the created document with the currently authenticated user.
        """
        user = decode_jwt_token(self.request)
        
        if user is None:
            # Token authentication failed
            raise PermissionDenied("You are not authenticated")

        # Associate the document with the currently authenticated user
        serializer.save(author=user)


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
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"doc": serializer.data}, status=200)
        except NotFound:
            return Response({"error": "The doc was not found."}, status=404)
        
    def put(self, request, *args, **kwargs):
        """
        Update the selected doc.
        """
        user = decode_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=401)

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data.get('doc'), partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"doc": {"modified": instance.modified}}, status=200)
        except ValidationError:
            return Response({"error": "The client did not provide the correct data, and the doc was not updated."}, status=400)
        except NotFound:
            return Response({"error": "The doc was not found."}, status=404)

    def delete(self, request, *args, **kwargs):
        """
        Delete the selected doc.
        """
        user = decode_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=401)

        instance = self.get_object()
        if instance.author == user:
            instance.delete()
            return Response({"message": "The doc was removed."}, status=200)
        else:
            return Response({"error": "You do not have permission to delete this document."}, status=403)

# Performs LLM inference on text provided.
# TODO : We need to set this up with our LLM.
@api_view(['POST'])
def generate_text(request):
    """
    Handles endpoint for /generate/text : POST
    requests a generative model to generate text, given a prompt.
    """

    # Extract data from the request
    data = request.data
    prompt_name = data.get('prompt', {}).get('name', '')
    messages = data.get('prompt', {}).get('messages', [])

    if not messages:
        return Response({"error": "Messages cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

    # Extract the first message
    first_message = messages[0]
    role = first_message.get("role", "")
    content = first_message.get("content", "")

    # TODO: Perform inference with your generative model using prompt_name and messages

    # Create a response data dictionary
    response_data = {
        "message": "Text generated successfully",
        "prompt": {
            "name": prompt_name,
            "messages": messages
        }
    }

    return Response(response_data, status=status.HTTP_200_OK)