from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.http import HttpResponse, HttpResponseRedirect

from accounts.forms import ProfileForm
from .models import Account, Profile


def landing(request):
    return HttpResponse("Hello, World!")


def home(request):
    return HttpResponse("Hello, Home!")


def profiles(request):
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if not form.is_valid():
            id: int = request.session["account"]
            existing_profiles = Account.get_all_profiles_for_account_by_account_id(id)
            context = {
                "form": form,
                "profiles": existing_profiles,
            }

            return render(request, "djangoflix/profiles.html", {"form": form})
        
        form.save()

        return redirect(reverse_lazy("djangoflix:profiles"))

    id: int = request.session["account"]
    existing_profiles = Account.get_all_profiles_for_account_by_account_id(id)
    add_profile = ProfileForm(initial={"account": id})
    context = {
        "form": add_profile,
        "profiles": existing_profiles,
    }
    
    return render(request, "djangoflix/profiles.html", context)


def select_profile(request, id: int):
    pass


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