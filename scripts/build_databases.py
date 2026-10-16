"""Download Hugging Face datasets and build SQLite databases."""
from pathlib import Path
import re
import sqlite3
import pandas as pd
from datasets import load_dataset

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATASETS = {
    "institutions": ("Mahadih534/Institutional-Information-of-Bangladesh", "institutions.db", "institutions"),
    "hospitals": ("Mahadih534/all-bangladeshi-hospitals", "hospitals.db", "hospitals"),
    "restaurants": ("Mahadih534/Bangladeshi-Restaurant-Data", "restaurants.db", "restaurants"),
}
ALIASES = {
    "name": ["name", "institution_name", "hospital_name", "restaurant_name", "institute_name", "title", "school_name", "college_name", "university_name", "organization_name"],
    "location": ["location", "address", "full_address", "district", "city", "area", "place", "upazila", "division"],
    "type": ["type", "category", "institution_type", "hospital_type", "cuisine", "cuisine_type", "institution_category"],
    "capacity": ["capacity", "beds", "bed_capacity", "total_beds", "number_of_beds", "bed_count"],
    "doctors": ["doctors", "doctor_count", "number_of_doctors"],
    "rating": ["rating", "average_rating", "restaurant_rating", "stars"],
}

def clean_column(value):
    name = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip().lower()).strip("_") or "unnamed_column"
    return "column_" + name if name[0].isdigit() else name

def load_dataframe(repo_id):
    print(f"\nLoading dataset: {repo_id}")
    ds = load_dataset(repo_id)
    # Hugging Face DatasetDict exposes split names; Dataset exposes column_names.
    if hasattr(ds, "keys") and not isinstance(ds, pd.DataFrame):
        frames = []
        keys = list(ds.keys())
        for split_name in keys:
            if str(split_name).lower() in {"validation", "valid", "test"}:
                continue
            frame = ds[split_name].to_pandas()
            if str(split_name).lower() in {"train", "training"}:
                frames.insert(0, frame)
            else:
                frames.append(frame)
        if not frames:
            frames = [ds[keys[0]].to_pandas()]
        return pd.concat(frames, ignore_index=True)
    return ds.to_pandas()

def sql_type(series):
    if pd.api.types.is_bool_dtype(series) or pd.api.types.is_integer_dtype(series):
        return "INTEGER"
    if pd.api.types.is_float_dtype(series):
        return "REAL"
    return "TEXT"

def create_database(repo_id, db_name, table):
    df = load_dataframe(repo_id)
    if df.empty:
        raise ValueError(f"Dataset {repo_id} is empty")
    names, used = [], set()
    for original in df.columns:
        base = clean_column(original)
        candidate, n = base, 2
        while candidate in used:
            candidate, n = f"{base}_{n}", n + 1
        names.append(candidate)
        used.add(candidate)
    df.columns = names
    for standard, candidates in ALIASES.items():
        if standard not in df.columns:
            source = next((c for c in candidates if c in df.columns), None)
            if source:
                df[standard] = df[source]
    df = df.astype(object).where(pd.notna(df), None)
    path = DATA_DIR / db_name
    with sqlite3.connect(path) as conn:
        definitions = ", ".join(f'"{col}" {sql_type(df[col])}' for col in df.columns)
        conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.execute(f'CREATE TABLE "{table}" ({definitions})')
        df.to_sql(table, conn, if_exists="append", index=False, chunksize=1000)
        for col in ("name", "location"):
            if col in df.columns:
                conn.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table}_{col}" ON "{table}" ("{col}")')
        conn.commit()
    print(f"Created {path} | table={table} | rows={len(df)}")
    print("Columns:", ", ".join(df.columns))

def main():
    failures = []
    for _, (repo, db, table) in DATASETS.items():
        try:
            create_database(repo, db, table)
        except Exception as exc:
            failures.append((db, str(exc)))
            print(f"ERROR building {db}: {exc}")
    if failures:
        print("\nFailed databases:")
        for db, error in failures:
            print(f"- {db}: {error}")
        raise SystemExit(1)
    print("\nAll three databases created successfully.")

if __name__ == "__main__":
    main()
