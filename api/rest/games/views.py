from typing import Optional

from django.contrib.auth.models import User
from django.db.transaction import atomic
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from backend.models import Game, GameConfigs, Ordering, Phrase, Team
from common.rest.exceptions import ErrorCode, ErrorCodeException
from common.rest.views import ActiveUserAPIViewMixin

from .serializers import (
    GameCreationSerializer,
    GameDetailsSerializer,
    GameSerializer,
    PhraseSerializer,
    TeamSerializer,
)


class GamesView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    queryset = Game.objects.order_by("-id")
    serializer_class = GameSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer: GameCreationSerializer = GameCreationSerializer(data=request.data)
        serializer.raise_validation_error_if_any()

        validated_data: dict = serializer.validated_data
        game_configs: GameConfigs = GameConfigs(
            phrase_order=Ordering(validated_data["phrase_order"]),
            team_order=Ordering(validated_data["team_order"]),
        )

        requester: User = request.user
        Game.objects.create(
            name=validated_data["name"],
            created_by_id=requester.id,
            updated_by_id=requester.id,
            configs=game_configs.to_dict(),
        )
        return self.generate_no_error_response({})


class GameView(ActiveUserAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GameDetailsSerializer

    def get_object(self) -> Game:
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return game

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    def put(self, request: Request, *args, **kwargs) -> Response:
        serializer: GameCreationSerializer = GameCreationSerializer(data=request.data)
        serializer.raise_validation_error_if_any()

        validated_data: dict = serializer.validated_data
        game_configs: GameConfigs = GameConfigs(
            phrase_order=Ordering(validated_data["phrase_order"]),
            team_order=Ordering(validated_data["team_order"]),
        )

        requester: User = request.user
        game: Game = self.get_object()
        game.config_object = game_configs
        game.name = validated_data["name"]
        game.updated_by_id = requester.id
        game.save()
        return self.generate_no_error_response({})

    def delete(self, request, *args, **kwargs) -> Response:
        game: Game = self.get_object()
        game.delete()
        return self.generate_no_error_response({})


class PhrasesView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = PhraseSerializer

    def get_queryset(self):
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return Phrase.objects.filter(game=game).order_by("id")

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)

        serializer: PhraseSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        requester: User = request.user
        validated_data: dict = serializer.validated_data
        Phrase.objects.create(
            game=game,
            value=validated_data["value"].upper(),
            created_by_id=requester.id,
            updated_by_id=requester.id,
        )
        return self.generate_no_error_response({})


class PhraseView(ActiveUserAPIViewMixin, generics.RetrieveDestroyAPIView):
    serializer_class = PhraseSerializer

    def get_object(self) -> Phrase:
        game_id: int = self.kwargs["game_id"]
        phrase_id: int = self.kwargs["phrase_id"]
        phrase: Optional[Phrase] = Phrase.objects.filter(id=phrase_id, game_id=game_id).first()
        if phrase is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return phrase

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    def delete(self, request, *args, **kwargs) -> Response:
        phrase: Phrase = self.get_object()
        phrase.delete()
        return self.generate_no_error_response({})


class TeamsView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = TeamSerializer

    def get_queryset(self):
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return Team.objects.filter(game=game).order_by("id")

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)

        serializer: TeamSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        requester: User = request.user
        validated_data: dict = serializer.validated_data
        Team.objects.create(
            game=game,
            name=validated_data["name"],
            created_by_id=requester.id,
            updated_by_id=requester.id,
        )
        return self.generate_no_error_response({})


class TeamView(ActiveUserAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TeamSerializer

    def get_object(self) -> Team:
        game_id: int = self.kwargs["game_id"]
        team_id: int = self.kwargs["team_id"]
        team: Optional[Team] = Team.objects.filter(id=team_id, game_id=game_id).first()
        if team is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return team

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    def put(self, request: Request, *args, **kwargs) -> Response:
        serializer: TeamSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        team: Team = self.get_object()
        requester: User = request.user
        validated_data: dict = serializer.validated_data
        team.name = validated_data["name"]
        team.updated_by_id = requester.id
        team.save()
        return self.generate_no_error_response({})

    def delete(self, request, *args, **kwargs) -> Response:
        team: Team = self.get_object()
        team.delete()
        return self.generate_no_error_response({})
