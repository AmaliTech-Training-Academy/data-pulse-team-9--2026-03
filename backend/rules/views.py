"""Validation rules router - PARTIAL implementation."""

from datapulse.exceptions import InvalidRuleException
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rules.models import ValidationRule
from rules.serializers import RuleCreateSerializer, RuleResponseSerializer, RuleUpdateSerializer

VALID_TYPES = {"NOT_NULL", "DATA_TYPE", "RANGE", "UNIQUE", "REGEX"}
VALID_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}


class RuleListCreateView(APIView):
    """Handle POST (create) and GET (list) for rules."""

    @extend_schema(
        request=RuleCreateSerializer,
        responses={201: RuleResponseSerializer},
        tags=["Rules"],
        summary="Create a new validation rule",
    )
    def post(self, request):
        """Create a new validation rule - IMPLEMENTED."""
        serializer = RuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data["rule_type"] not in VALID_TYPES:
            raise InvalidRuleException(f"Invalid rule_type: {VALID_TYPES}")

        if data["severity"] not in VALID_SEVERITIES:
            raise InvalidRuleException(f"Invalid severity: {VALID_SEVERITIES}")

        rule = ValidationRule.objects.create(**data)
        return Response(RuleResponseSerializer(rule).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter("dataset_type", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False),
        ],
        responses={200: RuleResponseSerializer(many=True)},
        tags=["Rules"],
        summary="List validation rules",
    )
    def get(self, request):
        """List validation rules - IMPLEMENTED."""
        dataset_type = request.query_params.get("dataset_type")
        queryset = ValidationRule.objects.filter(is_active=True)
        if dataset_type:
            queryset = queryset.filter(dataset_type=dataset_type)
        return Response(RuleResponseSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class RuleDetailView(APIView):
    """Handle PUT (update) and DELETE for a specific rule."""

    @extend_schema(
        request=RuleUpdateSerializer,
        responses={200: RuleResponseSerializer},
        tags=["Rules"],
        summary="Update a validation rule (TODO)",
    )
    def put(self, request, rule_id):
        """Update a validation rule - TODO: Implement."""
        from rest_framework.exceptions import APIException

        class NotImplementedException(APIException):
            status_code = 501
            default_detail = "PUT /api/rules/{id} not implemented"
            default_code = "not_implemented"

        raise NotImplementedException()
        try:
            rule = ValidationRule.objects.get(id=rule_id, is_active=True)
        except ValidationRule.DoesNotExist:
            from datapulse.exceptions import RuleNotFoundException

            raise RuleNotFoundException(f"Rule with id {rule_id} not found")

        serializer = RuleUpdateSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Update only fields that were provided
        for field, value in data.items():
            setattr(rule, field, value)

        # Validate rule_type and severity if they were changed
        if rule.rule_type not in VALID_TYPES:
            raise InvalidRuleException(f"Invalid rule_type: {VALID_TYPES}")
        if rule.severity not in VALID_SEVERITIES:
            raise InvalidRuleException(f"Invalid severity: {VALID_SEVERITIES}")

        rule.save()
        return Response(RuleResponseSerializer(rule).data, status=status.HTTP_200_OK)

    @extend_schema(
        responses={204: None},
        tags=["Rules"],
        summary="Delete a validation rule (TODO)",
    )
    def delete(self, request, rule_id):
        """Soft-delete a validation rule - TODO: Implement."""
        from rest_framework.exceptions import APIException

        class NotImplementedException(APIException):
            status_code = 501
            default_detail = "DELETE /api/rules/{id} not implemented"
            default_code = "not_implemented"

        raise NotImplementedException()
        try:
            rule = ValidationRule.objects.get(id=rule_id, is_active=True)
        except ValidationRule.DoesNotExist:
            from datapulse.exceptions import RuleNotFoundException

            raise RuleNotFoundException(f"Rule with id {rule_id} not found")

        rule.is_active = False
        rule.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
