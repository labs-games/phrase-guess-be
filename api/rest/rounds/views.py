import random
from typing import Optional

from django.contrib.auth.models import User
from django.db.transaction import atomic
from more_itertools import circular_shifts, first_true
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from backend.models import Game, Ordering, Phrase, Round, RoundConfigs, Team
from common.rest.exceptions import ErrorCode, ErrorCodeException
from common.rest.views import ActiveUserAPIViewMixin

from .serializers import RoundCreationSerializer, RoundSerializer, RoundUpdationSerializer


class RoundsView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = RoundSerializer

    def get_queryset(self):
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id)
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return Round.objects.filter(game=game).order_by("id")

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request, *args, **kwargs) -> Response:
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id)
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)

        if Round.objects.filter(game=game, is_ended=False).exists():
            raise ErrorCodeException(ErrorCode.any_round_still_ongoing)

        serializer: RoundCreationSerializer = RoundCreationSerializer(data=request.data)
        serializer.raise_validation_error_if_any()
        validated_data: dict = serializer.validated_data

        team_ids_order: list[int] = self._compute_team_ids_order(
            game=game, starting_team_id=validated_data["starting_team_id"]
        )
        configs: RoundConfigs = RoundConfigs(team_ids_ordering=team_ids_order)

        phrase: Phrase = self._compute_phrase(game)
        requester: User = request.user
        Round.objects.create(
            game=game,
            phrase=phrase,
            name=validated_data["name"],
            configs=configs.to_dict(),
            created_by_id=requester.id,
            updated_by_id=requester.id,
        )
        return self.generate_no_error_response({})

    def _compute_team_ids_order(self, game: Game, starting_team_id: int) -> list[int]:
        team_ids: list[int] = [t.id for t in Team.objects.filter().order_by("id")]
        if not team_ids:
            raise ErrorCodeException(ErrorCode.empty_teams)

        if game.config_object.team_order == Ordering.random:
            random.shuffle(team_ids)

        if starting_team_id not in team_ids:
            return team_ids

        return list(
            first_true(circular_shifts(team_ids), pred=lambda ids: ids[0] == starting_team_id)
        )

    def _compute_phrase(self, game: Game) -> Phrase:
        used_phrase_ids: list[int] = list(
            Round.objects.filter(game=game).values_list("phrase_id", flat=True)
        )
        available_phrases: list[Phrase] = list(
            Phrase.objects.exclude(id__in=used_phrase_ids).filter(game=game).order_by("id")
        )
        if not available_phrases:
            raise ErrorCodeException(ErrorCode.phrases_all_used)

        if game.config_object.phrase_order == Ordering.random:
            random.shuffle(available_phrases)
        return available_phrases[0]


class RoundView(ActiveUserAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoundSerializer

    def get_object(self) -> Round:
        game_id: int = self.kwargs["game_id"]
        round_id: int = self.kwargs["round_id"]
        game_round: Optional[Round] = Round.objects.filter(id=round_id, game_id=game_id).first()
        if game_round is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return game_round

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    def put(self, request: Request, *args, **kwargs) -> Response:
        serializer: RoundUpdationSerializer = RoundUpdationSerializer(data=request.data)
        serializer.raise_validation_error_if_any()

        game_round: Round = self.get_object()
        requester: User = request.user
        validated_data: dict = serializer.validated_data
        game_round.name = validated_data["name"]
        game_round.updated_by_id = requester.id
        game_round.save()
        return self.generate_no_error_response({})

    def delete(self, request, *args, **kwargs) -> Response:
        game_round: Round = self.get_object()
        game_round.delete()
        return self.generate_no_error_response({})
