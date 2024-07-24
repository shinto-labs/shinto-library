PIPENV_RUN=pipenv run

install:
	./scripts/install.sh

release:
	./scripts/release.sh

merge_into_main:
	./scripts/merge_into_main.sh

clean:
	./scripts/clean.sh

hard_clean:
	./scripts/clean.sh --hard

test:
	$(PIPENV_RUN) nose2 -v -s tests

test_coverage:
	$(PIPENV_RUN) nose2 -v -s tests -C --coverage=shinto --coverage-report=term

test_coverage_html:
	$(PIPENV_RUN) nose2 -v -s tests -C --coverage=shinto --coverage-report=term --coverage-report=html

ruff:
	$(PIPENV_RUN) ruff check -v .

ruff_format:
	$(PIPENV_RUN) ruff format -v .
