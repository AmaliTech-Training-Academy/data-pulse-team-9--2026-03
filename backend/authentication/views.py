from authentication.serializers import LoginSerializer, TokenSerializer, UserCreateSerializer, UserResponseSerializer
from authentication.services import authenticate_user, create_user
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(APIView):
    """Register a new user and return JWT tokens (Access + Refresh)."""

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

        refresh = RefreshToken.for_user(user)
        return Response(
            TokenSerializer(
                {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "token_type": "bearer",
                }
            ).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate user and return JWT tokens (Access + Refresh)."""

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={200: TokenSerializer},
        tags=["Auth"],
        summary="Login and get JWT tokens",
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

        refresh = RefreshToken.for_user(user)
        return Response(
            TokenSerializer(
                {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "token_type": "bearer",
                }
            ).data,
            status=status.HTTP_200_OK,
        )


class UserMeView(APIView):
    """Get the profile of the currently logged-in user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserResponseSerializer},
        tags=["Auth"],
        summary="Get current user profile",
    )
    def get(self, request):
        serializer = UserResponseSerializer(request.user)
        return Response(serializer.data)


class UserListView(APIView):
    """List all users - Admin only."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserResponseSerializer(many=True)},
        tags=["Auth"],
        summary="List all users (Admin only)",
    )
    def get(self, request):
        if getattr(request.user, "role", "USER") != "ADMIN":
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        from authentication.models import User

        users = User.objects.all().order_by("-created_at")
        serializer = UserResponseSerializer(users, many=True)
        return Response(serializer.data)
