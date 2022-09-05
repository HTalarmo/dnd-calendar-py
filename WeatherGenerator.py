import copy
import csv
from collections import namedtuple
from dataclasses import dataclass
from typing import Tuple, Union
import dice

import numpy as np


@dataclass
class Weather:
    """ Contains the weather at one specific hour in time """
    temperature: Union[float, None] = 0  # temperature in F, because the rules do F. Use get_temperature() to get in C
    precipitation_state: str = ""
    precipitation_duration: int = 0
    wind_direction: int = 0  # Direction in degrees [0, 359]
    wind_strength: str = ""  # Wind speed classification as per pathfinder 1E rules
    wind_speed: int = 0  # Speed in mph (because the rules write it in that, so in-code it's easier)
    cloud_cover: str = "None"  # Current cloud cover

    def to_json(self):
        return {attr: getattr(self,attr) for attr in dir(self) if not attr.startswith("__") and not callable(getattr(self, attr))}

    @staticmethod
    def from_json(json_obj):
        w = Weather()
        d = dir(w)
        for key, val in json_obj.items():
            if key in d:
                setattr(w, key, val)
        return w

    def get_temperature(self):
        """
        Returns the temperature in celsius
        :return: float
        """
        return (self.temperature - 32) / 1.8

    def get_temperature_str(self):
        """
        Returns the temperature in celsius with the unit listed. The output is also always the required 7 characters
        wide.
        :return: string
        """
        return f"{self.get_temperature():>5.1f} C"

    def get_precipitation(self):
        """
        Returns The precipitation state string by itself
        :return: string
        """
        return self.precipitation_state

    def get_precipitation_formatted(self):
        """
        Returns the precipitation state as a formatted string so that the text always fits
        :return: string
        """
        return f"{self.get_precipitation():>12}"

    def wind_speed_str(self) -> str:
        """
        Returns wind speed as a in m/s string
        :return: Wind speed
        """
        speed_in_ms = int(self.wind_speed * 0.44704)
        return f"{speed_in_ms} m/s"

    def wind_direction_str(self) -> str:
        """
        Returns wind direction as a string. Basically rounds it up to the nearest of the 8 cardinal directions
        :return: str
        """
        # Ensure that wind direction makes sense
        self.wind_direction = self.wind_direction % 360
        direction_str = ""
        if (270 + 23) <= self.wind_direction < 360 or 0 <= self.wind_direction < (90 - 23):
            direction_str += "North"
        elif (90 + 23) <= self.wind_direction < (270 - 23):
            direction_str += "South"

        if 23 < self.wind_direction < (180 - 23):
            if direction_str != "":
                direction_str += "-"
            direction_str += "East"
        elif (180 + 23) < self.wind_direction < 360 - 23:
            if direction_str != "":
                direction_str += "-"
            direction_str += "West"
        return direction_str

    def wind_direction_symb(self) -> str:
        """
        Returns wind direction as a symbol
        :return: symbol
        """
        dir_str = self.wind_direction_str()
        if dir_str == "North":
            return "↑"
        elif dir_str == "North-East":
            return "↗"
        elif dir_str == "East":
            return "→"
        elif dir_str == "South-East":
            return "↘"
        elif dir_str == "South":
            return "↓"
        elif dir_str == "South-West":
            return "↙"
        elif dir_str == "West":
            return "←"
        elif dir_str == "North-West":
            return "↖"
        else:
            return ""

    def wind_direction_short(self) -> str:
        """
        Returns wind direction in shortened form
        :return: abbreviation
        """
        split_direction = self.wind_direction_str().split("-")
        abbreviated_string = ""
        for s in split_direction:
            abbreviated_string += s[0]
        return abbreviated_string

    def cloud_cover_formatted(self) -> str:
        """
        Returns the formatted cloud cover string
        :return: cloud cover formatted to fit max length
        """
        return f"{self.cloud_cover:>14}"

    def warning_symbols(self, unicode: bool = False) -> str:
        """
        Returns a string containig warning labels about different weather features.
        If winds are at least strong winds, shows a warning for high winds.
        If Temperatures are below zero ⛄ or over 30 C 🌡, shows a warning for high or low temperature
        If there's precipitation, shows a symbol for that 🌧
        If there's a storm, shows an extra warning for that
        :param unicode: Use unicode symbols for this (may not be monospace depending on font
        :return: warning string of symbols
        """
        if self.wind_speed > 50 or self.precipitation_state == "Thunderstorm":
            if unicode:
                overall_warning = "⚠"
            else:
                overall_warning = "!"
        else:
            overall_warning = ""

        if self.wind_speed > 20:
            if unicode:
                wind_warning = "➢"
            else:
                wind_warning = "W"
        else:
            wind_warning = ""

        if self.temperature < 32:
            if unicode:
                temperature_warning = "❄"
            else:
                temperature_warning = "T"
        elif self.temperature > 90:
            if unicode:
                temperature_warning = "🌡"
            else:
                temperature_warning = "T"
        else:
            temperature_warning = ""

        if "fog" in self.precipitation_state.lower():
            if unicode:
                precipitation_warning = "🌫"
            else:
                precipitation_warning = "F"
        elif "thunderstorm" in self.precipitation_state.lower():
            if unicode:
                precipitation_warning = "⛈"
            else:
                precipitation_warning = "S"
        elif self.precipitation_state != "":
            if unicode:
                precipitation_warning = "🌧"
            else:
                precipitation_warning = "R"
        else:
            precipitation_warning = ""

        return f"{overall_warning:1}{wind_warning:1}{temperature_warning:1}{precipitation_warning:1}"

    def __str__(self):
        if len(self.precipitation_state) == 0:
            return f"{self.get_temperature():>5.1f} C"
        else:
            return f"{self.get_temperature():>5.1f} C, {self.get_precipitation()} [{self.precipitation_duration}]"


