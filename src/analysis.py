from pathlib import Path
import os

import pandas as pd
from scipy.stats import mannwhitneyu

try:
    from src.db import get_connection
except ModuleNotFoundError:
    from db import get_connection


TABLE_DIR = Path(__file__).resolve().parent.parent/"outputs"/"tables"
FIGURE_DIR = Path(__file__).resolve().parent.parent/"outputs"/"figures"
CACHE_DIR = Path(__file__).resolve().parent.parent/"outputs"/".matplotlib"

os.environ.setdefault("MPLCONFIGDIR",str(CACHE_DIR))

import matplotlib.pyplot as plt


def get_response_frequencies(conn):
    query = """
    WITH sample_totals AS (
        SELECT sample_id, SUM(count) AS total_count
        FROM cell_counts
        GROUP BY sample_id)
    SELECT
        c.sample_id AS sample,
        u.subject_id AS subject,
        u.response,
        s.time_from_treatment_start AS timepoint,
        c.population,
        ROUND(100.0 * c.count / t.total_count, 4) AS percentage
    FROM cell_counts c
    JOIN sample_totals t
        ON c.sample_id = t.sample_id
    JOIN samples s
        ON c.sample_id = s.sample_id
    JOIN subjects u
        ON s.subject_id = u.subject_id
    WHERE
        u.condition = 'melanoma'
        AND u.treatment = 'miraclib'
        AND s.sample_type = 'PBMC'
        AND u.response IN ('yes', 'no')
    ORDER BY c.population, u.response, c.sample_id
    """
    return pd.read_sql_query(query, conn)


def adjust_pvalues(pvalues):
    values = pd.Series(pvalues, dtype=float)
    order = values.sort_values().index
    adjusted = pd.Series(index=values.index, dtype=float)
    running_min = 1.0

    for rank, idx in reversed(list(enumerate(order, start=1))):
        running_min = min(running_min, values.loc[idx] * len(values) / rank)
        adjusted.loc[idx] = running_min

    return adjusted.clip(upper=1.0)


def run_response_stats(df):
    rows = []

    for population, group in df.groupby("population"):
        responders = group.loc[group["response"] == "yes", "percentage"]
        non_responders = group.loc[group["response"] == "no", "percentage"]
        test = mannwhitneyu(responders, non_responders, alternative="two-sided")

        rows.append(
            {
                "population": population,
                "responder_median": round(responders.median(), 4),
                "non_responder_median": round(non_responders.median(), 4),
                "median_difference": round(responders.median() - non_responders.median(), 4),
                "p_value": test.pvalue,
            }
        )

    results = pd.DataFrame(rows).sort_values("p_value")
    results["p_value_adj"] = adjust_pvalues(results["p_value"])
    results["significant"] = results["p_value_adj"] < 0.05
    return results


def save_response_plot(df, output_path):
    populations = sorted(df["population"].unique())
    positions = range(len(populations))

    fig, ax = plt.subplots(figsize=(10, 6))
    for offset, response, color in [(-0.18, "no", "#9CA3AF"), (0.18, "yes", "#2563EB")]:
        values = [
            df.loc[(df["population"] == population) & (df["response"] == response), "percentage"]
            for population in populations
        ]
        ax.boxplot(
            values,
            positions=[pos + offset for pos in positions],
            widths=0.3,
            patch_artist=True,
            boxprops={"facecolor": color, "alpha": 0.75},
            medianprops={"color": "black"},
        )

    ax.set_xticks(list(positions))
    ax.set_xticklabels(populations)
    ax.set_xlabel("Cell population")
    ax.set_ylabel("Relative frequency (%)")
    ax.set_title("Melanoma PBMC samples treated with miraclib")
    ax.legend(
        handles=[
            plt.Line2D([0], [0], color="#9CA3AF", lw=8, label="non-responder"),
            plt.Line2D([0], [0], color="#2563EB", lw=8, label="responder"),
        ]
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def run_analysis():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    try:
        df = get_response_frequencies(conn)
    finally:
        conn.close()

    stats = run_response_stats(df)

    df.to_csv(TABLE_DIR / "response_frequencies.csv", index=False)
    stats.to_csv(TABLE_DIR / "response_stats.csv", index=False)
    save_response_plot(df, FIGURE_DIR / "response_frequency_boxplot.png")

    return df, stats


def main():
    df, stats = run_analysis()
    print(f"Wrote {len(df)} comparison rows")
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
