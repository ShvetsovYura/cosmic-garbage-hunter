import asyncio
import curses
import time
from random import choice, randint
from typing import Final

STAR_SYMBOLS: Final[list[str]] = ["+", "*", ".", ":"]
STARS: Final[int] = 400
TIC_TIMEOUT = 0.1


async def blink(canvas, row: int, col: int, symbol: str = "*"):
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


async def fire(
    canvas,
    start_row: float,
    start_col: float,
    row_delta: float = -0.3,
    col_delta: float = 0.0,
) -> None:
    row, col = start_row, start_col
    canvas.addstr(round(row), round(col), "*")
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(col), "O")
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(col), " ")
    await asyncio.sleep(0)

    row += row_delta
    col += col_delta

    sym = "-" if col_delta else "|"

    rows, cols = canvas.getmaxyx()
    max_row, max_col = rows - 1, cols - 1

    curses.beep()

    while 0 < row < max_row and 0 < col < max_col:
        canvas.addstr(round(row), round(col), sym)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(col), " ")
        await asyncio.sleep(0)
        row += row_delta
        col += col_delta


def get_row(max_: int):
    return randint(0, max_ - 1)


def get_col(max_: int):
    return randint(0, max_ - 1)


def draw(canvas):
    curses.curs_set(False)
    coros = [
        blink(canvas, get_row(curses.LINES), get_col(curses.COLS), choice(STAR_SYMBOLS))
        for _ in range(STARS)
    ]
    coros.append(fire(canvas, start_row=curses.LINES // 2, start_col=curses.COLS // 2))
    while True:
        for coro in coros.copy():
            try:
                coro.send(None)
                canvas.refresh()
            except StopIteration:
                coros.remove(coro)
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
