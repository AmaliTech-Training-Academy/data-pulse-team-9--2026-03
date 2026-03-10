from rest_framework import permissions


class IsDatasetOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to allow only the uploader of a dataset or an admin to access its reports.
    Expects the view to have a 'dataset' object or the object itself to be a 'QualityScore' with a '.dataset'.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if getattr(request.user, "role", "USER") == "ADMIN":
            return True

        # If the object is a QualityScore, check its dataset.uploaded_by
        if hasattr(obj, "dataset"):
            return obj.dataset.uploaded_by == request.user

        # If the object is a Dataset, check uploaded_by directly
        if hasattr(obj, "uploaded_by"):
            return obj.uploaded_by == request.user

        return False
