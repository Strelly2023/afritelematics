from __future__ import annotations

from architecture_validator.model import RuleResult, pass_or_fail
from architecture_validator.scanners.files import iter_text_files, read_text


def check_replay(config: dict[str, object]) -> RuleResult:
    issues: list[str] = []
    docs = read_text(str(config["docs_path"]))

    for required in (
        "Replay SHALL remain the authoritative operational evidence.",
        "All sensitive actions MUST be replay-verifiable.",
        "replay integrity",
        "maintain replay compatibility",
    ):
        if required not in docs:
            issues.append(f"Missing replay governance requirement: {required}")

    replay_corpus = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in iter_text_files(config.get("replay_source_roots", []))
    )
    for fragment in config.get("required_replay_fragments", []):
        if str(fragment) not in replay_corpus:
            issues.append(f"Missing replay implementation signal: {fragment}")

    return pass_or_fail("Replay Integrity", issues)
