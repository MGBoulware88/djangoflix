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


    class Meta:
        abstract = True


    @staticmethod
    def _fetch_data(url_ext: str) -> requests.Response | None:
        print(f"Fetching from {BASE_URL}{url_ext}?language=en-US")
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
                TMDBMovie._process_movie(responsejson)
                return
            
            print(f"\nBad Response:\n{response.status_code}\n")
        
        except requests.exceptions.RequestException as e:
            print(f"\nFetch Movie failed:\n{e}\n")
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_movie(cls, movie_data: dict):
        this_movie = TMDBMovie.objects.filter(
            tmdb_id=movie_data["id"]
        ).first()
        if not this_movie:
            this_movie = TMDBMovie(
                name=movie_data["title"],
                overview=movie_data["overview"],
                tmdb_id=movie_data["id"],
                img_fetch_path=movie_data["poster_path"],
                release_date=movie_data["release_date"],
                runtime=movie_data["runtime"],
                cast=None,
                crew=None
            )
        # save to db to get id
        this_movie.save()
        # 2. Process genres
        Genre.process_all_genres(movie_data["genres"], this_movie)
        # 3. Save changes 
        this_movie.save()
        # 4. (optional) Write to JSON to reduce API usage
        ContentData._write_to_json(movie_data, f"Movies/{this_movie.name}")


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


    @classmethod
    def get_one_series_by_id(cls, id: int):
        try:
            this_series = TMDBTVSeries.objects.get(tmdb_id__exact=id)
            return this_series
        except cls.DoesNotExist:
            print(f"\nNo TV Series found with TMDB ID: {id}.\n")
            return None


    @classmethod
    def fetch_one_series_by_id(cls, id: str) -> None:
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
            
        except requests.exceptions.RequestException as e:
            print(f"\nFetch Series failed:\n{e}\n")
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_series(cls, series_data: dict):
        this_series = TMDBTVSeries.objects.filter(
            tmdb_id = series_data["id"],
        ).first()
        if not this_series:
            this_series = TMDBTVSeries(
                name=series_data["name"],
                overview=series_data["overview"],
                tmdb_id=series_data["id"],
                img_fetch_path=series_data["backdrop_path"],
                cast=None,
                crew=None,
                total_seasons=series_data["number_of_seasons"],
                total_episodes=series_data["number_of_episodes"],
                first_air_date=series_data["first_air_date"],
                last_air_date=series_data["last_air_date"]
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

    
    @classmethod
    def fetch_all_seasons_for_series(cls, series: TMDBTVSeries):
        if not hasattr(series, "season_data"):
            print(f"\nThis series is missing season data:\n{series}\n")
            return
        print(f"\nSeason Data:\n{series.season_data}\n")
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
        series = TMDBTVSeries.get_one_series_by_id(int(series_id))
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
            
        except requests.exceptions.RequestException as e:
            print(f"\nFetch Season failed:\n{e}\n")
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_season(cls, season_data: dict, series: TMDBTVSeries):
        this_season = TMDBTVSeason.objects.filter(
            tmdb_id = season_data["id"]
        ).first()

        if not this_season:
            this_season = TMDBTVSeason(
                name=season_data["name"],
                overview=season_data["overview"],
                tmdb_id=season_data["id"],
                img_fetch_path=season_data["poster_path"],
                cast=None,
                crew=None,
                season_number=season_data["season_number"],
                air_date=season_data["air_date"]
            )
        # This episodes list has all the data we need to go fetch
        # all of the episode details for this season
        this_season.episode_data = season_data["episodes"]
        print(f"\nEpisode Data:\n{this_season.episodes}\n")
        this_season.save()
        # Seasons don't have genre data, but series requires ID
        this_season.series = series
        this_season.save()
        
        path = f"TV/{series.name}/{this_season.name}"
        ContentData._write_to_json(season_data, path)
       
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
        
        except requests.exceptions.RequestException as e:
            print(f"\nFetch Episode failed:\n{e}\n")
        except json.JSONDecodeError:
            print("JSON decode failed!")


    @classmethod
    def _process_episode(cls, episode_data: dict, season: TMDBTVSeason):
        this_episode = TMDBTVEpisode.objects.filter(
            tmdb_id=episode_data["id"]
        ).first()
        if not this_episode:
            this_episode = TMDBTVEpisode(
                name=episode_data["name"],
                overview=episode_data["overview"],
                tmdb_id=episode_data["id"],
                img_fetch_path=\
                    episode_data["still_path"]\
                    if not episode_data["still_path"] == None\
                    else "",
                cast={"cast": episode_data["guest_stars"]},
                crew={"crew": episode_data["crew"]},
                episode_number=episode_data["episode_number"],
                air_date=\
                    episode_data["air_date"]\
                    if not episode_data["air_date"] == None\
                    else "unavailable",
                runtime=\
                    episode_data["runtime"]\
                    if not episode_data["runtime"] == None\
                    else 0
            )
        this_episode.season = season
        this_episode.save()
        
        try:
            Genre.process_all_genres(episode_data["genres"], this_episode)
        except KeyError:
            print(f"Episode \"{this_episode.name}\" missing Genres data.\n")
        
        this_episode.save()

        path = "TV/{0}/{1}-Episode{2}".format(
                season.series.name,
                season.name,
                this_episode.episode_number
            )
        ContentData._write_to_json(episode_data, path)