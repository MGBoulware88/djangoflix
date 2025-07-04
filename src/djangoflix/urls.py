from django.urls import path

from . import views


app_name = "djangoflix"
urlpatterns = [
    path("", views.landing, name="landing"),
    path("home/", views.home, name="home"),
    path("profiles/", views.profiles, name="profiles"),
    path("profiles/<int:id>/", views.select_profile, name="select_profile"),
    path("browse/", views.browse, name="browse"),
    path("movies/", views.movies, name="movies"),
    path("tv/", views.tv, name="tv"),
    path("favorites/", views.favorites, name="favorites"),
    path("search/", views.search, name="search"),
    path("results/", views.results, name="results"),
    path("details/<int:id>/<str:origin>", views.details, name="details"),
    path("watch/<int:id>/<str:origin>/", views.watch, name="watch"),
    path("favorite/<int:id>/<str:origin>/<str:destination>/<str:action>/", views.favorite, name="favorite"),
]