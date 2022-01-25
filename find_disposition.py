#!/usr/bin/env python

import pandas as pd
import numpy as np
import argparse
import re
import yaml


def get_args():
    parser = argparse.ArgumentParser(description=f"Crea la distribuzione dei posti in un'aula a partire dall'elenco degli studenti e dalla matrice dei posti disponibili.\n IMPORTANTE: le aule devono essere rappresentate con la cattedra in basso, le file numerate in maniera crescente, lasciando uno spazio nel caso in cui non sia presenta una fila.")
    parser.add_argument('rooms', nargs='*', type=str, default=["Rb", "R"], help="La lista delle aule nelle quali dividere gli studenti.")
    parser.add_argument('-s', '--students', type=str, default="Lista_Prenotati_294874.xlsx", help="Percorso del file Excel contenente l'elenco degli studenti prenotati.")
    parser.add_argument('-n', '--name', type=str, default="COD_yyyymmdd", help="Nome dei files di output. Default: '<COD>_yyyymmdd'.")
    parser.add_argument("--style", action="store_true", default="Add style to the resulting sheet.")
    args = parser.parse_args()
    return args


def snake_j(row, i, j):
    return row.index[len(row) - row.index.get_loc(j) - 1] if i % 4 == 2 else j


def stamp_id(room_name, config, matricole, prenotati):
    window = config["position"]
    
    rows = list(map(int, re.findall(r"\d+", window)))
    cols = re.findall(r"[a-zA-Z]", window)
    cols = [ord(a.lower())-97 for a in cols]

    if "filename" in config:
        aula = pd.read_csv(config["filename"], sep="\t", header=None)
        
    else: # retrieve from Google's API
        # this might return a wrong CSV, beware
        sheet_id = "1yuDN40n8pcoP2FgjUwuR6oxKvNRSa2jbJTVhOrsB5_A"
        sheet_name = sheet_name.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

        aula = pd.read_csv(
            url,
            header=None
        )

    aula = aula.iloc[rows[0]: rows[1], cols[0]: cols[1] + 1].copy()
    aula = aula.set_index(aula.columns[0])

    slots = (~aula.isna()).sum().sum()
    # if len(matricole) < nans:
    #     matricole += ["x" for _ in range(nans - len(matricole))]
        
    print(slots, len(matricole))
    
    aula = aula.rename(columns={c: "" for c in aula.columns if type(c)==str and "Unnamed" in c})
    aula = aula.rename(index = {i: chr(int(i)+64) if i>0 else np.NaN for i in aula.index})
    
    #import IPython; IPython.embed(); exit(-1)
    
    placement = aula.copy()
    
    for i, row in aula.sort_index().iterrows():
    
        row = row.astype(float)
        if not matricole:
            break
        
        for j, place in row.iteritems():
            
            if not matricole:
                break
                
            # import IPython; IPython.embed(); exit(-1)
            if place == 1: # force notation here
                curr_matricola = matricole.pop(0) 
                placement.loc[i, j] = str(curr_matricola)
                
                if not curr_matricola == "x":
                    prenotati.loc[curr_matricola, ["AULA", "POSTO"]] = room_name, f"{i}{snake_j(row, ord(i), j)}"

        #print(placement)
        #exit(-1)
        
    placement = placement.fillna("")
    placement[""] = ""
    
    placement = placement.append(pd.Series(
        {c:"Professor Desk" if c==placement.columns[placement.shape[1]//2] else "" for c in placement.columns}, 
        name=""
    ))
    
    # print(placement)
    return placement, matricole


def styled_seats(x):
    checkerboard = lambda d: np.row_stack(d[0]*(np.r_[d[1]*[True,False]], np.r_[d[1]*[False,True]]))[:d[0], :d[1]]
    
    df1 = pd.DataFrame(np.where((x.values != "")&checkerboard(x.shape), 
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
    prenotati = pd.read_excel(args.students, skiprows=range(5)).sort_values(by="COGNOME")
    prenotati = prenotati.drop(["DOMANDA", "RISPOSTA"], axis=1).set_index("MATRICOLA")
    prenotati = prenotati.assign(AULA=np.NaN, POSTO=np.NaN)

    matricole = prenotati[~prenotati.NOTE.str.contains("Esame online", na=False)].index.to_list()
    
    with open("riferimenti_aule.yaml", "r") as f:
        riferimenti = yaml.load(f, yaml.SafeLoader)

    writer = pd.ExcelWriter(f"{args.name}_disposizioni.xlsx")
    
    if len(args.rooms) > 1 and len(set(args.rooms)) == 1:
        room_names = [f"{i+1}{r}" for i, r in enumerate(args.rooms)]
    else:
        room_names = args.rooms
        
    print("Room names:", room_names)
    
    for i, (a, room_name) in enumerate(zip(args.rooms, room_names)):
        config = riferimenti.get(a)
        if "position" not in config:
            raise RuntimeError("Specify a position window in YAML reference file!")
        
        aula, matricole = stamp_id(room_name, config, matricole, prenotati)
        
        if args.style:
            aula = aula.style.apply(styled_seats, axis=None)
        
        aula.to_excel(writer, sheet_name=f"Aula_{room_name}")

    # remove placeholders "x"
    # matricole = [m for m in matricole if m != "x"]
    assert len(matricole) == 0, f"Aule indicate non sufficienti, rimangono {len(matricole)} studenti ({matricole})"
    prenotati.to_excel(f"{args.name}_prenotati.xlsx")
    writer.save()
    
    
    
if __name__ == '__main__':
    args = get_args()
    main(args)



    