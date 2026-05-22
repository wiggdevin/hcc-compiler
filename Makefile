.PHONY: validate build check harvest extract verify route curate curate-smoke patterns-smoke embed derive-patterns patterns retrieve compile

validate:
	uv run python scripts/curation/validate_library.py library

build:
	uv run python scripts/curation/build_index.py library library.db

check: validate build
	uv run pytest -q

harvest:
	HCC_LIVE_HTTP=1 uv run python scripts/curation/harvest.py --domain nutrition --since 2022

extract:
	HCC_LIVE_LLM=1 uv run python scripts/curation/extract.py $(shell ls -t harvest-output/*.json | head -1)

verify:
	uv run python scripts/curation/verify.py draft-output

route:
	uv run python scripts/curation/route.py draft-output verify-output library

curate: harvest extract verify route

curate-smoke:
	uv run pytest tests/test_pipeline_smoke.py -q

patterns-smoke:
	uv run pytest tests/test_patterns_smoke.py -q

embed: build

derive-patterns:
	uv run python scripts/curation/derive_patterns.py

patterns: embed derive-patterns

retrieve:
	$(if $(QUERY),,$(error Usage: make retrieve QUERY="your search text"))
	uv run python scripts/retrieve.py "$(QUERY)"

compile:
	$(if $(INTAKE),,$(error Usage: make compile INTAKE=path/to/intake.yaml))
	uv run python scripts/compile_plan.py "$(INTAKE)"
