"""
Part 1: Initialize the SQLite database and load cell-count.csv.

Run with:  python load_data.py
"""

import sys
from pathlib import Path

import pandas as pd

from src.db import DB_PATH, POPULATIONS, get_connection, initialize_schema

CSV_PATH = Path(__file__).resolve().parent / "data" / "cell-count.csv"

SUBJECT_COLS = ["subject", "project", "condition", "age", "sex", "treatment", "response"]
SAMPLE_COLS = ["sample", "subject", "sample_type", "time_from_treatment_start"]


def read_source(csv_path=CSV_PATH):
    """Read the raw CSV and validate that every expected column is present."""
    if not csv_path.exists():
        sys.exit(f"ERROR: CSV not found at {csv_path}")

    df = pd.read_csv(csv_path)

    expected = set(SUBJECT_COLS) | set(SAMPLE_COLS) | set(POPULATIONS)
    missing = expected - set(df.columns)
    if missing:
        sys.exit(f"ERROR: CSV is missing expected columns: {sorted(missing)}")

    return df


def to_rows(df):
    """Convert a DataFrame to a list of tuples with NaN mapped to None."""
    return list(df.astype(object).where(pd.notna(df), None).itertuples(index=False, name=None))


def build_frames(df):
    """Split the flat CSV into the four normalized tables."""
    projects = df[["project"]].drop_duplicates().sort_values("project")

    subjects = (
        df[SUBJECT_COLS]
        .drop_duplicates()
        .sort_values("subject")
        .reset_index(drop=True)
    )

    samples = (
        df[SAMPLE_COLS]
        .drop_duplicates()
        .sort_values("sample")
        .reset_index(drop=True)
    )

    counts = df.melt(
        id_vars=["sample"],
        value_vars=POPULATIONS,
        var_name="population",
        value_name="count",
    ).sort_values(["sample", "population"])

    return projects, subjects, samples, counts


def validate(df, subjects, samples):
    """Fail loudly if the source data violates our normalization assumptions."""
    if subjects["subject"].duplicated().any():
        sys.exit("ERROR: subject attributes are not stable across rows.")
    if samples["sample"].duplicated().any():
        sys.exit("ERROR: duplicate sample_id with conflicting attributes.")
    if df["sample"].duplicated().any():
        sys.exit("ERROR: duplicate sample_id in source CSV.")


def load(conn, projects, subjects, samples, counts):
    """Insert all rows in dependency order inside a single transaction."""
    conn.executemany("INSERT INTO projects VALUES (?)", to_rows(projects))
    conn.executemany(
        "INSERT INTO subjects (subject_id, project_id, condition, age, sex, treatment, response) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        to_rows(subjects),
    )
    conn.executemany(
        "INSERT INTO samples (sample_id, subject_id, sample_type, time_from_treatment_start) "
        "VALUES (?, ?, ?, ?)",
        to_rows(samples),
    )
    conn.executemany(
        "INSERT INTO cell_counts (sample_id, population, count) VALUES (?, ?, ?)",
        to_rows(counts),
    )
    conn.commit()


def report(conn):
    n_samples = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
    print(f"Loaded {n_samples} samples into {DB_PATH.name}")


def main():
    df = read_source()
    print(f"Read {len(df):,} rows from {CSV_PATH.name}")

    projects, subjects, samples, counts = build_frames(df)
    validate(df, subjects, samples)

    conn = get_connection()
    try:
        initialize_schema(conn)
        load(conn, projects, subjects, samples, counts)
        report(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
