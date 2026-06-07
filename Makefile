PY ?= python3
PIP ?= $(PY) -m pip
MAIN = pac-man.py
CONFIG = config.json
MAZE = mazegenerator-00001-py3-none-any.whl

.PHONY: install run debug clean lint lint-strict

install:
	$(PIP) install --upgrade pip
	$(PIP) install pygame
	$(PIP) install ./$(MAZE) || true

run:
	$(PY) $(MAIN) $(CONFIG)

debug:
	$(PY) -m pdb $(MAIN) $(CONFIG)

lint:
	flake8 . && mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 . && mypy . --strict --ignore-missing-imports

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache */__pycache__
	find . -name '*.pyc' -delete
