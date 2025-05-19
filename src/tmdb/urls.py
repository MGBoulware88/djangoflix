from django.urls import path

from . import views


app_name="tmdb"
urlpatterns = [
    path("tmdb/", views.home, name="home"),
    path("tmdb/movies/", views.movies, name="movies"),
    path("tmdb/tv/", views.tv_series, name="tv_series"),
]