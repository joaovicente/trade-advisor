clean:
	rm -rf .venv/

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "Execute following command to activate your virtual environment:"
	@echo "source .venv/bin/activate"

teardown:
	deactivate