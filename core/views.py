from rest_framework import status, generics
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate, login

from core.serializers import CreateUserSerializer, LoginSerializer, UserSerializer


class SignUpView(generics.CreateAPIView):
    serializer_class = CreateUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exceptions=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_created)


# class LoginView(GenericAPIView):
#
#     def post(self, request):
#         username = request.data.get('username')
#         password = request.data.get('password')
#         user = authenticate(username=username, password=password)
#
#         if user is not None:
#             login(request, user)
#             return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
#         else:
#             return Response({'message': 'Invalid login credentials'}, status=status.HTTP_401_UNAUTHORIZED)