PDM_RUN=pdm run

install:
	./scripts/install.sh

update:
	./scripts/update.sh

clean:
	./scripts/clean.sh

release:
	./scripts/release.sh

test:
	$(PDM_RUN) nose2 -v -s tests

test_coverage:
	$(PDM_RUN) nose2 -v -s tests -C --coverage=shinto --coverage-report=term --coverage-report=term-missing

test_coverage_html:
	$(PDM_RUN) nose2 -v -s tests -C --coverage=shinto --coverage-report=term --coverage-report=term-missing --coverage-report=html

ruff:
	$(PDM_RUN) ruff check -v .

ruff_format:
	$(PDM_RUN) ruff format -v .

generate_docs:
	$(PDM_RUN) sphinx-apidoc -f -o docs/modules shinto && cd docs && make html

merge_dev:
	git checkout main && git pull && git merge --no-ff -m "Merge development into main" development && git push && git checkout development
