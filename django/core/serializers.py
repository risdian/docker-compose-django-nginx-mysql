from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatHistory, AI, AIFile, Customer   # Import AI from the same models module as ChatHistory

class ChatHistorySerializer(serializers.ModelSerializer):
    # customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    ai = serializers.PrimaryKeyRelatedField(queryset=AI.objects.all())

    class Meta:
        model = ChatHistory
        fields = ['user_id', 'chat_id', 'ai', 'message', 'timestamp', 'from_ai']

class AIDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIFile
        fields = ['id', 'file', 'description']
        

class AiTutorSerializer(serializers.ModelSerializer):
    files = AIDataSerializer(many=True, read_only=True)

    class Meta:
        model = AI
        fields = ['id', 'name', 'description', 'files']