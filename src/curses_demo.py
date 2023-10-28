import asyncio
import curses
import itertools
import os
import time
from curses import window
from pathlib import Path
from random import choice, randint
from typing import Final

STAR_SYMBOLS: Final[list[str]] = ["+", "*", ".", ":"]
STARS: Final[int] = 200
TIC_TIMEOUT = 0.1
spacesheep_frames = []
spacesheep_frames_path = Path(__file__).parent.resolve() / "sprites/spacesheep"


def read_sprites() -> None:
    if not spacesheep_frames_path.exists():
        raise FileNotFoundError(spacesheep_frames_path)
    for dirpath, dirname, filenames in os.walk(spacesheep_frames_path):
        for filename in filenames:
            file_ = spacesheep_frames_path.joinpath(filename)
            if file_.exists() and file_.is_file():
                with open(file_, mode="r", encoding="utf-8") as frame:
                    spacesheep_frames.append(frame.read())


async def blink(canvas: window, row: int, col: int, symbol: str = "*") -> None:
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

        for _ in range(randint(10, 100)):
            await asyncio.sleep(0)


def draw_frame(
    canvas: window,
    start_row: float,
    start_col: float,
    text: str,
    negative: bool = False,
) -> None:
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

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

            if symbol == " ":
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else " "
            canvas.addch(row, column, symbol)


async def delay(count: int) -> None:
    for _ in range(count):
        await asyncio.sleep(0)


async def animate_spaceship(canvas: window, row: float, col: float) -> None:
    for frame in itertools.cycle(spacesheep_frames):
        draw_frame(canvas, row, col, frame)
        await delay(2)
        draw_frame(canvas, row, col, frame, negative=True)


def get_row(max_: int):
    return randint(0, max_ - 1)


def get_col(max_: int):
    return randint(0, max_ - 1)


def draw(canvas: window):
    curses.curs_set(False)
    # coros = []
    coros = [
        blink(canvas, get_row(curses.LINES), get_col(curses.COLS), choice(STAR_SYMBOLS))
        for _ in range(STARS)
    ]
    coros.append(animate_spaceship(canvas, curses.LINES // 2, curses.COLS // 2))
    while True:
        for coro in coros.copy():
            coro.send(None)
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    read_sprites()
    curses.update_lines_cols()
    curses.wrapper(draw)
