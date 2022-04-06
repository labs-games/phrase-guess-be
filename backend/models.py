from django.db import models
import enum


class Game(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_id = models.IntegerField()


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


class Round(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    phrase = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by_id = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by_id = models.IntegerField()


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
