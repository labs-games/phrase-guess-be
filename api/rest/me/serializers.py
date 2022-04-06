from django.contrib.auth.models import User
from rest_framework import serializers

from common.rest.serializers import BaseSerializerMixin


class MeSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = User
        fields = ["id", "username", "is_active"]
        read_only_fields = ["__all__"]


class LoginRequestSerializer(serializers.Serializer, BaseSerializerMixin):
    username = serializers.CharField()
    password = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer, BaseSerializerMixin):
    session_token = serializers.CharField()
    expire_time = serializers.DateTimeField(help_text="Example: 2022-01-21T04:17:07Z")
