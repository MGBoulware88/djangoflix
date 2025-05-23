from django.contrib.auth.models import User
from django import db
from django.utils import timezone
from datetime import date, datetime


ICON_CHOICES = {
    "default.png": "default.png",
    "boy_blue.png": "boy_blue.png",
    "girl_blue.png": "girl_blue.png",
    "boy_brown.png": "boy_brown.png",
    "girl_brown.png": "girl_brown.png",
    "boy_red.png": "boy_red.png",
    "girl_red.png": "girl_red.png",
    "girl_blond.png": "girl_blond.png",
    "girl_green.png": "girl_green.png",
    "girl_pink.png": "girl_pink.png",
    "clown.png": "clown.png",
    "king.png": "king.png",
    "princess.png": "princess.png",
    "mermaidA.png": "mermaidA.png",
    "mermaidB.png": "mermaidB.png",
}


class SharedData(db.models.Model):
    created_at = db.models.DateTimeField(auto_now_add=True)
    updated_at = db.models.DateTimeField(null=True, auto_now=True)

    class Meta:
        abstract = True


class ContentData(SharedData):
    name = db.models.CharField(max_length=255)
    overview = db.models.CharField(null=True, default=None, max_length=9999)
    img_path = db.models.CharField(max_length=50)
    # TODO: Add cast/crew info to content
    # {"cast": list[dict]}
    cast = db.models.JSONField(null=True)
    # {"crew": list[dict]}
    crew = db.models.JSONField(null=True)
    tmdb_id = db.models.PositiveBigIntegerField(null=True)

    class Meta:
        abstract = True


### Movies and TV Series
class WatchableContent(ContentData):
    content_type = db.models.CharField(max_length=15)
    genres = db.models.ManyToManyField("tmdb.Genre")
    release_date = db.models.DateField()
    duration = db.models.PositiveIntegerField() # Movies stored in minutes, TV stored in seasons


    def __str__(self) -> str:
        return self.title
    

    @classmethod
    def get_one_series_for_season(cls, tmdb_id):
        try:
            series = cls.objects.get(tmdb_id=tmdb_id, content_type="TV")
            return series
        except cls.DoesNotExist:
            print(f"\nFailed to locate Series {tmdb_id}\n")
            return None
        except cls.MultipleObjectsReturned:
            print(f"Multiple results for Series {tmdb_id}\n")
            return None


### TV Seasons
class TVSeason(ContentData):
    series = db.models.ForeignKey(
        WatchableContent,
        on_delete=db.models.CASCADE,
        related_name="seasons",
        null=True
    )
    season_number = db.models.PositiveIntegerField()
    air_date = db.models.CharField(max_length=10) # "YYYY-MM-DD"


    ## Make sure WatachableContent is a TV Series before adding
    def add_series(self, tmdb_id) -> None:
        try:
            series = WatchableContent.get_one_series_for_season(tmdb_id)
            self.series = series

        except AttributeError:
            print(f"Series {series} missing required attributes\n")
    

    @classmethod
    def get_one_season_for_episode(cls, tmdb_id):
        try:
            season = cls.objects.get(tmdb_id=tmdb_id )
            return season
        except cls.DoesNotExist:
            print(f"\nFailed to locate Season {season.name} for {season.series}\n")
            return None
        except cls.MultipleObjectsReturned:
            print(f"Multiple results for Season {season.name} for {season.series}\n")
            return None


### TV Episodes
class TVEpisode(ContentData):
    season = db.models.ForeignKey(
        TVSeason,
        on_delete=db.models.CASCADE,
        related_name="episodes",
        null=True
    )
    episode_number = db.models.PositiveIntegerField()
    air_date = db.models.CharField(max_length=10) # "YYYY-MM-DD"
    runtime = db.models.PositiveIntegerField()


    def add_season(self, tmbd_id) -> None:
        try:
            season = TVSeason.get_one_season_for_episode(tmbd_id)
            self.season = season
        except AttributeError:
            print(f"\nSeason {season} missing required attributes\n")


class Account(SharedData):
    # stored in db as int, but returns User obj when accessed at runtime
    user: User | None = db.models.OneToOneField(
        User, on_delete=db.models.CASCADE, null=True
    )
    activation_date = db.models.DateTimeField(
        null=True, auto_now_add=True
    )
    active: bool = db.models.BooleanField(default=True)


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
    def get_all_profiles_for_account_by_id(cls, account_id: int):
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
        self.activation_date = timezone.now()


    def deactivate_account(self) -> None:
        self.active = False
        self.activation_date = None


class Profile(SharedData):
    profile_name = db.models.CharField(max_length=16)
    icon = db.models.CharField(
        max_length=30,
        default="default.png",
        choices=ICON_CHOICES,
    )
    account = db.models.ForeignKey(
        Account,
        on_delete=db.models.CASCADE,
        related_name="profiles",
    )
    favorites = db.models.ManyToManyField(WatchableContent)

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