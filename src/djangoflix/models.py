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
        return self.name
    

    def is_tv(self) -> bool:
        return self.content_type == "TV"


    def get_current_seasons(self):
        if not self.is_tv():
            return None
        
        try:
            seasons = self.seasons.filter(air_date__lte=timezone.now())
            return seasons

        except Exception as e:
            print(f"\nget_current_seasons for {self.name} failed with error:\n{e}\n")
            return None
    
    
    @classmethod
    def get_context(cls, all_content) -> dict:
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
                    case "War":
                        war.append(content)
                    case "War & Politics":
                        war.append(content)
                    case "Western":
                        western.append(content)
                    case _:
                        continue

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
            "mystery": mystery,
            "reality": reality,
            "romance": romance,
            "scifi": scifi,
            "thriller": thriller,
            "tv_movie": tv_movie,
            "war": war,
        }

        return context
    
    
    @classmethod
    def get_all_content(cls):
        try:
            content = cls.objects.filter(release_date__lte=timezone.now())
            if len(content) > 0:
                return content
            return None
        
        except Exception as e:
            print(f"\nError: {e}\n")
            return None
    
    
    @classmethod
    def get_all_movies(cls):
        try:
            movies = cls.objects.filter(content_type="Movie")\
                                .filter(release_date__lte=timezone.now())
            if len(movies) > 0:
                return movies
            return None
            
        except Exception as e:
            print(f"\nError: {e}\n")
            return None
    

    @classmethod
    def get_all_tv(cls):
        try:
            tv = cls.objects.filter(content_type="TV")\
                            .filter(release_date__lte=timezone.now())
            if len(tv) > 0:
                return tv
            return None
        
        except Exception as e:
            print(f"\nError: {e}\n")
            return None
    
    
    @classmethod
    def get_one_content_by_id(cls, id):
        try:
            content = cls.objects.get(pk=id)
            return content
        except cls.DoesNotExist:
            print(f"\nNo content found with id {id}\n")
            return None
        except cls.MultipleObjectsReturned:
            print(f"\nMultiple results found for content with id {id}\n")
            return None
    

    @classmethod
    def get_one_content_by_tmdb_id(cls, tmdb_id):
        try:
            content = cls.objects.get(tmdb_id=tmdb_id)
            return content
        except cls.DoesNotExist:
            print(f"\nNo content found with id {tmdb_id}\n")
            return None
        except cls.MultipleObjectsReturned:
            print(f"\nMultiple results found for content with id {tmdb_id}\n")
            return None
    
    
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
    def add_series(self, series: WatchableContent) -> None:
        try:
            if series.is_tv():
                self.series = series
            else:
                raise TypeError

        except TypeError:
            print(f"\ncontent_type of {series} is not 'TV'\n")
    

    def get_current_episodes(self):
        try:
            episodes = self.episodes.filter(air_date__lte=timezone.now())
            
            return episodes
        
        except Exception as e:
            print(f"\nget_episodes for {self.series.name}:{self.name}\
                   failed with error:\n{e}\n")
            return []
    

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


    def add_season(self, season: TVSeason) -> None:
        try:
            self.season = season
        except AttributeError:
            print(f"\nSeason {season} missing required attributes\n")


    @classmethod
    def get_one_episode_by_id(cls, id: int):
        try:
            episode = cls.objects.get(pk=id)
            return episode
        except cls.DoesNotExist:
            print(f"Could not find episode with id {id}\n")
            return None
        except cls.MultipleObjectsReturned:
            print(f"Multiple results for episode with id {id}\n")
            return None


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
            favorites = self.favorites.all()
            # From Django docs, count() definition:
            # '. . .you should always use count() rather than loading all of
            # the record into Python objects and calling len() on the result 
            # (unless you need to load the objects into memory anyway, 
            # in which case len() will be faster).'
            if len(favorites) == 0:
                return None
            
            return favorites
        except Exception as e:
            print(f"\nget_favorites for {self.id} failed with error:\n{e}")
            return None