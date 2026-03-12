from authentication.views import LoginView, RegisterView, UserListView, UserMeView
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register", RegisterView.as_view(), name="auth-register"),
    path("login", LoginView.as_view(), name="auth-login"),
    path("me", UserMeView.as_view(), name="auth-me"),
    path("users", UserListView.as_view(), name="user-list"),
    path("token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
]
