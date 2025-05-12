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
    path("search/", views.search, name="search"),
    path("favorites/", views.favorites, name="favorites"),
    path("details/<int:content_id>/", views.details, name="details"),
]