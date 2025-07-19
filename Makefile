.EXPORT_ALL_VARIABLES:
# Get changed files


# if you wrap everything in uv run, it runs slower.
ifeq ($(origin VIRTUAL_ENV),undefined)
    VENV := uv run
else
    VENV :=
endif

uv.lock: pyproject.toml
	@echo "Installing dependencies"
	@uv sync

# tests can't be expected to pass if dependencies aren't installed.
# tests are often slow and linting is fast, so run tests on linted code.
test: uv.lock
	@echo "Running unit tests"
	# $(VENV) pytest --doctest-modules ai_fish_tank
	# $(VENV) python -m unittest discover
	$(VENV) py.test tests -vv -n 2 --cov=ai_fish_tank --cov-report=html --cov-fail-under 50 --cov-branch --cov-report=xml --junitxml=junit.xml -o junit_family=legacy

.PHONY: isort
isort:
	@echo "Formatting imports"
	$(VENV) isort .


.PHONY: black
black:
	@echo "Formatting code"
	$(VENV) metametameta pep621
	$(VENV) black ai_fish_tank # --exclude .venv
	$(VENV) black tests # --exclude .venv
	$(VENV) black demo # --exclude .venv
	$(VENV) black scripts # --exclude .venv
	@touch .build_history/black
	$(VENV) ./make_prompt.sh


.PHONY: pre-commit
pre-commit:
	@echo "Pre-commit checks"
	$(VENV) pre-commit run --all-files




.PHONY: bandit
bandit:
	@echo "Security checks"
	$(VENV)  bandit ai_fish_tank -r --quiet




.PHONY: pylint
pylint:
	@echo "Linting with pylint"
	$(VENV) ruff check --fix
	$(VENV) pylint ai_fish_tank --fail-under 9.8


# for when using -j (jobs, run in parallel)
.NOTPARALLEL: isort black

check: test pylint bandit pre-commit

.PHONY: publish
publish: test
	rm -rf dist && hatch build

.PHONY: mypy
mypy:
	$(VENV) mypy ai_fish_tank --ignore-missing-imports --check-untyped-defs


check_docs:
	$(VENV) interrogate ai_fish_tank --verbose
	$(VENV) pydoctest --config .pydoctest.json | grep -v "__init__" | grep -v "__main__" | grep -v "Unable to parse"

make_docs:
	pdoc ai_fish_tank --html -o docs --force

check_md:
	$(VENV) mdformat README.md docs/*.md
	$(VENV) linkcheckMarkdown README.md
	$(VENV) markdownlint README.md --config .markdownlintrc

check_spelling:
	$(VENV) pylint ai_fish_tank --enable C0402 --rcfile=.pylintrc_spell
	$(VENV) codespell README.md --ignore-words=private_dictionary.txt
	$(VENV) codespell ai_fish_tank --ignore-words=private_dictionary.txt

check_changelog:
	$(VENV) changelogmanager validate

check_all_docs: check_docs check_md check_spelling check_changelog


