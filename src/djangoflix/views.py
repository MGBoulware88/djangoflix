from django.shortcuts import render
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect

from .models import Account, Profile


def landing(request):
    return HttpResponse("Hello, World!")


def home(request):
    return HttpResponse("Hello, Home!")


def profiles(request):
    id: int = request.session["account"]
    existing_profiles = Account.get_all_profiles_for_account_by_account_id(id)
    context = {"profiles": existing_profiles}
    
    return render(request, "djangoflix/profiles.html", context)


def browse(request):
    return HttpResponse("Hello, browse!")


def movies(request):
    return HttpResponse("Hello, movies!")


def tv(request):
    return HttpResponse("Hello, tv!")


def search(request):
    return HttpResponse("Hello, search!")


def favorites(request):
    return HttpResponse("Hello, Favorites!")


def details(request):
    return HttpResponse("Hello, Details!")