#!/usr/bin/env python

# from ast import arg
from pathlib import Path
import pandas as pd
import numpy as np
import argparse
import re
import yaml


def get_args():
    parser = argparse.ArgumentParser(description=f"Crea la distribuzione dei posti in un'aula a partire dall'elenco degli studenti e dalla matrice dei posti disponibili.\n IMPORTANTE: le aule devono essere rappresentate con la cattedra in basso, le file numerate in maniera crescente, lasciando uno spazio nel caso in cui non sia presenta una fila.")
    parser.add_argument('-f', '--folder', type=Path, default=None, help="Percorso nel quale ricercare elenco studenti, file di configurazione e eventualmente excel con disposizioni, il nome del file finale avrà il nome della cartella come prefisso.")
    parser.add_argument('-r', '--rooms', type=str, default=None, help="Aule da considerare, separate da virgola. Indicare questo oppure inserire un file di configurazione YAML.")
    parser.add_argument('--nopc_students', type=str, default="", help="Lista delle matricole (senza spazi, separate da virgola) degli studenti che necessitano di essere posizionati in aula multimediale.")
    parser.add_argument('--nopc_room', type=str, default="5T", help="Aula multimediale nella quale inserire nopc_students. Default è '5T'.")
    parser.add_argument('--dsa_room', type=str, default=True, help="Aula nella quale saranno posizionati gli studenti DSA.")
    parser.add_argument('-n', '--name', type=str, default="COD_yyyymmdd", help="Prefisso del nome dei files di output. Default: '<COD>_yyyymmdd'.")
    parser.add_argument("--nostyle", action="store_true", help="Prevent adding style to the resulting sheet.")
    args = parser.parse_args()
    return args


def snake_j(row, i, j):
    rev_j = row.index[len(row) - row.index.get_loc(j) - 1]
    if i % 4 == 2 and not np.isnan(row[rev_j]):
         return rev_j
    return j


