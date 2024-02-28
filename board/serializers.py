from rest_framework import serializers
from .models import User, Project, Task, Category, Comment
from rest_framework_simplejwt.tokens import RefreshToken

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'phone', 'role', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': False},
            'role': {'required': False},
            'password': {'required': False}
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()
        return instance


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title', 'description')

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ('id', 'title', 'description', 'categories', 'priority', 'project', 'status')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'text', 'user', 'task', 'file')

class TokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer for obtaining a JSON Web Token and Refresh Token pair.
    """
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

class TokenRefreshSerializer(serializers.Serializer):
    """
    Serializer for refreshing an existing JSON Web Token.
    """
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

