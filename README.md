# Teiko Immune Cell Analysis

This project analyzes immune cell count data from clinical trial samples. The goal is to load the raw CSV into a SQLite database, calculate cell population frequencies, compare responder and non-responder groups, and answer the requested subset questions.

The project creates reproducible output tables, a response comparison plot, and a small Streamlit dashboard to review the results.

Live dashboard: https://teiko-immune-analysis-ms.streamlit.app/

## How to run

Run these commands from the repository root.

```bash
make setup
make pipeline
make dashboard
```

`make setup` installs the required Python packages.

`make pipeline` rebuilds the SQLite database and regenerates all tables and figures.

`make dashboard` starts the Streamlit dashboard.

After starting the dashboard locally, open:

```text
http://localhost:8501
```

In GitHub Codespaces, open the forwarded port for `8501` to view the dashboard.

## Project structure

```text
data/cell-count.csv              Input data file
load_data.py                     Loads the CSV into SQLite
run_pipeline.py                  Runs the full analysis pipeline
src/db.py                        Database schema and connection setup
src/frequencies.py               Creates the cell frequency table
src/analysis.py                  Runs the responder vs non-responder analysis
src/queries.py                   Runs the subset queries and the additional B-cell query
dashboard.py                     Streamlit dashboard
outputs/tables/                  Generated CSV files
outputs/figures/                 Generated plot
Makefile                         Commands used for setup, pipeline, and dashboard
```

I split the code by task so each file has one main job. The database setup is separate from the analysis code, and `run_pipeline.py` connects the steps in the same order as the assignment. This makes the project easier to run again or change later without putting everything into one long script.

## Database schema

The project uses a SQLite database named `immune_cells.db`. The schema has four main tables:

```text
projects
subjects
samples
cell_counts
```

`projects` stores one row for each project in the dataset.

`subjects` stores subject-level information, including project, condition, age, sex, treatment, and response.

`samples` stores sample-level information, including sample type and time from treatment start.

`cell_counts` stores one row for each sample and immune cell population. Each sample has rows for `b_cell`, `cd8_t_cell`, `cd4_t_cell`, `nk_cell`, and `monocyte`.

The source CSV is flat, so the same subject information appears repeatedly across multiple samples. The database separates project, subject, sample, and cell count information so the repeated metadata is stored in a cleaner way. This also makes the SQL queries easier to write because filters such as treatment, response, sample type, and timepoint are connected through clear table relationships.

This design would also scale better than keeping everything in one wide table. If there were hundreds of projects and thousands of samples, new projects and samples could be added without changing the whole schema. If more immune cell populations were added later, they could be stored as additional rows in `cell_counts` instead of adding many new columns.

## Part 1: Data loading

`load_data.py` initializes the database schema and loads all rows from `data/cell-count.csv`.

Run it directly with:

```bash
python load_data.py
```

The loading script reads the CSV, checks that the expected columns are present, and then splits the file into relational tables. Project values go into `projects`, subject metadata goes into `subjects`, sample metadata goes into `samples`, and the five cell count columns are reshaped into the `cell_counts` table. The database is recreated each time the script runs so the pipeline starts from a clean version of the input data.

## Part 2: Cell frequency table

Part 2 calculates the relative frequency of each immune cell population in each sample.

For each sample, the total count is calculated by summing:

```text
b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte
```

Then each population percentage is calculated as:

```text
count / total_count * 100
```

The output file is:

```text
outputs/tables/cell_frequencies.csv
```

The output columns are:

```text
sample, total_count, population, count, percentage
```

This table is useful because raw counts are harder to compare when samples have different total cell counts. Converting the counts to percentages gives a common scale across samples. The same frequency values are also used later for the responder versus non-responder comparison.

## Part 3: Statistical analysis

Part 3 compares immune cell relative frequencies between responders and non-responders.

The comparison is limited to:

```text
condition = melanoma
treatment = miraclib
sample_type = PBMC
response = yes or no
```

For each immune cell population, the analysis compares the sample-level percentage values for responders against the sample-level percentage values for non-responders. The Mann-Whitney U test is used because it compares two groups without requiring a normal distribution assumption. Since five populations are tested, the p-values are adjusted with the Benjamini-Hochberg method.

Generated files:

```text
outputs/tables/response_frequencies.csv
outputs/tables/response_stats.csv
outputs/figures/response_frequency_boxplot.png
```

The strongest raw difference was for `cd4_t_cell`, with a raw p-value of about `0.0133`. After Benjamini-Hochberg correction, its adjusted p-value was about `0.0667`, so it was not significant at the `0.05` level. Based on this sample-level analysis, there is not enough statistical evidence to say that any one immune cell population clearly differs between responders and non-responders.

## Part 4: Subset analysis

Part 4 looks at baseline melanoma PBMC samples from subjects treated with `miraclib`.

The filter is:

```text
condition = melanoma
treatment = miraclib
sample_type = PBMC
time_from_treatment_start = 0
```

Generated files:

```text
outputs/tables/baseline_samples.csv
outputs/tables/baseline_samples_by_project.csv
outputs/tables/baseline_subjects_by_response.csv
outputs/tables/baseline_subjects_by_sex.csv
```

Results:

```text
Baseline samples: 656

Samples by project:
prj1: 384
prj3: 272

Subjects by response:
no: 325
yes: 331

Subjects by sex:
F: 312
M: 344
```

The baseline subset has 656 samples. These samples come from `prj1` and `prj3`, and the responder and non-responder counts are fairly close. The male and female counts are also reasonably balanced, with a slightly higher number of male subjects in this subset.

## Additional B-cell question

The final B-cell question is separate from Part 4. It considers melanoma male responders at time `0` across all sample types and treatment types.

Generated file:

```text
outputs/tables/melanoma_male_responder_bcell_average.csv
```

Result:

```text
Average B cells: 10206.15
```

This means that among melanoma male responders at time `0`, the average B-cell count is `10206.15` when all sample types and treatment types are included.

## Dashboard

The dashboard shows the main output tables and the response comparison plot in one place. It includes summary metrics, the full frequency table, the responder versus non-responder boxplot, the statistical results, the Part 4 subset outputs, and the additional B-cell result.

The deployed version is available here:

```text
https://teiko-immune-analysis-ms.streamlit.app/
```

To run it locally instead:

```bash
make dashboard
```

Local dashboard URL:

```text
http://localhost:8501
```

In Codespaces, this same dashboard is available through the forwarded `8501` port.

## Reproducibility

All generated files can be recreated from the input CSV by running:

```bash
make pipeline
```

The pipeline rebuilds the database from `data/cell-count.csv` and regenerates the tables and figure in `outputs/`. This keeps the submitted results tied to the source data instead of relying on manually edited output files.

To confirm the loaded database matches the source CSV, run:

```bash
make verify
```

This runs `verify_load.py`, which checks for orphaned rows, confirms every sample has all five populations, and reconciles the total cell count against the CSV.
