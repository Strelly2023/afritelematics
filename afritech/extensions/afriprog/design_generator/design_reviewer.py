from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DesignReviewScore:
    name: str
    score: int
    reason: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class DesignReview:
    admitted: bool
    scores: tuple[DesignReviewScore, ...]
    violations: tuple[str, ...]

    @property
    def overall_score(self) -> int:
        if not self.scores:
            return 0
        return min(score.score for score in self.scores)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "overall_score": self.overall_score,
            "scores": [
                score.canonical_dict()
                for score in self.scores
            ],
            "violations": list(self.violations),
            "write_enabled": False,
            "authority": "proposal_only",
        }


class DesignReviewer:
    """
    Score design proposals without granting authority.

    Scores are deterministic 0-100 values. Any constitutional safety violation
    rejects the design regardless of other scores.
    """

    UNSAFE_TERMS = frozenset(
        {
            "bypass authentication",
            "disable validation",
            "skip evidence",
            "modify constitution",
            "auto-merge changes",
            "auto merge changes",
            "force merge",
            "push to main",
            "self authorize",
        }
    )

    def review(self, design) -> DesignReview:
        payload = design.canonical_dict()
        violations = self._violations(payload)
        scores = (
            self._score_modularity(payload),
            self._score_testability(payload),
            self._score_security(payload),
            self._score_data_model_clarity(payload),
            self._score_api_completeness(payload),
            self._score_constitutional_safety(payload, violations),
        )

        return DesignReview(
            admitted=not violations and all(score.score >= 70 for score in scores),
            scores=scores,
            violations=violations,
        )

    def _violations(self, payload: dict[str, Any]) -> tuple[str, ...]:
        text = str(payload).lower().replace("_", " ")
        return tuple(
            sorted(
                term
                for term in self.UNSAFE_TERMS
                if term in text
            )
        )

    def _score_modularity(self, payload: dict[str, Any]) -> DesignReviewScore:
        modules = payload["architecture"]["modules"]["modules"]
        score = 100 if {"domain", "application", "infrastructure", "api"}.issubset(modules) else 60
        return DesignReviewScore("modularity", score, "layered modules present")

    def _score_testability(self, payload: dict[str, Any]) -> DesignReviewScore:
        tasks = payload["implementation_plan"]["tasks"]
        has_tests = "tests" in payload["architecture"]["modules"]["modules"]
        score = 90 if tasks and has_tests else 60
        return DesignReviewScore("testability", score, "implementation tasks and tests layer present")

    def _score_security(self, payload: dict[str, Any]) -> DesignReviewScore:
        non_functional = payload["requirements"]["non_functional"]
        constraints = payload["requirements"]["constraints"]
        security_terms = " ".join(non_functional + constraints).lower()
        score = 90 if "role-aware" in security_terms and "no authority creation" in security_terms else 65
        return DesignReviewScore("security", score, "role and authority boundaries checked")

    def _score_data_model_clarity(self, payload: dict[str, Any]) -> DesignReviewScore:
        tables = payload["database"]["tables"]
        score = 95 if all(table.get("columns") for table in tables) else 50
        return DesignReviewScore("data_model_clarity", score, "tables include explicit columns")

    def _score_api_completeness(self, payload: dict[str, Any]) -> DesignReviewScore:
        endpoint_count = len(payload["api"]["endpoints"])
        table_count = len(payload["database"]["tables"])
        score = 90 if endpoint_count >= table_count * 2 else 60
        return DesignReviewScore("api_completeness", score, "CRUD read/create coverage checked")

    def _score_constitutional_safety(
        self,
        payload: dict[str, Any],
        violations: tuple[str, ...],
    ) -> DesignReviewScore:
        safe = (
            payload["write_enabled"] is False
            and payload["authority"] == "proposal_only"
            and not violations
        )
        return DesignReviewScore(
            "constitutional_safety",
            100 if safe else 0,
            "proposal-only authority and unsafe prompt terms checked",
        )
