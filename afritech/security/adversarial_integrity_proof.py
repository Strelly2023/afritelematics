"""Gate 7 adversarial integrity proof harness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from afritech.security.adversarial_proof import (
    AdversarialAttackEvidence,
    SecurityAdversarialProofError,
    run_security_adversarial_proof,
)


AUTHORITY_LAW = "Malicious behavior must not create valid truth."

REQUIRED_SCENARIOS = (
    "identity_spoofing_resistance",
    "replay_forgery_resistance",
    "injection_resistance",
    "authority_isolation",
)

REPORT_FILES = {
    "identity_spoofing_resistance": "identity_spoofing.json",
    "replay_forgery_resistance": "replay_forgery.json",
    "injection_resistance": "injection_attacks.json",
    "authority_isolation": "authority_isolation.json",
}

SCENARIO_ATTACKS = {
    "identity_spoofing_resistance": (
        "mobile_replay_spoofing",
        "invalid_partition_id",
    ),
    "replay_forgery_resistance": (
        "fake_replay_hash",
        "tampered_event_log",
        "duplicate_worker_result",
    ),
    "injection_resistance": (
        "raw_external_input_to_core",
        "provider_response_injection",
        "timestamp_manipulation",
    ),
    "authority_isolation": (
        "fake_observability_evidence",
        "fake_replay_hash",
        "provider_response_injection",
    ),
}


class AdversarialIntegrityProofError(RuntimeError):
    """Raised when adversarial behavior creates valid replay truth."""


@dataclass(frozen=True)
class AdversarialIntegrityScenarioProof:
    scenario: str
    attacks: tuple[AdversarialAttackEvidence, ...]
    baseline_replay_hash: str

    @property
    def all_attacks_rejected(self) -> bool:
        return all(attack.disposition == "rejected" for attack in self.attacks)

    @property
    def replay_truth_preserved(self) -> bool:
        return all(
            attack.observed_replay_hash == self.baseline_replay_hash
            for attack in self.attacks
        )

    @property
    def authority_isolated(self) -> bool:
        return all(attack.truth_authority == "replay_validation" for attack in self.attacks)

    @property
    def verified(self) -> bool:
        return (
            self.scenario in REQUIRED_SCENARIOS
            and self.all_attacks_rejected
            and self.replay_truth_preserved
            and self.authority_isolated
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "all_attacks_rejected": self.all_attacks_rejected,
            "attacks": [attack.canonical_dict() for attack in self.attacks],
            "authority_isolated": self.authority_isolated,
            "authority_law": AUTHORITY_LAW,
            "baseline_replay_hash": self.baseline_replay_hash,
            "replay_truth_preserved": self.replay_truth_preserved,
            "scenario": self.scenario,
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class AdversarialIntegrityProofReport:
    scenarios: tuple[AdversarialIntegrityScenarioProof, ...]
    baseline_replay_hash: str

    @property
    def verified(self) -> bool:
        return (
            tuple(scenario.scenario for scenario in self.scenarios)
            == REQUIRED_SCENARIOS
            and all(scenario.verified for scenario in self.scenarios)
            and len(self.baseline_replay_hash) == 64
        )

    @property
    def adversarial_integrity_hash(self) -> str:
        return _canonical_hash(
            {
                "authority_law": AUTHORITY_LAW,
                "baseline_replay_hash": self.baseline_replay_hash,
                "scenario_hashes": {
                    scenario.scenario: scenario.report_hash()
                    for scenario in self.scenarios
                },
                "verified": self.verified,
            }
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "adversarial_integrity_hash": self.adversarial_integrity_hash,
            "authority_law": AUTHORITY_LAW,
            "baseline_replay_hash": self.baseline_replay_hash,
            "required_scenarios": list(REQUIRED_SCENARIOS),
            "scenarios": [scenario.canonical_dict() for scenario in self.scenarios],
            "schema": "afritech.adversarial_integrity_proof_report.v1",
            "verified": self.verified,
        }


def run_adversarial_integrity_proof() -> AdversarialIntegrityProofReport:
    try:
        security = run_security_adversarial_proof()
    except SecurityAdversarialProofError as exc:
        raise AdversarialIntegrityProofError(str(exc)) from exc

    attack_index = {attack.attack_name: attack for attack in security.attacks}
    scenarios = tuple(
        AdversarialIntegrityScenarioProof(
            attacks=tuple(attack_index[name] for name in SCENARIO_ATTACKS[scenario]),
            baseline_replay_hash=security.baseline_replay_hash,
            scenario=scenario,
        )
        for scenario in REQUIRED_SCENARIOS
    )
    report = AdversarialIntegrityProofReport(
        baseline_replay_hash=security.baseline_replay_hash,
        scenarios=scenarios,
    )
    if not report.verified:
        raise AdversarialIntegrityProofError("adversarial integrity proof failed")
    return report


def write_adversarial_integrity_proof_reports(
    output_dir: str | Path = "reports/adversarial_integrity_proof_v1",
) -> AdversarialIntegrityProofReport:
    report = run_adversarial_integrity_proof()
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for scenario in report.scenarios:
        _write_json(target / REPORT_FILES[scenario.scenario], scenario.canonical_dict())
    _write_json(
        target / "adversarial_integrity_equivalence.json",
        {
            "adversarial_integrity_hash": report.adversarial_integrity_hash,
            "authority_law": AUTHORITY_LAW,
            "equivalent": report.verified,
            "scenario_hashes": {
                scenario.scenario: scenario.report_hash()
                for scenario in report.scenarios
            },
            "schema": "afritech.adversarial_integrity_equivalence_report.v1",
        },
    )
    return report


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = write_adversarial_integrity_proof_reports()
    except AdversarialIntegrityProofError as exc:
        print(f"Adversarial integrity proof FAILED: {exc}")
        return 1
    print(
        "Adversarial integrity proof PASSED: "
        f"scenarios={len(report.scenarios)} "
        f"adversarial_integrity_hash={report.adversarial_integrity_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

