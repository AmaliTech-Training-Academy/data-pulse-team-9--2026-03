"""Custom exceptions for the DataPulse API."""

from rest_framework.exceptions import APIException
from rest_framework import status


class DataPulseException(APIException):
    """Base exception for all DataPulse API errors."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An internal server error occurred."
    default_code = "internal_server_error"


class DatasetNotFoundException(DataPulseException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested dataset was not found."
    default_code = "dataset_not_found"


class InvalidFileException(DataPulseException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The uploaded file is invalid or unsupported."
    default_code = "invalid_file"


class RuleNotFoundException(DataPulseException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The specified validation rule was not found."
    default_code = "rule_not_found"


class InvalidRuleException(DataPulseException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The validation rule configuration is invalid."
    default_code = "invalid_rule"


class QualityCheckFailedException(DataPulseException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Quality checks failed to run on the dataset."
    default_code = "quality_check_failed"
