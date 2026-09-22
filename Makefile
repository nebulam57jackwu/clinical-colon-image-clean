.PHONY: verify

verify:
	python3 -m py_compile scripts/export_lake_manifest.py
	git diff --check
