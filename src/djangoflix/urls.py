from django.urls import path

from . import views


app_name = "djangoflix"
urlpatterns = [
    # path("", views.IndexView.as_view(), name="index"),
    path("", views.index, name="index"),
    path("", views.home, name="home"),
    path("", views.browse, name="browse"),
    path("", views.movies, name="movies"),
    path("", views.tv, name="tv"),
    path("", views.search, name="search"),
]