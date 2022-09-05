from enum import Enum

from dndcalendar import DnDCalendar, Event
from gui_utils import Button, define_colors
import curses

from text_changers import TextBiggener, WeatherSymbols
from dateprompt import DatePrompt
from eventeditwindow import EventEditWindow


class CalendarSelectionMode(Enum):
    TIME = 1
    EDIT = 2
    EVENT = 3


class CalendarWindow:
    def __init__(self, start_time: int, calendar: DnDCalendar):
        """
        Curses-based calendar window
        :param start_time: Time to start off from as time since epoch
        :param calendar: The calendar object to use
        """
        self._window = curses.newwin(curses.LINES, curses.COLS)
        self._window.attron(curses.color_pair(1))
        self._cursor_time: int = start_time
        self._used_calendar: str = "human"

        # Selection-based variables
        self._edit_cursor: int = 0
        self._event_cursor: int = 0
        self._selection_mode: CalendarSelectionMode = CalendarSelectionMode.TIME
        self._calendar: DnDCalendar = calendar

        # Screen size variables
        self._info_panel_width: int = 45
        self._date_width: int = 14
        self._date_start: int = 2
        self._date_delimiter: int = self._date_start + self._date_width + 2
        self._time_start: int = self._date_delimiter + 2
        self._time_width: int = 7
        self._weather_width: int = 4
        self._weather_start: int = self._time_start + self._time_width + 1
        self._weather_delimiter: int = self._weather_start + self._weather_width + 1
        self._event_start: int = self._weather_start + self._weather_width + 3

        self._resize_window()
        #self.redraw()

    def _resize_window(self) -> None:
        """
        Figures out window size related variables
        :return: None
        """
        self._shown_hours_amount = curses.LINES - 2 - 2  # 2 for up and bottom border, 2 for the labels
        if self._shown_hours_amount < 24:
            required_days = 3
        else:
            required_days = 3 + 2*(self._shown_hours_amount-24)//48
        self._days_fetched = required_days
        self._current_day_fetching_offset = (1+required_days)//2 - 1

        self._events_width = curses.COLS - self._event_start - self._info_panel_width - 3

    def redraw(self) -> None:
        """
        Redraws the entire window
        :return: None
        """
        self._window.clear()
        self.draw_frame()
        self.draw_hour_labels()
        self.draw_hours()
        self.draw_side_panel()
        self.draw_event_list()
        self._window.refresh()

    def change_settings(self, climate = None, elevation = None, calendar_name = None):
        if climate is not None:
            self._calendar

    def draw_frame(self) -> None:
        """
        Draws the main frame for the window. Borders and lines etc.
        :return: None
        """
        right_side_start = curses.COLS-self._info_panel_width-2

        # top and bottom
        for x in range(curses.COLS-1):
            if x < right_side_start:
                self._window.addch(2, x, "─")
            self._window.addch(0, x, "═")
            self._window.addch(curses.LINES-1, x, "═")
        # Sides
        for y in range(curses.LINES-1):
            self._window.addch(y, self._date_delimiter, "│")
            self._window.addch(y, self._weather_delimiter, "│")
            self._window.addch(y, 0, "║")
            self._window.addch(y, right_side_start, "║")
            self._window.addch(y, curses.COLS-2, "║")
        # corners
        self._window.addch(0, 0, "╔")
        self._window.addch(0, curses.COLS-2, "╗")
        self._window.addch(curses.LINES-1, 0, "╚")
        self._window.addch(curses.LINES-1, curses.COLS-2, "╝")

        # Left side boxes
        self._window.addch(2, 0, "╟")
        self._window.addch(2, right_side_start, "╢")
        self._window.addch(0, self._date_delimiter, "╤")
        self._window.addch(curses.LINES-1, self._date_delimiter, "╧")
        self._window.addch(0, self._weather_delimiter, "╤")
        self._window.addch(curses.LINES-1, self._weather_delimiter, "╧")
        self._window.addch(2, self._date_delimiter, "┼")
        self._window.addch(2, self._weather_delimiter, "┼")

        # Right side boxing
        right_side_divider = 18
        self._window.addch(0, right_side_start, "╦")
        self._window.addch(curses.LINES-1, right_side_start, "╩")
        for x in range(right_side_start+1, curses.COLS-2):
            self._window.addch(8, x, "─")
            self._window.addch(right_side_divider, x, "─")
        self._window.addch(8, right_side_start, "╟")
        self._window.addch(right_side_divider, right_side_start, "╟")
        self._window.addch(8, curses.COLS-2, "╢")
        self._window.addch(right_side_divider, curses.COLS-2, "╢")

        # event boxing
        for y in range(right_side_divider+1, curses.LINES-1):
            self._window.addch(y, right_side_start+16, "│")
        self._window.addch(right_side_divider, right_side_start+16, "┬")
        self._window.addch(curses.LINES-1, right_side_start+16, "╧")

    def draw_hour_labels(self) -> None:
        """
        Draws labels for the time window at the top
        :return: None
        """
        self._window.addstr(1, self._date_start, f"{'Date':>{self._date_width}}")
        self._window.addstr(1, self._time_start, f"{'Time':<{self._time_width}}")
        self._window.addstr(1, self._event_start, f"{'Events'}")

    def draw_hours(self) -> None:
        """
        Draws the time window contents
        :return: None
        """
        start_time = self._cursor_time - (self._shown_hours_amount // 2)

        start_row = 3
        for row in range(self._shown_hours_amount):
            current_time = start_time + row
            selected_day = False
            date_info = self._calendar.reckoningHandler.epoch_to_date(current_time, self._used_calendar)
            calendar_info = self._calendar.get_time(current_time)

            # draw date
            datestr = f"{date_info.date_string(short=True):>{self._date_width}}"
            if self._selection_mode == CalendarSelectionMode.TIME:
                if current_time == self._cursor_time:
                    selected_day = True
                    self._window.attron(curses.A_REVERSE)
                elif current_time == self._cursor_time - 1:
                    datestr = "▲" + datestr[1:]
                elif current_time == self._cursor_time + 1:
                    datestr = "▼" + datestr[1:]
            self._window.addstr(start_row+row, self._date_start, datestr)

            # Draw time
            time_str = f"[{date_info.time_string()}]"
            self._window.addstr(start_row+row, self._time_start, time_str)

            # Draw weather
            weather_str = f"{calendar_info.weather.warning_symbols(False)}"
            self._window.addstr(start_row+row, self._weather_start, f"{weather_str}")

            # Draw events
            event_str = f"{calendar_info.event_str(maxwidth=self._events_width)}"
            self._window.addstr(start_row+row, self._event_start, event_str)

            if selected_day:
                self._window.attroff(curses.A_REVERSE)

    def draw_side_panel(self) -> None:
        """
        Draws the right side panel. Clock and current day weather to be precise. Event list and the buttons are done
        separately
        :return: None
        """
        date_info = self._calendar.reckoningHandler.epoch_to_date(self._cursor_time, self._used_calendar)
        calendar_info = self._calendar.get_time(self._cursor_time)
        start_x = curses.COLS-self._info_panel_width
        content_width = self._info_panel_width - 3

        # clear old texts
        for y in range(1, 17):
            if y != 8:
                self._window.addstr(y, start_x, " "*content_width)

        # Create the clock
        text_biggener = TextBiggener()
        hour_str = date_info.time_string()
        biggened_hour = text_biggener.biggen_text(hour_str, shadow=False)
        biggened_width = len(biggened_hour[0])
        biggened_hour_start = start_x+content_width//2-biggened_width//2
        for y, l in enumerate(biggened_hour):
            self._window.addstr(2+y, biggened_hour_start, l)

        # Draw date
        date_str = date_info.date_string()
        date_str_width = len(date_str)
        date_str_start = start_x + content_width//2-date_str_width//2
        self._window.addstr(9, date_str_start, date_str)

        # Draw climate and elevation
        climate_ele_str = f"{calendar_info.generator_state.season_str()} - {calendar_info.generator_state.climate_str()} - {calendar_info.generator_state.elevation_str()}"
        climate_str_width = len(climate_ele_str)
        climate_str_start = start_x + content_width//2-climate_str_width//2
        self._window.addstr(10, climate_str_start, climate_ele_str)

        # Draw weather symbol
        weather_symbols = WeatherSymbols()
        if calendar_info.weather.precipitation_state != "":
            weather = calendar_info.weather.precipitation_state
        else:
            weather = calendar_info.weather.cloud_cover
        weather_symbol = weather_symbols.weather_string_to_symbol(weather)
        symbol_start = start_x + content_width - 16  # Offset for temperature
        for y, l in enumerate(weather_symbol):
            self._window.addstr(12+y, symbol_start, f"{l:^14}")
        if weather == "":
            weather = "Clear"
        self._window.addstr(17, symbol_start+1, f"{weather:^13}")

        # draw wind info
        wind_label = f"{'Wind':^17}"
        wind_top = f"{calendar_info.weather.wind_direction_short()} {calendar_info.weather.wind_speed_str()}"
        wind_top = f"{wind_top:^17}"
        wind_bot = f"{calendar_info.weather.wind_strength:^17}"

        self._window.addstr(12, start_x, wind_label)
        self._window.addstr(13, start_x, wind_top)
        self._window.addstr(14, start_x, wind_bot)

        # Temperatre
        temp_label = f"{'Temperature':^17}"
        temp_info = f"{calendar_info.weather.get_temperature_str():^17}"

        self._window.addstr(16, start_x, temp_label)
        self._window.addstr(17, start_x, temp_info)

    def draw_event_list(self) -> None:
        """
        Draws the list of events for the day as well as the buttons
        :return: None
        """
        start_y = 19
        start_x = curses.COLS - self._info_panel_width-1

        add_selected = False
        #del_selected = False
        jump_selected = False
        menu_selected = False
        if self._selection_mode == CalendarSelectionMode.EDIT:
            if self._edit_cursor == 0:
                add_selected = True
            #elif self._edit_cursor == 1:
            #    del_selected = True
            elif self._edit_cursor == 1:
                jump_selected = True
            elif self._edit_cursor == 2:
                menu_selected = True

        Button.draw_button(window=self._window, start_y=start_y, start_x=start_x+1, height=3, width=13, text="Add Event", selected=add_selected)
        # Button.draw_button(window=self._window, start_y=start_y+3, start_x=start_x+1, height=3, width=13, text="Del Event", selected=del_selected)
        Button.draw_button(window=self._window, start_y=start_y+3, start_x=start_x+1, height=3, width=13, text="Jump to", selected=jump_selected)
        Button.draw_button(window=self._window, start_y=start_y+6, start_x=start_x+1, height=3, width=13, text="Menu", selected=menu_selected)

        maxwidth = self._info_panel_width - 17

        max_events = curses.LINES-1 - start_y
        # clear out any remaining events
        for y in range(max_events):
            self._window.addstr(start_y+y, start_x+16, " "*maxwidth)

        events = self._calendar.get_time(self._cursor_time).events
        for i, event in enumerate(events):
            if self._selection_mode == CalendarSelectionMode.EVENT and self._event_cursor == i:
                self._window.attron(curses.A_REVERSE)
            self._window.addstr(start_y+i, start_x+16, event.to_string(maxwidth))
            self._window.attroff(curses.A_REVERSE)

    def right(self) -> None:
        """
        Process pressing right
        :return: None
        """
        if self._selection_mode == CalendarSelectionMode.TIME:
            self._selection_mode = CalendarSelectionMode.EDIT
            self.draw_hours()
            self.draw_event_list()
        elif self._selection_mode == CalendarSelectionMode.EDIT and len(self._calendar.get_time(self._cursor_time).events) > 0:
            self._selection_mode = CalendarSelectionMode.EVENT
            self._edit_cursor = 0
            self.draw_event_list()

    def left(self) -> None:
        """
        Process pressing left
        :return: None
        """
        if self._selection_mode == CalendarSelectionMode.EVENT:
            self._selection_mode = CalendarSelectionMode.EDIT
            self._event_cursor = 0
            self.draw_event_list()
        elif self._selection_mode == CalendarSelectionMode.EDIT:
            self._selection_mode = CalendarSelectionMode.TIME
            self._edit_cursor = 0
            self.draw_hours()
            self.draw_event_list()

    def up(self) -> None:
        """
        Process pressing up
        :return: None
        """
        if self._selection_mode == CalendarSelectionMode.TIME:
            self._cursor_time -= 1
            self.draw_hours()
            self.draw_side_panel()
            self.draw_event_list()
        elif self._selection_mode == CalendarSelectionMode.EDIT and self._edit_cursor > 0:
            self._edit_cursor -= 1
            self.draw_event_list()
        elif self._selection_mode == CalendarSelectionMode.EVENT and self._event_cursor > 0:
            self._event_cursor -= 1
            self.draw_event_list()

    def down(self) -> None:
        """
        Process pressing down
        :return: None
        """
        if self._selection_mode == CalendarSelectionMode.TIME:
            self._cursor_time += 1
            self.draw_hours()
            self.draw_side_panel()
            self.draw_event_list()
        elif self._selection_mode == CalendarSelectionMode.EDIT and self._edit_cursor < 2:
            self._edit_cursor += 1
            self.draw_event_list()
        elif self._selection_mode == CalendarSelectionMode.EVENT and len(self._calendar.get_time(self._cursor_time).events) > self._event_cursor+1:
            self._event_cursor += 1
            self.draw_event_list()

    def enter(self) -> None:
        """
        Process pressing enter
        :return: None
        """
        if self._selection_mode == CalendarSelectionMode.EDIT:
            if self._edit_cursor == 0:
                event = EventEditWindow.execute(window_width=curses.COLS-self._info_panel_width-1, start_time=self._cursor_time, calendar_used=self._used_calendar)
                if not event.delete_event:
                    self._calendar.add_event(event)
                self.redraw()
            elif self._edit_cursor == 1:
                date, calendar_name = DatePrompt.execute(self._cursor_time, self._used_calendar)
                self._cursor_time = date
                self._used_calendar = calendar_name
                self.redraw()
            elif self._edit_cursor == 2:
                return 0
        elif self._selection_mode == CalendarSelectionMode.EVENT:
            event = self._calendar.get_time(self._cursor_time).events[self._event_cursor]
            # Remove event during editing and put it back in if not deleted
            self._calendar.remove_event(event)
            event = EventEditWindow.execute(window_width=curses.COLS-self._info_panel_width-1, start_time=event.start_time_epoch, calendar_used=self._used_calendar, event=event)
            if not event.delete_event:
                self._calendar.add_event(event)
            if len(self._calendar.get_time(self._cursor_time).events) == 0:
                self._selection_mode = CalendarSelectionMode.EDIT
                self._event_cursor = 0

            self.redraw()



def main(stdscr):
    curses.noecho()
    curses.curs_set(0)
    curses.cbreak()
    stdscr.nodelay(0)
    stdscr.keypad(True)
    define_colors()
    stdscr.clear()
    calendar = DnDCalendar()
    event = Event("Denford", "This is a test event. Ignore this.", 100000*24+10, 4)
    calendar.add_event(event)
    event = Event("Somewhere", "Derp derp", 100000*24+12, 4)
    calendar.add_event(event)
    win = CalendarWindow(100000*24, calendar)

    while True:
        char = win._window.getch()
        if char == ord('q'): break # q
        elif char == ord('d'): win.right()
        elif char == ord('a'): win.left()
        elif char == ord('w'): win.up()
        elif char == ord('s'): win.down()
        elif char == 10:  win.enter()

if __name__ == "__main__":
    curses.wrapper(main)


