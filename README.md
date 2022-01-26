# exam-positioner
Script per la disposizione degli studenti iscritti a un esame nelle classi, matricola per matricola. Inserire le mappe delle aule [qui](https://docs.google.com/spreadsheets/d/1yuDN40n8pcoP2FgjUwuR6oxKvNRSa2jbJTVhOrsB5_A/edit?usp=sharing), con una configurazione simile al foglio "Aule R". In alternativa è possibile utilizzare un file locale in formato '\*.csv'.

A partire dall'elenco degli studenti iscritti all'esame (fornito dal portale della didattica, in formato '\*.xlsx') e dalla lista delle aule da utilizzare, lo script genera un file Excel con le mappe di ciascuna aula e l'elenco complessivo degli studenti con aula e posto al quale sono stati assegnati. 
**IMPORTANTE:** le aule devono essere rappresentate con la cattedra in basso, le file numerate in maniera crescente, lasciando uno spazio nel caso in cui non sia presenta una fila. 

Il file di configurazione `riferimenti_aule.yaml` deve contenere per ogni aula utilizzata i riferimenti del foglio Excel da considerare e il riquadro nella quale è posizionata la mappa (ad esempio `B1:W20`, considerando gli indici di righe e colonne).

## Utilizzo
Lanciare lo script in questo modo:
```
find_disposition.py [-h] [-s STUDENTS] [--excluded_students EXCLUDED_STUDENTS]
                    [--multimedia_room MULTIMEDIA_ROOM] [-y YCONFIG] [-n NAME]
                    [--style] [rooms ...]

positional arguments:
  rooms                 La lista delle aule nelle quali dividere gli studenti.

optional arguments:
  -h, --help            show this help message and exit
  -s STUDENTS, --students STUDENTS
                        Percorso del file Excel contenente l'elenco degli studenti prenotati.
  --excluded_students EXCLUDED_STUDENTS
                        Lista delle matricole (senza spazi, separate da virgola) degli studenti che
                        necessitano di essere posizionati in aula multimediale.
  --multimedia_room MULTIMEDIA_ROOM
                        Aula multimediale nella quale inserire excluded_students. Default è '5T'.
  -y YCONFIG, --yconfig YCONFIG
                        File con le posizioni delle tabelle all'interno di 'args.maps'.
  -n NAME, --name NAME  Nome dei files di output. Default: '<COD>_yyyymmdd'.
  --style, Add style to the resulting sheet (Applica una colorazione a scacchiera sulle mappe in output).
```