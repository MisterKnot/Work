import sqlite3
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

DB_PATH = Path(__file__).resolve().parent / "vsl_schedule.db"
SEED_PATH = Path(__file__).resolve().parent / "seed_data.json"

SCHEMA = """
CREATE TABLE IF NOT EXISTS schedule_entry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shift TEXT NOT NULL,
    qc INTEGER NOT NULL,
    vessel TEXT NOT NULL,
    service TEXT,
    owner TEXT,
    loa REAL,
    moves INTEGER,
    moves_remaining INTEGER,
    arrival_road TEXT,
    working_start TEXT,
    ets TEXT
);
"""

FIELDS = ("id", "shift", "qc", "vessel", "service", "owner", "loa", "moves",
          "moves_remaining", "arrival_road", "working_start", "ets")


@dataclass
class ScheduleEntry:
    id: Optional[int]
    shift: str
    qc: int
    vessel: str
    service: Optional[str] = None
    owner: Optional[str] = None
    loa: Optional[float] = None
    moves: Optional[int] = None
    moves_remaining: Optional[int] = None
    arrival_road: Optional[str] = None
    working_start: Optional[str] = None
    ets: Optional[str] = None


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def seed_if_empty(conn):
    count = conn.execute("SELECT COUNT(*) FROM schedule_entry").fetchone()[0]
    if count:
        return
    with open(SEED_PATH) as f:
        rows = json.load(f)
    for row in rows:
        conn.execute(
            "INSERT INTO schedule_entry (shift, qc, vessel, service, owner, loa, moves, moves_remaining, arrival_road, working_start, ets) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (row.get("shift"), row.get("qc"), row.get("vessel"), row.get("service"),
             row.get("owner"), row.get("loa"), row.get("moves"), row.get("moves_remaining"),
             row.get("arrival_road"), row.get("working_start"), row.get("ets")),
        )
    conn.commit()


def row_to_entry(row):
    return ScheduleEntry(
        id=row["id"], shift=row["shift"], qc=row["qc"], vessel=row["vessel"],
        service=row["service"], owner=row["owner"], loa=row["loa"], moves=row["moves"],
        moves_remaining=row["moves_remaining"], arrival_road=row["arrival_road"],
        working_start=row["working_start"], ets=row["ets"],
    )


def list_entries(conn, shift=None):
    if shift:
        rows = conn.execute("SELECT * FROM schedule_entry WHERE shift = ? ORDER BY qc", (shift,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM schedule_entry ORDER BY shift, qc").fetchall()
    return [row_to_entry(r) for r in rows]


def get_entry(conn, entry_id):
    row = conn.execute("SELECT * FROM schedule_entry WHERE id = ?", (entry_id,)).fetchone()
    return row_to_entry(row) if row else None


def add_entry(conn, entry: ScheduleEntry):
    cur = conn.execute(
        "INSERT INTO schedule_entry (shift, qc, vessel, service, owner, loa, moves, moves_remaining, arrival_road, working_start, ets) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (entry.shift, entry.qc, entry.vessel, entry.service, entry.owner, entry.loa,
         entry.moves, entry.moves_remaining, entry.arrival_road, entry.working_start, entry.ets),
    )
    conn.commit()
    return cur.lastrowid


def update_entry(conn, entry: ScheduleEntry):
    conn.execute(
        "UPDATE schedule_entry SET shift=?, qc=?, vessel=?, service=?, owner=?, loa=?, moves=?, moves_remaining=?, arrival_road=?, working_start=?, ets=? WHERE id=?",
        (entry.shift, entry.qc, entry.vessel, entry.service, entry.owner, entry.loa,
         entry.moves, entry.moves_remaining, entry.arrival_road, entry.working_start, entry.ets, entry.id),
    )
    conn.commit()


def delete_entry(conn, entry_id):
    conn.execute("DELETE FROM schedule_entry WHERE id = ?", (entry_id,))
    conn.commit()
