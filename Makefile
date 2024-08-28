SRC_DIR ?= ./src
MYPY_DIRS := $(shell find ${SRC_DIR}/package ! -path '*.egg-info*' -type d -maxdepth 1 -mindepth 1 | xargs)

.PHONY: lint
lint:
	ruff check --target-version=py39 ./src

.PHONY: lint-github
lint-github:
	ruff check --output-format=github --target-version=py39 ./src

.PHONY: mypy
mypy: $(MYPY_DIRS)
	$(foreach d, $(MYPY_DIRS), python -m mypy $(d);)

.PHONY: test
test:
	pytest --cov ${SRC_DIR}/tests -v -s ${SRC_DIR}/tests

.PHONY: develop
develop:
	python -m pip install --editable ${SRC_DIR}
	python -m pip install -U -r requirements-dev.txt