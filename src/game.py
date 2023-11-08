import asyncio
import curses
import itertools
import time
from curses import window
from pathlib import Path
from random import choice, randint
from typing import Any, Coroutine, Final
import uuid
from src import curses_tools, obstacles
from src import physics, utils
from src.debug_messages import print_ship_info
from src.explosion import explode

STAR_SYMBOLS: Final[list[str]] = ['+', '*', '.', ':']
STARS: Final[int] = 400
TIC_TIMEOUT = 0.1
COROS: list[Coroutine[Any, Any, None]] = []

base_path = Path(__file__).parent.resolve()


SPRITES: dict[str, dict[str, Any]] = {
    'ship': {'path': base_path.joinpath('sprites/spacesheep'), 'sprites': {}},
    'garbage': {'path': base_path.joinpath('sprites/garbage'), 'sprites': {}},
    'gameover': {'path': base_path.joinpath('sprites/gameover'), 'sprites': {}},
}

CURRENT_SHIP_FRAME: str | None = None

SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

SHIP_ROW: float = 0
SHIP_COL: float = 0

STEP_DELTA: Final[float] = 1.6
OBSTACLES: list[obstacles.Obstacle] = []
OBSTACLES_IN_LAST_COLLISIONS: list[obstacles.Obstacle] = []


async def fly_garbage(canvas: window, column: int, garbage_frame: str, speed: float = 0.5) -> None:
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row: float = 0

    fig_rows, fig_cols = curses_tools.get_frame_size(garbage_frame)

    obs = obstacles.Obstacle(int(row), int(column), fig_rows, fig_cols, uid=uuid.uuid4())
    OBSTACLES.append(obs)

    while row < rows_number:
        for obstacle in OBSTACLES_IN_LAST_COLLISIONS:
            if obstacle.uid == obs.uid:
                OBSTACLES.remove(obs)
                await explode(canvas, round(row) + (fig_rows // 2) - 1, round(column) + (fig_cols // 2) - 1)
                return

        curses_tools.draw_frame(canvas, row, column, garbage_frame)
        obs.row = int(row)
        await asyncio.sleep(0)
        curses_tools.draw_frame(canvas, row, column, garbage_frame, negative=True)
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
        await utils.delay(20)

        canvas.addstr(row, col, symbol)
        await utils.delay(3)

        canvas.addstr(row, col, symbol, curses.A_BOLD)
        await utils.delay(5)

        canvas.addstr(row, col, symbol)
        await utils.delay(3)

        await utils.delay(randint(1, 50))


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
        _, fig_cols = curses_tools.get_frame_size(fig)
        col_position = randint(0, max_cols - fig_cols)
        COROS.append(fly_garbage(canvas, col_position, fig))
        await utils.delay(randint(1, 30))


async def animate_spaceship() -> None:
    global CURRENT_SHIP_FRAME
    for frame in itertools.cycle(SPRITES['ship']['sprites'].values()):
        CURRENT_SHIP_FRAME = frame
        await utils.delay(2)


def get_row(max_: int) -> int:
    return randint(0, max_ - 1)


def get_col(max_: int) -> int:
    return randint(0, max_ - 1)


def new_position(max_pos: int, frame_size: int, cur_pos: float, delta: float) -> float:
    return max(0.0, min(max_pos - frame_size, cur_pos + delta))


async def move_ship(canvas: window) -> None:
    global SHIP_ROW, SHIP_COL
    col_speed = 0.0
    row_speed = 0.0
    max_rows, max_cols = canvas.getmaxyx()
    while True:
        if not CURRENT_SHIP_FRAME:
            continue
        fig_rows, fig_cols = curses_tools.get_frame_size(CURRENT_SHIP_FRAME)
        for obstacle in OBSTACLES:
            if obstacle.has_collision(round(SHIP_ROW), round(SHIP_COL), fig_rows, fig_cols):
                COROS.append(show_gameover(canvas))
                return

        row_direction, col_direction, is_space = read_controls(canvas)
        _, ship_cols = curses_tools.get_frame_size(CURRENT_SHIP_FRAME)
        if is_space:
            COROS.append(fire(canvas, SHIP_ROW, SHIP_COL + (ship_cols / 2)))

        frame_rows, frame_cols = curses_tools.get_frame_size(CURRENT_SHIP_FRAME)

        row_speed, col_speed = physics.update_speed(
            row_speed, col_speed, row_direction, col_direction  # type: ignore[arg-type]
        )

        SHIP_COL = new_position(max_cols, frame_cols, SHIP_COL, (STEP_DELTA * col_speed))
        SHIP_ROW = new_position(max_rows, frame_rows, SHIP_ROW, (STEP_DELTA * row_speed))

        print_ship_info(canvas, SHIP_ROW, SHIP_COL, row_speed, col_speed, STEP_DELTA)

        curses_tools.draw_frame(canvas, SHIP_ROW, SHIP_COL, CURRENT_SHIP_FRAME)
        prev_frame = CURRENT_SHIP_FRAME
        await asyncio.sleep(0)
        curses_tools.draw_frame(canvas, SHIP_ROW, SHIP_COL, prev_frame, negative=True)


async def show_gameover(canvas: window) -> None:
    text = SPRITES['gameover']['sprites']['gameover']
    while True:
        max_rows, max_cols = canvas.getmaxyx()
        text_row_position: int = max_rows // 2 - len(text.split('\n')) // 2
        text_col_position: int = (max_cols // 2) - (len(text.split('\n', maxsplit=1)[0]) // 2)

        curses_tools.draw_frame(canvas, text_row_position, text_col_position, text)

        await asyncio.sleep(0)


def draw(canvas: window) -> None:
    global COROS, SHIP_ROW, SHIP_COL

    curses.curs_set(False)  # убрать курсор, чтобы не мешал
    canvas.nodelay(True)  # неблокриующий ражим
    COROS = [blink(canvas, get_row(curses.LINES), get_col(curses.COLS), choice(STAR_SYMBOLS)) for _ in range(STARS)]
    SHIP_ROW, SHIP_COL = curses.LINES // 2, curses.COLS // 2

    COROS.append(fill_orbit_with_garbage(canvas))
    COROS.append(animate_spaceship())
    # COROS.append(fire(canvas, curses.LINES // 2, curses.COLS // 2))
    COROS.append(move_ship(canvas))
    COROS.append(fly_garbage(canvas, 10, SPRITES['garbage']['sprites']['duck']))
    # COROS.append(obstacles.show_obstacles(canvas, OBSTACLES))

    while True:
        for coro in COROS.copy():
            try:
                coro.send(None)
            except StopIteration:
                COROS.remove(coro)
        _, columns_number = canvas.getmaxyx()
        canvas.addstr(0, columns_number - 10, f'coros: {len(COROS)}')
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


def main() -> None:
    utils.load_all_sprites(SPRITES)
    curses.update_lines_cols()
    curses.wrapper(draw)


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
        for obstacle in OBSTACLES:
            is_collision = obstacle.has_collision(round(row), round(col))
            if is_collision:
                OBSTACLES_IN_LAST_COLLISIONS.append(obstacle)
                return

        canvas.addstr(round(row), round(col), sym)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(col), ' ')
        await asyncio.sleep(0)
        row += row_delta
        col += col_delta
