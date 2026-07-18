SHELL := /bin/bash
BASE ?= origin/main
HEAD ?= HEAD

.PHONY: test-fast test-changed test-lf test-full test-release novacodepro-dev novacodepro-test novacodepro-ncp003-test novacodepro-ncp004-test novacodepro-ncp005-test novacodepro-ncp006b-test novacodepro-ncp007-test novacodepro-e2e novacodepro-ncp004-e2e novacodepro-ncp005-e2e novacodepro-ncp006b-e2e novacodepro-ncp007-e2e novacodepro-build novacodepro-down novacodepro-ai-worker novacodepro-knowledge-worker novacodepro-design-worker novacodepro-design-validate novacodepro-development-worker novacodepro-ncp006b-accessibility

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

novacodepro-ncp005-test:
	./scripts/novacodepro/test_ncp005.sh

novacodepro-ncp006b-test:
	./scripts/novacodepro/test_ncp006b.sh

novacodepro-ncp007-test:
	./scripts/novacodepro/test_ncp007.sh

novacodepro-e2e:
	./scripts/novacodepro/e2e_ncp003.sh

novacodepro-ncp004-e2e:
	./scripts/novacodepro/e2e_ncp004.sh

novacodepro-ncp005-e2e:
	./scripts/novacodepro/e2e_ncp005.sh

novacodepro-ncp006b-e2e:
	./scripts/novacodepro/e2e_ncp006b.sh

novacodepro-ncp007-e2e:
	./scripts/novacodepro/e2e_ncp007.sh

novacodepro-build:
	cd novacodepro_portal && npm run build

novacodepro-down:
	./scripts/novacodepro/dev_down.sh

novacodepro-ai-worker:
	./scripts/novacodepro/ai_worker.sh

novacodepro-knowledge-worker:
	./scripts/novacodepro/knowledge_worker.sh

novacodepro-design-worker:
	./scripts/novacodepro/design_worker.sh

novacodepro-development-worker:
	./scripts/novacodepro/development_worker.sh

novacodepro-design-validate:
	./scripts/novacodepro/validate_design.sh

novacodepro-ncp006b-accessibility:
	./scripts/novacodepro/accessibility_ncp006b.sh
