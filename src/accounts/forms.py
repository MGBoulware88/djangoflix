from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from djangoflix.models import Account, Profile, ICON_CHOICES


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
                code="password",
            )


class LoginForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=30)
    password = forms.CharField(
        min_length=8,
        max_length=50,
        widget=forms.PasswordInput,
    )

    ## Overriding __init__ to pass current request to clean
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)


    # Overriding clean to add invalid credentials to form.non_field_errors
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data["username"]
        password = cleaned_data["password"]
        
        authenticated_user = authenticate(
            self.request,
            username=username,
            password=password
        )

        if not authenticated_user:
            raise ValidationError("Invalid credentials.", code="credentials")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["account", "profile_name", "icon"]
        help_texts = {
            "profile_name": "Max 16 characters.",
        }
        labels = {
            "profile_name": "Profile Name",
            "icon": "Profile Icon",
        }
        widgets = {
            "account": forms.HiddenInput,
            "form": forms.RadioSelect(choices=ICON_CHOICES),
        }


    # Adding session's account ID to __init__ so that I can ignore
    # Account field value that may have been tampered with
    # It is still convenient to have it exist in the form
    def __init__(self, *args, **kwargs):
        self.account_id = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)
    

    # Profile names are not unique in the database schema,
    # but must be unique per Account
    def clean(self):
        cleaned_data = super().clean()
        if not "account" in cleaned_data:
            raise ValidationError("I can't process this. Logout and try again.")
        try:
            profile_name = cleaned_data["profile_name"]
        except KeyError:
            return
        # Ensure correct val for Account using session
        this_account = Account.get_one_account_by_id(self.account_id)
        cleaned_data["account"] = this_account
        
        # The __iexact filter may not function properly in SQLite
        # if the profile_name includes chars 'outside the ASCII range'
        used_name = this_account.profiles.filter(
            profile_name__iexact=profile_name
        ).first()
        if used_name:
            raise ValidationError(
                "That profile name is already in use.",
                code="used_name",
            )

# TODO: Add password/username recovery forms