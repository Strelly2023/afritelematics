#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

python3 -m pytest \
  afritech/tests/api/test_novacodepro_auth_sessions.py \
  afritech/tests/api/test_novacodepro_platform_api.py \
  afritech/tests/api/test_novacodepro_ncp003_api.py \
  afritech/tests/api/test_novacodepro_ai_execution_api.py \
  afritech/tests/api/test_novacodepro_requirements_api.py \
  afritech/tests/api/test_novacodepro_traceability_api.py \
  afritech/tests/api/test_novacodepro_knowledge_api.py \
  afritech/tests/api/test_novacodepro_knowledge_search_api.py \
  afritech/tests/api/test_novacodepro_knowledge_retrieval_api.py \
  -q

cd novacodepro_portal
npm test
npm run test:accessibility
npm run build
