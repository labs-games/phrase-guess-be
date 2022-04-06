from typing import Optional

from django.contrib.auth.models import User
from django.db.transaction import atomic
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from backend.models import Game, Phrase, Team
from common.rest.exceptions import ErrorCode, ErrorCodeException
from common.rest.views import ActiveUserAPIViewMixin

from .serializers import GameSerializer, PhraseSerializer, TeamSerializer


class GamesView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    queryset = Game.objects.order_by("-id")
    serializer_class = GameSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer: GameSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        requester: User = request.user
        validated_data: dict = serializer.validated_data
        Game.objects.create(
            name=validated_data["name"], created_by_id=requester.id, updated_by_id=requester.id
        )
        return self.generate_no_error_response({})


class GameView(ActiveUserAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Game.objects.order_by("-id")
    serializer_class = GameSerializer

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
        serializer: GameSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        game: Game = self.get_object()
        requester: User = request.user
        validated_data: dict = serializer.validated_data
        game.name = validated_data["name"]
        game.updated_by_id = requester.id
        game.save()
        return self.generate_no_error_response({})

    def delete(self, request, *args, **kwargs) -> Response:
        game: Game = self.get_object()
        game.delete()
        return self.generate_no_error_response({})


class PhrasesView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    queryset = Phrase.objects.order_by("id")
    serializer_class = PhraseSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer: PhraseSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        requester: User = request.user
        validated_data: dict = serializer.validated_data
        Phrase.objects.create(
            value=validated_data["value"], created_by_id=requester.id, updated_by_id=requester.id
        )
        return self.generate_no_error_response({})


class PhraseView(ActiveUserAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Phrase.objects.order_by("id")
    serializer_class = PhraseSerializer

    def get_object(self) -> Phrase:
        phrase_id: int = self.kwargs["phrase_id"]
        phrase: Optional[Phrase] = Phrase.objects.filter(id=phrase_id).first()
        if phrase is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return phrase

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    def put(self, request: Request, *args, **kwargs) -> Response:
        serializer: PhraseSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        phrase: Phrase = self.get_object()
        requester: User = request.user
        validated_data: dict = serializer.validated_data
        phrase.value = validated_data["value"]
        phrase.updated_by_id = requester.id
        phrase.save()
        return self.generate_no_error_response({})

    def delete(self, request, *args, **kwargs) -> Response:
        phrase: Phrase = self.get_object()
        phrase.delete()
        return self.generate_no_error_response({})


class TeamsView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    queryset = Team.objects.order_by("-id")
    serializer_class = TeamSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer: TeamSerializer = self.get_serializer(data=request.data)
        serializer.raise_validation_error_if_any()

        requester: User = request.user
        validated_data: dict = serializer.validated_data
        Team.objects.create(
            name=validated_data["name"], created_by_id=requester.id, updated_by_id=requester.id
        )
        return self.generate_no_error_response({})


class TeamView(ActiveUserAPIViewMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.order_by("-id")
    serializer_class = TeamSerializer

    def get_object(self) -> Team:
        team_id: int = self.kwargs["team_id"]
        team: Optional[Team] = Team.objects.filter(id=team_id).first()
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
