import curses
import uuid
from dataclasses import dataclass
from typing import List, Dict

import numpy as np
from WeatherGenerator import Weather, WeatherGenerator, WeatherGeneratorState
from gui_utils import draw_box
from reckoninghandler import ReckoningHandler


class Event:
    def __init__(self, location: str, description: str, start_time_epoch: int, duration: int = 1):
        """
        Contains data for a single event
        :param location: The name of the location the event happens in
        :param description: Description of the event
        :param start_time_epoch: Start time as hours since epoch
        :param duration: How many hours the event lasts
        """
        self.delete_event = False
        self.location = location
        self.description = description
        self.start_time_epoch = int(start_time_epoch)
        self.duration = int(duration)  # in hours
        self.id = str(uuid.uuid4())
        if self.duration < 1:
            self.duration = 1  # anything less than 1 hour doesn't really make a difference in the calendar

    def to_json(self):
        return {attr: getattr(self,attr) for attr in dir(self) if not attr.startswith("__") and not callable(getattr(self, attr))}

    @staticmethod
    def from_json(json_obj):
        e = Event("", "", 1)
        d = dir(e)
        for key, val in json_obj.items():
            if key in d:
                setattr(e, key, val)
        return e

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.start_time_epoch < other.start_time_epoch

    def to_string(self, maxlength: int):
        if len(self.description) > maxlength:
            return self.description[:maxlength - 3] + "..."
        else:
            return f"{self.description:<{maxlength}}"


@dataclass
class Hour:
    """
    Contains information about the goings-on of a single hour
    """
    time_from_epoch: int  # Current time
    weather: Weather  # Current weather
    generator_state: WeatherGeneratorState  # The state of the weather generator at this point
    events: List[Event]  # List of events at this hour


    def to_json(self):
        res = {}
        res["time_from_epoch"] = self.time_from_epoch
        res['weather'] = self.weather.to_json()
        res['generator_state'] = self.generator_state.to_json()
        res['events'] = []
        for event in self.events:
            res['events'].append(event.to_json())
        return res

    @staticmethod
    def from_json(json_obj):
        time_from_epoch = json_obj['time_from_epoch']
        weather = Weather.from_json(json_obj['weather'])
        generator_state = WeatherGeneratorState.from_json(json_obj['generator_state'])
        events = []
        for event in json_obj['events']:
            events.append(Event.from_json(event))
        return Hour(time_from_epoch=time_from_epoch, weather=weather, generator_state=generator_state, events=events)

    def event_str(self, maxwidth: int = 16):
        """
        Returns the event listing of the hour as a string
        :param maxwidth: Max number of characters for the event description
        :return: Event listing
        """
        if len(self.events) == 0:
            event_str = " "*maxwidth
        elif len(self.events) == 1:
            if len(self.events[0].description) > maxwidth:
                event_str = self.events[0].description[:maxwidth - 3] + "..."
            else:
                event_str = self.events[0].description
        else:
            event_str = f"{'[...]':<{maxwidth}}"
        return event_str

