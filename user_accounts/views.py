from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

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

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_mailgun_email(recipient_emails, subject, message):
    """
    recipient_emails is a list of emails.
    """

    mailgun_domain = os.getenv("MAILGUN_DOMAIN")
    site_domain = "conduits.link"

    return requests.post(
        "https://api.mailgun.net/v3/" + mailgun_domain + "/messages",
        auth=("api", os.getenv("MAILGUN_API_KEY")),
        data={"from": "Conduit <admin@" + site_domain + ">",
            "to": recipient_emails,
            "subject": subject,
            "html": message})

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



def verify_jwt_token(request):
    """
    Verify the JWT token in the request.

    Args:
        request: The request object.

    Returns:
        User object if the token is valid, None otherwise.
    """
    print(request)

    import logging
    logger = logging.getLogger(__name__)
    logger.debug("JWT cookie: ")
    logger.debug(request.COOKIES)
    logger.debug(request.COOKIES.get('jwt'))
    try:
        # Attempt to authenticate the request using JWT token
        user, _ = JWTAuthentication().authenticate(request)
        return user
    except AuthenticationFailed:
        # Token authentication failed
        return None

class RegistrationEmailAPIView(APIView):
    # Anyone with the URL can register.
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')

        if not is_valid_email(email):
            return Response({'detail': 'Invalid email address.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if is_existing_user(email):
            return Response({"detail": "Account already registered with this email address."}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate UID as string
        uid = urlsafe_base64_encode(force_bytes(email))

        # Create registration link with UID as string
        registration_link = "https://www.conduits.link/register/" + uid

        # Send email
        subject = 'Account Registration'
        message = f'Click the following link to create your account:\n\n<a href="{registration_link}">{registration_link}</a>'
        recipient_list = [email]

        email_response = send_mailgun_email(recipient_list, subject, message)

        if email_response.status_code != 200:
            return Response({"message": "Internal server error occurred while sending email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'message': 'Email sent successfully'})

    def get(self, request):
        return Response({'error': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
class UserRegistrationAPIView(APIView):
    # Anyone with the URL can register.
    permission_classes = []

    def post(self, request, pk):
        try:
            # Decode the UID to get the email address
            email = force_str(urlsafe_base64_decode(pk))

            if not is_valid_email(email):
                return Response({"detail": "Invalid registration link."}, status=status.HTTP_401_UNAUTHORIZED)

            if is_existing_user(email):
                return Response({"detail": "Account already registered with this email address."}, status=status.HTTP_401_UNAUTHORIZED)

            # Serialize and validate the incoming data
            serializer = UserAuthSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)


            # Create a new user
            user = User.objects.create_user(username=serializer.validated_data['username'],
                                            email=email,
                                            password=serializer.validated_data['password'])

            # Return a success response
            return Response({"detail": "Account created successfully."}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            # Handle any exceptions or errors during account creation
            print(f"Error creating account: {str(e)}")
            return Response({"detail": f"Error creating account: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserLoginAPIView(APIView):
    # Anyone with the URL can login.
    permission_classes = []
    
    def post(self, request):
        try:
            # Serialize and validate the incoming login data
            serializer = UserAuthSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Authenticate user
            user = authenticate(request, username=serializer.validated_data['username'],
                                password=serializer.validated_data['password'])

            if user is not None:
                # Generate JWT token
                refresh = RefreshToken.for_user(user)
                token = str(refresh.access_token)

                # Set JWT token as a cookie
                response_data = {'detail': 'Login successful.'}
                response = Response(response_data)

                # Set JWT token as a cookie
                response.set_cookie(key='jwt', value=token, httponly=True, samesite='None', domain=os.getenv("DOMAIN"), secure=True, path="/")

                return response

            else:
                return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            # Handle any exceptions or errors during login
            return Response({"detail": f"Error during login: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocsCreateRetrieveView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Handles requests for store/docs.
    GET: Retrieve all docs for the authenticated user.
    POST: Create a new document for the authenticated user.
    """
    queryset = EditorFile.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

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

        user = verify_jwt_token(request)

        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Retrieve the queryset for the currently authenticated user's documents
        queryset = EditorFile.objects.filter(author=user)

        # Serialize the queryset
        serializer = FileListSerializer(queryset, many=True)

        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to create a new document for the currently authenticated user.
        """
        # Verify JWT token
        user = verify_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=401)

        # Call the create method to create and return a new document
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Associate the created document with the currently authenticated user.
        """
        # Verify JWT token
        user = verify_jwt_token(self.request)
        
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
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        """
        Retrieve the selected doc.
        """
        # Verify JWT token
        user = verify_jwt_token(request)
        
        if user is None:
            # Token authentication failed
            return Response({"error": "Unauthorized"}, status=401)

        return self.retrieve(request, *args, **kwargs)

    def perform_update(self, serializer):
        """
        Perform the update operation and associate the updated document with the currently authenticated user.
        """
        # Verify JWT token
        user = verify_jwt_token(self.request)
        
        if user is None:
            # Token authentication failed
            raise PermissionDenied("You are not authenticated")

        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """
        Perform the delete operation only if the requesting user is the owner of the document.
        """
        # Verify JWT token
        user = verify_jwt_token(self.request)
        
        if user is None:
            # Token authentication failed
            raise PermissionDenied("You are not authenticated")

        if instance.author == user.username:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this document.")

# Performs LLM inference on text provided.
# TODO : We need to set this up with our LLM.
def generate_text(request):
    """
    Handles endpoint for /generate/text : POST
    requests a generative model to generate text, given a prompt.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'})
    
    try:
        # Assuming your request data is in JSON format
        data = json.loads(request.body.decode('utf-8'))

        # Extract data from the request
        prompt_name = data.get('promptName', '')
        messages = data.get('messages', [])

        role = messages[0].get("role")
        content = messages[0].get("content")

        # TODO: Perform inference with your generative model using prompt_name and messages

        # Create a response JSON
        response_data = {
            "status": 200,  # Adjust the status code accordingly
            "message": "Text generated successfully",
            "data": {
                "promptName": prompt_name,
                "messages": messages
            }
        }

        return JsonResponse(response_data, status=200)

    except json.JSONDecodeError as e:
        return JsonResponse({"error": "Invalid JSON format in the request"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
