import curses
import curses.textpad

from WeatherGenerator import ClimateData
from gui_utils import draw_box, define_colors, elevation_to_str
import numpy as np


class CampaignNamePrompt:
    def __init__(self):
        self.width = 30
        self.height = 8
        self.start_x = curses.COLS//2 - self.width//2
        self.start_y = curses.LINES//2 - self.height//2
        self.window = curses.newwin(self.height, self.width, self.start_y, self.start_x)
        self.window.attron(curses.color_pair(1))
        self.window.refresh()
        draw_box(self.window)
        self.window.addstr(2, 3, "Enter campaign name: ")
        self.empty_name = "_______________________"
        self.name = ""
        self.chars_entered = 0
        self.max_chars = len(self.empty_name)
        self.selection = 0

    def draw_name(self):
        if len(self.name) == 0:
            self.window.addstr(3, 3, self.empty_name)
        else:
            self.window.addstr(3, 3, f"{self.name:<{self.max_chars}}")

    def draw_selection(self):
        if self.selection == 0:
            self.window.attron(curses.A_REVERSE)
        self.draw_name()
        self.window.attroff(curses.A_REVERSE)

        if self.selection == 1:
            self.window.attron(curses.A_REVERSE)
        self.window.addstr(5, 10, "Accept")
        self.window.attroff(curses.A_REVERSE)

    def enter_is_terminate(self, x):
        if x == 10:
            return 7
        elif x == 8 and self.chars_entered > 0:
            self.chars_entered -= 1
            return x
        elif x == 8 and self.chars_entered <= 0:
            return ""
        elif self.chars_entered < self.max_chars:
            self.chars_entered += 1
            return x

    def up(self):
        if self.selection > 0:
            self.selection -= 1

    def down(self):
        if self.selection < 1:
            self.selection += 1

    def enter(self):
        if self.selection == 0:
            win = curses.newwin(1, self.max_chars+2, self.start_y+3, self.start_x+3)
            win.attron(curses.color_pair(1))
            curses.curs_set(True)
            win.addstr(0, 0, self.name)
            pad = curses.textpad.Textbox(win)
            self.name = pad.edit(self.enter_is_terminate)[:self.max_chars].rstrip()
            curses.curs_set(False)
            del pad
            del win
        else:
            return self.name

    @staticmethod
    def execute():
        prompt = CampaignNamePrompt()
        while True:
            prompt.draw_selection()
            char = prompt.window.getch()
            if char == ord('w'):
                prompt.up()
            elif char == ord('s'):
                prompt.down()
            elif char == 10:
                r = prompt.enter()
                if r is not None:
                    return r

class ClimateAndElevationPrompt:
    def __init__(self, start_climate: str = None, start_elevation: int = None):
        self.width = 36
        self.height = 9
        self.start_x = curses.COLS//2 - self.width//2
        self.start_y = curses.LINES//2 - self.height//2
        self.window = curses.newwin(self.height, self.width, self.start_y, self.start_x)
        self.window.attron(curses.color_pair(1))
        self.window.refresh()
        draw_box(self.window)
        self.window.addstr(2, 3, "Select climate and elevation: ")
        self.selection = 0

        self.climates = ClimateData().climates
        if start_climate is None:
            self.climate_select = 1
        else:
            self.climate_select = int(np.where(self.climates == start_climate)[0])
        self.climate_start_x = 3
        self.climate_width = 9
        self.window.addstr(4, self.climate_start_x, f"{'Climate':^{self.climate_width}}")

        self.elevations = ["Sea level", "Lowlands", "Highlands"]
        if start_elevation is None:
            self.elevation_select = 1
        else:
            elevation_str = elevation_to_str(start_elevation)
            for i in range(len(self.elevations)):
                if self.elevations[i].lower() == elevation_str.lower():
                    self.elevation_select = i
                    break
            else:
                self.elevation_select = 1
        self.elevation_start_x = self.climate_start_x + self.climate_width + 2
        self.elevation_width = 11
        self.window.addstr(4, self.elevation_start_x, f"{'Elevation':^{self.elevation_width}}")

        self.accept_start_x = self.elevation_start_x + self.elevation_width + 2

    def draw_selection(self):
        self.window.addstr(5, 1, " "*30)
        self.window.addstr(7, 1, " "*30)
        if self.selection == 0:
            self.window.addstr(5, self.climate_start_x+self.climate_width//2-1, "▲")
            self.window.addstr(7, self.climate_start_x+self.climate_width//2-1, "▼")
            self.window.attron(curses.A_REVERSE)
        self.window.addstr(6, self.climate_start_x, f"{self.climates[self.climate_select]:^{self.climate_width}}")
        self.window.attroff(curses.A_REVERSE)

        if self.selection == 1:
            self.window.addstr(5, self.elevation_start_x+self.elevation_width//2-1, "▲")
            self.window.addstr(7, self.elevation_start_x+self.elevation_width//2-1, "▼")
            self.window.attron(curses.A_REVERSE)
        self.window.addstr(6, self.elevation_start_x, f"{self.elevations[self.elevation_select]:^{self.elevation_width}}")
        self.window.attroff(curses.A_REVERSE)

        if self.selection == 2:
            self.window.attron(curses.A_REVERSE)
        self.window.addstr(6, self.accept_start_x, "Accept")
        self.window.attroff(curses.A_REVERSE)

    def up(self):
        if self.selection == 0:
            self.climate_select += 1
            if self.climate_select >= len(self.climates):
                self.climate_select = 0
        elif self.selection == 1:
            self.elevation_select += 1
            if self.elevation_select >= len(self.elevations):
                self.elevation_select = 0

    def down(self):
        if self.selection == 0:
            self.climate_select -= 1
            if self.climate_select < 0:
                self.climate_select = len(self.climates)-1
        if self.selection == 1:
            self.elevation_select -= 1
            if self.elevation_select < 0:
                self.elevation_select = len(self.elevations)-1

    def right(self):
        if self.selection < 2:
            self.selection += 1

    def left(self):
        if self.selection > 0:
            self.selection -= 1

    def enter(self):
        if self.selection == 2:
            if self.elevation_select == 0:
                elevation = 500
            elif self.elevation_select == 1:
                elevation = 1500
            else:
                elevation = 6000
            return self.climates[self.climate_select], elevation

    @staticmethod
    def execute(start_climate: str = None, start_elevation: int = None):
        prompt = ClimateAndElevationPrompt(start_climate, start_elevation)
        while True:
            prompt.draw_selection()
            char = prompt.window.getch()
            if char == ord('w'):
                prompt.up()
            elif char == ord('s'):
                prompt.down()
            elif char == ord('a'):
                prompt.left()
            elif char == ord('d'):
                prompt.right()
            elif char == 10:
                r = prompt.enter()
                if r is not None:
                    return r


def main(stdscr):
    curses.noecho()
    curses.curs_set(0)
    curses.cbreak()
    stdscr.nodelay(0)
    stdscr.keypad(True)
    define_colors()
    stdscr.clear()
    print(ClimateAndElevationPrompt.execute())


if __name__ == "__main__":
    curses.wrapper(main)