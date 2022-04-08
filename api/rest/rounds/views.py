import random
from dataclasses import dataclass
from typing import Optional

from django.contrib.auth.models import User
from django.db.transaction import atomic
from more_itertools import circular_shifts, first_true
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from backend.models import (
    SCORE_PER_LETTERS,
    WRONG_PHRASE_PENALTY,
    Game,
    Guess,
    GuessStatus,
    GuessType,
    Ordering,
    Phrase,
    Round,
    RoundConfigs,
    Team,
)
from common.rest.exceptions import ErrorCode, ErrorCodeException
from common.rest.views import ActiveUserAPIViewMixin

from .serializers import (
    GuessCreationSerializer,
    GuessSerializer,
    RoundCreationSerializer,
    RoundSerializer,
    RoundUpdationSerializer,
)


class RoundsView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = RoundSerializer

    def get_queryset(self):
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return Round.objects.filter(game=game).order_by("id")

    def get(self, request: Request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request, *args, **kwargs) -> Response:
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
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
        team_ids: list[int] = [t.id for t in Team.objects.filter(game=game).order_by("id")]
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


@dataclass
class GuessJudgement:
    status: GuessStatus
    score: int
    should_round_ended: bool


class GuessesView(ActiveUserAPIViewMixin, generics.ListCreateAPIView):
    serializer_class = GuessSerializer

    def get_queryset(self):
        round_id: int = self.kwargs["round_id"]
        game_round: Optional[Round] = Round.objects.filter(id=round_id).first()
        if game_round is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)
        return Guess.objects.filter(round=game_round).order_by("id")

    def get(self, request, *args, **kwargs) -> Response:
        data: dict = super().get(request, *args, **kwargs).data
        return self.generate_no_error_response(data)

    @atomic
    def post(self, request, *args, **kwargs) -> Response:
        game_id: int = self.kwargs["game_id"]
        game: Optional[Game] = Game.objects.filter(id=game_id).first()
        if game is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)

        round_id: int = self.kwargs["round_id"]
        game_round: Optional[Round] = Round.objects.filter(id=round_id).first()
        if game_round is None:
            raise ErrorCodeException(ErrorCode.resource_not_found)

        if game_round.is_ended:
            raise ErrorCodeException(ErrorCode.bad_request)

        serializer: GuessCreationSerializer = GuessCreationSerializer(data=request.data)
        serializer.raise_validation_error_if_any()
        validated_data: dict = serializer.validated_data

        team: Optional[Team] = Team.objects.filter(id=validated_data["team_id"], game=game).first()
        if team is None:
            raise ErrorCodeException(ErrorCode.bad_request)

        guess_type: GuessType = GuessType(validated_data["type"])
        guess_value: str = validated_data["value"].upper().strip()
        judgement: GuessJudgement = self._judge_guess(
            game_round=game_round,
            guess_type=guess_type,
            guess_value=guess_value,
        )

        requester: User = request.user
        Guess.objects.create(
            round=game_round,
            team=team,
            type=guess_type,
            status=judgement.status,
            value=guess_value,
            score=judgement.score,
            created_by_id=requester.id,
        )
        if judgement.should_round_ended:
            game_round.is_ended = True
            game_round.save()
        return self.generate_no_error_response(
            {
                "status": judgement.status,
                "score": judgement.score,
                "team_id": team.id,
                "should_end": judgement.should_round_ended,
            }
        )

    def _judge_guess(
        self, game_round: Round, guess_type: GuessType, guess_value: str
    ) -> GuessJudgement:
        if guess_type == GuessType.phrase:
            return self._judge_phrase_guess(game_round, guess_value)
        else:
            return self._judge_letter_guess(game_round, guess_value)

    def _judge_phrase_guess(self, game_round: Round, guess_value: str) -> GuessJudgement:
        phrase_value: str = game_round.phrase.value
        if phrase_value != guess_value:
            return GuessJudgement(
                status=GuessStatus.wrong, score=WRONG_PHRASE_PENALTY, should_round_ended=False
            )
        unguessed_letters: list[str] = _get_unguessed_letters(game_round)
        return GuessJudgement(
            status=GuessStatus.correct,
            score=len(unguessed_letters) * SCORE_PER_LETTERS,
            should_round_ended=True,
        )

    def _judge_letter_guess(self, game_round: Round, guess_value: str) -> GuessJudgement:
        unguessed_letters: list[str] = _get_unguessed_letters(game_round)
        if guess_value not in unguessed_letters:
            return GuessJudgement(status=GuessStatus.wrong, score=0, should_round_ended=False)

        guess_value_counts: int = len(
            [letter for letter in unguessed_letters if letter == guess_value]
        )
        return GuessJudgement(
            status=GuessStatus.correct,
            score=guess_value_counts * SCORE_PER_LETTERS,
            should_round_ended=guess_value_counts == len(unguessed_letters),
        )


def _get_unguessed_letters(game_round: Round) -> list[str]:
    phrase_value: str = game_round.phrase.value
    guessed_letters: set[str] = {
        g.value
        for g in Guess.objects.filter(
            round=game_round, status=GuessStatus.correct, type=GuessType.letter
        )
    }
    return [c for c in phrase_value if c not in guessed_letters and c != " "]
