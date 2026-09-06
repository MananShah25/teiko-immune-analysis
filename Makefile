PYTHON ?= python3

.PHONY: setup pipeline dashboard verify

setup:
	$(PYTHON) -m pip install -r requirements.txt

pipeline:
	$(PYTHON) run_pipeline.py

dashboard:
	$(PYTHON) -m streamlit run dashboard.py

verify:
	$(PYTHON) verify_load.py
