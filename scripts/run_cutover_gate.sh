#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKIP_PHASE1=0
SKIP_GUARDS=0

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "NO-GO: cutover gate failed - $*"
  exit 1
}

main() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-phase1)
        SKIP_PHASE1=1
        ;;
      --skip-guards)
        SKIP_GUARDS=1
        ;;
      *)
        fail "unknown argument: $1"
        ;;
    esac
    shift
  done

  cd "$ROOT_DIR"

  if [[ "$SKIP_GUARDS" == "0" ]]; then
    log "Running Phase 1 governance guard"
    python3 -m afritech.guards.guard_phase1_runbook

    log "Running Phase 2 migration governance guard"
    python3 -m afritech.guards.guard_phase2_migration
  else
    log "Skipping governance guards by explicit override"
  fi

  if [[ "$SKIP_PHASE1" == "0" ]]; then
    log "Running governed Phase 1 setup gate in Postgres mode"
    "$ROOT_DIR/scripts/run_phase1_setup.sh" --with-postgres
  else
    log "Skipping Phase 1 setup gate by explicit override"
  fi

  log "Running deterministic cutover runbook"
  "$ROOT_DIR/scripts/afriride_postgres_cutover_runbook.sh"

  log "GO: cutover gate passed"
}

main "$@"
