from pathlib import Path

import numpy as np
from nicegui import app, ui

colors = {1: "green", 0: "grey", -1: "red"}


# Function to update the matrix when an input changes
def update_matrix(matrix, button, row, col):
    new_val = matrix[row, col] + 1
    matrix[row, col] = new_val if new_val <= 1 else -1
    button.set_text(matrix[row, col])
    button.props(f"color={colors[matrix[row, col]]}")


def main_ui():
    @ui.refreshable
    def matrix_ui(matrix=np.zeros((1, 1), dtype=int)):
        # Build the matrix interface
        buttons = [
            [None for _ in range(matrix.shape[1])] for _ in range(matrix.shape[0])
        ]
        with ui.grid(rows=matrix.shape[0] + 1, columns=matrix.shape[1] + 1):
            ui.notify(f"Matrix shape: {matrix.shape}")
            # Header
            ui.label("")
            for i in range(matrix.shape[1]):
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
                        lambda button=button, i=row, j=column: update_matrix(
                            matrix, button, i, j
                        )
                    )
                    buttons[row][column] = button

        with ui.row(align_items="center"):
            filename = ui.input("Save as", placeholder="room name")
            ui.button(
                "Save",
                on_click=lambda: np.save("rooms/" + filename.value + ".npy", matrix),
            )

    def load_matrix(filename):
        if not Path("rooms/" + filename + ".npy").exists():
            ui.notify(f"{filename} does not exist")
            return
        matrix = np.load("rooms/" + filename + ".npy")
        matrix_ui.refresh(matrix)

    with ui.row():
        with ui.dropdown_button("Room"):
            for file in Path("rooms").glob("*.npy"):
                ui.item(file.stem, on_click=lambda f=file.stem: load_matrix(f))

    matrix_ui()


if __name__ in {"__main__", "__mp_main__"}:
    main_ui()
    ui.run()
