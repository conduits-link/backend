from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import EditorFile

from .serializers import FileDetailSerializer, FileCreateSerializer, FilePatchSerializer, FileListSerializer

class DocsCreateRetrieveView(generics.CreateAPIView, generics.RetrieveAPIView):
    """
    Handles requests for store/docs.
    POST: Create a new document for the authenticated user.
    GET: Retrieve all docs for the authenticated user.
    """
    queryset = EditorFile.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

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
        return EditorFile.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve documents for the currently authenticated user.
        """
        # Call the list method to retrieve and return the documents
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to create a new document for the currently authenticated user.
        """
        # Call the create method to create and return a new document
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Associate the created document with the currently authenticated user.
        """
        # Associate the document with the currently authenticated user
        serializer.save(user=self.request.user)

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

    def perform_update(self, serializer):
        """
        Perform the update operation and associate the updated document with the currently authenticated user.
        """
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """
        Perform the delete operation only if the requesting user is the owner of the document.
        """
        if instance.user == self.request.user:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this document.")