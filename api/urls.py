from django.urls import path

from .rest.games import views as games_views
from .rest.me import views as me_views

urlpatterns = [
    path("login/", me_views.LoginView.as_view()),
    path("me/", me_views.MeView.as_view()),
    path("games/<int:game_id>/", games_views.GameView.as_view()),
    path("games/", games_views.GamesView.as_view()),
    path("phrases/<int:phrase_id>/", games_views.PhraseView.as_view()),
    path("phrases/", games_views.PhrasesView.as_view()),
    path("teams/<int:team_id>/", games_views.TeamView.as_view()),
    path("teams/", games_views.TeamsView.as_view()),
]
