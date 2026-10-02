# Vessel Schedule App (PCT)

Digitalizes the PCT daily vessel schedule (Excel) into a Flet desktop/web app.

## Run
```
pip install -r requirements.txt
python main.py
```

- Data is stored in `vsl_schedule.db` (SQLite), seeded on first run from
  `seed_data.json` (extracted from `VslSchedule 021026.xlsx`).
- Three shift tabs: MORNING / AFTERNOON / NIGHT, matching the Excel layout.
- Search, add, edit, delete vessel schedule entries.
