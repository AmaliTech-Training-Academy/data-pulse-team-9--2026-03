"""Authentication router - IMPLEMENTED."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken
from drf_spectacular.utils import extend_schema

from authentication.serializers import UserCreateSerializer, LoginSerializer, TokenSerializer
from authentication.services import create_user, authenticate_user


class RegisterView(APIView):
    """Register a new user and return a JWT token."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    @extend_schema(
        request=UserCreateSerializer,
        responses={201: TokenSerializer},
        tags=["Auth"],
        summary="Register a new user",
    )
    
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = create_user(data["email"], data["password"], data["full_name"])
        if user is None:
            return Response(
                {"detail": "Email already registered"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = AccessToken.for_user(user)
        return Response(
            TokenSerializer({"access_token": str(token), "token_type": "bearer"}).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate user and return a JWT token."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenSerializer},
        tags=["Auth"],
        summary="Login and get JWT token",
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = authenticate_user(data["email"], data["password"])
        if user is None:
            return Response(
                {"detail": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token = AccessToken.for_user(user)
        return Response(
            TokenSerializer({"access_token": str(token), "token_type": "bearer"}).data,
            status=status.HTTP_200_OK,
        )
