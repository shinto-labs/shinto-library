PDM_RUN=pdm run

install:
	pdm sync

update:
	pdm lock --refresh
	pdm update

clean:
	pdm cache clear
	find . -name "__pycache__" | xargs rm -rf
	find . -name "build" | xargs rm -rf
	find . -name ".coverage" | xargs rm -rf
	find . -name "*,cover" | xargs rm -rf
	find . -name "htmlcov" | xargs rm -rf
	find . -name ".ruff_cache" | xargs rm -rf
	find . -name "*.egg-info" | xargs rm -rf
	find . -name ".venv" | xargs rm -rf
	find . -name ".pdm-python" | xargs rm -rf

release:
	./.github/release.sh

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
