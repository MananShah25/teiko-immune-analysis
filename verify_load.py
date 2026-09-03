"""
Optional integrity verification for the loaded database.

Run with:  python verify_load.py
Exits non-zero if any check fails.
"""

import sys
from pathlib import Path

import pandas as pd

from src.db import POPULATIONS, get_connection

CSV_PATH = Path(__file__).resolve().parent / "data" / "cell-count.csv"


def check(label, passed, detail=""):
    mark = "PASS" if passed else "FAIL"
    print(f"  [{mark}] {label}{f' — {detail}' if detail else ''}")
    return passed


def main():
    conn = get_connection()
    scalar = lambda q: conn.execute(q).fetchone()[0]
    results = []

    print("\nIntegrity checks")
    print("-" * 60)

    orphan_samples = scalar(
        "SELECT COUNT(*) FROM samples s "
        "LEFT JOIN subjects u ON s.subject_id = u.subject_id "
        "WHERE u.subject_id IS NULL"
    )
    results.append(check("No orphan samples", orphan_samples == 0, f"{orphan_samples} found"))

    orphan_counts = scalar(
        "SELECT COUNT(*) FROM cell_counts c "
        "LEFT JOIN samples s ON c.sample_id = s.sample_id "
        "WHERE s.sample_id IS NULL"
    )
    results.append(check("No orphan cell counts", orphan_counts == 0, f"{orphan_counts} found"))

    bad_pop = scalar(
        "SELECT COUNT(*) FROM ("
        "  SELECT sample_id FROM cell_counts GROUP BY sample_id "
        f"  HAVING COUNT(*) != {len(POPULATIONS)}"
        ")"
    )
    n_samples = scalar("SELECT COUNT(*) FROM samples")
    results.append(
        check(
            f"Every sample has exactly {len(POPULATIONS)} populations",
            bad_pop == 0,
            f"{n_samples:,} samples checked",
        )
    )

    bad_null = scalar(
        "SELECT COUNT(*) FROM subjects "
        "WHERE response IS NULL AND NOT (condition = 'healthy' AND treatment = 'none')"
    )
    n_null = scalar("SELECT COUNT(*) FROM subjects WHERE response IS NULL")
    results.append(
        check(
            "NULL response only for healthy/untreated subjects",
            bad_null == 0,
            f"{n_null} such subjects",
        )
    )

    db_total = scalar("SELECT SUM(count) FROM cell_counts")
    csv_total = int(pd.read_csv(CSV_PATH)[POPULATIONS].values.sum())
    results.append(
        check(
            "Total cell count matches source CSV",
            db_total == csv_total,
            f"{db_total:,}",
        )
    )

    print("-" * 60)
    conn.close()

    if all(results):
        print(f"All {len(results)} checks passed.\n")
    else:
        print(f"{results.count(False)} of {len(results)} checks FAILED.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
