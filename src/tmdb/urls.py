from django.urls import path

from . import views


app_name="tmdb"
urlpatterns = [
    path("", views.home, name="home"),
    path("tmdb/process/", views.process_form, name="process"),
]