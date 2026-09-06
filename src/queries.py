from pathlib import Path

import pandas as pd

try:
    from src.db import get_connection
except ModuleNotFoundError:
    from db import get_connection


TABLE_DIR = Path(__file__).resolve().parent.parent/"outputs"/"tables"


def get_baseline_samples(conn):
    query = """
    SELECT
        s.sample_id AS sample,
        u.subject_id AS subject,
        u.project_id AS project,
        u.response,
        u.sex,
        s.sample_type,
        s.time_from_treatment_start AS timepoint
    FROM samples s
    JOIN subjects u
        ON s.subject_id=u.subject_id
    WHERE
        u.condition='melanoma'
        AND u.treatment='miraclib'
        AND s.sample_type='PBMC'
        AND s.time_from_treatment_start=0
    ORDER BY u.project_id, s.sample_id
    """
    return pd.read_sql_query(query, conn)


def get_samples_by_project(conn):
    query = """
    SELECT
        u.project_id AS project,
        COUNT(*) AS sample_count
    FROM samples s
    JOIN subjects u
        ON s.subject_id=u.subject_id
    WHERE
        u.condition='melanoma'
        AND u.treatment='miraclib'
        AND s.sample_type='PBMC'
        AND s.time_from_treatment_start=0
    GROUP BY u.project_id
    ORDER BY u.project_id
    """
    return pd.read_sql_query(query, conn)


def get_subjects_by_response(conn):
    query = """
    SELECT
        u.response,
        COUNT(DISTINCT u.subject_id) AS subject_count
    FROM samples s
    JOIN subjects u
        ON s.subject_id=u.subject_id
    WHERE
        u.condition='melanoma'
        AND u.treatment='miraclib'
        AND s.sample_type='PBMC'
        AND s.time_from_treatment_start=0
    GROUP BY u.response
    ORDER BY u.response
    """
    return pd.read_sql_query(query, conn)


def get_subjects_by_sex(conn):
    query = """
    SELECT
        u.sex,
        COUNT(DISTINCT u.subject_id) AS subject_count
    FROM samples s
    JOIN subjects u
        ON s.subject_id=u.subject_id
    WHERE
        u.condition='melanoma'
        AND u.treatment='miraclib'
        AND s.sample_type='PBMC'
        AND s.time_from_treatment_start=0
    GROUP BY u.sex
    ORDER BY u.sex
    """
    return pd.read_sql_query(query, conn)


def get_male_responder_bcell_average(conn):
    query = """
    SELECT
        ROUND(AVG(c.count), 2) AS avg_b_cell_count
    FROM cell_counts c
    JOIN samples s
        ON c.sample_id=s.sample_id
    JOIN subjects u
        ON s.subject_id=u.subject_id
    WHERE
        u.condition='melanoma'
        AND u.sex='M'
        AND u.response='yes'
        AND s.time_from_treatment_start=0
        AND c.population='b_cell'
    """
    return pd.read_sql_query(query, conn)


def run_queries():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        outputs = {
            "baseline_samples": get_baseline_samples(conn),
            "baseline_samples_by_project": get_samples_by_project(conn),
            "baseline_subjects_by_response": get_subjects_by_response(conn),
            "baseline_subjects_by_sex": get_subjects_by_sex(conn),
            "melanoma_male_responder_bcell_average": get_male_responder_bcell_average(conn),
        }
    finally:
        conn.close()

    for name, df in outputs.items():
        df.to_csv(TABLE_DIR/f"{name}.csv", index=False)

    return outputs


def main():
    outputs = run_queries()
    for name, df in outputs.items():
        print(f"{name}: {len(df)} rows")


if __name__ == "__main__":
    main()
