import asyncio
import curses
import time
from typing import Final, Optional
from random import choice, random, randint

STAR_SYM: Final[str] = "*"
STAR_SYMBOLS: Final[list[str]] = ["+", "*", ".", ":"]
STARS: Final[int] = 600
TIC_TIMEOUT = 0.1


def draw_sym(
    canvas,
    row: int,
    col: int,
    delay: float,
    effect: int = 0,
    sym: str = STAR_SYM,
):
    canvas.addstr(row, col, sym, effect)
    canvas.refresh()
    time.sleep(delay)


async def blink(canvas, row, column, symbol="*"):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await asyncio.sleep(0)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await asyncio.sleep(0)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        await asyncio.sleep(0)
        for _ in range(3):
            await asyncio.sleep(0)


def main(canvas):
    canvas.border()
    row, column = (3, 9)
    # canvas.addstr(row, column, "Pipa!")
    curses.curs_set(False)
    canvas.refresh()
    blind(canvas)


def get_row(max: int):
    return randint(0, max - 1)


def get_col(max: int):
    return randint(0, max - 1)


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
