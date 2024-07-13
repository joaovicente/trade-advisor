clean:
	rm -rf .venv/

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

teardown:
	deactivate