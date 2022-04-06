from rest_framework import serializers

from backend.models import Game, Phrase, Team
from common.rest.serializers import BaseSerializerMixin


class GameSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = Game
        fields = ["id", "name"]
        read_only_fields = ["__all__"]


class PhraseSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = Phrase
        fields = ["id", "value"]
        read_only_fields = ["__all__"]


class TeamSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = Phrase
        fields = ["id", "name"]
        read_only_fields = ["__all__"]
