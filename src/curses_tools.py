import asyncio
from curses import window
import curses


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


async def fire(
    canvas: window, start_row: float, start_col: float, row_delta: float = -0.9, col_delta: float = 0.0
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