class GeneratingPopupWindow:
    def __init__(self):
        self._window = curses.newwin(5, 21, curses.LINES//2-3, curses.COLS//2-10)
        self._window.attron(curses.color_pair(1))
        draw_box(self._window, 0, 0, 5, 21)
        s = "Generating...."
        s = f"{s:^18}"
        self._window.addstr(2, 1, s)
        self._window.refresh()

class DnDCalendar:
    def __init__(self, import_history=None, climate: str = "temperate",
                 elevation: int = 1500):
        """
        Contains the data for each hour of each day in the entire calendar
        :param import_history: Allows importing already existing history
        :param climate: Which climate to use
        :param elevation: What the elevation is
        """
        if import_history is None:
            import_history = {}
        self.reckoningHandler = ReckoningHandler()
        self.history: Dict[int, Hour] = import_history
        self.climate = climate
        self.elevation = elevation
        self.weather_generator = WeatherGenerator()

        self._time_generated = 24 * 3  # How many hours are generated before/after a given time at most

    def to_json(self):
        res = {}
        res['history'] = {}
        for key, val in self.history.items():
            res['history'][int(key)] = val.to_json()
        res['climate'] = self.climate
        res['elevation'] = self.elevation
        return res

    @staticmethod
    def from_json(json_obj):
        climate = json_obj['climate']
        elevation = json_obj['elevation']
        history = {}
        for key, val in json_obj['history'].items():
            history[int(key)] = Hour.from_json(val)
        return DnDCalendar(import_history=history, climate=climate, elevation=elevation)

    def get_climates(self):
        return self.weather_generator.climate_list

    def _add_hours(self, start_time_from_epoch: int, num_hours: int, weather_generator: WeatherGenerator) -> None:
        """
        Adds hours into the calendar from the start time
        :param start_time_from_epoch: The start hour from epoch (the first hour that will be generated)
        :param num_hours: Number of hours generated. Must be at least 1.
        :param weather_generator: Weather generator to use.
        :return: None
        """
        # Somehow these end up sometimes being numpy int32's which breaks JSON serialization.
        # FIXME: Figure out how the hell this happens.
        start_time_from_epoch = int(start_time_from_epoch)
        num_hours = int(num_hours)
        if start_time_from_epoch - 1 in self.history:
            weather_generator_state = self.history[start_time_from_epoch - 1].generator_state
            # Check that season hasn't changed
            season = self.reckoningHandler.get_season(start_time_from_epoch)
            if weather_generator_state.season != season:
                weather_generator_state.season = season
            weather_generator.set_state(weather_generator_state)
            weather_generator.advance_hour()
        else:
            season = self.reckoningHandler.get_season(start_time_from_epoch)
            self.weather_generator.initialize(season=season, climate=self.climate, elevation=self.elevation,
                                              hour=start_time_from_epoch % 24)
        for hour in range(num_hours):
            this_hour = start_time_from_epoch + hour
            weather = weather_generator.get_weather()
            generator_state = weather_generator.get_state()
            if this_hour in self.history:
                break  # This means that we hit a section of already generated hours. Staph.
            self.history[start_time_from_epoch + hour] = Hour(time_from_epoch=this_hour, weather=weather,
                                                              generator_state=generator_state, events=[])
            weather_generator.advance_hour()

    def get_time(self, time_from_epoch: int) -> Hour:
        """
        Get a given datetime. If the date is not currently in the calendar, it will be generated.
        :param time_from_epoch: The time from epoch
        :return: The data on the hour
        """
        # If the hour isn't in the list, generate it and some time before it
        if time_from_epoch not in self.history:
            # find the smallest hour
            win = GeneratingPopupWindow()
            generated_hours = np.sort(np.array(list(self.history.keys())))
            hours_before = generated_hours[np.where(generated_hours < time_from_epoch)[0]]
            if hours_before.shape[0] == 0:  # There are no hours before time_from_epoch generated
                start_time_from_epoch = time_from_epoch - self._time_generated
                self._add_hours(start_time_from_epoch, num_hours=self._time_generated * 2,
                                weather_generator=self.weather_generator)
            else:  # There are hours, check if they are at most time_generated in the past
                times_since_last_hour = time_from_epoch - int(hours_before[-1])
                # FIXME: Check if this is off by one
                if times_since_last_hour <= self._time_generated:
                    start_time_from_epoch = int(hours_before[-1]) + 1
                    hours_added = times_since_last_hour + self._time_generated
                    self._add_hours(start_time_from_epoch, num_hours=hours_added,
                                    weather_generator=self.weather_generator)
                else:
                    start_time_from_epoch = time_from_epoch - self._time_generated
                    self._add_hours(start_time_from_epoch, num_hours=self._time_generated * 2,
                                    weather_generator=self.weather_generator)
            del win
        return self.history[time_from_epoch]

    def add_event(self, event: Event) -> None:
        """
        Add a new event to the calendar
        :param event: The event object to add
        :return: None
        """
        # check that date exists
        self.get_time(event.start_time_epoch)
        for hour in range(event.duration):
            self.history[event.start_time_epoch + hour].events.append(event)

    def remove_event(self, event: Event) -> None:
        """
        Remove an event from the calendar
        :param event: Event to be removed
        :return: None
        """
        # Check that the time exists
        self.get_time(event.start_time_epoch)
        for hour in range(event.duration+1):
            if event in self.history[event.start_time_epoch + hour].events:
                self.history[event.start_time_epoch + hour].events.remove(event)

    def regenerate_weather(self, starting_time: int) -> None:
        """
        Regenerates weather from the starting time onwards
        :param starting_time: Time from epoch
        :return: None
        """
        date_info = self.reckoningHandler.epoch_to_date(starting_time, 'kitsune')
        hour = date_info.hour
        season = self.reckoningHandler.get_season(starting_time)
        self.weather_generator = WeatherGenerator()
        self.weather_generator.initialize(season, self.climate, self.elevation, hour)
        generated_times = np.array(list(self.history.keys()))
        hours_to_generate = generated_times[np.where(generated_times >= starting_time)]
        previous_hour = int(hours_to_generate[0]-2)
        for t in hours_to_generate:
            if previous_hour is None:
                previous_hour = int(t-2)
            if previous_hour < t-1:
                hour = self.reckoningHandler.epoch_to_date(int(t), 'human').hour
                season = self.reckoningHandler.get_season(starting_time)
                self.weather_generator.initialize(season, self.climate, self.elevation, hour)
            self.history[int(t)].weather = self.weather_generator.get_weather()
            self.history[int(t)].generator_state = self.weather_generator.get_state()
            self.weather_generator.advance_hour()
            previous_hour = t


    def change_climate(self, new_climate_start_time: int, new_climate: str) -> None:
        """
        Change climate starting from new_climate_start_time. This will go through times already generated from this
        point onwards and re-generates the weather for each of them to match the climate.
        :param new_climate_start_time: time from epoch when the new climate starts
        :param new_climate: What climate to set to
        :return:
        """
        # check that the climate is real
        if new_climate in self.get_climates():
            self.climate = new_climate
            self.regenerate_weather(starting_time=new_climate_start_time)
            print(f"Changed climate to {new_climate}")

    def change_elevation(self, new_elevation_start_time: int, new_elevation: int) -> None:
        """
        Change current elevation from the starting time to new elevation.
        :param new_elevation_start_time:
        :param new_elevation:
        :return:
        """
        self.elevation = new_elevation
        self.regenerate_weather(starting_time=new_elevation_start_time)
        print(f"Changed elevation to {new_elevation}")


if __name__ == "__main__":
    cal = DnDCalendar()
    rh = ReckoningHandler()
    t = rh.string_to_epoch("14.3.2E1394", 'human')
    # create a few days
    cal.get_time(t)
    # create an event
    e = Event(location="Denford", description="Test event", start_time_epoch=t, duration=4)
    cal.add_event(e)
    e = Event(location="Somewhere", description="Another test", start_time_epoch=t + 2, duration=4)
    cal.add_event(e)
    # print days
    for d in range(48):
        h = cal.get_time(t - 24 + d)
        date_str = rh.epoch_to_date(t - 24 + d, 'human').datetime_string()
        print(
            f"{date_str} {h.weather.warning_symbols(unicode=True)} {h.weather.get_temperature_str()} {h.weather.wind_direction_symb()}{h.weather.wind_speed_str():>6} {h.weather.wind_strength:>10} {h.weather.cloud_cover_formatted()} {h.weather.get_precipitation_formatted()}")
