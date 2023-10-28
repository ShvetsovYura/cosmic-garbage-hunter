import asyncio
import curses
import time
from random import choice, randint
from typing import Final

STAR_SYMBOLS: Final[list[str]] = ["+", "*", ".", ":"]
STARS: Final[int] = 600
TIC_TIMEOUT = 0.1


async def blink(canvas, row: int, col: int, symbol: str = "*"):
    while True:
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
    while True:
        for coro in coros.copy():
            coro.send(None)
            canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
