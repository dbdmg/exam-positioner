from itertools import product
from pathlib import Path
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import yaml


class Room:
    def __init__(self, name: str, matrix: np.ndarray, **kwargs):
        self.matrix = matrix
        self.name = name

    @classmethod
    def from_yaml(cls, file: str, **kwargs):
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
        return cls(Path(path).stem, np.load(path), **kwargs)

    def assign(self, row: int, col: int, id: int):
        self.matrix[row, col] = id

    def plot(self):
        colors_by_values = {-1: (224, 224, 224), 0: (255, 255, 255), 100: (255, 255, 0)}
        colors = np.zeros((*self.matrix.shape, 3), dtype=np.uint8)
        for i, color in colors_by_values.items():
            if i == 100:
                colors[self.matrix >= 1] = color
            else:
                colors[self.matrix == i] = color
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.imshow(colors, aspect="auto")
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

        ax.set_xticks(np.arange(self.matrix.shape[1]))
        ax.set_xticklabels(np.arange(1, self.matrix.shape[1] + 1))
        ax.set_yticks(np.arange(self.matrix.shape[0]))
        ax.set_yticklabels(
            [chr(i) for i in reversed(range(65, 65 + self.matrix.shape[0]))]
        )
        return fig
