PYTHON=python

setup:
	$(PYTHON) -m pip install -r requirements.txt

pipeline:
	$(PYTHON) run_pipeline.py

dashboard:
	streamlit run dashboard.py
