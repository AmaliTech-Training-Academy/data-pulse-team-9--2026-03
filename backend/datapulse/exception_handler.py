"""Custom DRF exception handler."""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that catches standard DRF exceptions and our custom
    DataPulse exceptions to return a standardized JSON error format.
    """
    # Call DRF's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Standardize the payload shape: {"detail": "message", "code": "error_code"}
        if isinstance(response.data, dict):
            if "detail" in response.data:
                response.data["code"] = getattr(exc, "default_code", "error")
            else:
                # If there are field errors, wrap them in detail
                response.data = {
                    "detail": "Validation error.",
                    "code": "validation_error",
                    "errors": response.data,
                }
        elif isinstance(response.data, list):
            response.data = {
                "detail": response.data[0],
                "code": getattr(exc, "default_code", "error"),
            }

    else:
        # Fallback for unexpected exceptions not handled by DRF (e.g., raw Python exceptions)
        return Response(
            {
                "detail": str(exc) if hasattr(exc, "__str__") else "An unexpected error occurred.",
                "code": "internal_error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
