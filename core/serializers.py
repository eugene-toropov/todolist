from rest_framework import serializers, exceptions
from django.contrib.auth.hashers import make_password

from core.models import User
from todolist.fields import PasswordField


class CreateUserSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания объекта User.
    """
    password = PasswordField()
    password_repeat = PasswordField(validate=False)
    username = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password_repeat', 'email', 'first_name', 'last_name')

    def validate(self, data: dict) -> dict:
        """
        Метод проверки повторного ввода пароля пользователя.
        :param data:
        :return:
        """
        if data['password'] != data['password_repeat']:
            raise exceptions.ValidationError('Passwords must match!')
        return data

    def create(self, validated_data: dict) -> User:
        del validated_data['password_repeat']
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def validate_username(self, value):
        """
        Метод проверки свободного доступа имя пользователя.
        :param value:
        :return:
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists!')
        return value


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор входа пользователя.
    """
    username = serializers.CharField(required=True)
    password = PasswordField(validate=False)


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор объекта пользователя.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class UpdatePasswordSerializer(serializers.Serializer):
    """
    Сериализатор обновления пароля пользователя.
    """
    old_password = PasswordField(validate=False)
    new_password = PasswordField()

    def validate_old_password(self, old_password):
        """
        Метод валидации старого пароля пользователя.
        :param old_password:
        :return:
        """
        request = self.context['request']

        if not request.user.is_authenticated:
            raise exceptions.NotAuthenticated

        if not request.user.check_password(old_password):
            raise exceptions.ValidationError('Current password is incorrect!')

        return old_password

