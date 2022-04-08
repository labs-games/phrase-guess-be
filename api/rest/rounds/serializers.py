from rest_framework import serializers

from backend.models import Guess, GuessType, Round
from common.rest.serializers import BaseSerializerMixin


class RoundCreationSerializer(serializers.Serializer, BaseSerializerMixin):
    name = serializers.CharField(max_length=200)
    starting_team_id = serializers.IntegerField()


class RoundUpdationSerializer(serializers.Serializer, BaseSerializerMixin):
    name = serializers.CharField(max_length=200)


class RoundSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    team_ordering = serializers.SerializerMethodField()

    def get_team_ordering(self, obj: Round) -> list[int]:
        return obj.config_object.team_ids_ordering

    class Meta:
        model = Round
        fields = ["id", "name", "is_ended", "phrase_id", "team_ordering"]
        read_only_fields = ["__all__"]


class GuessCreationSerializer(serializers.Serializer, BaseSerializerMixin):
    team_id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=[g.value for g in GuessType])
    value = serializers.CharField(max_length=200, default='', required=False)

    def validate(self, attrs: dict) -> dict:
        if attrs["type"] == GuessType.letter and len(attrs["value"]) > 1:
            raise serializers.ValidationError(
                {"value": [serializers.ErrorDetail("Too long", code="max_length")]}
            )
        return attrs


class GuessSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = Guess
        fields = ["id", "team_id", "type", "status", "value", "score"]
        read_only_fields = ["__all__"]
