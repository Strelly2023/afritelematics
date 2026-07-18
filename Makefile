SHELL := /bin/bash
BASE ?= origin/main
HEAD ?= HEAD

.PHONY: test-fast test-changed test-lf test-full test-release novacodepro-dev novacodepro-test novacodepro-ncp003-test novacodepro-ncp004-test novacodepro-e2e novacodepro-ncp004-e2e novacodepro-build novacodepro-down novacodepro-ai-worker

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

novacodepro-dev:
	./scripts/novacodepro/dev_up.sh

novacodepro-test:
	./scripts/novacodepro/test_ncp003.sh

novacodepro-ncp003-test:
	./scripts/novacodepro/test_ncp003.sh

novacodepro-ncp004-test:
	./scripts/novacodepro/test_ncp004.sh

novacodepro-e2e:
	./scripts/novacodepro/e2e_ncp003.sh

novacodepro-ncp004-e2e:
	./scripts/novacodepro/e2e_ncp004.sh

novacodepro-build:
	cd novacodepro_portal && npm run build

novacodepro-down:
	./scripts/novacodepro/dev_down.sh

novacodepro-ai-worker:
	./scripts/novacodepro/ai_worker.sh
