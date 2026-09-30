.PHONY: test verify

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

verify:
	$(PYTHON) -m py_compile scripts/export_lake_manifest.py
	$(MAKE) test PYTHON="$(PYTHON)"
	git diff --check
