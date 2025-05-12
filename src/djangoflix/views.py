from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseNotAllowed

from accounts.forms import ProfileForm
from .models import Account


### landing, pre-login/reg to djangoflix/
### Also used when redirected from / url
def landing(request):
    return render(request, "djangoflix/landing.html")


##### User is logged in now #####

### Display Profiles after User logins to Account
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


### POST route to store Profile in session
### then redirect to Home
def select_profile(request, id: int):
    if not request.method == "POST":
        raise HttpResponseNotAllowed(["POST"])
    
    request.session["profile"] = id

    return redirect(reverse_lazy("djangoflix:home"))



def home(request):
    return HttpResponse("Hello, Home!")


def browse(request):
    return HttpResponse("Hello, browse!")


def movies(request):
    return HttpResponse("Hello, movies!")


def tv(request):
    return HttpResponse("Hello, tv!")


def favorites(request):
    return HttpResponse("Hello, Favorites!")


def search(request):
    return HttpResponse("Hello, search!")


def details(request):
    return HttpResponse("Hello, Details!")