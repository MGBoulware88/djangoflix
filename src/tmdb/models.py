import json
import requests
import os
from django.db import models
from dotenv import load_dotenv

from djangoflix.models import WatchableContent, TVSeason, TVEpisode

load_dotenv()


BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/original"
HEADER = {
    "accept": "application/json",
    "Authorization": os.getenv("TMDB_AUTH")
}


class ContentData(models.Model):
    name = models.CharField(max_length=255)
    overview = models.CharField(null=True, default=None, max_length=9999)
    tmdb_id = models.PositiveBigIntegerField(unique=True)
    # The string used to both fetch image from TMDB and load static
    img_path = models.CharField(max_length=50)
    # Storing these as 'raw' JSON for now to limit API usage
    # TODO: Add cast/crew info to content
    # {"cast": list[dict]}
    cast = models.JSONField(null=True)
    # {"crew": list[dict]}
    crew = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)


    class Meta:
        abstract = True


    @staticmethod
    def _fetch_data(url_ext: str) -> requests.Response | None:
        try:
            response = requests.get(
                BASE_URL + url_ext + "?language=en-US",
                headers=HEADER
            )
            return response
        except requests.exceptions.RequestException as e:
            print(f"\nFetch Data failed:\n{e}\n")
            return None
        

    @staticmethod
    def _fetch_image(img_path: str) -> requests.Response | None:
        print(f"Fetching from {IMG_BASE_URL}{img_path}")
        try:
            response = requests.get(IMG_BASE_URL + img_path, headers=HEADER)
            return response
        except requests.exceptions.RequestException as e:
            print(f"\nFetch Image failed:\n{e}\n")
            return None


    @staticmethod
    def _write_to_json(data: dict, path: str) -> None:
        with open(
            f"src/tmdb/json/{path}.json",
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
    
    
    @staticmethod
    def _write_image(response: requests.Response, path: str) -> None:
        with open(path, "wb") as image:
            image.write(response.content)


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
    

    def __str__(self):
        return f"{self.name}"
    
    
    def _to_dict(self) -> dict:
        movie_dict = {
            field.name: getattr(self, field.name)\
            for field in self._meta.fields
        }
        movie_dict["duration"] = movie_dict["runtime"]
        movie_dict["content_type"] = "Movie"
        
        del movie_dict["id"]
        del movie_dict["runtime"]
        del movie_dict["tmdb_id"]
        del movie_dict["created_at"]
        del movie_dict["updated_at"]

        return movie_dict
    
    
    def _add_to_djangoflix(self, data: dict=None):
        if data == None:
            data = self._to_dict()
        
        # get_or_create isn't working as expected
        try:
            new_movie = WatchableContent.objects.get(
                name__exact=self.name,
                release_date__exact=self.release_date
            )
            return False
            
        except WatchableContent.MultipleObjectsReturned:
            print(f"\nMultiple objects were found for {self.name}.\n")
            return False
        
        except WatchableContent.DoesNotExist:
            new_movie = WatchableContent.objects.create(**data)
            new_movie.save()
            # _to_dict()/data doesn't include M2M fields
            for genre in self.genres.all():
                new_movie.genres.add(genre)
            new_movie.save()
        
            return True
        
            
    
    def _fetch_movie_image(self):
        if not hasattr(self, "img_path"):
            print(f"\n{self} is missing the img_path attr.\n")
            return
        
        if self.img_path == "/missing.png":
            print(f"\n{self} doesn't have an image, fetch cancelled.\n")
            return
        
        try:
            response = ContentData._fetch_image(self.img_path)

            if not response:
                print("Invalid response object")
                return

            if response.status_code == 200:
                path = f"src/tmdb/static/tmdb/movie{self.img_path}"
                ContentData._write_image(response, path)
                
                return

            print(f"\nFetch Image Bad Response:\n{response.status_code}\n")

        except Exception as e:
            print(f"\nAn exception occurred:\n{e}\n")


    @classmethod
    def add_movie_from_json(cls, data: dict) -> bool:
        """
        Adds TMDBMovie if not exist and adds WatchableContent if not exist.

        Parameters
        ----------
        data : dict
            field data for adding the content

        Returns
        -------
        bool
        """

        if not type(data) == dict:
            return False
        
        existing_movie = cls.objects.filter(pk=data["id"]).first()
        if existing_movie:
            existing_movie._add_to_djangoflix()
            return True
        
        new_movie = TMDBMovie._process_movie(data)
        added = new_movie._add_to_djangoflix()

        return added

    
    
    @classmethod
    def fetch_one_movie_by_id(cls, id: str):
        try:
            response = ContentData._fetch_data("/movie/%s" % id)

            if not response:
                print("Invalid response object")
                return
            
            if response.status_code == 200:
                responsejson = response.json()
                # print(f"\nResponse JSON:\n{responsejson}\n")
                this_movie = TMDBMovie._process_movie(responsejson)
                # (optional) Write to JSON to reduce API usage
                ContentData._write_to_json(responsejson, f"Movies/{this_movie.name}")
                return
            
            print(f"\nBad Response:\n{response.status_code}\n")
        
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_movie(cls, movie_data: dict):
        this_movie = TMDBMovie.objects.filter(
            tmdb_id=movie_data["id"]
        ).first()
        # TODO: fetch movie.credits to get cast & crew
        if not this_movie:
            this_movie = TMDBMovie(
                name=movie_data["title"] or "missing",
                overview=movie_data["overview"] or "missing",
                tmdb_id=movie_data["id"],
                img_path=movie_data["poster_path"] or "/missing.png",
                release_date=movie_data["release_date"] or "missing",
                runtime=movie_data["runtime"] or 999,
                cast=None,
                crew=None
            )
        # save to db to get id
        this_movie.save()
        # 2. Process genres
        Genre.process_all_genres(movie_data["genres"], this_movie)
        # 3. Save changes 
        this_movie.save()
        # 4. Fetch image
        this_movie._fetch_movie_image()

        return this_movie
        

class TMDBTVSeries(ContentData):
    genres = models.ManyToManyField(Genre)
    total_seasons = models.PositiveIntegerField()
    total_episodes = models.PositiveIntegerField()
    first_air_date = models.CharField(max_length=10) # "YYYY-MM-DD"
    last_air_date = models.CharField(max_length=10) # "YYYY-MM-DD"


    def __str__(self) -> str:
        if hasattr(self, "name") and hasattr(self, "total_seasons"):
            return f"Series: {self.name} has {self.total_seasons} season(s)."
        
        return "Invalid Series object."


    def _fetch_series_image(self):
        if not hasattr(self, "img_path"):
            print(f"\n{self} is missing the img_path attr.\n")
            return
        
        if self.img_path == "/missing.png":
            print(f"\n{self} doesn't have an image, fetch cancelled.\n")
            return
        
        try:
            response = ContentData._fetch_image(self.img_path)

            if not response:
                print("Invalid response object")
                return

            if response.status_code == 200:
                path = f"src/tmdb/static/tmdb/tv/series{self.img_path}"
                ContentData._write_image(response, path)
                
                return

            print(f"\nFetch Image Bad Response:\n{response.status_code}\n")

        except Exception as e:
            print(f"\nAn exception occurred:\n{e}\n")
    
    
    @classmethod
    def get_one_series_by_tmdb_id(cls, id: int):
        try:
            this_series = TMDBTVSeries.objects.get(tmdb_id__exact=id)
            return this_series
        except cls.DoesNotExist:
            print(f"\nNo TV Series found with TMDB ID: {id}.\n")
            return None


    @classmethod
    def fetch_one_series_by_tmdb_id(cls, id: str) -> None:
        try:
            response = ContentData._fetch_data("/tv/%s" % id)

            if not response:
                print("Invalid response object")
                return

            if not response.status_code == 200:
                print(f"\nBad Response:\n{response.status_code}\n")
                return

            responsejson = response.json()
            this_series = TMDBTVSeries._process_series(responsejson)
            # Now fetch the season data, which will fetch the episode data
            TMDBTVSeason.fetch_all_seasons_for_series(this_series)
            
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_series(cls, series_data: dict):
        this_series = TMDBTVSeries.objects.filter(
            tmdb_id = series_data["id"],
        ).first()
        if not this_series:
            this_series = TMDBTVSeries(
                name=series_data["name"] or "missing",
                overview=series_data["overview"] or "missing",
                tmdb_id=series_data["id"],
                img_path=series_data["backdrop_path"] or "/missing.png",
                cast=None,
                crew=None,
                total_seasons=series_data["number_of_seasons"] or 999,
                total_episodes=series_data["number_of_episodes"] or 999,
                first_air_date=series_data["first_air_date"] or "missing",
                last_air_date=series_data["last_air_date"] or "missing",
            )
        # This seasons list has all the data we need to go fetch
        # all of the season details for this series
        this_series.season_data = series_data["seasons"]
        this_series.save()
        
        try:
            Genre.process_all_genres(series_data["genres"], this_series)
            this_series.save()
        except KeyError:
            print(f"Series \"{series_data["name"]}\" missing Genres data.")

        path = f"TV/{this_series.name}/{this_series.name}"
        ContentData._write_to_json(series_data, path)
        this_series._fetch_series_image()

        return this_series


class TMDBTVSeason(ContentData):
    series = models.ForeignKey(
        TMDBTVSeries,
        on_delete=models.CASCADE,
        related_name="seasons",
    )
    season_number = models.PositiveIntegerField()
    air_date = models.CharField(max_length=10) # "YYYY-MM-DD"


    def __str__(self) -> str:
        if hasattr(self, "name") and hasattr(self, "series"):
            return f"This is {self.name} of {self.series.name}"
        
        return "Invalid Season."

    
    def _fetch_season_image(self):
        if not hasattr(self, "img_path"):
            print(f"\n{self} is missing the img_path attr.\n")
            return
        
        if self.img_path == "/missing.png":
            print(f"\n{self} doesn't have an image, fetch cancelled.\n")
            return
        
        try:
            response = ContentData._fetch_image(self.img_path)

            if not response:
                print("Invalid response object")
                return

            if response.status_code == 200:
                path = f"src/tmdb/static/tmdb/tv/season{self.img_path}"
                ContentData._write_image(response, path)
                
                return

            print(f"\nFetch Image Bad Response:\n{response.status_code}\n")

        except Exception as e:
            print(f"\nAn exception occurred:\n{e}\n")
    
    
    @classmethod
    def fetch_all_seasons_for_series(cls, series: TMDBTVSeries):
        if not hasattr(series, "season_data"):
            print(f"\nThis series is missing season data:\n{series}\n")
            return
        # print(f"\nSeason Data:\n{series.season_data}\n")
        for season in series.season_data:
            try:
                cls._fetch_one_season_for_series_with_season_number(
                    series,
                    season['season_number']
                )
            except KeyError:
                print(f"\nThis season doesn't have a number:\n{season}\n")
    

    @classmethod
    def fetch_one_season_by_series_id(cls, series_id: str, season_number: str):
        # Just get the series and call existing methods
        series = TMDBTVSeries.get_one_series_by_tmdb_id(int(series_id))
        if not series:
            print("Can't fetch season with not found series")
            return
        
        cls._fetch_one_season_for_series_with_season_number(
            series,
            int(season_number)
        )

    
    @classmethod
    def _fetch_one_season_for_series_with_season_number(
                                                          cls,
                                                          series: TMDBTVSeries,
                                                          season_number: int
                                                       ) -> None:
        try:
            response = ContentData._fetch_data(
                "/tv/{}/season/{}".format(series.tmdb_id, season_number)
            )

            if not response:
                print("Invalid response object")
                return

            if not response.status_code == 200:
                print(f"\nBad Response:\n{response.status_code}\n")
                return
            
            responsejson = response.json()
            this_season = TMDBTVSeason._process_season(responsejson, series)
            # Now grab all the episode data for this season
            TMDBTVEpisode.fetch_all_episodes_for_season(this_season)
            
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_season(cls, season_data: dict, series: TMDBTVSeries):
        this_season = TMDBTVSeason.objects.filter(
            tmdb_id = season_data["id"]
        ).first()

        if not this_season:
            this_season = TMDBTVSeason(
                name=season_data["name"] or "missing",
                overview=season_data["overview"] or "missing",
                tmdb_id=season_data["id"],
                img_path=season_data["poster_path"] or "/missing.png",
                cast=None,
                crew=None,
                season_number=season_data["season_number"] or 999,
                air_date=season_data["air_date"] or "missing"
            )
        # This episodes list has all the data we need to go fetch
        # all of the episode details for this season
        this_season.episode_data = season_data["episodes"]
        # print(f"\nEpisode Data:\n{this_season.episode_data}\n")
        this_season.save()
        # Seasons don't have genre data, but series requires ID
        this_season.series = series
        this_season.save()
        
        path = f"TV/{series.name}/{this_season.name}"
        ContentData._write_to_json(season_data, path)
        this_season._fetch_season_image()
       
        return this_season


class TMDBTVEpisode(ContentData):
    season = models.ForeignKey(
        TMDBTVSeason,
        on_delete=models.CASCADE,
        related_name="episodes",
    )
    episode_number = models.PositiveIntegerField()
    air_date = models.CharField(max_length=10) # "YYYY-MM-DD"
    runtime = models.PositiveIntegerField()


    def __str__(self) -> str:
        if hasattr(self, "name") and hasattr(self, "episode_number"):
            return f'Episode #{self.episode_number}, titled "{self.name}"'
        
        return "Invalid Episode object."
    

    def _fetch_episode_image(self):
        if not hasattr(self, "img_path"):
            print(f"\n{self} is missing the img_path attr.\n")
            return
        
        if self.img_path == "/missing.png":
            print(f"\n{self} doesn't have an image, fetch cancelled.\n")
            return
        
        try:
            response = ContentData._fetch_image(self.img_path)

            if not response:
                print("Invalid response object")
                return

            if response.status_code == 200:
                path = f"src/tmdb/static/tmdb/tv/episode{self.img_path}"
                ContentData._write_image(response, path)
                
                return

            print(f"\nFetch Image Bad Response:\n{response.status_code}\n")

        except Exception as e:
            print(f"\nAn exception occurred:\n{e}\n")
    
    
    @classmethod
    def fetch_all_episodes_for_season(cls, season: TMDBTVSeason):
        if not hasattr(season, "episode_data"):
            print(f"\nThis season is missing episode data:\n{season}\n")
            return
        
        for episode in season.episode_data:
            try:
                cls._fetch_one_episode_for_season_with_episode_number(
                    season,
                    episode["episode_number"]
                )
            except KeyError:
                print(f"\nThis episode doesn't have a number:\n{episode}\n")
                

    @classmethod
    def _fetch_one_episode_for_season_with_episode_number(
                                                          cls,
                                                          season: TMDBTVSeason,
                                                          episode_number: int
                                                         ):
        try:
            response = ContentData._fetch_data(
                "/tv/{0}/season/{1}/episode/{2}".format(
                    season.series.tmdb_id,
                    season.season_number,
                    episode_number
                )
            )

            if not response:
                print("Invalid response object")
                return

            if not response.status_code == 200:
                print(f"\nBad Response:\n{response.status_code}\n")
                return
            
            responsejson = response.json()
            # End of the line, nothing to store and pass
            TMDBTVEpisode._process_episode(responsejson, season)
        
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_episode(cls, episode_data: dict, season: TMDBTVSeason):
        this_episode = TMDBTVEpisode.objects.filter(
            tmdb_id=episode_data["id"]
        ).first()
        if not this_episode:
            this_episode = TMDBTVEpisode(
                name=episode_data["name"] or "missing",
                overview=episode_data["overview"] or "missing",
                tmdb_id=episode_data["id"],
                img_path=episode_data["still_path"] or "/missing.png",
                cast={"cast": episode_data["guest_stars"]} or {"cast": None},
                crew={"crew": episode_data["crew"]} or {"crew": None},
                episode_number=episode_data["episode_number"] or 999,
                air_date=episode_data["air_date"] or "missing",
                runtime=episode_data["runtime"] or 0
            )
        this_episode.season = season
        this_episode.save()

        path = "TV/{0}/{1}-Episode{2}".format(
                season.series.name,
                season.name,
                this_episode.episode_number
            )
        ContentData._write_to_json(episode_data, path)
        this_episode._fetch_episode_image()