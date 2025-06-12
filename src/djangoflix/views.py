from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseNotAllowed

from accounts.forms import ProfileForm
from .models import Account, Profile, WatchableContent, TVEpisode


### landing, pre-login/reg to djangoflix/
### Also used when redirected from / url
def landing(request):
    if "profile" in request.session:
        return redirect("djangoflix:home")
    elif "account" in request.session:
        return redirect("djangoflix:profiles")
    
    return render(request, "djangoflix/landing.html")


##### User is logged in now #####

### Display Profiles after User logins to Account
def profiles(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, account=request.session["account"])
        
        if not form.is_valid():
            id: int = request.session["account"]
            existing_profiles = Account.get_all_profiles_for_account_by_id(id)
            context = {
                "form": form,
                "profiles": existing_profiles,
            }
            return render(request, "djangoflix/profiles.html", context)
        
        form.save()

        return redirect(reverse_lazy("djangoflix:profiles"))

    # handle case for user going to /profiles w/o proper login procedure
    try:
        id: int = request.session["account"]
    except KeyError:
        return redirect(reverse_lazy("accounts:login"))
    existing_profiles = Account.get_all_profiles_for_account_by_id(id)
    add_profile_form = ProfileForm(
        initial={
            "account": request.session["account"],
            "icon": "default.png",
        }
    )
    context = {
        "form": add_profile_form,
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
    # Handle case for user manually going to /home w/o proper login procedure
    try:
        this_profile = Profile.get_one_profile_by_id(request.session["profile"])
        if not this_profile:
            raise Profile.DoesNotExist
    # KeyError catches login skippers, DoesNotExist catches invalid session data
    except (KeyError, Profile.DoesNotExist):
        if not "account" in request.session:
            # Send them to the login page, not register
            # If they are trying to get to home, they probably have an account
            return redirect(reverse_lazy("accounts:login"))
        elif not "profile" in request.session:
            return redirect(reverse_lazy("djangoflix:profiles"))
        else:
            return redirect(reverse_lazy("accounts:logout"))
    
    favorites = this_profile.get_favorites()
    context = {
        "profile": this_profile,
        "favorites": favorites,
    }
    
    return render(request, "djangoflix/home.html", context)


### browse, movies, & tv all use view_content.html template,
### with different queries
def browse(request):
    if not request.method == "GET":
        return HttpResponseNotAllowed(["GET"])
    try:
        this_profile = Profile.get_one_profile_by_id(request.session["profile"])
        if not this_profile:
            raise Profile.DoesNotExist
    # KeyError catches login skippers, DoesNotExist catches invalid session data
    except (KeyError, Profile.DoesNotExist):
        if not "account" in request.session:
            # Send them to the login page, not register
            # If they are trying to get to home, they probably have an account
            return redirect(reverse_lazy("accounts:login"))
        elif not "profile" in request.session:
            return redirect(reverse_lazy("djangoflix:profiles"))
        else:
            return redirect(reverse_lazy("accounts:logout"))
        
    all_content = WatchableContent.get_all_content()
    context = WatchableContent.get_context(all_content)
    context["origin"] = "Browse"
    
    
    return render(request, "djangoflix/view_content.html", context)


def movies(request):
    if not request.method == "GET":
        return HttpResponseNotAllowed(["GET"])
    try:
        this_profile = Profile.get_one_profile_by_id(request.session["profile"])
        if not this_profile:
            raise Profile.DoesNotExist
    # KeyError catches login skippers, DoesNotExist catches invalid session data
    except (KeyError, Profile.DoesNotExist):
        if not "account" in request.session:
            # Send them to the login page, not register
            # If they are trying to get to home, they probably have an account
            return redirect(reverse_lazy("accounts:login"))
        elif not "profile" in request.session:
            return redirect(reverse_lazy("djangoflix:profiles"))
        else:
            return redirect(reverse_lazy("accounts:logout"))
        
    all_content = WatchableContent.get_all_movies()
    context = WatchableContent.get_context(all_content)
    context["origin"] = "Movies"
    
    return render(request, "djangoflix/view_content.html", context)


def tv(request):
    if not request.method == "GET":
        return HttpResponseNotAllowed(["GET"])
    try:
        this_profile = Profile.get_one_profile_by_id(request.session["profile"])
        if not this_profile:
            raise Profile.DoesNotExist
    # KeyError catches login skippers, DoesNotExist catches invalid session data
    except (KeyError, Profile.DoesNotExist):
        if not "account" in request.session:
            # Send them to the login page, not register
            # If they are trying to get to home, they probably have an account
            return redirect(reverse_lazy("accounts:login"))
        elif not "profile" in request.session:
            return redirect(reverse_lazy("djangoflix:profiles"))
        else:
            return redirect(reverse_lazy("accounts:logout"))
        
    all_content = WatchableContent.get_all_tv()
    context = WatchableContent.get_context(all_content)
    context["origin"] = "TV"
    
    return render(request, "djangoflix/view_content.html", context)


def favorites(request):
    if not request.method == "GET":
        return HttpResponseNotAllowed(["GET"])
    try:
        this_profile = Profile.get_one_profile_by_id(request.session["profile"])
        if not this_profile:
            raise Profile.DoesNotExist
    # KeyError catches login skippers, DoesNotExist catches invalid session data
    except (KeyError, Profile.DoesNotExist):
        if not "account" in request.session:
            return redirect(reverse_lazy("accounts:login"))
        elif not "profile" in request.session:
            return redirect(reverse_lazy("djangoflix:profiles"))
        else:
            return redirect(reverse_lazy("accounts:logout"))
        
    all_favorites = this_profile.favorites.all()

    context = {
        "favorites": all_favorites,
        "origin": "Favorites",
    }
    
    return render(request, "djangoflix/favorites.html", context)


def search(request):
    return HttpResponse("Hello, search!")


def details(request, id, origin):
    if not request.method == "GET":
        return HttpResponseNotAllowed(["GET"])
    try:
        this_profile = Profile.get_one_profile_by_id(request.session["profile"])
        if not this_profile:
            raise Profile.DoesNotExist
    # KeyError catches login skippers, DoesNotExist catches invalid session data
    except (KeyError, Profile.DoesNotExist):
        if not "account" in request.session:
            return redirect(reverse_lazy("accounts:login"))
        elif not "profile" in request.session:
            return redirect(reverse_lazy("djangoflix:profiles"))
        else:
            return redirect(reverse_lazy("accounts:logout"))
    
    this_content = WatchableContent.get_one_content_by_id(id)
    
    if this_content in this_profile.favorites.all():
        favorite = True
    else:
        favorite = False
    
    genres = []
    if this_content:
        all_genres = this_content.genres.all()
        for genre in all_genres:
            genres.append(genre.name)
    
    seasons = []
    if this_content.content_type == "TV":
        all_seasons = this_content.get_current_seasons()
        for season in all_seasons:
            season.all_episodes = season.get_current_episodes()
            seasons.append(season)

    context = {
        "content": this_content,
        "origin": origin,
        "genres": genres,
        "favorite": favorite,
        "seasons": seasons,
    }

    return render(request, "djangoflix/view_details.html", context)


def watch(request, id, origin):
    if not request.method == "GET":
        return HttpResponseNotAllowed(["GET"])
    try:
        this_profile = Profile.get_one_profile_by_id(request.session["profile"])
        if not this_profile:
            raise Profile.DoesNotExist
    # KeyError catches login skippers, DoesNotExist catches invalid session data
    except (KeyError, Profile.DoesNotExist):
        if not "account" in request.session:
            return redirect(reverse_lazy("accounts:login"))
        elif not "profile" in request.session:
            return redirect(reverse_lazy("djangoflix:profiles"))
        else:
            return redirect(reverse_lazy("accounts:logout"))
        
    this_content = WatchableContent.get_one_content_by_id(id)

    if this_content in this_profile.favorites.all():
        favorite = True
    else:
        favorite = False
    
    context = {
        "content": this_content,
        "origin": origin,
        "favorite": favorite,
    }

    return render(request, "djangoflix/watch_content.html", context)


def favorite(request, id, origin, destination: str, action: str):
    if not request.method == "POST":
        return HttpResponseNotAllowed(["POST"])
    
    profile = Profile.get_one_profile_by_id(request.session["profile"])
    content = WatchableContent.get_one_content_by_id(id)
    if action == "add":
        profile.favorites.add(content)
    elif action == "remove":
        profile.favorites.remove(content)
    else:
        print(f"\nNo action provided for {content}\n")
    
    profile.save()

    # All views that allow favoriting content
    match destination:
        case "details":
            return redirect(reverse_lazy(
                    "djangoflix:details",
                    kwargs={"id": id, "origin": origin}
                )
            )
        case "watch":
            return redirect(reverse_lazy(
                    "djangoflix:watch",
                    kwargs={"id": id, "origin": origin}
                )
            )
        case "favorites":
            return redirect(reverse_lazy("djangoflix:favorites"))
        case _:
            print(f"\nMissing or invalid destination of {destination}\n")
            return HttpResponse("😒")