from rest_framework import serializers

from backend.models import Round
from common.rest.serializers import BaseSerializerMixin


class RoundCreationSerializer(serializers.Serializer, BaseSerializerMixin):
    name = serializers.CharField(max_length=200)
    starting_team_id = serializers.IntegerField()


class RoundUpdationSerializer(serializers.Serializer, BaseSerializerMixin):
    name = serializers.CharField(max_length=200)


class RoundSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = Round
        fields = ["id", "name", "is_ended", "phrase_id", "team_sequence"]
        read_only_fields = ["__all__"]
