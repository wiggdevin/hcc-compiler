validate:
	python scripts/curation/validate_library.py library

build:
	python scripts/curation/build_index.py library library.db

check: validate build
	pytest -q

harvest:
	HCC_LIVE_HTTP=1 python scripts/curation/harvest.py --domain nutrition --since 2022

extract:
	HCC_LIVE_LLM=1 python scripts/curation/extract.py $(shell ls -t harvest-output/*.json | head -1)

verify:
	python scripts/curation/verify.py draft-output

route:
	python scripts/curation/route.py draft-output verify-output library

curate: harvest extract verify route

curate-smoke:
	python -m pytest tests/test_pipeline_smoke.py -q

patterns-smoke:
	python -m pytest tests/test_patterns_smoke.py -q

.PHONY: embed
embed: build

derive-patterns:
	python scripts/curation/derive_patterns.py

patterns: embed derive-patterns

retrieve:
	$(if $(QUERY),,$(error Usage: make retrieve QUERY="your search text"))
	python scripts/retrieve.py "$(QUERY)"
