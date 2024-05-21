
.PHONY: install test lint format

install:
	pdm install

test:
	pdm run pytest

lint:
	pdm run ruff MADS_ML_Assignment_Nicky
	pdm run mypy MADS_ML_Assignment_Nicky

format:
	pdm run isort -v MADS_ML_Assignment_Nicky
	pdm run black MADS_ML_Assignment_Nicky