def stamp_id(room_name, config, matricole, prenotati):
    window = config["position"]

    # B2:U20 is the format of config["position"] (the letter can also be AA, AB, etc.)
    
    rows = list(map(int, re.findall(r"\d+", window)))
    cols = re.findall(r"[A-Z]+", window)
    cols = [ord(c[-1].lower())-97 + 26*(len(c)-1) for c in cols]

    if "filename" in config:
        if config["filename"].name.endswith(".csv"):
            aula = pd.read_csv(config["filename"], sep="\t", header=None)
        elif config["filename"].name.endswith(".xlsx"):
            aula = pd.read_excel(config["filename"], sheet_name=config["sheet"], header=None)
        
    else: # retrieve from Google's API
        # this might return a wrong CSV, beware
        sheet_id = "1yuDN40n8pcoP2FgjUwuR6oxKvNRSa2jbJTVhOrsB5_A"
        sheet_name = config["sheet"].replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        aula = pd.read_csv(
            url,
            header=None
        )
        
    col_names = aula.loc[rows[0]-1, cols[0]+1: cols[1]]  
    aula = aula.iloc[rows[0]: rows[1], cols[0]: cols[1] + 1].copy()
    aula = aula.set_index(aula.columns[0]).rename_axis(None)
    aula.columns = col_names

    aula = aula.map(lambda x: np.NaN if x==0 else x)
    slots = (~aula.isna()).sum().sum()
        
    print(f"| Room {room_name.ljust(3)} | Slots: {slots}, remaining students: {len(matricole)}")

    if len(matricole) < np.nansum(aula.values):
        matricole += ["x" for _ in range(int(np.nansum(aula.values)) - len(matricole))]
    
    aula = aula.rename(columns={c: "" for c in aula.columns if type(c)==str and "Unnamed" in c})
    aula = aula.rename(index = {i: chr(int(i)+64) if i>0 else np.NaN for i in aula.index})
        
    placement = aula.copy()
    
    for i, row in aula.sort_index().iterrows():
    
        row = row.astype(float)
        if not matricole:
            break
        
        for j, place in row.items():
            if not matricole:
                break
                
            if place == 1: # force notation here
                curr_matricola = matricole.pop(0) 
                sn_j = snake_j(row, ord(i), j) 
                placement.loc[i, sn_j] = float(curr_matricola) if not curr_matricola == "x" else -1.
                
                if not curr_matricola == "x":
                    prenotati.loc[curr_matricola, ["AULA", "POSTO"]] = str(room_name), f"{i}{int(sn_j)}"

    placement = placement.fillna("")
    placement[""] = ""
    
    placement.loc[""] = pd.Series(
        {c:"Professor Desk" if c==placement.columns[placement.shape[1]//2] else "" for c in placement.columns}, 
        )
    return placement, matricole


def styled_seats(x):
    checkerboard = lambda d: np.row_stack(d[0]*(np.r_[d[1]*[True,False]], np.r_[d[1]*[False,True]]))[:d[0], :d[1]]
    if np.NaN in x.index: x.loc[np.NaN, :] = np.NaN
    if np.NaN in x.columns: x[[np.NaN]] = np.NaN
    df1 = pd.DataFrame(np.where(x.notna()&checkerboard(x.shape), 
                                'background-color: lightgrey;\
                                width: 50px;\
                                text-align: center',
                                'width: 50px;\
                                text-align: center'
                               ),
                        index=x.index, columns=x.columns
                       )
    df1.iloc[-1] = x.iloc[-1].apply(lambda x: "" if x == "" else 'background-color: lightgrey; text-align: center')
    return df1


def main(args):
    args.yconfig = args.folder / "riferimenti_aule.yaml"
    args.name = args.folder / args.folder.stem        

    if args.yconfig.exists():
        with open(args.yconfig, "r") as f:
            riferimenti = yaml.load(f, yaml.SafeLoader)
            riferimenti = {str(k): v for k, v in riferimenti.items()}
    elif args.rooms is not None:
        with open("riferimenti_aule_all.yaml", "r") as f:
            aule_db = yaml.load(f, yaml.SafeLoader)
        def process_room(room):
            try:
                return int(room)
            except:
                return room
            
        riferimenti = {a: aule_db.get(a, aule_db.get(process_room(a))) for a in args.rooms.split(",")}
    else:
        raise FileNotFoundError(f"File {args.yconfig} not found. Please create a conf file or provide a list of rooms.") 

    prenotati = pd.DataFrame()
    for p in args.folder.glob("VISAP_Elenco_Studenti_*"):
        if p.suffix == ".xlsx": 
            tmp = pd.read_excel(p) 
            row_toskip = (tmp.iloc[:,0]=="MATRICOLA").argmax()
            col = tmp.xs(row_toskip)
            tmp = tmp.drop(range(row_toskip+1))
            tmp.columns = col
        else:
            tmp = pd.read_csv(p)
        prenotati = pd.concat([prenotati,tmp], ignore_index=True)
        
    plen = len(prenotati)
    prenotati = prenotati.drop_duplicates()
    if plen != len(prenotati): print("Attenzione: studenti duplicati nella tabella\n")

    prenotati.columns = [c.strip() for c in prenotati.columns]
    prenotati = prenotati.drop(["DATA PRENOTAZIONE", "DOMANDA", "RISPOSTA", "CORSO", "CDL", "NUMERO CORSO"], axis=1).sort_values(by="COGNOME").set_index("MATRICOLA")
    prenotati = prenotati.assign(AULA=np.NaN, POSTO=np.NaN)
    prenotati.AULA = prenotati.AULA.astype('str')
    
    # prenotati.NOTE = prenotati.NOTE.astype('str')
    if not prenotati.NOTE.dtype == 'object': prenotati.NOTE = ""
    matricole = prenotati[~prenotati.NOTE.str.contains("Esame online", na=False)].index.to_list()

    if args.dsa_room == True:
        args.dsa_room = list(riferimenti.keys())[0]
    if args.dsa_room is not None:
        matricole_dsa = prenotati[prenotati.NOTE.str.contains("Dsa", na=False)|prenotati.NOTE.str.contains("Tempo aggiuntivo", na=False)].index.to_list()
        print(f"\nDsa students ({', '.join(prenotati[prenotati.index.isin(matricole_dsa)].COGNOME)}) will be placed in room {args.dsa_room}\n")
        matricole = [m for m in matricole if m not in matricole_dsa]
    
    if "nopc_students" in riferimenti.keys():
        args.nopc_students = riferimenti.pop("nopc_students")
    if args.nopc_students:
        ex_students = [int(m) for m in str(args.nopc_students).split(",")]
        prenotati.loc[ex_students, "AULA"] = args.nopc_room
        matricole = [m for m in matricole if m not in ex_students]
        print(f"These students will be placed in {args.nopc_room}:")
        print(ex_students, "\n")
    else:
        ex_students = []

    writer_d = pd.ExcelWriter(f"{args.name}_disposizioni.xlsx")
    writer_p = pd.ExcelWriter(f"{args.name}_prenotati.xlsx")
    
    
    args.rooms = list(riferimenti.keys())
        
    if len(args.rooms) > 1 and len(set(args.rooms)) == 1:
        room_names = [f"{i+1}{r}" for i, r in enumerate(args.rooms)]
    else:
        room_names = args.rooms
        
    print("Room names:", room_names, "\n")
    
    for i, (a, room_name) in enumerate(zip(args.rooms, room_names)):
        config = riferimenti.get(a)
        if "position" not in config:
            raise RuntimeError("Specify a position window in YAML reference file!")
        if "filename" not in config and args.folder:
            config["filename"] = args.folder / "Aule esame.xlsx"
            if not config["filename"].exists(): config["filename"] = Path.cwd() / "Aule esami Polito, disposizione posti.xlsx"
        
        if args.dsa_room is not None and room_name==args.dsa_room:
            print(f"Placing dsa students in {room_name}")
            matricole = matricole_dsa + matricole
        aula, matricole = stamp_id(room_name, config, matricole, prenotati)
        
        aula = aula.map(lambda x: 'x' if x==-1 else x).map(lambda x: int(x) if isinstance(x, float) else x)
        if not args.nostyle:
            aula = aula.rename(columns={c: f"nan_{j}" if pd.isnull(c) else c for j, c in enumerate(aula.columns)})
            aula = aula.style.apply(styled_seats, axis=None)
        
        aula.to_excel(writer_d, sheet_name=f"Aula_{room_name}")

        prenotati[prenotati.AULA == room_name].to_excel(writer_p, sheet_name=f"Aula_{room_name}")

    # remove placeholders "x"
    # matricole = [m for m in matricole if m != "x"]
    if len(matricole) != 0:
        if len(matricole) + len(ex_students) < 1: # Se pochi, vengono caricati in 5T: NON PIU' DISPONIBILE
            prenotati.loc[matricole, "AULA"] = args.nopc_room
            print(f"\nℹ️  {len(matricole)} extra students are placed in {args.nopc_room}")
        else:
            raise ValueError(f"⚠️  Designated rooms are not sufficient, {len(matricole)} students missing ({matricole})")

    if args.nopc_students:
        prenotati[prenotati.AULA == args.nopc_room].to_excel(writer_p, sheet_name=f"Aula_{args.nopc_room}")
        
    if len(room_names) > 1 or args.nopc_students:
        prenotati.to_excel(writer_p, sheet_name=f"Elenco Complessivo")
        
    with open(f"{args.name}_limiti.txt", "w") as f:
        limiti = prenotati[prenotati.AULA != args.nopc_room].groupby("AULA").agg({
                "COGNOME": ["min", "max"]
            })
        f.write(str(limiti))
        print("\n✔️  Students succesfully allocated\n", str(limiti))

    writer_d.close()
    writer_p.close()
        
    
if __name__ == '__main__':
    args = get_args()
    main(args)



    
