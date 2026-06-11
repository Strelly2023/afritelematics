from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from afritech.cli.commands.inspect_chain import run as inspect_chain
from afritech.cli.commands.run_pilot_check import run as run_pilot_check
from afritech.cli.commands.simulate_network import run as simulate_network
from afritech.cli.commands.simulate_network import run_five_node as simulate_five_node
from afritech.cli.commands.simulate_network import run_twenty_node as simulate_twenty_node
from afritech.cli.commands.start_node import run as start_node
from afritech.extensions.afriprog.copilot_assist import (
    collect_context,
    explain_code,
    emit_governance_ready_proposal,
    generate_context_aware_proposal,
    generate_suggestion,
    inspect_context_proposal,
    validate_context_proposal,
    validate_suggestion_gate,
)
from afritech.design.uml import parse_uml, uml_to_proposal, validate_uml_design
from afritech.runtime_verification import (
    build_drift_context,
    classify_drift,
    detect_drift,
    drift_to_proposal,
    evaluate_contracts,
    observe_runtime,
)


COMMANDS = {
    "start-node": start_node,
    "inspect-chain": inspect_chain,
    "run-pilot-check": run_pilot_check,
    "simulate-5-node": simulate_five_node,
    "simulate-20-node": simulate_twenty_node,
    "simulate-network": simulate_network,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("AfriTech CLI")
    parser.add_argument(
        "command",
        choices=sorted(
            tuple(COMMANDS)
            + (
                "suggest",
                "fix",
                "explain",
                "testgen",
                "replaygen",
                "propose",
                "proposal-inspect",
                "proposal-validate",
                "proposal-emit",
                "uml-import",
                "uml-parse",
                "uml-validate",
                "uml-propose",
                "verify-start",
                "drift-list",
                "drift-inspect",
                "drift-propose",
            )
        ),
    )
    parser.add_argument("prompt", nargs="?")
    parser.add_argument("--validator", default="")
    parser.add_argument("--from-failure", default="")
    parser.add_argument("--diagram-type", default="class")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args(argv)

    if args.command in COMMANDS:
        result = COMMANDS[args.command]()
    else:
        result = _run_copilot_assist_command(args)
    _emit(result, as_json=args.json)
    return 0


def _emit(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        print(result.get("summary", json.dumps(result, sort_keys=True, default=str)))


def _run_copilot_assist_command(args: argparse.Namespace) -> Dict[str, Any]:
    prompt = args.prompt or ""
    if args.command == "suggest":
        suggestion = generate_suggestion(
            kind="inline_code_suggestion",
            intent=prompt,
            target="developer_workspace",
        )
        return _suggestion_payload(suggestion)

    if args.command == "fix":
        suggestion = generate_suggestion(
            kind="fix_failing_validator",
            intent=f"Fix failing validator: {args.validator or prompt}",
            target=args.validator or "validator",
        )
        return _suggestion_payload(suggestion)

    if args.command == "explain":
        explanation = explain_code(target=prompt, code="")
        suggestion = generate_suggestion(
            kind="explain_this_code",
            intent=f"Explain {prompt}",
            target=prompt,
        )
        return {**_suggestion_payload(suggestion), "code_explanation": explanation}

    if args.command == "testgen":
        suggestion = generate_suggestion(
            kind="generate_tests",
            intent=f"Generate tests for {prompt}",
            target=prompt,
        )
        return {**_suggestion_payload(suggestion), "context": collect_context(target=prompt)}

    if args.command == "replaygen":
        suggestion = generate_suggestion(
            kind="generate_replay_fixture",
            intent=f"Generate replay fixture for {prompt}",
            target=prompt,
        )
        return _suggestion_payload(suggestion)

    if args.command == "propose":
        proposal = generate_context_aware_proposal(
            intent=prompt,
            affected_files=("developer_workspace",),
            from_failure=args.from_failure or None,
        )
        return _proposal_payload(proposal)

    if args.command == "proposal-inspect":
        proposal = generate_context_aware_proposal(
            intent=prompt or "inspect proposal",
            affected_files=("developer_workspace",),
        )
        return inspect_context_proposal(proposal)

    if args.command == "proposal-validate":
        proposal = generate_context_aware_proposal(
            intent=prompt or "validate proposal",
            affected_files=("developer_workspace",),
        )
        return {
            "proposal": proposal.canonical_dict(),
            "validation": validate_context_proposal(proposal),
        }

    if args.command == "proposal-emit":
        proposal = generate_context_aware_proposal(
            intent=prompt or "emit proposal",
            affected_files=("developer_workspace",),
        )
        return emit_governance_ready_proposal(proposal)

    if args.command in {"uml-import", "uml-parse", "uml-validate", "uml-propose"}:
        model = parse_uml(_uml_source(prompt), diagram_type=args.diagram_type)
        if args.command in {"uml-import", "uml-parse"}:
            return {"uml_model": model, "activation_allowed": False}
        validation = validate_uml_design(model)
        if args.command == "uml-validate":
            return {"uml_model": model, "validation": validation}
        proposal = uml_to_proposal(model)
        return {
            "uml_model": model,
            "validation": validation,
            "proposal": proposal.canonical_dict(),
            "governance_review_required": True,
            "activation_allowed": False,
            "runtime_mutation_allowed": False,
        }

    if args.command in {"verify-start", "drift-list", "drift-inspect", "drift-propose"}:
        return _run_runtime_verification_command(args.command)

    raise ValueError(f"unsupported Copilot Assist command: {args.command}")


def _suggestion_payload(suggestion) -> Dict[str, Any]:
    payload = suggestion.canonical_dict()
    gate = validate_suggestion_gate(suggestion)
    return {
        "summary": (
            f"{payload['kind']} suggestion emitted as developer assistance only; "
            "validators, replay, and governance remain required."
        ),
        "suggestion": payload,
        "validation_gate": gate,
        "authority": "developer_assistance_only",
        "accepted": False,
        "runtime_mutation": False,
    }


def _proposal_payload(proposal) -> Dict[str, Any]:
    return {
        "summary": (
            "Context-aware proposal prepared for governance review; "
            "approval, activation, rollback execution, and runtime mutation remain denied."
        ),
        "proposal": proposal.canonical_dict(),
        "validation": validate_context_proposal(proposal),
        "governance_review_required": True,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }


def _uml_source(prompt: str) -> str:
    return prompt or "Customer\n- name\n- email\n+ placeOrder()"


def _run_runtime_verification_command(command: str) -> Dict[str, Any]:
    observation = observe_runtime(
        event="OrderShipped",
        state_before="Pending",
        expected_state="Paid",
        observed_state="Pending",
        contract="order_must_be_paid_before_shipping",
        trace=("OrderCreated", "OrderShipped"),
    )
    evaluation = evaluate_contracts(observation)
    drift = classify_drift(detect_drift(observation, evaluation) or {})
    context = build_drift_context(
        drift,
        timestamp="2026-06-06T00:00:00Z",
        affected_files=("contracts/order.yaml",),
    )
    if command == "verify-start":
        return {
            "status": "verification_observation_complete",
            "observation": observation,
            "evaluation": evaluation,
            "activation_allowed": False,
            "runtime_mutation_allowed": False,
        }
    if command == "drift-list":
        return {
            "drifts": (drift,),
            "governance_required": True,
            "activation_allowed": False,
            "runtime_mutation_allowed": False,
        }
    if command == "drift-inspect":
        return {
            "drift": drift,
            "context": context,
            "governance_required": True,
            "activation_allowed": False,
            "runtime_mutation_allowed": False,
        }
    proposal = drift_to_proposal(drift, context)
    return {
        "drift": drift,
        "context": context,
        "proposal": proposal.canonical_dict(),
        "governance_review_required": True,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
