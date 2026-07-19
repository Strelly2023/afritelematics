#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
cd novacodepro_portal
node --test tests/ncp008Portal.test.js tests/ncp008OperationsFlow.test.js
