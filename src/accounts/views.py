from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

from .forms import RegistrationForm, LoginForm
from djangoflix.models import Account


def register(request):
    if request.method == "POST":
        reg_form = RegistrationForm(request.POST)
        if not reg_form.is_valid():
            return render(request, "registration/register.html", context={"form": reg_form})
        
        new_user = User.objects.create_user(
            username=reg_form.cleaned_data["username"],
            password=reg_form.cleaned_data["password"],
        )
        if not new_user:
            # do something
            pass
        # Log the new user in so they are stored in session
        login(request, new_user)
        # Create Account, assign this user
        new_account = Account(user=new_user)
        new_account.save()
        # Add new_account to session
        request.session["account"] = new_account.id
        request.session["username"] = new_user.username
        # Redirect to profiles page
        return redirect(
            reverse_lazy("djangoflix:profiles")
        )
    
    form = RegistrationForm()

    return render(request, "registration/register.html", context={"form": form})


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
    
    login_form = LoginForm(request.POST)
    if not login_form.is_valid():
        return render(
            request, "registration/login.html", context={"form": login_form}
        )
    
    authenticated_user = authenticate(
        request,
        username=login_form.cleaned_data["username"],
        password=login_form.cleaned_data["password"],
    )
    if not authenticated_user:
        # TODO: Handle failed login after valid form
        pass

    login(request, authenticated_user)
    this_account = Account.objects.filter(user=authenticated_user.id).first()
    if not this_account:
        # TODO: handle failed account lookup after valid user
        pass
    
    request.session["account"] = this_account.id
    request.session["username"] = authenticated_user.username

    return redirect(
        reverse_lazy("djangoflix:profiles")
    )


def logout_user(request):
    logout(request)

    request.session["logout"] = True

    return redirect("accounts:login")