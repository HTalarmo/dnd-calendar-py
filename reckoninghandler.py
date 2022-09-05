from dataclasses import dataclass
from typing import Tuple, List

import numpy as np


class UnknownCalendarException(Exception):
    """ Exception raised when a calendar name is not recognized

        Attributes:
            calendar_name -- name of the calendar that caused  the error
            message -- explanation of the error
    """

    def __init__(self, calendar_name: str, message: str = "Calendar {} not found"):
        self.calendar_name = calendar_name
        self.message = message.format(self.calendar_name)
        super().__init__(self.message)


class InvalidDateException(Exception):
    """ When a date input is invalid """

    def __init__(self, input_str: str, message: str = "Input string {} is invalid"):
        self.message = message.format(message.format(input_str))
        super().__init__(self.message)


@dataclass
class DnDate:
    _year: int = 0  # Important: This is the real true value that starts from 0
    era: int = 0
    num_eras: int = 1
    month_num: int = 0
    month: str = ""
    dow_num: int = 0
    dow: str = ""
    dow_short: str = ""
    day_of_month: int = 0
    hour: int = 0
    calendar_name: str = ""

    @property
    def year(self) -> int:
        """
        Use this for UI elements. It accounts for the fact that years start from in the positive range.
        :return: year as integer (should never be 0)
        """
        if self.era > 0:
            return self._year + 1
        else:
            return self._year

    @property
    def erastring(self) -> str:
        """
        Converts the era number into a string. If before reckoning begins, era is BR. If there's only one era,
        the era is not named. If there's more than one era for the calendar, it's denoted with #E. If something
        broke, era is FF.
        :return: string
        """
        if self.era == 0:
            return "BR"
        elif self.era > 0:
            if self.num_eras == 1:
                return ""
            else:
                return f"{self.era}E"
        else:
            return "FF"

    def time_string(self) -> str:
        """
        Convert time to a string
        :return: string in format xx:00
        """
        return f"{self.hour:0>2}:00"

    def date_string(self, short: bool = False, delimiter: str = ".", short_dow: bool = False) -> str:
        """
        Convert date to string format
        :param short: Set to True to get the date in a dd.mm.eeyyyy format (e: era)
        :param delimiter: Set the delimiter for short format
        :param short_dow: Set to True to use shortened versions of weekdays
        :return: date as string
        """
        if short:
            return f"{self.day_of_month}{delimiter}{self.month_num}{delimiter}{self.erastring}{abs(self.year)}"
        else:
            if self.dow_num == -1:
                dow_str = ""
            elif short_dow:
                dow_str = self.dow_short + ", "
            else:
                dow_str = self.dow + ", "
            if self.erastring == "":
                year_str = str(abs(self.year))  # Year is always a positive number
            else:
                year_str = f"{self.erastring} {abs(self.year)}"
            return f"{dow_str}{self.day_of_month} of {self.month}, {year_str}"

    def datetime_string(self, short_date: bool = False, date_delimiter: str = ".", short_dow: bool = False) -> str:
        """
        The full date and time in string format
        :param short_date: Set to True to use the short date format dd.mm.eeyyyy (e: era)
        :param date_delimiter: Set delimiter for short format
        :param short_dow: Set to True to use the shortened versions of weekdays
        :return: Time and date as string
        """
        return f"{self.time_string()} " \
               f"{self.date_string(short=short_date, delimiter=date_delimiter, short_dow=short_dow)}"


