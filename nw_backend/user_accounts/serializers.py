from .models import EditorFile
from rest_framework import serializers

class FileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('title', 'body', "created", 'modified')    

class FileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('_id', 'created', 'modified')    

class FilePatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('title', 'body')   

class FileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('title', "created", 'modified') 