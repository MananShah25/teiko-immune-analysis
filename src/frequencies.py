from pathlib import Path

import pandas as pd

try:
    from src.db import get_connection
except ModuleNotFoundError:
    from db import get_connection


OUTPUT_PATH = Path(__file__).resolve().parent.parent / "outputs" / "tables" / "cell_frequencies.csv"


def get_cell_frequencies(conn):
    query = """
    WITH sample_totals AS (
        SELECT
            sample_id,
            SUM(count) AS total_count
        FROM cell_counts
        GROUP BY sample_id
    )
    SELECT
        c.sample_id AS sample,
        t.total_count,
        c.population,
        c.count,
        ROUND(100.0 * c.count / t.total_count, 4) AS percentage
    FROM cell_counts c
    JOIN sample_totals t
        ON c.sample_id = t.sample_id
    ORDER BY c.sample_id, c.population
    """
    return pd.read_sql_query(query, conn)


def save_cell_frequencies(output_path=OUTPUT_PATH):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        df = get_cell_frequencies(conn)
    finally:
        conn.close()

    df.to_csv(output_path, index=False)
    return df


def main():
    df = save_cell_frequencies()
    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