class ReckoningHandler:
    # noinspection PyDictCreation
    def __init__(self):
        """
        Handles the reckoning of different calendar systems. Dates and times should always be listed as integers
        everywhere and this handler should be used to convert the integer from relative time to epoch to actual
        human-readable dates.
        """
        # calendars stored here
        # TODO: move these to a separate file. A JSON probably.
        self._calendars = {}
        self._calendars["human"] = {"months": np.array(
            [["Sharis", "Lathis", "Sunus", "Talas", "Savris", "Malus", "Chautis", "Myrus", "Auris"],
             [34, 34, 33, 34, 34, 33, 34, 34, 33]]),
                                    "weekdays": np.array([["Gondag", "Ildag", "Waudag", "Seludag", "Tyrdag", "Liidag",
                                                           "Tordag", "Eldag"],
                                                          ["Gon.", "Ild.", "Wau.", "Sel.", "Tyr.", "Lli.", "Tor.",
                                                           "Eld."]]),
                                    "epoch_offset": 0,
                                    "era_start_dates": np.array([-2692 * 303 * 24, 0])}
        self._calendars["drow"] = {"months": np.array(
            [["Arcania", "Feralia", "Radikas", "Venia", "Noctil", "Aquor", "Mortalis", "Tenebris"],
             [36, 36, 36, 36, 36, 36, 36, 36]]),
                                   "weekdays": None,
                                   "era_start_dates": np.array([421141 * 24])}
        self._calendars["kitsune"] = {"months": np.array([["Winter", "Spring", "Summer", "Fall"], [76, 76, 76, 75]]),
                                      "weekdays": None,
                                      "era_start_dates": np.array([-569075 * 24])}

    @property
    def calendar_list(self) -> List[str]:
        """
        List of currently loaded calendars.
        :return: list of calendar names
        """
        return list(self._calendars.keys())

    def find_month_and_day(self, day_of_year: int, calendar_name: str) -> Tuple[int, str, int]:
        """
        Day of the year = the number of days since the start of the year. This converts that into the respective month
        and day. If day_of_year is more than the number of days in a year for the calendar, it loops around.
        :param day_of_year: The day of the year
        :param calendar_name: Which calendar to use for the conversion
        :return: month (int), month name (str), day (int)
        :raises UnknownCalendarException: if calendar_name is not found in the list of calendars
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        months = self._calendars[calendar_name]['months']
        while day_of_year > sum(months[1].astype(int)):
            day_of_year -= sum(months[1].astype(int))
        day_of_month = day_of_year
        month = 0
        for month in range(0, months.shape[1]):
            days_in_month = int(months[1][month])
            if day_of_month >= days_in_month:
                day_of_month -= days_in_month
            else:
                break

        return month, str(months[0][month]), int(day_of_month)

    def calculate_day_of_year(self, day_of_month: int, month: int, calendar_name: str) -> int:
        """
        Calculates the day of the year from a given day of the month and the month number. Effectively does the reverse
        of find_month_and_day.
        :param day_of_month: Which day of the month it is.
        :param month: Which month it is.
        :param calendar_name: Which calendar system the date is in.
        :return: The number of the day from the start of the year
        :raises UnknownCalendarException: if calendar_name not found in calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        day_of_year = 0
        months = self._calendars[calendar_name]["months"]
        for i in range(0, month):
            day_of_year += int(months[1][i])
        day_of_year += day_of_month

        return int(day_of_year)

    def epoch_to_dow(self, time_from_epoch: int, calendar_name: str) -> Tuple[int, str, str]:
        """
        Converts time from epoch to day of the week. If the calendar does not have weekdays, the weekday number will
        be set to -1.
        :param time_from_epoch:
        :param calendar_name: Name of the calendar to use
        :return: The number of DoW, name of DoW, shortened name of the DoW
        :raises UnknownCalendarException: If calendar_name not found in calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)

        weekdays = self._calendars[calendar_name]['weekdays']
        if weekdays is None:
            return -1, "<NoWeekdays>", "<NoWeekdays>"
        else:
            total_weekdays = weekdays.shape[1]
            dow_num = (time_from_epoch // 24) % total_weekdays
            return dow_num, weekdays[0][dow_num].item(), weekdays[1][dow_num].item()

    def epoch_to_date(self, time_since_epoch: int, calendar_name: str) -> DnDate:
        """
        Converts time since epoch into a DnDate object for more human-readable use.
        :param time_since_epoch: Integer time from epoch (in hours)
        :param calendar_name: Calendar name to be used
        :return: DnDate object for the date
        :raises UnknownwCalendarException: if calendar_name not found in calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        calendar = self._calendars[calendar_name]
        months = calendar["months"]
        year_length = int(sum(months[1].astype(int)))

        # figure out era
        #   0: BR
        # > 0: 1E 2E...
        for i, era_start_date in enumerate(calendar["era_start_dates"]):
            if time_since_epoch < era_start_date:
                era = i
                break
        else:
            era = len(calendar['era_start_dates'])

        if era == 0:
            time_since_era_start = time_since_epoch - calendar['era_start_dates'][0].item()
        else:
            time_since_era_start = time_since_epoch - calendar['era_start_dates'][era - 1].item()

        days_since_era_start = time_since_era_start // 24

        year = days_since_era_start // year_length

        day_of_year = days_since_era_start % year_length
        month, month_str, day_of_month = self.find_month_and_day(day_of_year, calendar_name)
        dow_num, dow, dow_short = self.epoch_to_dow(days_since_era_start, calendar_name)
        # TODO: Allow the start of the era to begin at other times than midnight (might be messy)
        hour = time_since_era_start % 24  # Assumes that start of the era is at midnight.

        return DnDate(_year=year, era=era, num_eras=len(calendar['era_start_dates']), month_num=month + 1,
                      month=month_str, dow_num=dow_num,
                      dow=dow, dow_short=dow_short,
                      day_of_month=day_of_month + 1, hour=hour, calendar_name=calendar_name)

    def string_to_epoch(self, date_str: str, calendar_name: str, delimiter: str = '.') -> int:
        """
        Converts a string (short format) date to time since epoch. Only deals with dates, so will always end up at the
        start of the day for that date. If you want to add the hour as well, just add +<hours> to the result.
        :param date_str: The date string in short format (dd.mm.eeyyyy e: era)
        :param calendar_name: The name of the calendar system the date is in
        :param delimiter: What delimiter is being used for the short date
        :return: Hours from epoch on that date at midnight
        :raises InvalidDateException: If it fails to parse date_str
        :raises UnknownCalendarException: If calendar_name is not found in calendar list
        """
        # parse the string
        split_str = date_str.split(delimiter)
        if len(split_str) != 3:
            raise InvalidDateException(date_str)
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        try:
            day = int(split_str[0]) - 1  # Note: epoch is time from the start of day 1. So at midnight, day = 0
            month_num = int(split_str[1]) - 1
            era_and_year = split_str[2]

            if era_and_year.startswith("BR"):
                era = 0
                year = int(era_and_year[2:])
            elif "E" in era_and_year:
                index = era_and_year.find("E")
                era = int(era_and_year[:index])
                year = int(era_and_year[index + 1:]) - 1
            else:
                era = 1
                year = int(era_and_year) - 1
        except ValueError:
            raise InvalidDateException(date_str)

        # start processing details. At this point we know the day, month number, era number and year.
        day_of_year = self.calculate_day_of_year(day, month_num, calendar_name)
        year_length_in_days = self.days_in_year(calendar_name)
        era_start_times = self._calendars[calendar_name]["era_start_dates"]

        # check that the era actually has the given number of years
        if 0 < era < len(era_start_times):  # never true if len(era_start_times == 1
            era_start = era_start_times[era - 1]
            era_end = era_start_times[era]
            years_in_era = ((era_end - era_start) // 24) / year_length_in_days
            if years_in_era < year:  # FIXME: check if this is off-by-one. Might need to be year-1 or something.
                InvalidDateException(input_str=date_str, message="Era does not have that many years: {}")

        # If era == 0, then the number of years is actually years BEFORE reckoning, so we subtract it from era start
        if era == 0:
            year_offset_in_hours = era_start_times[0] - year * year_length_in_days * 24
        elif era > 0:
            year_offset_in_hours = year * year_length_in_days * 24 - era_start_times[era - 1]
        else:
            raise InvalidDateException(date_str, message="Unknown era in {}")

        # put the offset of the year and day of the year together to get the full time from epoch
        return int(year_offset_in_hours) + int(day_of_year) * 24

    def get_season(self, time_from_epoch: int) -> str:
        """
        Get the season for the time
        :param time_from_epoch: Time from epoch in hours
        :return: The season
        """
        # convert to kitsune calendar. Its months are just seasons anyways.
        kitsune_date = self.epoch_to_date(time_from_epoch, calendar_name="kitsune")
        return str(kitsune_date.month.lower())

    def days_in_month(self, month_num: int, calendar_name: str) -> int:
        """
        Returns how many days there are in a given month in a given calendar
        :param month_num: number of the month
        :param calendar_name: Name of the calendar
        :return: Number of days in the month
        :raises UnknownCalendarException: if calendar_name is not in the calendar list
        :raises InvalidDateException: if month_num isn't a valid month number
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        months = self._calendars[calendar_name]["months"]
        if 1 > month_num > months.shape[1]:
            raise InvalidDateException(str(month_num), message="Calendar does not have {} months in it")
        return int(months[1, month_num - 1])

    def months_in_year(self, calendar_name: str) -> int:
        """
        Returns how many months there are in a year for a given calendar
        :param calendar_name: Name of the calendar
        :return: Number of months in a year
        :raises UnknownCalendarException: if calendar_name is not in the calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        return int(self._calendars[calendar_name]["months"].shape[1])

    def days_in_year(self, calendar_name: str) -> int:
        """
        Returns how many days there are in a year
        :param calendar_name: Name of the calendar
        :return: Number of days in the calendar year
        :raises UnknownCalendarException: if calendar_name is not in the calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        return int(np.sum(self._calendars[calendar_name]["months"][1].astype(int)))

    def hours_in_year(self, calendar_name: str) -> int:
        """
        Returns the number of hours in a year for a given calendar
        :param calendar_name: Name of the calendar
        :return: Number of hours in the calendar
        :raises UnknownCalendarException: if calendar_name is not in the calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        return int(self.days_in_year(calendar_name)) * 24

    def years_in_era(self, era: int, calendar_name: str) -> int:
        """
        Returns how many years there are in a given era. If the era is the first or last era of the calendar, returns 0
        :param era: number of the era
        :param calendar_name: Name of the calendar
        :return: Number of years in the era
        :raises UnknownCalendarException: if calendar_name is not in the calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        era_start_dates = self._calendars[calendar_name]["era_start_dates"]
        if era == 0 or era == len(era_start_dates):
            return 0
        era_start = era_start_dates[era - 1]
        era_end = era_start_dates[era]
        days_since_era_start = (era_end - era_start) // 24
        return int(days_since_era_start // self.days_in_year(calendar_name))

    def num_of_eras(self, calendar_name: str) -> int:
        """
        Returns the number of eras for a given calendar
        :param calendar_name: Name of the calendar
        :return: Number of eras
        :raises
        :raises UnknownCalendarException: if calendar_name is not in the calendar list
        """
        if calendar_name not in self._calendars:
            raise UnknownCalendarException(calendar_name)
        return len(self._calendars[calendar_name]['era_start_dates'])


if __name__ == "__main__":
    cal = ReckoningHandler()


    def print_dates(time_from_epoch: int):
        dateobj = cal.epoch_to_date(time_from_epoch, 'human')
        print(f"Human Calendar: {dateobj.date_string(short=False)} | {dateobj.date_string(True)}")
        dateobj = cal.epoch_to_date(time_from_epoch, 'kitsune')
        print(f"Kitsune Calendar: {dateobj.date_string()} | {dateobj.date_string(True)}")
        dateobj = cal.epoch_to_date(time_from_epoch, 'drow')
        print(f"Drow Calendar: {dateobj.date_string()} | {dateobj.date_string(True)}")


    date_string = "1.1.2E1"
    calendarname = "human"
    print(f"Starting data: {date_string}, calendar name: {calendarname}")
    # date = cal.string_to_epoch(date_str, calendar_name)+24*74
    date = -2692 * 303 * 24 + 814 * 303 * 24 - 42 * 24 + 24
    print(date)
    print_dates(date)
