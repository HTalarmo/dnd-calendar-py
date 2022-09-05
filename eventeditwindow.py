import curses
from curses import textpad

from reckoninghandler import ReckoningHandler
from dndcalendar import Event, DnDCalendar
from gui_utils import draw_box, define_colors


class EventEditWindow:
    def __init__(self,  window_width: int, start_time: int, calendar_used: str, event: Event = None):
        self._window_width = window_width
        self._window = curses.newwin(curses.LINES, window_width, 0, 0)
        self._window.attron(curses.color_pair(1))
        self._current_selection = 1
        self._accept_select = 0
        self._calendar_used = calendar_used
        self._recokiningHandler = ReckoningHandler()
        if event is None:
            self._event = Event(location="....", start_time_epoch=start_time, duration=0, description="....")
            self._event.delete_event = True
        else:
            self._event = event

        self._max_description_lines = curses.LINES - 2 - 7 -2
        self._description_maxwidth = self._window_width-2-4
        self._description_max_input_size = self._max_description_lines*self._description_maxwidth-1
        self._location_maxlength = self._window_width-12-4
        self._location_input_length = len(self._event.location)
        self._description_input_length = len(self._event.description)

        self.redraw()

    def redraw(self):
        self.draw_frame()
        self.draw_selection()
        self._window.refresh()

    def draw_frame(self):
        draw_box(self._window, 0, 0, curses.LINES, self._window_width)

        for y in range(1, curses.LINES-1):
            self._window.addstr(y, 1, " "*(self._window_width-3))

        self._window.addstr(3, 2, "Location:                      ")
        self._window.addstr(4, 2, "Start Day:                     ")
        self._window.addstr(5, 2, "Start time:                    ")
        self._window.addstr(6, 2, "Duration:                      ")
        self._window.addstr(8, 2, "Description:                   ")
        for x in range(1, self._window_width-2):
            self._window.addch(9, x, "┅")

    def draw_selection(self):
        date_info = self._recokiningHandler.epoch_to_date(self._event.start_time_epoch, self._calendar_used)
        if self._current_selection == 0 and self._accept_select == 0:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(1, 2, "Accept")
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 0 and self._accept_select == 1:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(1, 12, "Cancel")
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 0 and self._accept_select == 2:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(1, 22, "Delete")
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 1:
            self._window.attron(curses.A_REVERSE)
        if len(self._event.location) == 0:
            self._window.addstr(3, 12, "    ")
        else:
            self._window.addstr(3, 12, self._event.location)
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 2:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(4, 13, f"{date_info.date_string(short=True)}")
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 3:
            self._window.attron(curses.A_REVERSE)
        self._window.addstr(5, 14, f"{date_info.time_string()}")
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 4:
            self._window.attron(curses.A_REVERSE)
        duration_str = ""
        days = self._event.duration // 24
        hours = self._event.duration % 24
        if days > 0:
            duration_str += f"{days} days "
        if hours > 0:
            duration_str += f"{hours} hours"
        self._window.addstr(6, 12, f"{duration_str}")
        self._window.attroff(curses.A_REVERSE)

        if self._current_selection == 5:
            self._window.attron(curses.A_REVERSE)
        chunk_width = self._description_maxwidth
        split_description = [self._event.description[i: i + chunk_width] for i in
                             range(0, len(self._event.description), chunk_width)]
        split_description = split_description[:self._max_description_lines]
        for y in range(self._max_description_lines):
            if len(split_description) > y:
                self._window.addstr(10+y, 2, f"{split_description[y]:<{chunk_width}}")
            else:
                self._window.attroff(curses.A_REVERSE)
                self._window.addstr(10+y, 2, " "*chunk_width)
        self._window.attroff(curses.A_REVERSE)

    def location_enter_is_terminate(self, x: int):
        if x == 10:
            return 7
        elif x == 8 and self._location_input_length > 0:
            self._location_input_length -= 1
            return x
        elif x == 8 and self._location_input_length <= 0:
            return ""
        elif self._location_input_length < self._location_maxlength:
            self._location_input_length += 1
            return x

    def description_enter_is_terminate(self, x: int):
        if x == 10:
            return 7
        elif x == 8 and self._description_input_length > 0:
            self._description_input_length -= 1
            return x
        elif x == 8 and self._description_input_length <= 0:
            return ""
        elif self._description_input_length < self._description_maxwidth*self._max_description_lines:
            self._description_input_length += 1
            return x


    def up(self):
        if self._current_selection > 0:
            self._current_selection -= 1

    def down(self):
        if self._current_selection < 5:
            self._current_selection += 1

    def left(self):
        if self._current_selection == 0 and self._accept_select > 0:
            self._accept_select -= 1
        elif self._current_selection == 2:
            self._event.start_time_epoch -= 24
        elif self._current_selection == 3:
            self._event.start_time_epoch -= 1
        elif self._current_selection == 4 and self._event.duration > 1:
            self._event.duration -= 1

    def right(self):
        if self._current_selection == 0 and self._accept_select < 2:
            self._accept_select += 1
        elif self._current_selection == 2:
            self._event.start_time_epoch += 24
        elif self._current_selection == 3:
            self._event.start_time_epoch += 1
        elif self._current_selection == 4:
            self._event.duration += 1

    def enter(self):
        if self._current_selection == 1:
            self._window.move(1, 12)
            curses.curs_set(True)
            pad_window = curses.newwin(1, self._window_width-12-2, 3, 12)
            pad_window.attron(curses.color_pair(1))
            pad_window.move(0, 0)
            pad_window.addstr(self._event.location)
            pad = textpad.Textbox(pad_window)
            result = pad.edit(self.location_enter_is_terminate)
            del pad
            curses.curs_set(False)
            self._event.location = result[:self._location_maxlength]
        elif self._current_selection == 5:
            self._description_input_length = len(self._event.description)
            curses.curs_set(True)
            pad_window = curses.newwin(self._max_description_lines, self._description_maxwidth, 10, 2)
            pad_window.attron(curses.color_pair(1))
            pad_window.move(0, 0)
            split_description = [self._event.description[i: i + self._description_maxwidth] for i in
                                 range(0, len(self._event.description), self._description_maxwidth)]
            for y, row in enumerate(split_description):
                pad_window.addstr(0+y, 0, row)
            pad = textpad.Textbox(pad_window)
            result = pad.edit(self.description_enter_is_terminate)
            del pad
            curses.curs_set(False)
            self._event.description = "".join(result.splitlines())[:self._description_max_input_size]
        elif self._current_selection == 0:
            if self._accept_select == 0:
                self._event.delete_event = False
            elif self._accept_select == 2:
                self._event.delete_event = True
            return self._event

        return None

    @staticmethod
    def execute(window_width: int, start_time: int, calendar_used: str, event: Event = None):
        win = EventEditWindow(window_width, start_time, calendar_used, event)
        while True:
            win.redraw()
            char = win._window.getch()
            if char == 10:
                r = win.enter()
                if r is not None:
                    return r
            elif char == ord('w'): win.up()
            elif char == ord('s'): win.down()
            elif char == ord('a'): win.left()
            elif char == ord('d'): win.right()


def main(stdscr):
    curses.noecho()
    curses.curs_set(0)
    curses.cbreak()
    stdscr.nodelay(0)
    stdscr.keypad(True)
    define_colors()
    stdscr.clear()
    calendar = DnDCalendar()
    event = Event("Denford", "This is a test event. Ignore this.", 100000*24, 4)
    calendar.add_event(event)
    event = Event("Somewhere", "Derp derp", 100000*24+2, 4)
    calendar.add_event(event)
    print(EventEditWindow.execute(50, 100000*24, 'human'))

if __name__ == "__main__":
    curses.wrapper(main)