@dataclass
class WeatherGeneratorState:
    season = "summer"
    climate = "temperate"
    elevation = 0
    hour: int = 0
    weather: Weather = None

    # temperature
    temperature_general: int = 0
    temperature_daytime: int = 0
    temperature_nighttime: int = 0
    temperature_change_step: int = 0
    temperature_refresh_timer: int = 0

    # precipitation
    current_precipitation_duration: int = 0
    queued_precipitation_start_time: int = 0
    queued_precipitation_duration: int = 0
    queued_precipitation_type: str = ""

    # wind
    wind_speed_class: int = 0

    # clouds
    cloud_cover_type: int = 0

    def to_json(self):
        res = {attr: getattr(self, attr) for attr in dir(self) if not attr.startswith("__") and attr != "weather" and not callable(getattr(self, attr))}
        res['weather'] = self.weather.to_json()
        return res

    @staticmethod
    def from_json(json_obj):
        state = WeatherGeneratorState()
        d = dir(state)
        for key, val in json_obj.items():
            if key in d:
                if key == "weather":
                    state.weather = Weather.from_json(val)
                else:
                    setattr(state, key, val)
        return state

    def climate_str(self):
        return self.climate.capitalize()

    def season_str(self):
        return self.season.capitalize()

    def elevation_str(self):
        if self.elevation < 1000:
            return "Sea level"
        elif 1000 <= self.elevation < 5000:
            return "Lowlands"
        elif 5000 <= self.elevation:
            return "Highlands"
        else:
            return "Underground"

class ClimateData:
    def __init__(self):
        temp_baselines = namedtuple("TemperatureBaseline", ["winter", "spring", "summer", "fall"])
        self.temperature_baselines = {"cold": temp_baselines(20, 30, 40, 30),
                                       "temperate": temp_baselines(30, 60, 80, 60),
                                       "tropical": temp_baselines(50, 75, 95, 75),
                                       "desert": temp_baselines(50, 75, 95, 75)}
        self.temperature_variations = {"cold": np.array([[20, 40, 60, 80, 95, 99, 100],
                                                          ["-3d10", "-2d10", "-1d10", "0d10", "1d10", "2d10", "3d10"],
                                                          ["1d4", "1d6+1", "1d6+2", "1d6+2", "1d6+1", "1d4", "1d2"]]),
                                        "temperate": np.array([[5, 15, 35, 65, 85, 95, 100],
                                                               ["-3d10", "-2d10", "-1d10", "0d10", "1d10", "2d10",
                                                                "3d10"],
                                                               ["1d2", "1d4", "1d4+1", "1d6+1", "1d4+1", "1d4",
                                                                "1d2"]]),
                                        "tropical": np.array([[10, 25, 55, 85, 100],
                                                              ["-2d10", "-1d10", "0d10", "1d10", "2d10"],
                                                              ["1d2", "1d2", "1d4", "1d4", "1d2"]]),
                                        "desert": np.array([[10, 25, 55, 85, 100],
                                                            ["-2d10", "-1d10", "0d10", "1d10", "2d10"],
                                                            ["1d2", "1d2", "1d4", "1d4", "1d2"]])}
        precip_frequency_baseline = namedtuple("PrecipitationFrequencyBaseline", ["spring", "summer", "fall", "winter"])
        self.precipitation_frequency_baselines = {"cold": precip_frequency_baseline(2, 1, 2, 3),
                                                   "temperate": precip_frequency_baseline(2, 3, 2, 1),
                                                   "tropical": precip_frequency_baseline(3, 2, 3, 1),
                                                   "desert": precip_frequency_baseline(0, 0, 0, 2)}
        ele_baseline = namedtuple("ElevationBaseline", ['temp_change', 'intensity', 'frequency_change'])
        self.elevation_baselines = {"sea level": ele_baseline(10, 2, 0),
                                     "lowland": ele_baseline(0, 1, 0),
                                     "highland": ele_baseline(-10, 1, -1)}
        self.precipitation_chances: np.array = [5, 15, 30, 60, 95]
        self.wind_speed_table = np.array([[50, 80, 90, 95, 100], ["Light winds", "Moderate winds", "Strong winds", "Severe winds", "Windstorm"], ["1d11+1", "1d10+10", "1d10+20", "1d20+30", "1d20+50"]])
        self.cloud_cover_types = np.array(["", "Light clouds", "Medium clouds", "Overcast"])

        self.seasons: np.array = np.array(["winter", "spring", "summer", "fall"])
        self.climates: np.array = np.array(["cold", "temperate", "tropical", "desert"])

