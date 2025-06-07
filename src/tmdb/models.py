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

    
    def _to_dict(self) -> dict:
        content_dict = {
            field.name: getattr(self, field.name)\
            for field in self._meta.fields
        }
        
        del content_dict["id"]
        del content_dict["created_at"]
        del content_dict["updated_at"]

        return content_dict
    
    
    def _add_to_djangoflix(self, genre_data: dict) -> WatchableContent | None:
        # get_or_create isn't working as expected
        try:
            new_content = WatchableContent.objects.get(
                tmdb_id=self.tmdb_id,
                name=self.name
            )
            if new_content.content_type == "Movie":
                new_content.img_path = "tmdb/movie" + self.img_path
            else:
                new_content.img_path = "tmdb/tv/series" + self.img_path
            if genre_data:
                Genre.process_all_genres(genre_data["genres"], new_content)
                
            new_content.save()
            return new_content
            
        except WatchableContent.MultipleObjectsReturned:
            print(f"\nMultiple objects were found for {self.name}.\n")
            return None
        
        except WatchableContent.DoesNotExist:
            content_data = self._to_dict()
            new_content = WatchableContent.objects.create(**content_data)
            new_content.save()

            if genre_data:
                Genre.process_all_genres(genre_data["genres"], new_content)
                new_content.save()
        
            return new_content


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

    def __str__(self) -> str:
        return self.name


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
        movie_dict = super()._to_dict()
        movie_dict["content_type"] = "Movie"
        movie_dict["img_path"] = "tmdb/movie" + self.img_path
        movie_dict["duration"] = self.runtime

        del movie_dict["runtime"]

        return movie_dict
            
    
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
        
        new_movie = TMDBMovie._process_movie(data)
        # img should already be downloaded
        path = f"src/tmdb/static/tmdb/movie{new_movie.img_path}"
        if not os.path.isfile(path):
            new_movie._fetch_movie_image()
        
        added = new_movie._add_to_djangoflix({"genres": data["genres"]})

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
                this_movie = TMDBMovie._process_movie(responsejson)
                this_movie._fetch_movie_image() 
                this_movie._add_to_djangoflix(
                    {"genres": responsejson["genres"]}
                )
                # (optional) Write to JSON to reduce API usage
                normalized_name = this_movie.name.replace(":", " -")
                ContentData._write_to_json(responsejson, f"Movies/{normalized_name}")
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


    def _to_dict(self) -> dict:
        series_dict = super()._to_dict()
        series_dict["content_type"] = "TV"
        # Update img_path for view convenience
        series_dict["img_path"] = "tmdb/tv/series" + self.img_path
        series_dict["duration"] = self.total_seasons
        series_dict["release_date"] = self.first_air_date

        del series_dict["total_seasons"]
        del series_dict["total_episodes"]
        del series_dict["first_air_date"]
        del series_dict["last_air_date"]

        return series_dict
    
    
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
    def add_series_from_json(cls, data: dict) -> bool:
        """
        Adds TMDBTVSeries if not exist and adds WatchableContent if not exist.

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
        
        new_series = TMDBTVSeries._process_series(data)
        # img should already be downloaded
        path = f"src/tmdb/static/tmdb/tv/series/{new_series.img_path}"
        if not os.path.isfile(path):
            new_series._fetch_series_image()
        
        added: WatchableContent | None = new_series._add_to_djangoflix(
                                                    {"genres": data["genres"]}
                                                )
        if added:
            TMDBTVSeason.add_all_seasons_from_json(new_series, added)
            return True

        return False
    
    
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
            this_series._fetch_series_image()
            added: WatchableContent | None = this_series._add_to_djangoflix(
                {"genres": responsejson["genres"]}
            )
            # (optional) Write to JSON to reduce API usage
            normalized_name = this_series.name.replace(":", " -")
            path = f"TV/{normalized_name}/{normalized_name}"
            ContentData._write_to_json(responsejson, path)

            # Now fetch the season data, which will fetch the episode data
            if added:
                TMDBTVSeason.fetch_all_seasons_for_series(this_series, added)
            
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
                img_path=series_data["poster_path"] or "/missing.png",
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

        return this_series


class TMDBTVSeason(ContentData):
    series = models.ForeignKey(
        TMDBTVSeries,
        on_delete=models.CASCADE,
        related_name="seasons",
        null=True
    )
    season_number = models.PositiveIntegerField()
    air_date = models.CharField(max_length=10) # "YYYY-MM-DD"


    def __str__(self) -> str:
        if hasattr(self, "name") and hasattr(self, "series"):
            return f"This is {self.name} of {self.series.name}"
        
        return "Invalid Season."

    
    def _to_dict(self) -> dict:
        season_dict = super()._to_dict()
        # Update img_path for view convenience
        season_dict["img_path"] = "tmdb/tv/season" + self.img_path

        del season_dict["series"]

        return season_dict
    
    
    def _add_to_djangoflix(self,
                           django_series: WatchableContent
                        ) -> TVSeason | None:
        try:
            new_season = TVSeason.objects.get(
                tmdb_id=self.tmdb_id
            )
            # Update img_path for view convenience
            new_season.img_path = "tmdb/tv/season" + self.img_path
            new_season.save()
            return new_season
        
        except TVSeason.MultipleObjectsReturned:
            print(f"\nMultiple objects were found for {self.name}.\n")
            return None
        
        except TVSeason.DoesNotExist:
            data = self._to_dict()
            new_season = TVSeason(**data)
            new_season.save()
            new_season.add_series(django_series)
            new_season.save()

            return new_season
        

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
    def add_all_seasons_from_json(cls,
                                  series: TMDBTVSeries,
                                  django_series: WatchableContent
                                ) -> None:
        for season in series.season_data:
            cls._add_season_from_json(season, series, django_series)
            
    
    @classmethod
    def _add_season_from_json(cls,
                              data: dict,
                              series: TMDBTVSeries,
                              django_series: WatchableContent
                            ) -> bool:
        path = f"src/tmdb/json/TV/{series.name}/{data['name']}.json"
        if not os.path.isfile(path):
            return False
        with open(path, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

            if not existing_data:
                return False
            
            new_season = TMDBTVSeason._process_season(existing_data, series)

        img_path = f"src/tmdb/static/tmdb/tv/season/{new_season.img_path}"
        if not os.path.isfile(img_path):
            new_season._fetch_season_image()
        
        added: TVSeason | None = new_season._add_to_djangoflix(django_series)

        if added:
            TMDBTVEpisode.add_all_episodes_from_json(new_season, added)
            return True
        
        return False
        

    # Called when adding entire TV Series
    @classmethod
    def fetch_all_seasons_for_series(cls, series: TMDBTVSeries, django_series: WatchableContent):
        if not hasattr(series, "season_data"):
            print(f"\nThis series is missing season data:\n{series}\n")
            return
        
        for season in series.season_data:
            try:
                cls._fetch_one_season_for_series_with_season_number(
                    series,
                    django_series,
                    season['season_number']
                )
            except KeyError:
                print(f"\nThis season doesn't have a number:\n{season}\n")
    

    # Called when TV Season chosen from TMDB FetchForm
    @classmethod
    def fetch_one_season_by_series_id(cls, series_id: str, season_number: str):
        # Just get the series and call existing methods
        series = TMDBTVSeries.get_one_series_by_tmdb_id(int(series_id))
        if not series:
            print("Can't fetch season with not found series")
            return
        django_series = WatchableContent.get_one_content_by_tmdb_id(series.tmdb_id)
        if not django_series:
            print("Can't fetch season with not found django series")
            return
        
        cls._fetch_one_season_for_series_with_season_number(
            series,
            django_series,
            int(season_number)
        )

    
    @classmethod
    def _fetch_one_season_for_series_with_season_number(
                                                          cls,
                                                          series: TMDBTVSeries,
                                                          django_series: WatchableContent,
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
            this_season._fetch_season_image()
            added: TVSeason | None = this_season._add_to_djangoflix(django_series)
            # (optional) Write to JSON to reduce API usage
            n_series_name = series.name.replace(":", " -")
            n_season_name = this_season.name.replace(":", " -")
            path = f"TV/{n_series_name}/{n_season_name}"
            ContentData._write_to_json(responsejson, path)
            # Now grab all the episode data for this season
            if added:
                TMDBTVEpisode.fetch_all_episodes_for_season(this_season, added)
            
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
        this_season.save()
        # Seasons don't have genre data, but series requires ID
        this_season.series = series
        this_season.save()
       
        return this_season


class TMDBTVEpisode(ContentData):
    season = models.ForeignKey(
        TMDBTVSeason,
        on_delete=models.CASCADE,
        related_name="episodes",
        null=True
    )
    episode_number = models.PositiveIntegerField()
    air_date = models.CharField(max_length=10) # "YYYY-MM-DD"
    runtime = models.PositiveIntegerField()


    def __str__(self) -> str:
        if hasattr(self, "name") and hasattr(self, "episode_number"):
            return f'Episode #{self.episode_number}, titled "{self.name}"'
        
        return "Invalid Episode object."
    

    def _to_dict(self) -> dict:
        episode_dict = super()._to_dict()
        episode_dict["img_path"] = "tmdb/tv/episode" + self.img_path
        
        del episode_dict["season"]

        return episode_dict
    
    
    def _add_to_djangoflix(self,
                           django_season: TVSeason
                        ) -> TVEpisode | None:
        try:
            new_episode = TVEpisode.objects.get(
                tmdb_id=self.tmdb_id
            )
            # Update img_path for view convenience
            new_episode.img_path = "tmdb/tv/episode" + self.img_path
            new_episode.save()
            return new_episode
        
        except TVEpisode.MultipleObjectsReturned:
            print(f"\nMultiple objects were found for {self.name}.\n")
            return None
        
        except TVEpisode.DoesNotExist:
            data = self._to_dict()
            new_episode = TVEpisode(**data)
            new_episode.save()
            new_episode.add_season(django_season)
            new_episode.save()

            return new_episode
    
    
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
    def add_all_episodes_from_json(cls,
                                   season: TMDBTVSeason,
                                   django_season: TVSeason
                                ) -> None:
        for episode in season.episode_data:
            cls._add_episode_from_json(episode, season, django_season)
    
    
    @classmethod
    def _add_episode_from_json(cls,
                               data: dict,
                               season: TMDBTVSeason,
                               django_season: TVSeason
                            ) -> TVEpisode | None:
        path = "src/tmdb/json/TV/{0}/{1}-Episode{2}.json".format(
            season.series.name,
            season.name,
            data["episode_number"]
        )
        if not os.path.isfile(path):
            return
        with open(path, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

            if not existing_data:
                return
            
            new_episode = TMDBTVEpisode._process_episode(existing_data, season)

        img_path = f"src/tmdb/static/tmdb/tv/episode/{new_episode.img_path}"
        if not os.path.isfile(img_path):
            new_episode._fetch_episode_image()

        added: TVEpisode | None = new_episode._add_to_djangoflix(django_season)

        return added
    
    
    @classmethod
    def fetch_all_episodes_for_season(cls, season: TMDBTVSeason, django_season: TVSeason):
        if not hasattr(season, "episode_data"):
            print(f"\nThis season is missing episode data:\n{season}\n")
            return
        
        for episode in season.episode_data:
            try:
                cls._fetch_one_episode_for_season_with_episode_number(
                    season,
                    django_season,
                    episode["episode_number"]
                )
            except KeyError:
                print(f"\nThis episode doesn't have a number:\n{episode}\n")
                

    @classmethod
    def _fetch_one_episode_for_season_with_episode_number(
                                                          cls,
                                                          season: TMDBTVSeason,
                                                          django_season: TVSeason,
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
            print(response)
            if not response:
                print("Invalid response object")
                return

            if not response.status_code == 200:
                print(f"\nBad Response:\n{response.status_code}\n")
                return
            
            responsejson = response.json()
            this_episode = TMDBTVEpisode._process_episode(responsejson, season)
            this_episode._fetch_episode_image()
            this_episode._add_to_djangoflix(django_season)
            # (optional) Write to JSON to reduce API usage
            n_series_name = season.series.name.replace(":", " -")
            n_season_name = season.name.replace(":", " -")
            path = "TV/{0}/{1}-Episode{2}".format(
                n_series_name,
                n_season_name,
                this_episode.episode_number
            )
            ContentData._write_to_json(responsejson, path)
        
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

        return this_episode