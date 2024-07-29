PDM_RUN=pdm run

install:
	./scripts/install.sh

clean:
	./scripts/clean.sh

release:
	./scripts/release.sh

test:
	$(PDM_RUN) nose2 -v -s tests

test_coverage:
	$(PDM_RUN) nose2 -v -s tests -C --coverage=shinto --coverage-report=term

test_coverage_html:
	$(PDM_RUN) nose2 -v -s tests -C --coverage=shinto --coverage-report=term --coverage-report=html

ruff:
	$(PDM_RUN) ruff check -v .

ruff_format:
	$(PDM_RUN) ruff format -v .
