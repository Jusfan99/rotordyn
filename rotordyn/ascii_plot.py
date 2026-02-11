"""ASCII mode shape plot matching ROTCO rout format.

80-column × 21-row grid, Y range [-1.0, +1.0], symbols:
  X = displacement point
  B = bearing location
  J = bearing journal (on zero line)
"""

from .engine import ModeResult


# Plot dimensions
PLOT_WIDTH = 81     # characters wide (including Y-axis labels)
PLOT_HEIGHT = 21    # rows for displacement range -1.0 to +1.0
DATA_WIDTH = 71     # columns available for data (after Y-axis label)
Y_MIN = -1.0
Y_MAX = 1.0
Y_TICKS = [1.0, 0.75, 0.5, 0.25, 0.0, -0.25, -0.5, -0.75, -1.0]


def generate_ascii_plot(mode: ModeResult, total_length: float) -> str:
    """Generate ASCII mode shape plot."""
    lines = []

    # Build a 2D character grid
    n_rows = PLOT_HEIGHT * 2 + 1  # each major division = 5 rows (4 between ticks + 1 tick)
    # Actually: 8 major divisions (from -1 to +1 in 0.25 steps) = 9 tick marks
    # 4 rows between each tick = 8*4 = 32 internal + 9 tick rows = 41
    # Simpler: use exactly 41 rows

    n_rows = 41  # 0.05 per row, from +1.0 (row 0) to -1.0 (row 40)
    n_cols = DATA_WIDTH  # data columns

    # Initialize grid with spaces
    grid = [[' '] * n_cols for _ in range(n_rows)]

    # Y value to row index
    def y_to_row(y: float) -> int:
        # y=+1.0 -> row 0, y=-1.0 -> row 40
        row = int(round((Y_MAX - y) / (Y_MAX - Y_MIN) * (n_rows - 1)))
        return max(0, min(n_rows - 1, row))

    # X position to column
    def x_to_col(length: float) -> int:
        if total_length <= 0:
            return 0
        col = int(round(length / total_length * (n_cols - 1)))
        return max(0, min(n_cols - 1, col))

    # Plot tick marks on grid (+)
    for y_tick in Y_TICKS:
        row = y_to_row(y_tick)
        for col_idx in range(0, n_cols, 10):
            grid[row][col_idx] = '+'
        # Fill horizontal lines with dashes at major ticks
        for col_idx in range(n_cols):
            if grid[row][col_idx] == ' ':
                grid[row][col_idx] = '-'

    # Vertical border lines at col 0 and col n_cols-1
    for r in range(n_rows):
        if grid[r][0] != '+':
            grid[r][0] = '|'
        if grid[r][n_cols - 1] != '+':
            grid[r][n_cols - 1] = '|'

    # Collect bearing positions and journal zero-crossing positions
    bearing_cols = set()
    journal_cols = set()
    for st in mode.stations:
        if st['type'] == 'bearing_jnl':
            col = x_to_col(st['length'])
            bearing_cols.add(col)
            journal_cols.add(col)

    # Plot displacement curve
    for st in mode.stations:
        if st['type'] == 'bearing_jnl':
            continue
        col = x_to_col(st['length'])
        row = y_to_row(st['displacement'])
        if col in bearing_cols:
            grid[row][col] = 'B'
        else:
            grid[row][col] = 'X'

    # Place J at zero line for journals
    zero_row = y_to_row(0.0)
    for col in journal_cols:
        grid[zero_row][col] = 'J'

    # Build output with Y-axis labels
    label_width = 6  # e.g. " 1.0 " or "-.25 "
    output_lines = []

    for r in range(n_rows):
        y_val = Y_MAX - r * (Y_MAX - Y_MIN) / (n_rows - 1)
        # Determine if this is a labeled tick row
        is_tick = any(abs(y_val - yt) < 0.001 for yt in Y_TICKS)

        if is_tick:
            if abs(y_val) < 0.001:
                label = " 0.  "
            elif abs(y_val) >= 1.0:
                label = f"{y_val:4.1f} "
            else:
                if y_val > 0:
                    label = f" {y_val:.2f} "
                else:
                    label = f"{y_val:.2f} "
        else:
            label = "      "

        row_str = ''.join(grid[r])
        output_lines.append(f"{label}{row_str}")

    return '\n'.join(output_lines)
