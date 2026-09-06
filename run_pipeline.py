from load_data import main as load_data
from src.analysis import run_analysis
from src.frequencies import save_cell_frequencies
from src.queries import run_queries


def main():
    load_data()
    save_cell_frequencies()
    run_analysis()
    run_queries()
    print("Pipeline complete")


if __name__ == "__main__":
    main()
