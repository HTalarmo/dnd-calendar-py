import curses
from curses import textpad
from typing import Tuple

from gui_utils import define_colors, draw_box
from reckoninghandler import DnDate, ReckoningHandler

class DatePrompt:
    def __init__(self, init_date: int, init_calendar: str):
        """
        Creates a date prompt for selecting a date
        :param init_date: Initial date to start from
        :param init_calendar: What calendar to use initially
        """
        # created in the center of the screen
        self._window_height = 10
        self._window_width = 46+4
        self._start_x = curses.COLS//2 - self._window_width//2
        self._start_y = curses.LINES//2 - self._window_height//2
        self._window = curses.newwin(self._window_height, self._window_width, self._start_y, self._start_x)
        self._window.attron(curses.color_pair(1))
        self._current_date = init_date
        self._reckoninghandler = ReckoningHandler()
        self._current_calendar_index = self._reckoninghandler.calendar_list.index(init_calendar)

        self._current_selection = 0
        self._year_numbers_entered = 0

        self._label_y_offset = 2
        self._up_arrow_y_offset = 4
        self._down_arrow_y_offset = self._up_arrow_y_offset+2
        self._selection_y_offset = self._up_arrow_y_offset+1

        self._gap_width = 2
        self._calendar_width = 8
        self._day_width = 3
        self._month_width = 5
        self._era_width = 3
        self._year_width = 5
        self._calendar_location_offset = 2+3
        self._day_location_offset = self._calendar_location_offset+self._calendar_width+self._gap_width
        self._month_location_offset = self._day_location_offset + self._day_width + self._gap_width
        self._era_location_offset = self._month_location_offset + self._month_width + self._gap_width
        self._year_location_offset = self._era_location_offset + self._era_width + self._gap_width
        self._accept_location_offset = self._year_location_offset + self._year_width + self._gap_width

    def draw_frame(self) -> None:
        """
        Draw the frame for the prompt (borders and stuff)
        :return: None
        """
        draw_box(self._window, 0, 0, self._window_height, self._window_width)

        self._window.addstr(self._label_y_offset, self._calendar_location_offset, "Calendar")
        self._window.addstr(self._label_y_offset, self._day_location_offset, "Day")
        self._window.addstr(self._label_y_offset, self._month_location_offset, "Month")
        self._window.addstr(self._label_y_offset, self._era_location_offset, "Era")
        self._window.addstr(self._label_y_offset, self._year_location_offset, "Year")

    def draw_selections(self) -> None:
        """
        Draw the selections and arrows
        :return: None
        """
        # clear
        self._window.addstr(self._up_arrow_y_offset, 1, " "*(self._window_width-3))
        self._window.addstr(self._selection_y_offset, 1, " "*(self._window_width-3))
        self._window.addstr(self._down_arrow_y_offset, 1, " "*(self._window_width-3))

        calendar_name = self._reckoninghandler.calendar_list[self._current_calendar_index]
        date_info = self._reckoninghandler.epoch_to_date(self._current_date, calendar_name)

        # Calendar selected
        if self._current_selection == 0:
            if self._current_calendar_index < len(self._reckoninghandler.calendar_list)-1:
                self._window.addstr(self._up_arrow_y_offset, self._calendar_location_offset, f"{'▲':^{self._calendar_width}}")
            if self._current_calendar_index > 0:
                self._window.addstr(self._down_arrow_y_offset, self._calendar_location_offset, f"{'▼':^{self._calendar_width}}")
            self._window.attron(curses.A_REVERSE)
            self._window.addstr(self._selection_y_offset, self._calendar_location_offset, f"{calendar_name:^{self._calendar_width}}")
            self._window.attroff(curses.A_REVERSE)
        else:
            self._window.addstr(self._selection_y_offset, self._calendar_location_offset, f"{calendar_name:^{self._calendar_width}}")

        # Day selected
        if self._current_selection == 1:
            self._window.addstr(self._up_arrow_y_offset, self._day_location_offset, f"{'▲':^{self._day_width}}")
            self._window.addstr(self._down_arrow_y_offset, self._day_location_offset, f"{'▼':^{self._day_width}}")
            self._window.attron(curses.A_REVERSE)
            self._window.addstr(self._selection_y_offset, self._day_location_offset, f"{date_info.day_of_month:^{self._day_width}}")
            self._window.attroff(curses.A_REVERSE)
        else:
            self._window.addstr(self._selection_y_offset, self._day_location_offset, f"{date_info.day_of_month:^{self._day_width}}")

        # month selected
        if self._current_selection == 2:
            self._window.addstr(self._up_arrow_y_offset, self._month_location_offset, f"{'▲':^{self._month_width}}")
            self._window.addstr(self._down_arrow_y_offset, self._month_location_offset, f"{'▼':^{self._month_width}}")
            self._window.attron(curses.A_REVERSE)
            self._window.addstr(self._selection_y_offset, self._month_location_offset, f"{date_info.month_num:^{self._month_width}}")
            self._window.attroff(curses.A_REVERSE)
        else:
            self._window.addstr(self._selection_y_offset, self._month_location_offset, f"{date_info.month_num:^{self._month_width}}")

        # Era selected
        if self._current_selection == 3:
            self._window.addstr(self._up_arrow_y_offset, self._era_location_offset, f"{'▲':^{self._era_width}}")
            self._window.addstr(self._down_arrow_y_offset, self._era_location_offset, f"{'▼':^{self._era_width}}")
            self._window.attron(curses.A_REVERSE)
            self._window.addstr(self._selection_y_offset, self._era_location_offset, f"{date_info.erastring:^{self._era_width}}")
            self._window.attroff(curses.A_REVERSE)
        else:
            self._window.addstr(self._selection_y_offset, self._era_location_offset, f"{date_info.erastring:^{self._era_width}}")

        # Year selected
        if self._current_selection == 4:
            self._window.addstr(self._up_arrow_y_offset, self._year_location_offset, f"{'▲':^{self._era_width}}")
            self._window.addstr(self._down_arrow_y_offset, self._year_location_offset, f"{'▼':^{self._era_width}}")
            self._window.attron(curses.A_REVERSE)
            self._window.addstr(self._selection_y_offset, self._year_location_offset, f"{abs(date_info.year):^{self._year_width}}")
            self._window.attroff(curses.A_REVERSE)
        else:
            self._window.addstr(self._selection_y_offset, self._year_location_offset, f"{abs(date_info.year):^{self._year_width}}")

        # Accept button
        if self._current_selection == 5:
            self._window.attron(curses.A_REVERSE)
            self._window.addstr(self._selection_y_offset, self._accept_location_offset, "Accept")
            self._window.attroff(curses.A_REVERSE)
        else:
            self._window.addstr(self._selection_y_offset, self._accept_location_offset, "Accept")

    def draw_date(self):
        calendar_name = self._reckoninghandler.calendar_list[self._current_calendar_index]
        date_info = self._reckoninghandler.epoch_to_date(self._current_date, calendar_name)
        self._window.addstr(self._selection_y_offset+2, 1, f"{date_info.date_string():^{self._window_width-3}}")

    def down(self):
        current_calendar_name = self._reckoninghandler.calendar_list[self._current_calendar_index]
        # Change calendar
        if self._current_selection == 0:
            if self._current_calendar_index > 0:
                self._current_calendar_index -= 1

        # Change day
        elif self._current_selection == 1:
            self._current_date -= 24

        # Change month
        elif self._current_selection == 2:
            date_info = self._reckoninghandler.epoch_to_date(self._current_date, current_calendar_name)
            if date_info.month_num == 1:
                last_month_num = self._reckoninghandler.months_in_year(current_calendar_name)
            else:
                last_month_num = date_info.month_num-1
            next_month_days = int(self._reckoninghandler.days_in_month(last_month_num, current_calendar_name))
            self._current_date -= next_month_days * 24

        # Change era
        elif self._current_selection == 3:
            date_info = self._reckoninghandler.epoch_to_date(self._current_date, current_calendar_name)
            num_eras = self._reckoninghandler.num_of_eras(current_calendar_name)
            days_in_year = self._reckoninghandler.days_in_year(current_calendar_name)
            if num_eras == 1 and date_info.era == 1:
                self._current_date -= (2*date_info.year-1)*days_in_year*24
            elif num_eras > 1:
                if date_info.era > 1:
                    years_in_last_era = self._reckoninghandler.years_in_era(date_info.era-1, current_calendar_name)
                    if date_info.year > years_in_last_era:
                        self._current_date -= date_info.year*days_in_year*24
                    else:
                        self._current_date -= years_in_last_era*days_in_year*24
                elif date_info.era == 1:
                    self._current_date -= (2*date_info.year-1)*days_in_year*24

        # Change year
        elif self._current_selection == 4:
            days_in_year = self._reckoninghandler.days_in_year(current_calendar_name)*24
            self._current_date -= days_in_year

        self.draw_date()
        self.draw_selections()


    def up(self):
        current_calendar_name = self._reckoninghandler.calendar_list[self._current_calendar_index]
        # Change calendar
        if self._current_selection == 0:
            if self._current_calendar_index < len(self._reckoninghandler.calendar_list)-1:
                self._current_calendar_index += 1

        # Change day
        elif self._current_selection == 1:
            self._current_date += 24

        # Change month
        elif self._current_selection == 2:
            date_info = self._reckoninghandler.epoch_to_date(self._current_date, current_calendar_name)
            this_month_days = int(self._reckoninghandler.days_in_month(date_info.month_num, current_calendar_name))
            self._current_date += this_month_days * 24

        # Change era
        elif self._current_selection == 3:
            date_info = self._reckoninghandler.epoch_to_date(self._current_date, current_calendar_name)
            num_eras = self._reckoninghandler.num_of_eras(current_calendar_name)
            days_in_year = self._reckoninghandler.days_in_year(current_calendar_name)
            if num_eras == 1 and date_info.era == 0:
                self._current_date += (2 * -date_info.year -1) * days_in_year * 24
            elif num_eras > 1:
                if date_info.era < num_eras-1:
                    years_in_next_era = self._reckoninghandler.years_in_era(date_info.era+1, current_calendar_name)
                    years_in_current_era = self._reckoninghandler.years_in_era(date_info.era, current_calendar_name)
                    if date_info.era == 0:
                        if -date_info.year > years_in_next_era:
                            self._current_date += (-date_info.year * days_in_year-1) * 24 + years_in_next_era*days_in_year*24
                        else:
                            self._current_date += (-date_info.year*2-1)*days_in_year*24
                    else:
                        self._current_date += years_in_current_era*days_in_year*24
                elif date_info.era == num_eras-1:
                    self._current_date += 24*days_in_year*self._reckoninghandler.years_in_era(date_info.era, current_calendar_name)

        # Change year
        elif self._current_selection == 4:
            days_in_year = self._reckoninghandler.days_in_year(current_calendar_name)*24
            self._current_date += days_in_year

        self.draw_date()
        self.draw_selections()

    def right(self):
        if self._current_selection < 5:
            self._current_selection += 1
        elif self._current_selection == 5:
            self._current_selection = 0
        self.draw_date()
        self.draw_selections()

    def left(self):
        if self._current_selection > 0:
            self._current_selection -= 1
        elif self._current_selection == 0:
            self._current_selection = 5
        self.draw_date()
        self.draw_selections()

    def enter(self):
        if self._current_selection == 4:
            current_calendar = self._reckoninghandler.calendar_list[self._current_calendar_index]
            date_info = self._reckoninghandler.epoch_to_date(self._current_date, current_calendar)
            self._window.move(self._selection_y_offset, self._year_location_offset)
            curses.curs_set(1)
            pad_window = curses.newwin(1, 6, self._start_y+self._selection_y_offset, self._start_x+self._year_location_offset)
            pad_window.attron(curses.color_pair(1))
            pad = textpad.Textbox(pad_window)
            year = pad.edit(self.enter_is_terminate)
            del pad
            if len(year) > 0:
                is_additive = False
                try:
                    if year.startswith("+") or year.startswith("-"):
                        is_additive = True
                    year = int(year)
                except ValueError:
                    year = date_info.year
                self._year_numbers_entered = 0
                curses.curs_set(0)

                if is_additive:
                    year_difference = year
                else:
                    year_difference = year - date_info.year

                days_in_year = self._reckoninghandler.days_in_year(current_calendar)
                years_in_current_era = self._reckoninghandler.years_in_era(date_info.era, current_calendar)
                if date_info.year + year_difference < 0:
                    year_difference = -(date_info.year - 1)
                    print(date_info.year-1)
                elif date_info.year + year_difference > years_in_current_era > 0:
                    year_difference = self._reckoninghandler.years_in_era(date_info.era, current_calendar) - date_info.year

                self._current_date += year_difference*days_in_year*24

            self.draw_selections()
            self.draw_date()
        elif self._current_selection == 5:
            return self._current_date, self._reckoninghandler.calendar_list[self._current_calendar_index]

        return None

    def enter_is_terminate(self, x):
        if x == 10:
            return 7
        elif x == 8 and self._year_numbers_entered > 0:
            self._year_numbers_entered -= 1
            return x
        elif x == 8 and self._year_numbers_entered <= 0:
            return ""
        elif self._year_numbers_entered < 5:
            self._year_numbers_entered += 1
            return x

    @staticmethod
    def execute(init_date: int, calendar_name: str) -> Tuple[int, str]:
        win = DatePrompt(init_date, calendar_name)
        while True:
            win.redraw()
            char = win._window.getch()
            if char == ord('q'):
                break  # q
            elif char == ord('d'):
                win.right()
            elif char == ord('a'):
                win.left()
            elif char == ord('w'):
                win.up()
            elif char == ord('s'):
                win.down()
            elif char == 10:
                r = win.enter()
                if r is not None:
                    del win
                    return r

    def redraw(self):
        self.draw_frame()
        self.draw_selections()
        self.draw_date()
        self._window.refresh()

def main(stdscr):
    curses.noecho()
    curses.curs_set(0)
    curses.cbreak()
    stdscr.nodelay(0)
    stdscr.keypad(True)
    define_colors()
    stdscr.clear()
    reckoning = ReckoningHandler()
    date = 100000*24
    print(DatePrompt.execute(date, 'human'))

if __name__ == "__main__":
    curses.wrapper(main)