class WeatherGenerator:
    def __init__(self):
        """
        Creates a weather generator. Before use, use the initialize() function to ensure that things like temperature
        and precipitation are initialized.
        """
        self.climate_data = ClimateData()

        # State
        self._state = WeatherGeneratorState()

    @property
    def climate_list(self):
        return self.climate_data.climates

    @staticmethod
    def _elevation_to_str(elevation: int) -> str:
        """
        Converts an elevation to a string that is used internally
        :param elevation: Elevation as an integer
        :return: Elevation string
        """
        if elevation < 1000:
            elevation_string = "sea level"
        elif elevation <= 5000:
            elevation_string = "lowland"
        else:
            elevation_string = "highland"
        return elevation_string

    def _get_precipitation_intensity_table(self, climate: str, elevation: int, frozen: bool) -> np.array:
        """
        Fetches the table for rolling precipitation intensity and duration from file
        :param climate: Which climate to fetch for
        :param elevation: Which elevation to fetch for (in ft from sea level)
        :param frozen: Whether the precipitation is frozen or not
        :return: The 2D table containing %die upper limit, precipitation type and intensity, and duration in hours
        """
        elevation_string = self._elevation_to_str(elevation)
        precipitation = self.climate_data.elevation_baselines[elevation_string].intensity
        if climate == "cold" or climate == "desert":
            precipitation -= 1
        elif climate == "tropical":
            precipitation += 1

        if precipitation < 0:
            precipitation = 0
        if precipitation > 3:
            precipitation = 3

        # precipitation data from csv
        with open("./precipitation_tables.csv") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            indexes = np.arange(1, 10)
            indexes += 10 * precipitation
            rows = np.array([row for idx, row in enumerate(reader) if idx in indexes])

        if frozen:
            rows = rows[:, 3:]
        else:
            rows = rows[:, :3]

        return rows[np.invert(np.all(rows == '', axis=1))]

    @staticmethod
    def _get_precipitation(precipitation_intensity_table: np.array) -> Tuple[str, int, int]:
        """
        Rolls a precipitation type from the precipitation intensity table
        :param precipitation_intensity_table: Precipitation intensity table fetched using
               _get_precipitation_intensity_table
        :return: Precipitation intensity, start time (in hours from this moment), duration in hours
        """
        r = dice.roll("1d100")
        for row in precipitation_intensity_table:
            if sum(r) <= int(row[0]):
                intensity_str = row[1]
                duration = sum(dice.roll(row[2]))
                break
        else:
            intensity_str = "<Error>"
            duration = 1
        # TODO: If thunderstorm, set wind to higher
        start_time = dice.roll("1d24-1")
        return intensity_str, start_time, duration

    def _check_for_precipitation(self, season: str, climate: str, elevation: int) -> bool:
        """
        Roll precipitation chance to see whether there's precipitation in the next 24 hours
        :param season: Current season
        :param climate: Current climate
        :param elevation: Current elevation in ft above sea level.
        :return: True, if there is precipitation. False if there is not.
        """
        elevation_str = self._elevation_to_str(elevation)
        frequency = int(self.climate_data.precipitation_frequency_baselines[climate]._asdict()[season])
        elevation_adjustment = self.climate_data.elevation_baselines[elevation_str].frequency_change
        frequency += elevation_adjustment
        if frequency < 0:
            frequency = 0
        if frequency > 4:
            frequency = 4
        precipitation_chance = int(self.climate_data.precipitation_chances[frequency])
        r = dice.roll("1d100")
        if sum(r) <= precipitation_chance:
            return True
        else:
            return False

    def _get_temperature(self, season: str, climate: str, elevation: int) -> Tuple[int, int]:
        """
        Calculates the general temperature for the next few days.
        :param season: Current season
        :param climate: Current climate
        :param elevation: Current elevation in ft above sea level
        :return: Temperature in F and the duration of this temperature
        """
        baseline_temp = self.climate_data.temperature_baselines[climate]._asdict()[season]
        elevation_str = self._elevation_to_str(elevation)
        elevation_adjustment = self.climate_data.elevation_baselines[elevation_str].temp_change
        variation_table = self.climate_data.temperature_variations[climate]
        r = sum(dice.roll("1d100"))
        for row in variation_table.T:
            if r <= int(row[0]):
                variation = dice.roll(row[1])
                try:
                    variation = sum(variation)
                except TypeError:
                    pass
                variation_duration = dice.roll(row[2])
                try:
                    variation_duration = sum(variation_duration)
                except TypeError:
                    pass
                break
        else:
            variation = 0
            variation_duration = -1
        return baseline_temp + elevation_adjustment + int(variation), int(variation_duration)

    @staticmethod
    def _get_night_temperature(temperature: int) -> int:
        """
        Returns nightly temperature based on current temperature
        :param temperature: Current daytime temperature
        :return: nighttime temperature
        """
        return temperature - dice.roll("2d6+3")

    @staticmethod
    def _get_temperature_daily_variation(temperature: int) -> int:
        """
        Returns daytime temperature for the current daily variation
        :param temperature: Current daytime temperature
        :return: Today's daytime temperature
        """
        return temperature + dice.roll("2d6-7")

    def advance_hour(self) -> Weather:
        """
        Advance the generator state by an hour. Returns the next hour's temperature.
        :return: Next hour's temperature
        """
        self._state.hour += 1
        # daily reset
        if self._state.hour == 24:
            self._state.hour = 0
            if self._check_for_precipitation(self._state.season, self._state.climate, self._state.elevation):
                frozen = self._state.weather.temperature < 32
                table = self._get_precipitation_intensity_table(self._state.climate, self._state.elevation, frozen)
                precipitation_type, start, duration = self._get_precipitation(table)
                self._state.queued_precipitation_type = precipitation_type
                self._state.queued_precipitation_start_time = start
                self._state.queued_precipitation_duration = duration
            else:
                self._state.queued_precipitation_duration = 0
                self._state.queued_precipitation_type = ""
                self._state.queued_precipitation_start_time = -10
            self._state.temperature_refresh_timer -= 1
            if self._state.temperature_refresh_timer <= 0:
                self._state.temperature_general, self._state.temperature_refresh_timer = self._get_temperature(
                    self._state.season, self._state.climate, self._state.elevation)
                self._state.temperature_daytime = self._get_temperature_daily_variation(self._state.temperature_general)
                self._state.temperature_change_step = \
                    (self._state.temperature_daytime - self._state.temperature_nighttime) // 4

        # temperature variations
        if 9 > self._state.hour >= 6 or 21 > self._state.hour >= 18:
            self._state.weather.temperature += self._state.temperature_change_step
        if self._state.hour == 9:
            self._state.weather.temperature = self._state.temperature_daytime
            self._state.temperature_nighttime = self._get_night_temperature(self._state.temperature_general)
            self._state.temperature_change_step = \
                (self._state.temperature_nighttime - self._state.temperature_daytime) // 4
        if self._state.hour == 21:
            self._state.weather.temperature = self._state.temperature_nighttime
            self._state.temperature_daytime = self._get_temperature_daily_variation(self._state.temperature_general)
            self._state.temperature_change_step = \
                (self._state.temperature_daytime - self._state.temperature_nighttime) // 4

        # precipitation
        self._state.current_precipitation_duration -= 1
        if self._state.current_precipitation_duration == 0:
            self._state.weather.precipitation_state = ""
        if self._state.hour == self._state.queued_precipitation_start_time:
            self._state.weather.precipitation_state = self._state.queued_precipitation_type
            self._state.current_precipitation_duration = self._state.queued_precipitation_duration
        self._state.weather.precipitation_duration = self._state.current_precipitation_duration

        # Wind
        if self._state.hour == 0:
            self._state.weather.wind_direction = dice.roll("1d360-1")
            r = sum(dice.roll("1d100"))
            for i, row in enumerate(self.climate_data.wind_speed_table.T):
                if r <= int(row[0]):
                    self._state.wind_speed_class = i
                    break
            else:
                self._state.wind_speed_class = 0

        # Cloud cover.
        if self._state.hour == 0:
            r = sum(dice.roll("1d100"))
            if r <= 50:
                self._state.cloud_cover_type = 0
            elif r <= 70:
                self._state.cloud_cover_type = 1
            elif r <= 85:
                self._state.cloud_cover_type = 2
            elif r <= 100:
                self._state.cloud_cover_type = 3

        minimum_clouds = 0
        if self._state.current_precipitation_duration > 0:
            minimum_clouds = 3
        elif -3 < self._state.current_precipitation_duration <= 0:
            minimum_clouds = 2 + self._state.current_precipitation_duration

        time_until_next_precipitation = self._state.queued_precipitation_start_time - self._state.hour
        if 3 >= time_until_next_precipitation > 0:
            if 3 - time_until_next_precipitation > minimum_clouds:
                minimum_clouds = 3 - time_until_next_precipitation

        if self._state.queued_precipitation_type == "Thunderstorm" or self._state.queued_precipitation_type == "Thunderstorm":
            minimum_wind_class = minimum_clouds - 1
        else:
            minimum_wind_class = 0

        if self._state.cloud_cover_type < minimum_clouds:
            cloud_cover = self.climate_data.cloud_cover_types[minimum_clouds]
        else:
            cloud_cover = self.climate_data.cloud_cover_types[self._state.cloud_cover_type]

        if self._state.wind_speed_class < minimum_wind_class:
            wind_speed_class = minimum_wind_class
        else:
            wind_speed_class = self._state.wind_speed_class

        self._state.weather.wind_strength = self.climate_data.wind_speed_table.T[wind_speed_class, 1]
        self._state.weather.wind_speed = int(dice.roll(self.climate_data.wind_speed_table.T[wind_speed_class, 2]))

        self._state.weather.cloud_cover = cloud_cover

        return self._state.weather

    def initialize(self, season: str, climate: str, elevation: int, hour: int) -> Weather:
        """
        Initializes the weather generator. in practice, it just sets the time to hour 23, then rolls it forward for 25
        hours to let the temperature settle in, then rolls it to the day hour specified. This ensure that the generator
        is in a sensible state.
        :param season: Current season
        :param climate: Current climate
        :param elevation: Current elevation in ft above sea level
        :param hour: Hour in the day (24h format) to initialize to
        :return: Current weather
        """
        self._state = WeatherGeneratorState()
        self._state.hour = 23
        self._state.season = season
        self._state.climate = climate
        self._state.elevation = elevation
        self._state.weather = Weather(temperature=0, precipitation_state="")
        for _ in range(24 + 1 + hour):
            self.advance_hour()
        return self._state.weather

    def change_climate(self, climate: str) -> bool:
        """
        Change the current climate
        :param climate: Climate to change to
        :return: True, if climate was changed. False otherwise.
        """
        if climate not in self.climate_data.climates:
            return False
        else:
            self._state.climate = climate
            return True

    def change_elevation(self, elevation: int) -> None:
        """
        Change current elevation
        :param elevation: Elevation to set to in ft above sea level
        :return: None
        """
        self._state.elevation = elevation

    def change_season(self, season: str) -> bool:
        """
        Change current season
        :param season: Season to change to
        :return: True if the season was recognized and set, False otherwise
        """
        if season not in self.climate_data.seasons:
            return False
        else:
            self._state.season = season
            return True

    def get_weather(self) -> Weather:
        """
        Return current weather
        :return: Current Weather
        """
        return copy.deepcopy(self._state.weather)

    def get_state(self) -> WeatherGeneratorState:
        """
        Get current generator state
        :return: GeneratorState object
        """
        return self._state

    def set_state(self, state: WeatherGeneratorState) -> None:
        """
        Set weather generator state
        :param state: State to set to
        :return: None
        """
        self._state = state


if __name__ == "__main__":
    generator = WeatherGenerator()
    generator.initialize(season="summer", climate="temperate", elevation=1500, hour=15)
    while True:
        generator.advance_hour()
        # noinspection PyProtectedMember
        print(f"[{generator._state.hour:0>2}:00] {str(generator.get_weather())}")
        input()
