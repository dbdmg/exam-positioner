from itertools import product
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


class Room:
    """
    Class to represent a room with a matrix of sits.

    Args:
        name (str): Name of the room.
        matrix (np.ndarray): Matrix of sits.
    """

    def __init__(self, name: str, matrix: np.ndarray, **kwargs):
        self.matrix = matrix.astype(np.int64)
        self.name = name

    @classmethod
    def from_yaml(cls, file: str, **kwargs):
        """
        Create a Room object from a YAML file.

        Args:
            file (str): Path to the YAML file.

        Returns:
            Room: Room object.

        Note:
            The YAML file should have the following structure:
            ```yaml
            size:
              rows: 5
              cols: 5
            sits:
              rows: [0, 1, 2, 3, 4]
              cols: [0, 1, 2, 3, 4]
            banned_sits:
              - start: "2:2"
                end: "2:2"
              - start: "0:0"
                end: "0:0"
            desk:
              start: "2:0"
              end: "2:0"
            ```
        """
        with open(file, "r") as f:
            config = yaml.safe_load(f)
        matrix = np.zeros(
            (config["size"]["rows"], config["size"]["cols"]), dtype=np.int64
        )
        for r, c in product(config["sits"]["rows"], config["sits"]["cols"]):
            matrix[r, c] = 1
        # Banned areas
        for range in config["banned_sits"]:
            start = list(map(int, range["start"].split(":")))
            end = list(map(int, range["end"].split(":")))
            banned_range = (*start, *end)
            matrix[
                banned_range[0] : banned_range[2] + 1,
                banned_range[1] : banned_range[3] + 1,
            ] = -1
        # Desk
        start = list(map(int, config["desk"]["start"].split(":")))
        end = list(map(int, config["desk"]["end"].split(":")))
        matrix[start[0] : end[0] + 1, start[1] : end[1] + 1] = -2
        return cls(Path(file).stem, matrix, **kwargs)

    @classmethod
    def from_numpy_file(cls, path: str, **kwargs):
        """
        Create a Room object from a numpy file.

        Args:
            path (str): Path to the numpy file.

        Returns:
            Room: Room object.
        """
        return cls(Path(path).stem, np.load(path), **kwargs)

    @classmethod
    def from_txt_file(cls, path: str, **kwargs):
        """
        Create a Room object from a txt file.

        Args:
            path (str): Path to the txt file.

        Returns:
            Room: Room object.
        """
        return cls(Path(path).stem, np.loadtxt(path, delimiter="\t"), **kwargs)

    @classmethod
    def from_excel_sheet(cls, path: str, sheet: str, **kwargs):
        """
        Create a Room object from an Excel sheet.

        Args:
            path (str): Path to the Excel file.
            sheet (str): Name of the sheet.

        Returns:
            Room: Room object.
        """
        room = (
            pd.read_excel("aule.xlsx", sheet_name=sheet)
            .apply(pd.to_numeric, errors="coerce")
            .to_numpy()
        )
        room = (room >= 0).astype(int)
        # Calculate the boundaries of True values as minx, maxx, miny, maxy
        minx, miny = room.shape
        maxx, maxy = 0, 0
        for i, j in product(range(room.shape[0]), range(room.shape[1])):
            if room[i, j]:
                minx = min(minx, i)
                miny = min(miny, j)
                maxx = max(maxx, i)
                maxy = max(maxy, j)
        room -= 1
        return cls(sheet, room[minx : maxx + 1, miny : maxy + 1], **kwargs)

    def write_numpy_file(self, path: str):
        """
        Write the matrix to a numpy file.

        Args:
            path (str): Path to the numpy file.
        """
        np.save(path, self.matrix)

    def assign(self, row: int, col: int, id: int):
        """
        Assign a student id to a sit.

        Args:
            row (int): Row of the sit.
            col (int): Column of the sit.
            id (int): Student id.
        """
        self.matrix[row, col] = id

    def plot(self):
        """
        Plot the matrix of sits.

        Returns:
            Figure: Figure with the plot.
        """
        colors_by_values = {-1: (224, 224, 224), 0: (255, 255, 255), 100: (255, 255, 0)}
        colors = np.zeros((*self.matrix.shape, 3), dtype=np.uint8)
        for i, color in colors_by_values.items():
            if i == 100:
                colors[self.matrix >= 1] = color
            else:
                colors[self.matrix == i] = color
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.imshow(colors, aspect="auto", origin="lower")
        # Annotate each cell with the value
        for i, j in product(range(self.matrix.shape[0]), range(self.matrix.shape[1])):
            if self.matrix[i, j] > 1:
                ax.text(
                    j,
                    i,
                    str(self.matrix[i, j]),
                    ha="center",
                    va="center",
                    color="black",
                )

        row_names = [chr(i) for i in range(65, 65 + self.matrix.shape[0])]
        column_names = [str(i) for i in range(1, self.matrix.shape[1] + 1)]

        invalid_along_columns = (self.matrix == -1).sum(axis=1) == self.matrix.shape[1]
        invalid_along_rows = (self.matrix == -1).sum(axis=0) == self.matrix.shape[0]

        # Insert empty strings for null rows and columns
        for i in invalid_along_columns.nonzero()[0]:
            row_names.insert(i, "")
        for i in invalid_along_rows.nonzero()[0]:
            column_names.insert(i, "")
        row_names = row_names[: self.matrix.shape[0]]
        column_names = column_names[: self.matrix.shape[1]]

        ax.set_xticks(np.arange(self.matrix.shape[1]))
        ax.set_xticklabels(column_names)
        ax.set_yticks(np.arange(self.matrix.shape[0]))
        ax.set_yticklabels(row_names)

        ax.set_title(f"Aula {self.name}")
        return fig
