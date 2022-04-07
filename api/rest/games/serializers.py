from django.db.models import Sum
from rest_framework import serializers

from backend.models import Game, Guess, Ordering, Phrase, Team
from common.rest.serializers import BaseSerializerMixin


class GameCreationSerializer(serializers.Serializer, BaseSerializerMixin):
    name = serializers.CharField(max_length=200)
    phrase_order = serializers.ChoiceField(choices=[o.value for o in Ordering])
    team_order = serializers.ChoiceField(choices=[o.value for o in Ordering])


class GameSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    phrase_order = serializers.SerializerMethodField()
    team_order = serializers.SerializerMethodField()

    def get_phrase_order(self, obj: Game) -> int:
        return obj.config_object.phrase_order.value

    def get_team_order(self, obj: Game) -> int:
        return obj.config_object.team_order.value

    class Meta:
        model = Game
        fields = ["id", "name", "phrase_order", "team_order"]
        read_only_fields = ["__all__"]


class GameDetailsSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    phrase_order = serializers.SerializerMethodField()
    team_order = serializers.SerializerMethodField()
    leaderboard = serializers.SerializerMethodField()

    def get_phrase_order(self, obj: Game) -> int:
        return obj.config_object.phrase_order.value

    def get_team_order(self, obj: Game) -> int:
        return obj.config_object.team_order.value

    def get_leaderboard(self, obj: Game) -> list[dict[str, int]]:
        return list(
            Guess.objects.filter(round__game=obj)
            .values("team_id")
            .order_by("team_id")
            .annotate(total_score=Sum("score"))
        )

    class Meta:
        model = Game
        fields = ["id", "name", "phrase_order", "team_order", "leaderboard"]
        read_only_fields = ["__all__"]


class PhraseSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = Phrase
        fields = ["id", "value"]
        read_only_fields = ["__all__"]


class TeamSerializer(serializers.ModelSerializer, BaseSerializerMixin):
    class Meta:
        model = Team
        fields = ["id", "name"]
        read_only_fields = ["__all__"]
