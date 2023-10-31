import asyncio
import curses
import itertools
import time
from curses import window
from pathlib import Path
from random import choice, randint
from typing import Any, Coroutine, Final

from . import utils

STAR_SYMBOLS: Final[list[str]] = ['+', '*', '.', ':']
STARS: Final[int] = 600
TIC_TIMEOUT = 0.1
COROS: list[Coroutine[Any, Any, None]] = []

base_path = Path(__file__).parent.resolve()


SPRITES: dict[str, dict[str, Any]] = {
    'ship': {'path': base_path.joinpath('sprites/spacesheep'), 'sprites': {}},
    'garbage': {'path': base_path.joinpath('sprites/garbage'), 'sprites': {}},
}

CURRENT_SHIP_FRAME: str | None = None

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

SHIP_ROW: float = 0
SHIP_COL: float = 0

STEP_DELTA = 5


async def delay(tiks: int = 0) -> None:
    for _ in range(tiks):
        await asyncio.sleep(0)


async def fly_garbage(canvas: window, column: int, garbage_frame: str, speed: float = 0.5) -> None:
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row: float = 0

    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


def read_controls(canvas: window) -> tuple[int, int, bool]:
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


async def blink(canvas: window, row: int, col: int, symbol: str = '*') -> None:
    while True:
        canvas.addstr(row, col, symbol, curses.A_DIM)
        await delay(20)

        canvas.addstr(row, col, symbol)
        await delay(3)

        canvas.addstr(row, col, symbol, curses.A_BOLD)
        await delay(5)

        canvas.addstr(row, col, symbol)
        await delay(3)

        await delay(randint(1, 50))


def get_random_garbage() -> str:
    garbage_names: list[str] = list(SPRITES['garbage']['sprites'].keys())
    garbage_name = choice(garbage_names)
    fig: str = SPRITES['garbage']['sprites'][garbage_name]
    return fig


async def fill_orbit_with_garbage(canvas: window) -> None:
    # TODO: Сделать так, чтобы при большом количестве объектов
    # они не накладывались друг на друга
    while True:
        fig = get_random_garbage()
        _, max_cols = canvas.getmaxyx()
        _, fig_cols = get_frame_size(fig)
        col_position = randint(0, max_cols - fig_cols)
        COROS.append(fly_garbage(canvas, col_position, fig))
        await delay(randint(1, 30))


def draw_frame(
    canvas: window,
    start_row: float,
    start_col: float,
    text: str,
    negative: bool = False,
) -> None:
    '''Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified.'''

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_col)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


async def animate_spaceship() -> None:
    global CURRENT_SHIP_FRAME
    for frame in itertools.cycle(SPRITES['ship']['sprites'].values()):
        CURRENT_SHIP_FRAME = frame
        await delay(2)


async def fire(
    canvas: window, start_row: float, start_col: float, row_delta: float = -0.3, col_delta: float = 0.0
) -> None:
    row, col = start_row, start_col
    canvas.addstr(round(row), round(col), '*')
    await delay(0)

    canvas.addstr(round(row), round(col), 'O')
    await delay(0)

    canvas.addstr(round(row), round(col), ' ')
    await delay(0)

    row += row_delta
    col += col_delta

    sym = '-' if col_delta else '|'

    rows, cols = canvas.getmaxyx()
    max_row, max_col = rows - 1, cols - 1

    curses.beep()

    while 0 < row < max_row and 0 < col < max_col:
        canvas.addstr(round(row), round(col), sym)
        await delay(0)
        canvas.addstr(round(row), round(col), ' ')
        await delay(0)
        row += row_delta
        col += col_delta


def get_row(max_: int) -> int:
    return randint(0, max_ - 1)


def get_col(max_: int) -> int:
    return randint(0, max_ - 1)


def get_frame_size(text: str) -> tuple[int, int]:
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])  # pylint:disable=R1728
    return rows, columns


def new_position(max_pos: int, frame_size: int, cur_pos: float, delta: int) -> int:
    return max(0, min(max_pos - frame_size, int(cur_pos) + delta))


async def move_ship(canvas: window) -> None:
    global SHIP_ROW, SHIP_COL

    while True:
        row_direction, col_direction, _ = read_controls(canvas)
        if CURRENT_SHIP_FRAME:
            if row_direction or col_direction:
                max_rows, max_cols = canvas.getmaxyx()
                frame_rows, frame_cols = get_frame_size(CURRENT_SHIP_FRAME)
                SHIP_COL = new_position(max_cols, frame_cols, SHIP_COL, (STEP_DELTA * col_direction))
                SHIP_ROW = new_position(max_rows, frame_rows, SHIP_ROW, (STEP_DELTA * row_direction))

            draw_frame(canvas, SHIP_ROW, SHIP_COL, CURRENT_SHIP_FRAME)
            prev_frame = CURRENT_SHIP_FRAME
            await asyncio.sleep(0)
            draw_frame(canvas, SHIP_ROW, SHIP_COL, prev_frame, negative=True)


def draw(canvas: window) -> None:
    global COROS, SHIP_ROW, SHIP_COL

    curses.curs_set(False)  # убрать курсор, чтобы не мешал
    canvas.nodelay(True)  # неблокриующий ражим
    COROS = [blink(canvas, get_row(curses.LINES), get_col(curses.COLS), choice(STAR_SYMBOLS)) for _ in range(STARS)]
    SHIP_ROW, SHIP_COL = curses.LINES // 2, curses.COLS // 2

    COROS.append(fill_orbit_with_garbage(canvas))
    COROS.append(animate_spaceship())
    COROS.append(fire(canvas, start_row=curses.LINES // 2, start_col=curses.COLS // 2))
    COROS.append(move_ship(canvas))
    COROS.append(fly_garbage(canvas, 10, SPRITES['garbage']['sprites']['duck']))

    while True:
        for coro in COROS.copy():
            try:
                coro.send(None)
            except StopIteration:
                COROS.remove(coro)
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    utils.load_all_sprites(SPRITES)
    curses.update_lines_cols()
    curses.wrapper(draw)