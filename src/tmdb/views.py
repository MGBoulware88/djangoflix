from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponseNotAllowed

from .forms import FetchForm
from .models import TMDBMovie, TMDBTVSeries, TMDBTVSeason, TMDBTVEpisode


### The TMDB FetchForm view
def home(request):
    if request.method == "GET":
        form = FetchForm()

        return render(request, "tmdb/home.html", context={"form": form})
        



### POST to movies to fetch Movie Details
def process_form(request):
    if not request.method == "POST":
        return HttpResponseNotAllowed(["POST"])
    
    match request.POST["type"]:
        case "movie":
            TMDBMovie.fetch_one_movie_by_id(request.POST["id"])
        case "series":
            TMDBTVSeries.fetch_one_series_by_id(request.POST["id"])
        case "season":
            TMDBTVSeason.fetch_one_season_by_series_id(
                request.POST["id"],
                request.POST["season"]
            )
        case _:
            print(f"\nInvalid type {request.POST["type"]}\n")
            return redirect(reverse_lazy("tmdb:home"))

    return redirect(reverse_lazy("tmdb:home"))
