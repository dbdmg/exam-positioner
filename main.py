from pathlib import Path

from algorithms import first_available_placing
from src import Bookings, GridRoom, Room

FOLDER = Path(".")
ROOMS = ["2", "4"]
NOPC_STUDENTS = []
NOPC_ROOM = ""
DSA_ROOM = "R2"

rooms = [GridRoom.from_txt_file(f"rooms/{r}.txt", v_space=1, h_space=2) for r in ROOMS]
bookings = Bookings(FOLDER.glob("*.csv"))
first_available_placing(rooms, bookings)

for room in rooms:
    room.plot().savefig(f"plots/{room.name}.pdf", dpi=300, bbox_inches="tight")
