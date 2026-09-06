from pathlib import Path

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
TABLE_DIR = ROOT/"outputs"/"tables"
FIGURE_PATH = ROOT/"outputs"/"figures"/"response_frequency_boxplot.png"


@st.cache_data
def read_csv(name):
    return pd.read_csv(TABLE_DIR/name)


st.set_page_config(page_title="Immune Cell Analysis", layout="wide")
st.title("Immune Cell Analysis")

cell_freq = read_csv("cell_frequencies.csv")
response_freq = read_csv("response_frequencies.csv")
response_stats = read_csv("response_stats.csv")
baseline = read_csv("baseline_samples.csv")
by_project = read_csv("baseline_samples_by_project.csv")
by_response = read_csv("baseline_subjects_by_response.csv")
by_sex = read_csv("baseline_subjects_by_sex.csv")
bcell_avg = read_csv("melanoma_male_responder_bcell_average.csv")

col1, col2, col3 = st.columns(3)
col1.metric("Samples", cell_freq["sample"].nunique())
col2.metric("Frequency rows", len(cell_freq))
col3.metric("Baseline subset", len(baseline))

tab1, tab2, tab3 = st.tabs(["Frequencies", "Response analysis", "Subset questions"])

with tab1:
    populations = sorted(cell_freq["population"].unique())
    selected = st.multiselect("Population", populations, default=populations)
    view = cell_freq[cell_freq["population"].isin(selected)]
    st.dataframe(view, use_container_width=True)

with tab2:
    if FIGURE_PATH.exists():
        st.image(str(FIGURE_PATH))

    significant = response_stats[response_stats["significant"].astype(bool)]
    if significant.empty:
        best = response_stats.loc[response_stats["p_value"].idxmin()]
        st.info(
            "No population shows a statistically significant difference after "
            f"Benjamini-Hochberg correction. The strongest signal is `{best['population']}` "
            f"(raw p = {best['p_value']:.4f}, adjusted p = {best['p_value_adj']:.4f})."
        )
    else:
        names = ", ".join(f"`{p}`" for p in significant["population"])
        st.info(
            f"Significant difference after Benjamini-Hochberg correction: {names}."
        )

    st.dataframe(response_stats, use_container_width=True)

with tab3:
    st.subheader("Baseline melanoma PBMC samples treated with miraclib")
    st.dataframe(baseline, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.dataframe(by_project, use_container_width=True)
    col2.dataframe(by_response, use_container_width=True)
    col3.dataframe(by_sex, use_container_width=True)

    st.subheader("Additional B-cell question")
    avg = bcell_avg.loc[0, "avg_b_cell_count"]
    st.metric("Average B cells for melanoma male responders at time 0", f"{avg:.2f}")
