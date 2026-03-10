from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    """Allow access only to users with ADMIN role."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "ADMIN")


class IsUserRole(permissions.BasePermission):
    """Allow access only to users with USER role (or Admin)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ["ADMIN", "USER"])
