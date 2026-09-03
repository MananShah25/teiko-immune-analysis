"""Database schema definition and connection management."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "immune_cells.db"

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

SCHEMA = """
DROP TABLE IF EXISTS cell_counts;
DROP TABLE IF EXISTS samples;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS projects;

CREATE TABLE projects (
    project_id TEXT PRIMARY KEY
);

CREATE TABLE subjects (
    subject_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    condition  TEXT NOT NULL,
    age        INTEGER NOT NULL CHECK (age > 0),
    sex        TEXT NOT NULL CHECK (sex IN ('M', 'F')),
    treatment  TEXT NOT NULL,
    response   TEXT CHECK (response IN ('yes', 'no')),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE samples (
    sample_id                 TEXT PRIMARY KEY,
    subject_id                TEXT NOT NULL,
    sample_type               TEXT NOT NULL,
    time_from_treatment_start INTEGER NOT NULL CHECK (time_from_treatment_start >= 0),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

CREATE TABLE cell_counts (
    sample_id  TEXT NOT NULL,
    population TEXT NOT NULL,
    count      INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population),
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
);

CREATE INDEX idx_subjects_cohort   ON subjects(condition, treatment, response);
CREATE INDEX idx_subjects_project  ON subjects(project_id);
CREATE INDEX idx_samples_subject   ON samples(subject_id);
CREATE INDEX idx_samples_filter    ON samples(sample_type, time_from_treatment_start);
CREATE INDEX idx_counts_population ON cell_counts(population);
"""


def get_connection(db_path=DB_PATH):
    """Open a SQLite connection with foreign key enforcement enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_schema(conn):
    """Drop and recreate all tables. Safe to run repeatedly."""
    conn.executescript(SCHEMA)
    conn.commit()
