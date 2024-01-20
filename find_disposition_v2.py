#!/usr/bin/env python

# from ast import arg
import argparse
import logging
import re
from itertools import product
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import polars as pl
import yaml
from xlsxwriter import Workbook


def get_args():
    parser = argparse.ArgumentParser(
        description=f"Crea la distribuzione dei posti in un'aula a partire dall'elenco degli studenti e dalla matrice dei posti disponibili.\n IMPORTANTE: le aule devono essere rappresentate con la cattedra in basso, le file numerate in maniera crescente, lasciando uno spazio nel caso in cui non sia presenta una fila."
    )
    parser.add_argument(
        "-f",
        "--folder",
        type=Path,
        default="test",
        help="Percorso nel quale ricercare elenco studenti, file di configurazione e eventualmente excel con disposizioni, il nome del file finale avrà il nome della cartella come prefisso.",
    )
    parser.add_argument(
        "--nopc_students",
        type=str,
        default="",
        help="Lista delle matricole (senza spazi, separate da virgola) degli studenti che necessitano di essere posizionati in aula multimediale.",
    )
    parser.add_argument(
        "--nopc_room",
        type=str,
        default="5T",
        help="Aula multimediale nella quale inserire nopc_students. Default è '5T'.",
    )
    parser.add_argument(
        "--dsa_room",
        type=str,
        default=None,
        help="Aula nella quale saranno posizionati gli studenti DSA.",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        default="COD_yyyymmdd",
        help="Prefisso del nome dei files di output. Default: '<COD>_yyyymmdd'.",
    )
    parser.add_argument(
        "--nostyle",
        action="store_true",
        help="Prevent adding style to the resulting sheet.",
    )
    parser.add_argument(
        "-r",
        "--rooms",
        type=str,
        nargs="*",
        default=None,
        help="Lista delle aule da processare. Default: tutte le aule presenti nel file di configurazione.",
    )
    args = parser.parse_args()
    return args


def place_student(
    room_dict: Dict[str, np.ndarray], student_id: int, room_name: Optional[str] = None
) -> Tuple[int, int]:
    if room_name is None:
        room_name = [k for k, m in room_dict.items() if (m == 1).sum() > 0][0]
    room_matrix = room_dict[room_name]
    # Find first available sit
    r, c = np.where(room_matrix == 1)
    if len(r) == 0:
        raise ValueError("No more sits available")
    room_matrix[r[0], c[0]] = student_id
    return {"room": room_name, "row": r[0], "col": c[0]}


def build_room_matrix(config: Dict[str, Any]) -> np.ndarray:
    matrix = np.zeros((config["size"]["rows"], config["size"]["cols"]), dtype=np.int64)
    for r, c in product(config["sits"]["rows"], config["sits"]["cols"]):
        matrix[r, c] = 1
    # Banned areas
    for range in config["banned_sits"]:
        start = list(map(int, range["start"].split(":")))
        end = list(map(int, range["end"].split(":")))
        banned_range = (*start, *end)
        matrix[
            banned_range[0] : banned_range[2] + 1, banned_range[1] : banned_range[3] + 1
        ] = -1
    # Desk
    start = list(map(int, config["desk"]["start"].split(":")))
    end = list(map(int, config["desk"]["end"].split(":")))
    matrix[start[0] : end[0] + 1, start[1] : end[1] + 1] = -2
    return matrix


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = get_args()
    name = args.folder / args.folder.stem

    with open(args.folder / "config.yaml", "r") as f:
        config = yaml.safe_load(f)

    rooms = {}
    for r in config["rooms"]:
        with open(f"room_formats/{r}.yaml", "r") as f:
            rooms[r] = build_room_matrix(yaml.safe_load(f))

    prenotati = pl.scan_csv(args.folder / "VISAP_Elenco_Studenti_*").collect()

    if prenotati.is_duplicated().any():
        logging.warning("Attenzione: studenti duplicati nella tabella\n")
        prenotati = prenotati.unique()

    prenotati = prenotati.select(
        "MATRICOLA", "COGNOME", "NOME", "DOCENTE", "NOTE"
    ).sort("COGNOME")
    # DSA students
    dsa = prenotati.filter(
        pl.col("NOTE").str.contains("Dsa")
        | pl.col("NOTE").str.contains("Tempo aggiuntivo")
    ).get_column("MATRICOLA")

    if dsa.shape[0] > 0:
        logging.info(
            f"Found {dsa.shape[0]} students with DSA requirements, they will be placed in room {args.dsa_room}"
        )
    # Not online students
    on_site = (
        prenotati.filter(
            pl.col("NOTE").str.contains("Esame online").not_()
            | pl.col("NOTE").is_null()
        )
        .filter(pl.col("MATRICOLA").is_in(dsa).not_())
        .get_column("MATRICOLA")
    )
    # No PC students
    nopc = pl.Series()
    if "nopc_students" in config.keys():
        nopc = on_site.filter(on_site.is_in(config["nopc_students"]))
        on_site = on_site.filter(on_site.is_in(config["nopc_students"]).not_())
        logging.info(f"{nopc.shape[0]} students will be placed in {args.nopc_room}:")

    prenotation_file = f"{name}_prenotati.xlsx"
    disposition_file = f"{name}_disposizioni.xlsx"

    positions = pl.concat([dsa, nopc, on_site]).to_frame()  # type: pl.DataFrame
    assigned_positions = []
    if dsa.shape[0] > 0:
        p = dsa.to_frame("MATRICOLA").with_columns(
            position=dsa.map_elements(
                lambda x: place_student(rooms, x, room_name=args.dsa_room)
            )
        )
        assigned_positions.append(p)
    if nopc.shape[0] > 0:
        p = nopc.to_frame("MATRICOLA").with_columns(
            position=nopc.map_elements(
                lambda x: {"room": args.nopc_room, "row": 0, "col": 0}
            )
        )
        assigned_positions.append(p)

    p = on_site.to_frame("MATRICOLA").with_columns(
        position=on_site.map_elements(lambda x: place_student(rooms, x))
    )
    assigned_positions.append(p)
    assigned_positions = pl.concat(assigned_positions)
    positions = positions.join(assigned_positions, on="MATRICOLA", how="left")
    positions = positions.unnest("position")

    with Workbook(disposition_file) as dw, Workbook(prenotation_file) as pw:
        for k, v in rooms.items():
            pl.DataFrame(v).write_excel(dw, worksheet=f"Aula_{k}")
            students_in_room = positions.filter(pl.col("room") == k)
            students_in_room.join(prenotati, on="MATRICOLA", how="left").write_excel(
                pw, worksheet=f"Aula_{k}"
            )

        positions.filter(pl.col("room") == args.nopc_room).join(
            prenotati, on="MATRICOLA", how="left"
        ).write_excel(pw, worksheet=f"Aula_{args.nopc_room}")


if __name__ == "__main__":
    main()
