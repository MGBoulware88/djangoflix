from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class RegistrationForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=30)
    email = forms.EmailField(max_length=100)
    password = forms.CharField(
        min_length=8,
        max_length=50,
        help_text="Must be at least 8 characters long.",
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        min_length=8,
        max_length=50,
        help_text="Please enter your password again for confirmation.",
        widget=forms.PasswordInput,
    )

    # Overriding clean for additional validations:
    # username cannot already be in use
    # email cannot already be in use
    # password & confirm password must match
    def clean(self):
        cleaned_data = super().clean()
        # These are in order so that if one fails, it immediately returns
        # a validation error without checking the rest
        username = cleaned_data["username"]
        # Using filter instead of get b/c we want to not find something
        existing_user = User.objects.filter(username=username).first()
        if existing_user:
            raise ValidationError(
                "Username taken. Please try another.",
                code="username",
            )
        email = cleaned_data.get("email")
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            raise ValidationError(
                "Email already taken. Were you trying to login?",
                code="email",
            )

        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if not password == confirm_password:
            raise ValidationError(
                "Password and Confirm password must match.",
                code=password,
            )



class LoginForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=30)
    password = forms.CharField(
        min_length=8,
        max_length=50,
        widget=forms.PasswordInput,
    )


class ProfileForm(forms.Form):
    profile_name = forms.CharField(min_length=3, max_length=16)
    profile_icon = forms.ChoiceField()


# TODO: Add password/username recovery forms