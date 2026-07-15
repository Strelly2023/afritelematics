from __future__ import annotations

from afritech.architecture.novaride_next_generation import novaride_next_generation_manifest


def test_mobile_release_certification_not_claimed_without_fresh_apks() -> None:
    metadata = novaride_next_generation_manifest()["runtime_metadata"]
    assert metadata["release_gates_passed"]["fresh_apk_builds"] is False
    assert metadata["release_gates_passed"]["public_download_validation"] is False
    assert metadata["release_gates_passed"]["physical_device_smoke"] is False
    assert metadata["APK_release_status"] == "not_built_or_published_in_this_runtime_pass"
