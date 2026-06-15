"""CI validator for AfriRide mobile app release readiness."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/mobile/release/afriride_mobile_release_readiness.json"
API = ROOT / "afritech/api/afriride_mobile_release_api.py"
APP = ROOT / "afritech/api/app.py"
RELEASE_HELPER = ROOT / "afritech/afriride_mobile_release.py"

VALIDATOR_NAME = "afritech.ci.afriride_mobile_release_validator"


@dataclass(frozen=True)
class AfriRideMobileReleaseValidatorReport:
    contract_present: bool
    manifests_present: bool
    app_sources_present: bool
    legal_docs_present: bool
    api_surface_present: bool
    release_gates_present: bool
    authority_boundary_present: bool
    verified: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "api_surface_present": self.api_surface_present,
            "app_sources_present": self.app_sources_present,
            "authority_boundary_present": self.authority_boundary_present,
            "contract_present": self.contract_present,
            "legal_docs_present": self.legal_docs_present,
            "manifests_present": self.manifests_present,
            "release_gates_present": self.release_gates_present,
            "schema": "afritech.afriride_mobile_release_validator_report.v1",
            "verified": self.verified,
        }


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return payload


def validate() -> AfriRideMobileReleaseValidatorReport:
    contract_present = CONTRACT.exists()
    contract = _read_json(CONTRACT) if contract_present else {}
    app_paths = contract.get("apps", [])
    if not isinstance(app_paths, list):
        app_paths = []
    required_docs = contract.get("required_docs", [])
    if not isinstance(required_docs, list):
        required_docs = []
    manifest_paths = [ROOT / str(path) for path in app_paths]
    manifests = [_read_json(path) for path in manifest_paths if path.exists()]
    manifests_present = (
        len(manifest_paths) == 3
        and all(path.exists() for path in manifest_paths)
        and {str(item.get("app_id")) for item in manifests}
        == {"afriride-rider", "afriride-driver", "afriride-operator-dashboard"}
    )
    app_sources_present = all(
        (ROOT / str(item.get("source_path", ""))).exists()
        for item in manifests
    )
    legal_docs_present = all(
        (ROOT / str(path)).exists()
        for path in required_docs
    )
    api_text = API.read_text(encoding="utf-8") if API.exists() else ""
    app_text = APP.read_text(encoding="utf-8") if APP.exists() else ""
    helper_text = RELEASE_HELPER.read_text(encoding="utf-8") if RELEASE_HELPER.exists() else ""
    api_surface_present = all(
        marker in api_text + app_text + helper_text
        for marker in (
            "build_afriride_mobile_release_readiness",
            "/public/afriride/mobile/release-readiness",
            "build_afriride_mobile_release_router",
        )
    )
    release_gates_present = all(
        item.get("required_capabilities")
        and item.get("required_backend_contracts")
        and item.get("release_gates")
        and item.get("required_store_assets") is not None
        for item in manifests
    )
    authority_boundary_present = (
        "mobile_apps_are_interface_only" in str(contract.get("authority_boundary"))
        and all("authority_boundary" in item for item in manifests)
        and contract.get("production_claim_allowed") is False
    )
    verified = all(
        (
            contract_present,
            manifests_present,
            app_sources_present,
            legal_docs_present,
            api_surface_present,
            release_gates_present,
            authority_boundary_present,
        )
    )
    return AfriRideMobileReleaseValidatorReport(
        contract_present=contract_present,
        manifests_present=manifests_present,
        app_sources_present=app_sources_present,
        legal_docs_present=legal_docs_present,
        api_surface_present=api_surface_present,
        release_gates_present=release_gates_present,
        authority_boundary_present=authority_boundary_present,
        verified=verified,
    )


def format_summary(report: AfriRideMobileReleaseValidatorReport) -> str:
    status = "PASSED" if report.verified else "FAILED"
    return (
        f"{VALIDATOR_NAME} {status} | "
        f"contract={report.contract_present} manifests={report.manifests_present} "
        f"sources={report.app_sources_present} legal={report.legal_docs_present} "
        f"api={report.api_surface_present} gates={report.release_gates_present} "
        f"authority={report.authority_boundary_present}"
    )


def main() -> int:
    report = validate()
    print(format_summary(report))
    return 0 if report.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
