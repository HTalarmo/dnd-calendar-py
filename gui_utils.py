import curses

def define_colors():
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK) # Main color
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_RED) # highlight color

def elevation_to_str(elevation: int) -> str:
    if elevation < 0:
        return "Underground"
    elif elevation < 1000:
        return "Sea level"
    elif elevation < 5000:
        return "Lowlands"
    else:
        return "Highlands"

def str_to_elevation(elevation_str: str) -> int:
    if elevation_str.lower() == "underground":
        return -100
    elif elevation_str.lower() == "sea level":
        return 500
    elif elevation_str.lower() == "lowlands":
        return 1500
    else:
        return 6000

def draw_box(window, start_y: int = None, start_x: int = None, window_height: int = None, window_width: int = None):
    """
    Draws a box on the given window. If no details given, will automatically make it as big as it can
    :param window: Window
    :param start_y: Start y-coordinate
    :param start_x: Start x-coordinate
    :param window_height: Box height
    :param window_width: Box width
    :return:
    """
    if start_x is None:
        start_x = 0
    if start_y is None:
        start_y = 0
    if window_height is None:
        window_height = window.getmaxyx()[0]
    if window_width is None:
        window_width = window.getmaxyx()[1]

    # top and bottom
    for x in range(start_x, start_x+window_width - 1):
        window.addch(start_y, x, "═")
        window.addch(start_y+window_height - 1, x, "═")
    # Sides
    for y in range(start_y, start_y+window_height):
        window.addch(y, start_x, "║")
        window.addch(y, start_x+window_width - 2, "║")

    # corners
    window.addch(start_y, start_x, "╔")
    window.addch(start_y, start_x+window_width - 2, "╗")
    window.addch(start_y+window_height - 1, start_x, "╚")
    window.addch(start_y+window_height - 1, start_x+window_width - 2, "╝")

class Button:
    @staticmethod
    def draw_button(window, start_y: int, start_x: int, height: int, width: int, text: str, selected: bool = False,
                    border:bool = True):
        if selected:
            window.attron(curses.A_REVERSE)
        if border:
            for x in range(width):
                window.addch(start_y, start_x+x, "─")
                window.addch(start_y+height-1, start_x+x, "─")
                for y in range(1, height-1):
                    window.addch(start_y+y, start_x+x, " ")
            for y in range(height):
                window.addch(start_y+y, start_x, "│")
                window.addch(start_y+y, start_x+width-1, "│")
            window.addch(start_y, start_x, "┌")
            window.addch(start_y, start_x+width-1, "┐")
            window.addch(start_y+height-1, start_x, "└")
            window.addch(start_y+height-1, start_x+width-1, "┘")
        text_x = start_x + (width)//2 - len(text)//2
        text_y = start_y + height//2
        window.addstr(text_y, text_x, text)
        if selected:
            window.attroff(curses.A_REVERSE)