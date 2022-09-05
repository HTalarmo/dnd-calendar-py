import curses

from WeatherGenerator import ClimateData
from calendarwindow import CalendarWindow
from dndcalendar import DnDCalendar
from gui_utils import draw_box, define_colors, elevation_to_str
import tkinter
from tkinter import filedialog
from dateprompt import DatePrompt
from prompts import ClimateAndElevationPrompt, CampaignNamePrompt
from text_changers import LogoLoader
import json
import numpy as np

class ConfirmDialog:
    def __init__(self, confirm_text: str):
        self.confirm_text = confirm_text
        self._window_width = len(confirm_text)+5
        self._window_height = 7
        self._window = curses.newwin(self._window_height, self._window_width, curses.LINES//2-4, curses.COLS//2-(len(self.confirm_text)+5)//2)
        self._window.attron(curses.color_pair(1))
        draw_box(self._window, 0, 0, 7, len(self.confirm_text)+5)
        s = f"{self.confirm_text:^{len(self.confirm_text)}}"
        self._window.addstr(2, 2, s)
        self._current_selection = 0

        self.draw_selection()

    def draw_selection(self):
        if self._current_selection == 0:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(4, self._window_width//2-8, "Accept")
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 1:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(4, self._window_width//2+2, "Decline")
        self._window.attroff(curses.A_REVERSE)

    def left(self):
        if self._current_selection == 1:
            self._current_selection = 0

    def right(self):
        if self._current_selection == 0:
            self._current_selection = 1

    def enter(self):
        if self._current_selection == 0:
            return True
        else:
            return False

    @staticmethod
    def execute(confirm_text: str):
        win = ConfirmDialog(confirm_text)
        while True:
            win.draw_selection()
            char = win._window.getch()
            if char == ord('a'):
                win.left()
            elif char == ord('d'):
                win.right()
            elif char == 10:
                return win.enter()

class MainMenuWindow:
    def __init__(self):
        """
        Menu that pops up
        Contains:

            Continue

            Change Climate
            Climate

            Change Elevation (500, 1500, 6000)
            Elevation

            Save

            -----

            Start New

            Load

            Exit
        """
        self._window_width = curses.COLS
        self._window_height = curses.LINES
        self._window = curses.newwin(self._window_height,self._window_width, 0, 0)
        self._window.attron(curses.color_pair(1))
        self._cursor = np.array([0, 1])

        self.save_info_height = 13
        self.save_info_width = 29
        self.save_start_x = self._window_width//2+-self.save_info_width//2
        self.save_start_y = 9

        self._save_name = "Campaign"
        self._save_file = ""
        self._calendar: DnDCalendar = None
        self._calendar_win = None
        self._climate_selection = 0
        self._elevation_selection = 0
        self._climates = ClimateData().climates
        self._elevations = ["Sea level", "Lowlands", "Highlands"]

        self.logo = LogoLoader.load_logo("logo.txt")

        self.redraw()

    @property
    def save_loaded(self):
        if self._calendar_win is not None and self._calendar is not None:
            return True
        else:
            return False

    def redraw(self):
        self._window.clear()
        self.draw_frame()
        self.draw_save_info()
        self.draw_selection()
        self._window.refresh()

    def draw_frame(self):
        self._window.clear()
        for i, y in enumerate(range(2, 2+len(self.logo))):
            self._window.addstr(y, 1, f"{self.logo[i]:^{self._window_width-2}}")
        draw_box(self._window, 0, 0, curses.LINES, curses.COLS)
        self._window.refresh()

    def draw_save_info(self):
        draw_box(self._window, start_y=self.save_start_y, start_x=self.save_start_x, window_height=self.save_info_height, window_width=self.save_info_width)
        if self.save_loaded:
            self._window.addstr(self.save_start_y+2, self.save_start_x+3, f"{self._save_name:^{self.save_info_width-6}}")
            date_info = self._calendar.reckoningHandler.epoch_to_date(self._calendar_win._cursor_time, self._calendar_win._used_calendar)
            self._window.addstr(self.save_start_y+4, self.save_start_x+3, f"Date: {date_info.date_string(short=True)}")
            self._window.addstr(self.save_start_y+5, self.save_start_x+3, f"Time: {date_info.time_string()}")
            self._window.addstr(self.save_start_y+7, self.save_start_x+3, f"Climate: {self._calendar.climate}")
            self._window.addstr(self.save_start_y+8, self.save_start_x+3, f"Elevation: {elevation_to_str(self._calendar.elevation)}")
        else:
            self._window.addstr(self.save_start_y+2, self.save_start_x+3, f"{'No save loaded':^{self.save_info_width-6}}")


    def draw_selection(self):
        if self.save_loaded:
            if self._cursor[0] == 0 and self._cursor[1] == 0:
                self._window.attron(curses.A_REVERSE)
            self._window.addstr(self.save_start_y+self.save_info_height-3, self.save_start_x+3, " Save ")
            self._window.attroff(curses.A_REVERSE)

            if self._cursor[0] == 0 and self._cursor[1] == 1:
                self._window.attron(curses.A_REVERSE)
            self._window.addstr(self.save_start_y+self.save_info_height-3, self.save_start_x+10, " Continue ")
            self._window.attroff(curses.A_REVERSE)

            if self._cursor[0] == 1:
                self._window.attron(curses.A_REVERSE)
            self._window.addstr(self.save_start_y + self.save_info_height+1,
                                self.save_start_x + self.save_info_width//2-14, " Change Climate / Elevation ")
            self._window.attroff(curses.A_REVERSE)

        if self._cursor[0] == 0 and (self._cursor[1] == 2 or not self.save_loaded):
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(self.save_start_y+self.save_info_height-3, self.save_start_x+self.save_info_width-9, " Load ")
        self._window.attroff(curses.A_REVERSE)

        if self._cursor[0] == 2:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(self.save_start_y+self.save_info_height+3, self.save_start_x+self.save_info_width//2-7, " New Campaign ")
        self._window.attroff(curses.A_REVERSE)

        if self._cursor[0] == 3:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(self.save_start_y+self.save_info_height+5, self.save_start_x+self.save_info_width//2-3, " Exit ")
        self._window.attroff(curses.A_REVERSE)

    def start_new(self):
        # Query for campaign name
        self._save_name = CampaignNamePrompt.execute()
        self.draw_frame()

        # Select start date
        start_time, calendar_name = DatePrompt.execute(100000, 'human')
        self.draw_frame()

        # Select climate
        prompt_result = ClimateAndElevationPrompt.execute()
        climate = str(prompt_result[0])
        elevation = int(prompt_result[1])
        self._climate_selection = int(np.where(self._climates == climate)[0])
        if elevation < 1000:
            self._elevation_selection = 0
        elif elevation < 5000:
            self._elevation_selection = 1
        else:
            self._elevation_selection = 2

        self._calendar = DnDCalendar(climate=climate, elevation=elevation)
        self._calendar_win = CalendarWindow(start_time, self._calendar)
        self._calendar_win._used_calendar = calendar_name

    def load_campaign(self):
        f = filedialog.askopenfile()
        if f is not None:
            data = json.load(f)
            self._save_name = data['save_name']
            self._calendar = DnDCalendar.from_json(data['calendar'])
            self._climates = self._calendar.get_climates()
            self._calendar_win = CalendarWindow(data['current_time'], self._calendar)
            self._calendar_win._used_calendar = data['calendar_used']
            f.close()
            self.run_calendar()

    def save_campaign(self):
        data = {}
        data['calendar'] = self._calendar.to_json()
        data['save_name'] = self._save_name
        data['current_time'] = int(self._calendar_win._cursor_time)
        data['calendar_used'] = self._calendar_win._used_calendar
        f = filedialog.asksaveasfile()
        if f is not None:
            json.dump(data, f)
        f.close()

    def continue_campaign(self):
        self.run_calendar()

    def query_directory(self):
        tkinter.Tk().withdraw()
        return filedialog.askopenfilename()

    def down(self):
        if self._cursor[0] == 0:
            if self.save_loaded:
                self._cursor[0] = 1
            else:
                self._cursor[0] = 2
            self._cursor[1] = 1
        elif 3 > self._cursor[0] > 0:
            self._cursor[0] += 1

    def up(self):
        if self._cursor[0] == 3:
            self._cursor[0] = 2
        elif self._cursor[0] == 2:
            if self.save_loaded:
                self._cursor[0] = 1
            else:
                self._cursor[0] = 0
        elif self._cursor[0] == 1:
            self._cursor[0] = 0

    def right(self):
        if self.save_loaded and self._cursor[0] == 0 and self._cursor[1] < 2:
            self._cursor[1] += 1

    def left(self):
        if self.save_loaded and self._cursor[0] == 0 and self._cursor[1] > 0:
            self._cursor[1] -= 1


    def run_calendar(self):
        while True:
            self._calendar_win.redraw()
            char = self._calendar_win._window.getch()
            if char == ord('d'):
                self._calendar_win.right()
            elif char == ord('a'):
                self._calendar_win.left()
            elif char == ord('w'):
                self._calendar_win.up()
            elif char == ord('s'):
                self._calendar_win.down()
            elif char == 10:
                r = self._calendar_win.enter()
                if r is not None:
                    break

    def enter(self):
        if self._cursor[0] == 3:
            exit()
        elif self._cursor[0] == 2:
            self.start_new()
            self.run_calendar()
        elif self._cursor[0] == 1:
            result = ClimateAndElevationPrompt.execute(self._calendar.climate, self._calendar.elevation)
            climate = str(result[0])
            elevation = int(result[1])
            print(climate, elevation)
            if climate != self._calendar.climate:
                self._calendar.change_climate(new_climate_start_time=self._calendar_win._cursor_time, new_climate=climate)
            if elevation_to_str(elevation) != elevation_to_str(self._calendar.elevation):
                self._calendar.change_elevation(new_elevation_start_time=self._calendar_win._cursor_time, new_elevation=elevation)
        elif self._cursor[0] == 0:
            if self.save_loaded:
                if self._cursor[1] == 0:
                    self.save_campaign()
                elif self._cursor[1] == 1:
                    self.continue_campaign()
                elif self._cursor[1] == 2:
                    self.load_campaign()
            else:
                self.load_campaign()
        self.redraw()


def main(stdscr):
    if curses.LINES < 29 or curses.COLS < 100:
        print("ERROR!")
        print("Required terminal size: 29, 100")
        print(f"Detected terminal size: {curses.LINES}, {curses.COLS}")
        exit()
    curses.noecho()
    curses.curs_set(0)
    curses.cbreak()
    stdscr.nodelay(0)
    stdscr.keypad(True)
    define_colors()
    stdscr.clear()
    win = MainMenuWindow()
    while True:
        win.redraw()
        char = win._window.getch()
        if char == ord('w'):
            win.up()
        elif char == ord('s'):
            win.down()
        elif char == ord('a'):
            win.left()
        elif char == ord('d'):
            win.right()
        elif char == 10:
            win.enter()

if __name__ == "__main__":
    tkinter.Tk().withdraw()
    curses.wrapper(main)
