import re

from rest_framework import serializers


class UserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField()

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default="bearer")


class UserResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    role = serializers.CharField()
    created_at = serializers.DateTimeField()
