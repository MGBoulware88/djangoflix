from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .forms import RegistrationForm, LoginForm
from djangoflix.models import Account


def register(request):
    if request.method == "GET":
        reg_form = RegistrationForm()

        return render(
            request,
            "registration/register.html",
            context={"form": reg_form}
        )
    
    reg_form = RegistrationForm(request.POST)
    if not reg_form.is_valid():
        return render(
            request,
            "registration/register.html",
            context={"form": reg_form}
        )
    # Anything that could cause create_user to fail 
    # is handled via form validation
    new_user = User.objects.create_user(
        username=reg_form.cleaned_data["username"],
        email=reg_form.cleaned_data["email"],
        password=reg_form.cleaned_data["password"]
    )
    # Note: login adds user to session via request.user
    login(request, new_user)
    new_account = Account.create_account(new_user)
    request.session["account"] = new_account.id
    
    return redirect(reverse_lazy("djangoflix:profiles"))


def login_user(request):
    if request.method == "GET":
        login_form = LoginForm()
        if "logout" in request.session:
            del request.session["logout"]
            context = {
                "logout": True,
                "form": login_form,
            }
        else:
            context = {
                "logout": False,
                "form": login_form,
            }

        return render(request, "registration/login.html", context)

    login_form = LoginForm(request.POST, request=request)
    if not login_form.is_valid():
        return render(
            request, "registration/login.html", context={"form": login_form}
        )
    
    # LoginForm.clean() already preforms this, but I still need a User
    authenticated_user = authenticate(
        request,
        username=login_form.cleaned_data["username"],
        password=login_form.cleaned_data["password"]
    )
    login(request, authenticated_user)

    this_account = Account.get_one_account_by_user_id(authenticated_user.id)
    # If Account.DoesNotExist, prev method returns None
    # that should mean this is a 'staff user' & we can safely redirect to
    # admin:index because it blocks unauthed acccess
    if not this_account:
        return redirect(reverse_lazy("admin:index"))
    
    request.session["account"] = this_account.id

    return redirect(
        reverse_lazy("djangoflix:profiles")
    )


def logout_user(request):
    logout(request)

    request.session["logout"] = True

    return redirect("accounts:login")