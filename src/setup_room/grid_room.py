from itertools import product

import numpy as np

from ..base.room import Room


class GridRoom(Room):
    def __init__(self, name: str, matrix: np.ndarray, v_space: int, h_space: int):
        super().__init__(name, matrix)

        self.matrix[self.matrix == 1] = 0
        for r, c in product(
            range(0, self.matrix.shape[0], v_space + 1),
            range(0, self.matrix.shape[1], h_space + 1),
        ):
            if self.matrix[r, c] == 0:
                self.matrix[r, c] = 1
