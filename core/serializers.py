from rest_framework import serializers, exceptions
from django.contrib.auth.hashers import make_password

from core.models import User
from todolist.fields import PasswordField


class CreateUserSerializer(serializers.ModelSerializer):
    password = PasswordField()
    password_repeat = PasswordField()
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password_repeat', 'email', 'first_name', 'last_name')

    def validate(self, data: dict) -> dict:
        if data['password'] != data['password_repeat']:
            raise exceptions.ValidationError('Passwords must match!')
        return data

    def create(self, validated_data: dict) -> User:
        del validated_data['password_repeat']
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = PasswordField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
