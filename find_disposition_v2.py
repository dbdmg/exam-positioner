#!/usr/bin/env python

# from ast import arg
import argparse
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import yaml


def get_args():
    parser = argparse.ArgumentParser(
        description=f"Crea la distribuzione dei posti in un'aula a partire dall'elenco degli studenti e dalla matrice dei posti disponibili.\n IMPORTANTE: le aule devono essere rappresentate con la cattedra in basso, le file numerate in maniera crescente, lasciando uno spazio nel caso in cui non sia presenta una fila."
    )
    parser.add_argument(
        "-f",
        "--folder",
        type=Path,
        default=None,
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


def snake_j(row, i, j):
    rev_j = row.index[len(row) - row.index.get_loc(j) - 1]
    if i % 4 == 2 and not np.isnan(row[rev_j]):
        return rev_j
    return j


def stamp_id(room_name, config, matricole, prenotati):
    window = config["position"]

    rows = list(map(int, re.findall(r"\d+", window)))
    cols = re.findall(r"[a-zA-Z]", window)

    cols = [ord(a.lower()) - 97 for a in cols]
    if "filename" in config:
        if config["filename"].name.endswith(".csv"):
            aula = pd.read_csv(config["filename"], sep="\t", header=None)
        elif config["filename"].name.endswith(".xlsx"):
            aula = pd.read_excel(
                config["filename"], sheet_name=config["sheet"], header=None
            )

    else:  # retrieve from Google's API
        # this might return a wrong CSV, beware
        sheet_id = "1yuDN40n8pcoP2FgjUwuR6oxKvNRSa2jbJTVhOrsB5_A"
        sheet_name = config["sheet"].replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        aula = pd.read_csv(url, header=None)

    col_names = aula.loc[rows[0] - 1, cols[0] + 1 : cols[1]]
    aula = aula.iloc[rows[0] : rows[1], cols[0] : cols[1] + 1].copy()

    row_names = aula.columns[0]
    # Flip vertically and horizontally
    if config["rotate"]:
        aula = aula.iloc[::-1]
        aula = aula.iloc[:, ::-1]

    aula = aula.set_index(row_names).rename_axis(None)
    aula.columns = col_names

    # Invert index
    if config["rotate"]:
        aula.index = aula.index[::-1]

    aula = aula.rename_axis(None, axis=1)

    aula = aula.applymap(lambda x: np.NaN if x == 0 else x)
    slots = (~aula.isna()).sum().sum()

    print(
        f"| Room {room_name.ljust(3)} | Slots: {slots}, remaining students: {len(matricole)}"
    )

    if len(matricole) < np.nansum(aula.values):
        matricole += ["x" for _ in range(int(np.nansum(aula.values)) - len(matricole))]

    aula = aula.rename(
        columns={c: "" for c in aula.columns if type(c) == str and "Unnamed" in c}
    )
    aula = aula.rename(
        index={i: chr(int(i) + 64) if i > 0 else np.NaN for i in aula.index}
    )

    placement = aula.copy()

    for i, row in aula.sort_index().iterrows():
        row = row.astype(float)
        if not matricole:
            break

        for j, place in row.items():
            if not matricole:
                break

            if place == 1:  # force notation here
                curr_matricola = matricole.pop(0)
                sn_j = snake_j(row, ord(i), j)
                placement.loc[i, sn_j] = str(curr_matricola)

                if not curr_matricola == "x":
                    prenotati.loc[curr_matricola, ["AULA", "POSTO"]] = (
                        room_name,
                        f"{i}{int(sn_j)}",
                    )

    placement = placement.fillna("")
    placement[""] = ""

    placement.loc[""] = pd.Series(
        {
            c: "Professor Desk"
            if c == placement.columns[placement.shape[1] // 2]
            else ""
            for c in placement.columns
        },
    )
    return placement, matricole


def styled_seats(x):
    checkerboard = lambda d: np.row_stack(
        d[0] * (np.r_[d[1] * [True, False]], np.r_[d[1] * [False, True]])
    )[: d[0], : d[1]]
    if np.NaN in x.index:
        x.loc[np.NaN, :] = np.NaN
    if np.NaN in x.columns:
        x[[np.NaN]] = np.NaN
    df1 = pd.DataFrame(
        np.where(
            x.notna() & checkerboard(x.shape),
            "background-color: lightgrey;\
                                width: 50px;\
                                text-align: center",
            "width: 50px;\
                                text-align: center",
        ),
        index=x.index,
        columns=x.columns,
    )
    df1.iloc[-1] = x.iloc[-1].apply(
        lambda x: "" if x == "" else "background-color: lightgrey; text-align: center"
    )
    return df1


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = get_args()
    config = args.folder / "riferimenti_aule.yaml"
    name = args.folder / args.folder.stem
    all_assignations = []

    with open(config, "r") as f:
        riferimenti = yaml.safe_load(f)

    prenotati = pl.scan_csv(args.folder / "VISAP_Elenco_Studenti_*").collect()

    if prenotati.is_duplicated().any():
        logging.warning("Attenzione: studenti duplicati nella tabella\n")
        prenotati = prenotati.unique()

    prenotati = (
        prenotati.select("MATRICOLA", "COGNOME", "NOME", "DOCENTE", "NOTE")
        .sort("COGNOME")
        .with_columns(
            pl.lit(None, dtype=pl.Utf8).alias("AULA"),
            pl.lit(None, dtype=pl.Utf8).alias("POSTO"),
        )
    )
    # DSA students
    dsa = prenotati.filter(
        pl.col("NOTE").str.contains("Dsa")
        | pl.col("NOTE").str.contains("Tempo aggiuntivo")
    ).select("MATRICOLA")

    if dsa.shape[0] > 0:
        logging.info(
            f"Found {dsa.shape[0]} students with DSA requirements, they will be placed in room {args.dsa_room}"
        )
    # Not online students
    on_site = (
        prenotati.filter(
            pl.col("NOTE").str.contains("Esame online").is_not()
            | pl.col("NOTE").is_null()
        )
        .select("MATRICOLA")
        .filter(pl.col("MATRICOLA").is_in(dsa).is_not())
    )
    # No PC students
    nopc = None
    if "nopc_students" in riferimenti.keys():
        on_site = on_site.filter(
            pl.col("MATRICOLA").is_in(riferimenti["nopc_students"]).is_not()
        )
        nopc = prenotati.filter(
            pl.col("MATRICOLA").is_in(riferimenti["nopc_students"])
        ).with_columns(
            pl.lit(args.nopc_room, dtype=pl.Utf8).alias("AULA"),
        )
        all_assignations.append(nopc)
        logging.info(f"{nopc.shape[0]} students will be placed in {args.nopc_room}:")

    # Get all rooms
    rooms = args.rooms or [r for r in riferimenti if r != "nopc_students"]
    rooms = list(map(str.upper, rooms))
    logging.info(f"Rooms: {rooms}")

    """Duplicate rooms if needed
    if len(args.rooms) > 1 and len(set(args.rooms)) == 1:
        room_names = [f"{i+1}{r}" for i, r in enumerate(args.rooms)]
    else:
        room_names = args.rooms
    """
    prenotation_file = f"{name}_prenotati.xlsx"
    disposition_file = f"{name}_disposizioni.xlsx"
    for r in rooms:
        config = riferimenti[r]
        if "position" not in config:
            raise RuntimeError("Specify a position window in YAML reference file!")
        if "filename" not in config and args.folder:
            config["filename"] = args.folder / "Aule esami.xlsx"
        if args.dsa_room is not None and r == args.dsa_room:
            logging.info(f"Placing dsa students in {r}")
            matricole = pl.concat([dsa, matricole])

        aula, matricole = stamp_id(
            r, config, matricole.to_pandas(), prenotati.to_pandas()
        )

        pl.DataFrame(aula).write_excel(disposition_file, worksheet=f"Aula_{r}")
        prenotati.filter(pl.col("AULA") == r).write_excel(
            prenotation_file, worksheet=f"Aula_{r}"
        )

    # remove placeholders "x"
    # matricole = [m for m in matricole if m != "x"]
    if matricole.shape[0] != 0:
        raise ValueError(
            f"⚠️  Designated rooms are not sufficient, {len(matricole)} students missing)"
        )

    if nopc:
        prenotati.filter(pl.col("AULA") == args.nopc_room).write_excel(
            prenotation_file, worksheet=f"Aula_{args.nopc_room}"
        )

    if len(rooms) > 1 or args.nopc_students:
        prenotati.write_excel(prenotation_file, worksheet=f"Elenco Complessivo")

    logging.info("\n✔️  Students succesfully allocated\n")


if __name__ == "__main__":
    main()
