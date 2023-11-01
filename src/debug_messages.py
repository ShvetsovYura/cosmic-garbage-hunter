from curses import window


def print_ship_info(
    canvas: window, row: float, col: float, row_speed: float, col_speed: float, step_delta: float
) -> None:
    canvas.addstr(1, 1, f'row speed: {row_speed:.3f}')
    canvas.addstr(2, 1, f'col speed: {col_speed:.3f}')

    canvas.addstr(4, 1, f'row delta: {(step_delta * row_speed):.3f}')
    canvas.addstr(5, 1, f'col delta: {step_delta * col_speed:.3f}')

    canvas.addstr(7, 1, f'row current: {row:.3f}')
    canvas.addstr(8, 1, f'col current: {col:.3f}')
