"""Build and release provenance for API contract publications."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from afritech.api_catalog.domains import ApiContract


REQUIRED_PRODUCTION_PROVENANCE = ("git_commit", "build_id", "pipeline_id", "release_id")


def publication_provenance(contract: ApiContract) -> dict[str, Any]:
    return {
        "domain": contract.domain,
        "contract_version": contract.version,
        "git_commit": os.getenv("GIT_COMMIT_SHA", "unknown"),
        "git_branch": os.getenv("GIT_BRANCH", "unknown"),
        "build_id": os.getenv("BUILD_ID", "local"),
        "pipeline_id": os.getenv("CI_PIPELINE_ID", "local"),
        "release_id": os.getenv("NOVATECH_RELEASE_ID", f"api-{contract.domain}-{contract.version}"),
        "builder": os.getenv("BUILD_ACTOR", "local-developer"),
        "repository": os.getenv("REPOSITORY_URL", "github.com/Strelly2023/afritelematics"),
        "published_at": datetime.now(UTC).isoformat(),
    }


def validate_publication_provenance(provenance: dict[str, Any], *, production: bool) -> list[str]:
    if not production:
        return []
    return [field for field in REQUIRED_PRODUCTION_PROVENANCE if provenance.get(field) in {None, "", "unknown", "local"}]
