"""Read-only SQLite search tools for the Bangladesh datasets."""
from pathlib import Path
import re
import sqlite3
from langchain_core.tools import tool

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STOP_WORDS = set("how many much what where which who are is the a an of in on at to for from find show give me all list tell about please can you there number count total dataset database records hospitals hospital institutions institution restaurants restaurant universities university colleges college information bangladesh data available located near search get display details provide institute".split())

def search_database(db_name, table, question):
    path = DATA_DIR / db_name
    if not path.exists():
        return f"Database {db_name} is missing. Run python scripts/build_databases.py first."
    try:
        with sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
            if not columns:
                return f"Table {table} is missing from {db_name}."
            terms = list(dict.fromkeys(w.lower() for w in re.findall(r"[a-zA-Z0-9]+", question) if len(w) > 1 and w.lower() not in STOP_WORDS))
            count_question = bool(re.search(r"\b(how many|count|number of|total)\b", question.lower()))
            searchable = [c for c in columns if c.lower() not in {"id", "index"}]
            if not terms:
                total = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                rows = conn.execute(f'SELECT * FROM "{table}" LIMIT 5').fetchall()
                return f"Total records: {total}\nColumns: {columns}\nSample: {[dict(r) for r in rows]}"
            clauses, params = [], []
            for term in terms:
                clauses.append("(" + " OR ".join(f'CAST("{c}" AS TEXT) LIKE ?' for c in searchable) + ")")
                params.extend([f"%{term}%"] * len(searchable))
            where = " AND ".join(clauses)
            if count_question:
                total = conn.execute(f'SELECT COUNT(*) FROM "{table}" WHERE {where}', params).fetchone()[0]
                examples = conn.execute(f'SELECT * FROM "{table}" WHERE {where} LIMIT 5', params).fetchall()
                return f"Matching dataset records: {total}\nSearch terms: {terms}\nSample records: {[dict(r) for r in examples]}"
            rows = conn.execute(f'SELECT * FROM "{table}" WHERE {where} LIMIT 10', params).fetchall()
            if not rows:
                return f"No matching records found in {table} for: {question}"
            return f"Found {len(rows)} matching records (maximum 10 shown):\n" + "\n".join(str(dict(r)) for r in rows)
    except sqlite3.Error as exc:
        return f"Database query failed: {exc}"

@tool
def institutions_db_tool(question: str) -> str:
    """Search the supplied institutions dataset for universities, colleges, schools, government institutions, locations, and record counts."""
    return search_database("institutions.db", "institutions", question)

@tool
def hospitals_db_tool(question: str) -> str:
    """Search the supplied hospital dataset for hospital names, locations, facilities, bed counts, doctors, and record counts."""
    return search_database("hospitals.db", "hospitals", question)

@tool
def restaurants_db_tool(question: str) -> str:
    """Search the supplied restaurant dataset for restaurant names, locations, cuisine, ratings, and record counts."""
    return search_database("restaurants.db", "restaurants", question)
