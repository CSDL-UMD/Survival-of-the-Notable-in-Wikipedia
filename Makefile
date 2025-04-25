#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = Survival_of_Notability
PYTHON_VERSION = 3.10
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python Dependencies
.PHONY: requirements
requirements:
	pip-compile requirements.in
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt
	



## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8 and black (use `make format` to do formatting)
.PHONY: lint
lint:
	flake8 survival_of_notability
	isort --check --diff --profile black survival_of_notability
	black --check --config pyproject.toml survival_of_notability

## Format source code with black
.PHONY: format
format:
	black --config pyproject.toml survival_of_notability



## Set up requirment.txt file
.PHONY: create_requirement
create_requirement:
	pip install pip-tools
	mkdir .myvenv
	touch Pipfile

## Set up python interpreter environment
.PHONY: create_environment
create_environment:
	pipenv --python $(shell which python3)
	@echo ">>> New pipenv created. Activate with:\npipenv shell"
	pipenv shell
	



#################################################################################
# PROJECT RULES                                                                 #
#################################################################################


## extract creation dates
.PHONY: creation_date
creation_date: requirements
	$(PYTHON_INTERPRETER) survival_of_notability/get_creation_dates.py


## Make Dataset
.PHONY: data
data: requirements
	$(PYTHON_INTERPRETER) survival_of_notability/dataset.py

## Make Retrospective Dataset
.PHONY: retrospective_data
retrospective_data:
	Rscript survival_of_notability/Compete.R


## Survival Analysis using R
.PHONY: compete_risk
compete_risk:
	Rscript survival_of_notability/Survival\ Analysis.R

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
