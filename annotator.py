import numpy as np
import pandas as pd
from nicegui import app, ui


def main_ui(rows, cols):
    matrix = np.ones((rows, cols), dtype=int)
    colors = ["yellow", "green", "red"]

    # Function to place elements in the matrix
    with ui.row(align_items="center"):
        h_space = 2
        v_space = 2
        ui.label("Space between elements:")
        ui.number(
            label="Horizontal space", value=h_space, min=0, max=10, step=1
        ).bind_value(globals(), "h_space")
        ui.number(
            label="Vertical space", value=v_space, min=0, max=10, step=1
        ).bind_value(globals(), "v_space")
        ui.button("Place", on_click=lambda: place(h_space, v_space))
    ui.separator()

    # Build the matrix interface
    buttons = [[None for _ in range(matrix.shape[1])] for _ in range(matrix.shape[0])]
    with ui.grid(rows=matrix.shape[0] + 1, columns=matrix.shape[1] + 1):
        # Header
        ui.label("")
        for i in range(matrix.shape[0]):
            ui.label(f"Column {i}")
        # Body
        for row in range(matrix.shape[0]):
            for column in range(matrix.shape[1] + 1):
                if column == 0:
                    ui.label(f"Row {row}")
                    continue
                column -= 1
                button = ui.button(
                    matrix[row, column], color=colors[matrix[row, column]]
                )
                button.on_click(
                    lambda button=button, i=row, j=column: update_matrix(button, i, j)
                )
                buttons[row][column] = button

    # Function to update the matrix when an input changes
    def update_matrix(button, row, col):
        matrix[row, col] += 1
        matrix[row, col] %= 3
        button.set_text(matrix[row, col])
        # Set color based on the mapping {0: yellow, 1: green, 2: red}
        button.props(f"color={colors[matrix[row, col]]}")

    # Function to place elements in the matrix
    def place(h_space, v_space):
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if i % (v_space + 1) == 0 and j % (h_space + 1) == 0:
                    if matrix[i, j] != 0:
                        update_matrix(buttons[i][j], i, j)


if __name__ in {"__main__", "__mp_main__"}:
    with ui.dialog().props("persistent") as dialog, ui.card():
        rows, cols = 10, 10
        with ui.row():
            ui.number(
                label="Rows", value=rows, min=1, max=100, step=1, precision=0
            ).bind_value(globals(), "rows")
            ui.number(
                label="Columns", value=cols, min=1, max=100, step=1, precision=0
            ).bind_value(globals(), "cols")
            ui.button("OK").on_click(lambda: dialog.submit((rows, cols)))

    async def show_welcome_message():
        await dialog
        main_ui(int(rows), int(cols))

    app.on_startup(show_welcome_message)

    ui.run(show_welcome_message=True)
