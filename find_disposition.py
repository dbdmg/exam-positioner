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
    args = parser.parse_args()
    return args


def snake_j(row, i, j):
    return row.index[len(row) - row.index.get_loc(j) - 1] if i % 4 == 2 else j


def stamp_id(a_name, sheet_name, window, matricole, prenotati):
    row_lims = re.findall(r"\d+", window)
    cols = re.findall(r"[a-zA-Z]", window)
    cols = [ord(a.lower())-97 for a in cols]

    sheet_id = "1yuDN40n8pcoP2FgjUwuR6oxKvNRSa2jbJTVhOrsB5_A"
    sheet_name = sheet_name.replace(" ", "%20")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

    aula = pd.read_csv(url, usecols=range(cols[0], cols[1]+1),
                               index_col=0,  skiprows=int(row_lims[0])-1,
                              ).iloc[:(int(row_lims[1])-int(row_lims[0])), :]
    if len(matricole) < np.nansum(aula.values):
        matricole += ["x" for _ in range(int(np.nansum(aula.values)) - len(matricole))]
        
    aula = aula.rename(columns={c: "" for c in aula.columns if type(c)==str and "Unnamed" in c})
    aula = aula.rename(index = {i: chr(int(i)+64) if i>0 else np.NaN for i in aula.index})

    for i, row in aula.sort_index().iterrows():
        for j, place in row.iteritems():
            if not np.isnan(place):
                curr_matricola = matricole.pop(0)
                aula.loc[i, snake_j(row, ord(i), j)] = curr_matricola
                if not curr_matricola == "x":
                    prenotati.loc[curr_matricola, ["AULA", "POSTO"]] = a_name, f"{i}{snake_j(row, ord(i), j)}"
    aula.loc[np.NaN] = ""
    aula[""] = ""
    
    aula = aula.append(pd.Series(
        {c:"Cattedra" if c==aula.columns[aula.shape[1]//2] else "" for c in aula.columns}, 
        name=""
    ))
    return aula, matricole


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
    for i, a in enumerate(args.rooms):
        sheet_name, window = riferimenti.get(a).values()
        aula, matricole = stamp_id(a, sheet_name, window, matricole, prenotati)
        
        aula.style.apply(styled_seats, axis=None).to_excel(writer, sheet_name=f"Aula {a}")

    assert len(matricole) == 0, f"Aule indicate non sufficienti, rimangono {len(matricole)} studenti ({matricole})"
    prenotati.to_excel(f"{args.name}_prenotati.xlsx")
    writer.save()
    
    
    
if __name__ == '__main__':
    args = get_args()
    main(args)



    