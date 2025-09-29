# Boggle (Flask)

Eén-speler Boggle als Python/Flask webapp. Woordenvalidatie, timer/training-modus en basisstatistieken.  
**Status:** Archived · **Rol:** Duo (coursework) · **Jaar:** 2023

## Tech stack
Python · Flask · Jinja2 · SQLite

## Highlights
- Valideert woorden tegen meegeleverde woordenlijst
- Speel met **timer (3 min)** of in **training-modus**
- **Variabel grid** (2×2 t/m 9×9)
- Per speler: naam, sessies en scores opgeslagen (SQLite)

## Snel starten
```bash
# Vereisten: Python 3.11+
git clone https://github.com/<jouw-user>/boggle-flask-2023.git
cd boggle-flask-2023
python -m venv .venv && . .venv/Scripts/activate  # Windows
# of: python3 -m venv .venv && source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
# Optioneel: set SECRET_KEY voor Flask sessions
# PowerShell: $env:SECRET_KEY="dev-secret"
python app.py   # of: flask run --host 0.0.0.0 --port 5000
