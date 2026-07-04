SHELL := /bin/bash
BASE ?= origin/main
HEAD ?= HEAD

.PHONY: test-fast test-changed test-lf test-full test-release

test-fast:
	./scripts/test_fast.sh

test-changed:
	BASE=$(BASE) HEAD=$(HEAD) ./scripts/test_changed.sh

test-lf:
	./scripts/test_last_failed.sh

test-full:
	./scripts/test_full.sh

test-release:
	./scripts/test_release.sh
