from __future__ import annotations


def explain_code(*, target: str, code: str = "") -> dict[str, object]:
    return {
        "target": target,
        "summary": "Advisory explanation generated for developer review.",
        "line_count": len(code.splitlines()),
        "explanation_authority": "advisory_only",
        "is_proof": False,
        "requires_validator_confirmation": True,
    }


__all__ = ["explain_code"]
