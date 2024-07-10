PIPENV_RUN=pipenv run

install:
	pip install pipenv && pipenv install --dev

test:
	$(PIPENV_RUN) nose2 -s tests

test_coverage:
	$(PIPENV_RUN) nose2 -s tests -C --coverage=shinto --coverage-report=term

test_coverage_html:
	$(PIPENV_RUN) nose2 -s tests -C --coverage=shinto --coverage-report=term --coverage-report=html

ruff:
	$(PIPENV_RUN) ruff check .

ruff_format:
	$(PIPENV_RUN) ruff format .

release:
	./release.sh
