from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import datetime


class SharedData(models.Model):
    created_at: datetime = models.DateTimeField(auto_now_add=True)
    updated_at: datetime = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        abstract = True


class WatchableContent(SharedData):
    title: str = models.CharField(max_length=100)
    content_type: str = models.CharField(max_length=15)
    genre: str = models.CharField(max_length=100)
    description: str = models.TextField()
    release_date: datetime.date = models.DateField()
    duration: int = models.PositiveIntegerField() # Movies stored in minutes, TV stored in seasons


    def __str__(self) -> str:
        return self.title


class Account(SharedData):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    activation_date: datetime = models.DateTimeField(null=True, auto_now_add=True)
    active: bool = models.BooleanField(default=True)


    def __str__(self) -> str:
        return self.user.username if self.user else "No user assigned yet."


    ### Account class methods
    @classmethod
    def get_one_account_by_id(cls, id: int):
        try:
            this_account = cls.objects.get(pk=id)
            return this_account
        except (KeyError, cls.DoesNotExist):
            return None
    
    
    @classmethod
    def get_all_profiles_for_account_by_account_id(cls, account_id: int):
        valid_account = cls.get_one_account_by_id(account_id)
        
        if not valid_account:
            return None

        try:
            all_profiles = valid_account.profiles.all()
            return all_profiles
        except Exception as e:
            print(e)
            return None


    ### Account instance methods
    def activate_account(self) -> None:
        self.active = True
        self.activation_date = datetime.now()


    def deactivate_account(self) -> None:
        self.active = False
        self.activation_date = None


class Profile(SharedData):
    profile_name: str = models.CharField(max_length=16)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="profiles")
    favorites = models.ManyToManyField(WatchableContent)


    # def __init__(self, data: dict) -> None:
    #     self.profile_name = data["profile_name"]
    #     self.account = data["account"]


    def __str__(self) -> str:
        return self.profile_name
    

    ### Profile class methods et all
    @classmethod
    def get_one_profile_by_name(cls, name: str):
        try:
            this_profile = cls.objects.get(profile_name__exact=name)
            return this_profile
        except (KeyError, cls.DoesNotExist):
            return None

    ### Profile instance methods et all
    