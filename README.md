# exam-positioner
Script per la disposizione degli studenti iscritti a un esame nelle classi.
Inserire le mappe delle aule [qui](https://docs.google.com/spreadsheets/d/1yuDN40n8pcoP2FgjUwuR6oxKvNRSa2jbJTVhOrsB5_A/edit?usp=sharing), con una configurazione simile al foglio "Aule R". In alternativa è possibile utilizzare un file locale in formato `*.xlsx` o `*.csv`.

A partire dall'elenco degli studenti iscritti all'esame (export VISAP del portale della didattica, in formato `*.csv` o Excel) e dalla lista delle aule da utilizzare, lo script genera un file Excel con le mappe di ciascuna aula e l'elenco complessivo degli studenti con aula e posto al quale sono stati assegnati.
**IMPORTANTE:** le aule devono essere rappresentate con la cattedra in basso, le file numerate in maniera crescente, lasciando uno spazio nel caso in cui non sia presente una fila.

Il file di configurazione `riferimenti_aule.yaml` nella cartella d'esame, se presente, ha priorità. Altrimenti le aule si indicano con `-r` e vengono risolte tramite `riferimenti_aule_all.yaml` (foglio Excel e riquadro della mappa, ad esempio `B1:W20`).

## Utilizzo

```
python find_disposition.py -f FOLDER [-r ROOMS] [--nopc_students MAT,MAT]
                           [--nopc_room 5T] [--dsa_room ROOM] [-n NAME]
                           [--order cognome] [--nostyle]
```

Esempio:

```
python find_disposition.py -f BigData_20260910 -r R1,R4
```

- `-f FOLDER` cartella con i file `VISAP_Elenco_Studenti_*`. Se sono presenti sia CSV sia XLS/XLSX, vengono usati solo i CSV.
- `-r ROOMS` aule separate da virgola (oppure `riferimenti_aule.yaml` nella cartella).
- `--order` ordinamento: `cognome` (default), `matricola`, `random`.
- `--nopc_students` / `--nopc_room` studenti da mettere in aula senza PC.
- `--dsa_room` aula per studenti DSA / tempo aggiuntivo (default: prima aula).
- `--nostyle` disabilita la colorazione a scacchiera.

Output nella stessa cartella: `<nome>_disposizioni.xlsx` (mappe, con il nome aula in A1), `<nome>_prenotati.xlsx`, `<nome>_limiti.txt`.
