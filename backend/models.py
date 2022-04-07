from __future__ import annotations

import enum
from dataclasses import dataclass

from django.db import models


class Ordering(enum.IntEnum):
    ordered = 1
    random = 2


@dataclass
class GameConfigs:
    phrase_order: Ordering
    team_order: Ordering

    @classmethod
    def from_dict(cls, to_parse: dict) -> GameConfigs:
        return GameConfigs(
            phrase_order=Ordering(to_parse.get("phrase_order", Ordering.ordered.value)),
            team_order=Ordering(to_parse.get("team_order", Ordering.ordered.value)),
        )

    def to_dict(self) -> dict:
        return {
            "phrase_order": self.phrase_order.value,
            "team_order": self.team_order.value,
        }


class Game(models.Model):
    name = models.CharField(max_length=200)
    configs = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_id = models.IntegerField()

    @property
    def config_object(self) -> GameConfigs:
        return GameConfigs.from_dict(self.configs)

    @config_object.setter
    def config_object(self, val: GameConfigs) -> None:
        self.configs = val.to_dict()


class Phrase(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    value = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_id = models.IntegerField()


class Team(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_id = models.IntegerField()


@dataclass
class RoundConfigs:
    team_ids_ordering: list[int]

    @classmethod
    def from_dict(cls, to_parse: dict) -> RoundConfigs:
        return RoundConfigs(team_ids_ordering=to_parse.get("team_ids_ordering", []))

    def to_dict(self) -> dict:
        return {
            "team_ids_ordering": self.team_ids_ordering,
        }


class Round(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    phrase = models.ForeignKey(Phrase, on_delete=models.CASCADE)
    configs = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_id = models.IntegerField()

    @property
    def config_object(self) -> RoundConfigs:
        return RoundConfigs.from_dict(self.configs)

    @config_object.setter
    def config_object(self, val: RoundConfigs) -> None:
        self.configs = val.to_dict()


class GuessType(enum.IntEnum):
    letter = 1
    phrase = 2


class GuessStatus(enum.IntEnum):
    correct = 1
    wrong = 2


class Guess(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    type = models.IntegerField(db_index=True)
    status = models.IntegerField(db_index=True)
    value = models.CharField(max_length=200)
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
