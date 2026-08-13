import sys
from datetime import date

if len(sys.argv) != 2:
    print("Usage : python fetch_data.py YYYY-MM-DD")
    sys.exit(1)

date_arg = sys.argv[1]

try:
    start_date = date.fromisoformat(date_arg)
except ValueError:
    print(f"Erreur : '{date_arg}' n'est pas une date valide (format attendu : YYYY-MM-DD)")
    sys.exit(1)

print(start_date)
