import numpy as np
from src import Bookings, Room


def first_available_placing(rooms: list[Room], bookings: Bookings):
    # Place all dsa bookings into first room
    dsa_room = rooms[0]
    for booking in bookings.dsa["MATRICOLA"]:
        row, col = find_empty_spot(dsa_room)
        dsa_room.assign(row, col, booking)
        bookings.assign_to_room(booking, dsa_room.name)
    # Place all the others
    for booking in bookings.on_site["MATRICOLA"]:
        # Find the room with the most empty spots
        room = max(rooms, key=lambda r: np.sum(r.matrix == 1))
        row, col = find_empty_spot(room)
        if row == -1:
            return
        room.assign(row, col, booking)
        bookings.assign_to_room(booking, room.name)


def find_empty_spot(room: Room) -> tuple[int, int]:
    r, c = np.where(room.matrix == 1)
    if len(r) == 0:
        return -1, -1
    return r[0], c[0]
