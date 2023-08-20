from rest_framework import status, generics, permissions
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout

from core.models import User
from core.serializers import CreateUserSerializer, LoginSerializer, UserSerializer, UpdatePasswordSerializer


class SignUpView(generics.CreateAPIView):
    """
    Представления регистрации пользователя.
    """
    serializer_class = CreateUserSerializer
    permission_classes = [AllowAny]


class LoginView(GenericAPIView):
    """
    Представление входа пользователя.
    """
    serializer_class = LoginSerializer

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid login credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class ProfileView(generics.RetrieveUpdateDestroyAPIView):
    """
    Представление профиля пользователя.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user

    def perform_destroy(self, instance: User):
        logout(self.request)


class UpdatePasswordView(generics.GenericAPIView):
    """"
    Представление обновления пароля пользователя.
    """
    serializer_class = UpdatePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response(serializer.data)
