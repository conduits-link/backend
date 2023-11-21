from rest_framework import generics
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import EditorFile

from .serializers import FileDetailSerializer, FileCreateSerializer, FilePatchSerializer, FileListSerializer

class FileCreateView(generics.CreateAPIView):
    queryset = EditorFile.objects.all()
    serializer_class = FileCreateSerializer
    parser_classes = (MultiPartParser, FormParser)

class FileDetailView(generics.RetrieveAPIView):
    queryset = EditorFile.objects.all()
    serializer_class = FileDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = {
            "message": "File retrieved successfully",
            "file": serializer.data
        }
        return Response(response_data)
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return FilePatchSerializer
        return self.serializer_class

class StoreView(generics.ListCreateAPIView):
    queryset = EditorFile.objects.all()
    serializer_class = FileListSerializer