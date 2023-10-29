import asyncio
import curses
import itertools
import os
import time
from curses import window
from pathlib import Path
from random import choice, randint
from typing import Final

STAR_SYMBOLS: Final[list[str]] = ['+', '*', '.', ':']
STARS: Final[int] = 200
TIC_TIMEOUT = 0.1
spacesheep_frames: list[str] = []
spacesheep_frames_path = Path(__file__).parent.resolve() / 'sprites/spacesheep'
CURRENT_SHIP_FRAME: str | None = None

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

SHIP_ROW: float = 0
SHIP_COL: float = 0

STEP_DELTA = 10


def read_sprites() -> None:
    if not spacesheep_frames_path.exists():
        raise FileNotFoundError(spacesheep_frames_path)
    for _, _, filenames in os.walk(spacesheep_frames_path):
        for filename in filenames:
            file_ = spacesheep_frames_path.joinpath(filename)
            if file_.exists() and file_.is_file():
                with open(file_, mode='r', encoding='utf-8') as frame:
                    spacesheep_frames.append(frame.read())


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
        for _ in range(randint(1, 10)):
            await asyncio.sleep(0)

        canvas.addstr(row, col, symbol, curses.A_DIM)
        await asyncio.sleep(0)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, col, symbol)
        await asyncio.sleep(0)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, col, symbol, curses.A_BOLD)
        await asyncio.sleep(0)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, col, symbol)
        await asyncio.sleep(0)
        for _ in range(3):
            await asyncio.sleep(0)

        for _ in range(randint(1, 100)):
            await asyncio.sleep(0)


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


async def delay(count: int) -> None:
    for _ in range(count):
        await asyncio.sleep(0)


async def animate_spaceship() -> None:
    global CURRENT_SHIP_FRAME
    for frame in itertools.cycle(spacesheep_frames):
        CURRENT_SHIP_FRAME = frame
        await delay(2)


async def fire(
    canvas: window, start_row: float, start_col: float, row_delta: float = -0.3, col_delta: float = 0.0
) -> None:
    row, col = start_row, start_col
    canvas.addstr(round(row), round(col), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(col), 'O')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(col), ' ')
    await asyncio.sleep(0)

    row += row_delta
    col += col_delta

    sym = '-' if col_delta else '|'

    rows, cols = canvas.getmaxyx()
    max_row, max_col = rows - 1, cols - 1

    curses.beep()

    while 0 < row < max_row and 0 < col < max_col:
        canvas.addstr(round(row), round(col), sym)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(col), ' ')
        await asyncio.sleep(0)
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


async def move_ship(canvas: window) -> None:
    global SHIP_ROW, SHIP_COL

    while True:
        row_direction, col_direction, _ = read_controls(canvas)
        if CURRENT_SHIP_FRAME:
            if row_direction or col_direction:
                max_rows, max_cols = canvas.getmaxyx()
                frame_rows, frame_cols = get_frame_size(CURRENT_SHIP_FRAME)

                if col_direction > 0:
                    next_right_pos = SHIP_COL + frame_cols + STEP_DELTA
                    if next_right_pos >= max_cols:
                        SHIP_COL = max_cols - frame_cols
                    else:
                        SHIP_COL = SHIP_COL + STEP_DELTA
                elif col_direction < 0:
                    SHIP_COL = max(0, SHIP_COL - STEP_DELTA)

                if row_direction > 0:
                    next_down_pos = SHIP_ROW + frame_rows + STEP_DELTA
                    if next_down_pos >= max_rows:
                        SHIP_ROW = max_rows - frame_rows
                    else:
                        SHIP_ROW = SHIP_ROW + STEP_DELTA
                elif row_direction < 0:
                    SHIP_ROW = max(0, SHIP_ROW - STEP_DELTA)

            draw_frame(canvas, SHIP_ROW, SHIP_COL, CURRENT_SHIP_FRAME)
            prev_frame = CURRENT_SHIP_FRAME
            await asyncio.sleep(0)
            draw_frame(canvas, SHIP_ROW, SHIP_COL, prev_frame, negative=True)


def draw(canvas: window) -> None:
    curses.curs_set(False)  # убрать курсор, чтобы не мешал
    canvas.nodelay(True)  # неблокриующий ражим
    coros = [blink(canvas, get_row(curses.LINES), get_col(curses.COLS), choice(STAR_SYMBOLS)) for _ in range(STARS)]
    global SHIP_ROW, SHIP_COL
    SHIP_ROW, SHIP_COL = curses.LINES // 2, curses.COLS // 2
    coros.append(animate_spaceship())
    coros.append(fire(canvas, start_row=curses.LINES // 2, start_col=curses.COLS // 2))
    coros.append(move_ship(canvas))
    while True:
        for coro in coros.copy():
            try:
                coro.send(None)
                canvas.refresh()

            except StopIteration:
                coros.remove(coro)
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    read_sprites()
    curses.update_lines_cols()
    curses.wrapper(draw)
