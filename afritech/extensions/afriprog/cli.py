from __future__ import annotations

import argparse
import json
import sys

from afritech.extensions.afriprog.command_center.task_dispatcher import (
    DispatchResult,
    TaskDispatcher,
)
from afritech.extensions.afriprog.design_generator.design_orchestrator import (
    DesignOrchestrator,
)
from afritech.extensions.afriprog.evidence.evidence_model import EvidenceRecord
from afritech.extensions.afriprog.execution.loop_engine import (
    VerificationLoopEngine,
)
from afritech.extensions.afriprog.monitoring.lifecycle_monitor import (
    LifecycleMonitor,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="afriprog",
        description="Afriprog autonomous coding command center",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("intent")
    run_parser.add_argument(
        "--summary",
        action="store_true",
        help="Print lifecycle summary instead of full dispatch receipt.",
    )
    run_parser.add_argument(
        "--objective",
        action="store_true",
        help="Run a bounded objective verification loop.",
    )
    run_parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum objective loop iterations, from 1 to 10.",
    )

    design_parser = subparsers.add_parser("design")
    design_parser.add_argument("intent")
    design_parser.add_argument(
        "--summary",
        action="store_true",
        help="Print concise design summary instead of full design proposal.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run":
        if args.objective:
            result = VerificationLoopEngine().run_description(
                args.intent,
                max_iterations=args.max_iterations,
            )
            payload = (
                _objective_summary_payload(result)
                if args.summary
                else result.canonical_dict()
            )
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0

        result = TaskDispatcher().dispatch(args.intent)
        payload = (
            _summary_payload(result)
            if args.summary
            else result.canonical_dict()
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "design":
        result = DesignOrchestrator().generate(args.intent)
        payload = (
            _design_summary_payload(result)
            if args.summary
            else result.canonical_dict()
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    return 1


def _summary_payload(result: DispatchResult) -> dict[str, object]:
    summary = LifecycleMonitor().snapshot(result).canonical_dict()
    records = _cli_evidence_records(result)

    return {
        **summary,
        "evidence": [
            record.canonical_dict()
            for record in records
        ],
        "evidence_count": len(records),
    }


def _cli_evidence_records(result: DispatchResult) -> tuple[EvidenceRecord, ...]:
    summary = LifecycleMonitor().snapshot(result).canonical_dict()

    return (
        EvidenceRecord(
            evidence_id=f"EVIDENCE-CLI-{result.generated.tasks[0].task_id if result.generated.tasks else 'NO-TASK'}",
            phase="PHASE_3_PROPOSAL_ONLY",
            source="evidence_generator",
            status=str(summary["status"]),
            subject=result.generated.intent,
            payload={
                "intent": result.generated.intent,
                "task_count": summary["task_count"],
                "admitted_count": summary["admitted_count"],
                "rejected_count": summary["rejected_count"],
                "write_enabled": False,
            },
        ),
    )


def _design_summary_payload(result) -> dict[str, object]:
    payload = result.canonical_dict()

    return {
        "intent": result.intent,
        "domain": payload["domain"]["domain"],
        "requirements_count": len(payload["requirements"]["functional"]),
        "module_count": len(payload["architecture"]["modules"]["modules"]),
        "database_table_count": len(payload["database"]["tables"]),
        "api_endpoint_count": len(payload["api"]["endpoints"]),
        "task_count": len(payload["implementation_plan"]["tasks"]),
        "review": payload["review"],
        "evidence": payload["evidence"],
        "write_enabled": False,
        "authority": "proposal_only",
    }


def _objective_summary_payload(result) -> dict[str, object]:
    payload = result.canonical_dict()
    latest = payload["iterations"][-1] if payload["iterations"] else {}
    evaluation = latest.get("evaluation", {})
    criteria = evaluation.get("criteria", [])

    return {
        "objective_id": payload["objective"]["objective_id"],
        "description": payload["objective"]["description"],
        "status": payload["status"],
        "satisfied": payload["satisfied"],
        "iteration_count": payload["iteration_count"],
        "criteria_count": len(criteria),
        "metrics": latest.get("metrics", {}),
        "write_enabled": False,
        "authority": "proposal_only",
    }


if __name__ == "__main__":
    sys.exit(main())
