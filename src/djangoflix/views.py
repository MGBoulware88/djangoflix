from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseNotAllowed

from accounts.forms import ProfileForm
from .models import Account, Profile, WatchableContent


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
    action = []
    adventure = []
    animated = []
    comedy = []
    crime = []
    documentary = []
    drama = []
    family = []
    fantasy = []
    history = []
    horror = []
    kids = []
    music = []
    mystery = []
    reality = []
    romance = []
    scifi = []
    thriller = []
    tv_movie = []
    war = []
    western = []

    for content in all_content:
        genres = content.genres.all()
        for genre in genres:
            match genre.name:
                case "Action":
                    action.append(content)
                case "Action & Adventure":
                    action.append(content)
                    adventure.append(content)
                case "Adventure":
                    adventure.append(content)
                case "Animation":
                    animated.append(content)
                case "Comedy":
                    comedy.append(content)
                case "Crime":
                    crime.append(content)
                case "Documentary":
                    documentary.append(content)
                case "Drama":
                    drama.append(content)
                case "Family":
                    family.append(content)
                case "Fantasy":
                    fantasy.append(content)
                case "History":
                    history.append(content)
                case "Horror":
                    horror.append(content)
                case "Kids":
                    kids.append(content)
                case "Music":
                    music.append(content)
                case "Mystery":
                    mystery.append(content)
                case "Reality":
                    reality.append(content)
                case "Romance":
                    romance.append(content)
                case "Science Fiction":
                    scifi.append(content)
                case "Sci-Fi & Fantasy":
                    scifi.append(content)
                    fantasy.append(content)
                case "Thriller":
                    thriller.append(content)
                case "TV Movie":
                    tv_movie.append(content)
                case "Music":
                    music.append(content)
                case "War":
                    war.append(content)
                case "War & Politics":
                    war.append(content)
                case "Western":
                    western.append(content)
                case _:
                    print(f"\nUnmapped genre name: {genre.name}\n")

    context = {
        "action": action,
        "adventure": adventure,
        "animated": animated,
        "comedy": comedy,
        "crime": crime,
        "documentary": documentary,
        "drama": drama,
        "family": family,
        "fantasy": fantasy,
        "history": history,
        "horror": horror,
        "kids": kids,
        "music": music,
        "mystery": mystery,
        "reality": reality,
        "romance": romance,
        "scifi": scifi,
        "thriller": thriller,
        "tv_movie": tv_movie,
        "war": war,
    }
    
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
        
    all_movies = WatchableContent.get_all_movies()
    action = []
    adventure = []
    animated = []
    comedy = []
    crime = []
    documentary = []
    drama = []
    family = []
    fantasy = []
    history = []
    horror = []
    kids = []
    music = []
    mystery = []
    reality = []
    romance = []
    scifi = []
    thriller = []
    tv_movie = []
    war = []
    western = []

    for movie in all_movies:
        genres = movie.genres.all()
        for genre in genres:
            match genre.name:
                case "Action":
                    action.append(movie)
                case "Action & Adventure":
                    action.append(movie)
                    adventure.append(movie)
                case "Adventure":
                    adventure.append(movie)
                case "Animation":
                    animated.append(movie)
                case "Comedy":
                    comedy.append(movie)
                case "Crime":
                    crime.append(movie)
                case "Documentary":
                    documentary.append(movie)
                case "Drama":
                    drama.append(movie)
                case "Family":
                    family.append(movie)
                case "Fantasy":
                    fantasy.append(movie)
                case "History":
                    history.append(movie)
                case "Horror":
                    horror.append(movie)
                case "Kids":
                    kids.append(movie)
                case "Music":
                    music.append(movie)
                case "Mystery":
                    mystery.append(movie)
                case "Reality":
                    reality.append(movie)
                case "Romance":
                    romance.append(movie)
                case "Science Fiction":
                    scifi.append(movie)
                case "Sci-Fi & Fantasy":
                    scifi.append(movie)
                    fantasy.append(movie)
                case "Thriller":
                    thriller.append(movie)
                case "TV Movie":
                    tv_movie.append(movie)
                case "Music":
                    music.append(movie)
                case "War":
                    war.append(movie)
                case "War & Politics":
                    war.append(movie)
                case "Western":
                    western.append(movie)
                case _:
                    print(f"\nUnmapped genre name: {genre.name}\n")

    context = {
        "action": action,
        "adventure": adventure,
        "animated": animated,
        "comedy": comedy,
        "crime": crime,
        "documentary": documentary,
        "drama": drama,
        "family": family,
        "fantasy": fantasy,
        "history": history,
        "horror": horror,
        "kids": kids,
        "music": music,
        "mystery": mystery,
        "reality": reality,
        "romance": romance,
        "scifi": scifi,
        "thriller": thriller,
        "tv_movie": tv_movie,
        "war": war,
    }
    
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
        
    all_tv = WatchableContent.get_all_tv()
    action = []
    adventure = []
    animated = []
    comedy = []
    crime = []
    documentary = []
    drama = []
    family = []
    fantasy = []
    history = []
    horror = []
    kids = []
    music = []
    mystery = []
    reality = []
    romance = []
    scifi = []
    thriller = []
    war = []
    western = []

    for tv in all_tv:
        genres = tv.genres.all()
        for genre in genres:
            match genre.name:
                case "Action":
                    action.append(tv)
                case "Action & Adventure":
                    action.append(tv)
                    adventure.append(tv)
                case "Adventure":
                    adventure.append(tv)
                case "Animation":
                    animated.append(tv)
                case "Comedy":
                    comedy.append(tv)
                case "Crime":
                    crime.append(tv)
                case "Documentary":
                    documentary.append(tv)
                case "Drama":
                    drama.append(tv)
                case "Family":
                    family.append(tv)
                case "Fantasy":
                    fantasy.append(tv)
                case "History":
                    history.append(tv)
                case "Horror":
                    horror.append(tv)
                case "Kids":
                    kids.append(tv)
                case "Music":
                    music.append(tv)
                case "Mystery":
                    mystery.append(tv)
                case "Reality":
                    reality.append(tv)
                case "Romance":
                    romance.append(tv)
                case "Science Fiction":
                    scifi.append(tv)
                case "Sci-Fi & Fantasy":
                    scifi.append(tv)
                    fantasy.append(tv)
                case "Thriller":
                    thriller.append(tv)
                case "Music":
                    music.append(tv)
                case "War":
                    war.append(tv)
                case "War & Politics":
                    war.append(tv)
                case "Western":
                    western.append(tv)
                case _:
                    print(f"\nUnmapped genre name: {genre.name}\n")

    context = {
        "action": action,
        "adventure": adventure,
        "animated": animated,
        "comedy": comedy,
        "crime": crime,
        "documentary": documentary,
        "drama": drama,
        "family": family,
        "fantasy": fantasy,
        "history": history,
        "horror": horror,
        "kids": kids,
        "music": music,
        "mystery": mystery,
        "reality": reality,
        "romance": romance,
        "scifi": scifi,
        "thriller": thriller,
        "war": war,
    }
    
    return render(request, "djangoflix/view_content.html", context)


def favorites(request):
    return HttpResponse("Hello, Favorites!")


def search(request):
    return HttpResponse("Hello, search!")


def details(request):
    return HttpResponse("Hello, Details!")