from django.urls import path

from .rest.me import views as me_views

urlpatterns = [
    path("login/", me_views.LoginView.as_view()),
    path("me/", me_views.MeView.as_view()),
]
