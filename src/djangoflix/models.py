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
    user: int = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
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
        except cls.DoesNotExist:
            return None
       

    @classmethod
    def get_one_account_by_user_id(cls, user_id: int):
        try:
            this_account = cls.objects.get(user=user_id)
            return this_account
        except cls.DoesNotExist:
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
    

    @classmethod
    def create_account(cls, user: User):
        new_account = cls.objects.create(user=user)
        return new_account


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

    def __str__(self) -> str:
        return self.profile_name
    

    ### Profile class methods et all   
    @classmethod
    def get_one_profile_by_id(cls, id: int):
        try:
            this_profile = cls.objects.get(pk=id)
            return this_profile
        except cls.DoesNotExist:
            return None
    

    ### Profile instance methods et all
    def get_favorites(self):
        try:
            favorites = []
            queryset = self.favorites.all()
            # From Django docs, count() definition:
            # '. . .you should always use count() rather than loading all of
            # the record into Python objects and calling len() on the result 
            # (unless you need to load the objects into memory anyway, 
            # in which case len() will be faster).'
            if len(queryset) == 0:
                return None
            # TODO: Test if this loop is redundant and I can just return the queryset after len() call
            for favorite in queryset:
                favorites.append(favorite)
            
            return favorites
        except Exception as e:
            print(f"\nget_favorites for {self.id} failed with error:\n{e}")
            return None