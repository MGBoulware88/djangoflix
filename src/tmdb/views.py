from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponseNotAllowed
import json

from .forms import FetchForm, UploadForm
from .models import TMDBMovie, TMDBTVSeries, TMDBTVSeason


### The TMDB FetchForm view
def home(request):
    if request.method == "GET":
        fetch_form = FetchForm()
        file_form = UploadForm()

        context={"fetch_form": fetch_form, "file_form": file_form}

        return render(request, "tmdb/home.html", context)
        

### Process FetchForm
def process_form(request):
    if not request.method == "POST":
        return HttpResponseNotAllowed(["POST"])
    
    match request.POST["type"]:
        case "movie":
            TMDBMovie.fetch_one_movie_by_id(request.POST["id"])
        case "series":
            TMDBTVSeries.fetch_one_series_by_tmdb_id(request.POST["id"])
        case "season":
            TMDBTVSeason.fetch_one_season_by_series_id(
                request.POST["id"],
                request.POST["season"]
            )
        case _:
            print(f"\nInvalid type {request.POST["type"]}\n")
            return redirect(reverse_lazy("tmdb:home"))

    return redirect(reverse_lazy("tmdb:home"))


### Process JSON upload
def process_upload(request):
    if not request.method == "POST":
        return HttpResponseNotAllowed(["POST"])
    
    file = request.FILES["file"]
    file_data = json.load(file)

    match request.POST["type"]:
        case "movie":
            TMDBMovie.add_movie_from_json(file_data)
        case "series":
            TMDBTVSeries.add_series_from_json(file_data)
        case "season":
            pass
        case _:
            print(f"\nInvalid type {request.POST["type"]}\n")
            return redirect(reverse_lazy("tmdb:home"))



    return redirect(reverse_lazy("tmdb:home"))