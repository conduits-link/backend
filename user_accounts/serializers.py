from .models import EditorFile
from rest_framework import serializers

class UserAuthSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class FileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('title', 'body', "created", 'modified')    

class FileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('title', 'created', 'modified')    

class FilePatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('title', 'body', 'modified')   

class FileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditorFile
        fields = ('title', 'body', "created", 'modified') 