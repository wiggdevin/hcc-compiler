validate:
	python scripts/curation/validate_library.py library

build:
	python scripts/curation/build_index.py library library.db

check: validate build
	pytest -q
