import json
import requests
import os
from django.db import models
from dotenv import load_dotenv

load_dotenv()


BASE_URL = "https://api.themoviedb.org/3"
HEADER = {
    "accept": "application/json",
    "Authorization": os.getenv("TMDB_AUTH")
}


class ContentData(models.Model):
    name = models.CharField(max_length=255)
    overview = models.CharField(null=True, default=None, max_length=9999)
    tmdb_id = models.PositiveBigIntegerField(unique=True)
    # The string used to fetch image from TMDB
    img_fetch_path = models.CharField(max_length=50)
    # The stored img after fetching from TMDB, initially null
    img_path = models.CharField(null=True, max_length=50)
    # Storing these as 'raw' JSON for now to limit API usage
    # TODO: Add cast/crew info to content
    # {"cast": list[dict]}
    cast = models.JSONField(null=True)
    # {"crew": list[dict]}
    crew = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    base_url = "https://api.themoviedb.org/3"
    header = {
        "accept": "application/json",
        "Authorization": os.environ.get("TMDB_AUTH")
    }

    class Meta:
        abstract = True


    @staticmethod
    def _fetch_data(url_ext: str):
        try:
            response = requests.get(
                BASE_URL + url_ext + "?language=en-US",
                headers=HEADER
            )
            return response
        except Exception as e:
            print(f"\nFetch failed with:\n{e}\n")
            return None
        

    @staticmethod
    def _write_to_json(data: dict) -> None:
        with open(
            f"src/tmdb/json/Movies/{data["title"]}.json",
            "w",
            encoding="utf-8"
        ) as outfile:
            jsondata = json.dumps(
                data, 
                indent=2,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False
            )
            outfile.write(jsondata)


class Genre(models.Model):
    name = models.CharField(max_length=255)
    tmdb_id = models.PositiveBigIntegerField(unique=True)


    @staticmethod
    def process_all_genres(genres: list[dict], object: object) -> None:
        """
        Calls _process_genre with object for each genre in the genres list.

        This method is intended for use in conjunction with other TMDB methods,
        and therefore does not save the instance to avoid redundancy.

        Parameters
        ----------
        genres : list[dict]
            id: int
                the genre.tmdb_id
            name: str
                the genre.name
        object : object
            the instance arg for each process_genre call
        
        Returns
        -------
        None
        """

        # TODO: Update to handle logging new genre creations when logging is added
        for genre in genres:
            Genre._process_genre(genre["id"], genre["name"], object)


    @staticmethod
    def _process_genre(id: int, name: str, object: object) -> tuple[object, bool] | bool:
        try:
            # get_or_create returns (object, created), but I only need the object
            this_genre, created = Genre.objects.get_or_create(tmdb_id=id, name=name)
            object.genres.add(this_genre)
            return (this_genre, created)
        # This except allows processing to continue 
        # so we can investigate the issue later
        # though, this should probably never actually happen
        except Genre.MultipleObjectsReturned:
            print(f"\nMultiple objects were found for {id}+{name}.\n")
            return False
    

class TMDBMovie(ContentData):
    genres = models.ManyToManyField(Genre)
    release_date = models.CharField(max_length=10) # "YYYY-MM-DD"
    runtime = models.PositiveIntegerField()


    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print(f"\nMovie init data:\n{data}\n")
        # Shared Fields
        self.name = data["title"]
        self.overview = data["overview"]
        self.tmdb_id = data["id"]
        self.img_fetch_path = data["poster_path"]
        # Cast & Crew aren't included in Movie Details
        self.cast = None
        self.crew = None
        # Unique to cls
        self.release_date = data["release_date"]
        self.runtime = data["runtime"]
    

    def __str__(self):
        return f"{self.name}"
    
    
    @classmethod
    def fetch_one_movie_by_id(cls, id: str):
        try:
            response = ContentData._fetch_data("/movie/%s" % id)
            
            if response.status_code == 200:
                responsejson = response.json()
                # print(f"\nResponse JSON:\n{responsejson}\n")
                TMDBMovie._process_movie(responsejson)
                return
            
            print(f"\nBad Response:\n{response.status_code}\n")
        
        except requests.exceptions.RequestException as e:
            print(f"\nFetch Movie failed:\n{e}\n")
        except json.JSONDecodeError:
            print("It happened again!")



    @classmethod
    def _process_movie(cls, movie_data: dict):
        # 1. Grab Movie from TMDB
        this_movie = TMDBMovie(movie_data)
        # save to db to get id
        this_movie.save()
        # 2. Process genres
        Genre.process_all_genres(movie_data["genres"], this_movie)
        # 3. Save changes 
        this_movie.save()
        # 4. (optional) Write to JSON to reduce API usage
        ContentData._write_to_json(movie_data)



class TMDBTVSeries(ContentData):
    genres = models.ManyToManyField(Genre)
    total_seasons = models.PositiveIntegerField()
    total_episodes = models.PositiveIntegerField()
    first_air_date = models.CharField(max_length=10) # "YYYY-MM-DD"
    last_air_date = models.CharField(max_length=10) # "YYYY-MM-DD"


    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Shared Fields
        self.name = data["name"]
        self.overview = data["overview"]
        self.tmdb_id = data["id"]
        self.img_fetch_path = data["backdrop_path"]
        # Cast & Crew aren't included until Seasons Details
        self.cast = None
        self.crew = None
        # Unique to cls
        self.total_seasons = data["number_of_seasons"]
        self.total_episodes = data["number_of_episodes"]
        self.first_air_date = data["first_air_date"]
        self.last_air_date = data["last_air_date"]
        # used to hold data required to create TMDBTVSeasons for this series
        self.season_data: list[dict] = data["seasons"]


class TMDBTVSeason(ContentData):
    series = models.ForeignKey(
        TMDBTVSeries,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    season_number = models.PositiveIntegerField()
    air_date = models.CharField(max_length=10) # "YYYY-MM-DD"
        

    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Shared fields
        self.name = data["name"]
        self.overview = data["overview"]
        self.tmdb_id = data["id"]
        self.img_fetch_path = data["poster_path"]
        self.cast = {"cast": data["guest_stars"]}
        self.crew = {"crew": data["crew"]}
        # Unique to cls
        self.season_number = data["season_number"]
        self.air_date = data["air_date"]
        # used to hold data required to create TMDBTVEpisodes for this season
        self.episode_data: list[dict] = data["episodes"]


class TMDBTVEpisode(ContentData):
    season = models.ForeignKey(
        TMDBTVSeason,
        on_delete=models.CASCADE,
        related_name="episodes",
    )
    episode_number = models.PositiveIntegerField()
    air_date = models.CharField(max_length=10) # "YYYY-MM-DD"
    runtime = models.PositiveIntegerField()


    def __init__(self, data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Shared fields
        self.name = data["name"]
        self.overview = data["overview"]
        self.tmdb_id = data["id"]
        self.img_fetch_path = data["still_path"]
        self.cast = {"cast": data["guest_stars"]}
        self.crew = {"crew": data["crew"]}
        # Unique to cls
        self.episode_number = data["episode_number"]
        self.air_date = data["air_date"]
        self.runtime = data["runtime"]