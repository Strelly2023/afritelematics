from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

APPS = {
    "personal": {
        "dir": ROOT / "novaid_personal_app",
        "name": "NovaID Personal",
        "package": "com.novatech.novaid.personal",
        "tabs": ["Home", "Wallet", "Share", "Consent", "Security", "Profile"],
        "buttons": [
            "Add Credential",
            "Verify Identity",
            "Share Identity",
            "Scan QR",
            "Revoke Access",
            "View Certificate",
            "Enable Passkey",
            "Manage Devices",
            "Start Recovery",
            "Contact Support",
        ],
        "flow": [
            "Identity Request",
            "Biometric Verification",
            "Document Validation",
            "Liveness Detection",
            "Policy Evaluation",
            "Identity Approved",
            "Digital Certificate Issued",
        ],
    },
    "business": {
        "dir": ROOT / "novaid_business_app",
        "name": "NovaID Business",
        "package": "com.novatech.novaid.business",
        "tabs": ["Dashboard", "Company", "Employees", "Certificates", "Risk", "Profile"],
        "buttons": [
            "Verify Business",
            "Add Director",
            "Invite Employee",
            "Issue Certificate",
            "View Digital Seal",
            "Download KYB Report",
        ],
    },
    "employee": {
        "dir": ROOT / "novaid_employee_app",
        "name": "NovaID Employee",
        "package": "com.novatech.novaid.employee",
        "tabs": ["ID", "Access", "Attendance", "HR", "Wallet", "Profile"],
        "buttons": [
            "Show Employee ID",
            "Check In",
            "Check Out",
            "Request Leave",
            "Submit Expense",
            "Open Access QR",
        ],
    },
    "inspector": {
        "dir": ROOT / "novaid_inspector_app",
        "name": "NovaID Inspector",
        "package": "com.novatech.novaid.inspector",
        "tabs": ["Scan", "Verify", "Offline", "Records", "Profile"],
        "buttons": [
            "Scan QR",
            "Verify Credential",
            "Offline Verify",
            "Save Inspection",
            "Sync Records",
            "Validate Certificate",
        ],
    },
    "partner": {
        "dir": ROOT / "novaid_partner_app",
        "name": "NovaID Partner",
        "package": "com.novatech.novaid.partner",
        "tabs": ["Dashboard", "Clients", "Certificates", "Webhooks", "Analytics", "Profile"],
        "buttons": [
            "Create OAuth Client",
            "Rotate Secret",
            "Issue Partner Certificate",
            "View API Usage",
            "Test Webhook",
        ],
    },
}


def read(app: Path, relative: str) -> str:
    return (app / relative).read_text(encoding="utf-8")


def test_novaid_app_metadata_and_release_configs() -> None:
    for spec in APPS.values():
        app = spec["dir"]
        app_json = read(app, "app.json")
        package_json = read(app, "package.json")
        app_config = read(app, "src/appConfig.ts")

        assert spec["name"] in app_json
        assert spec["package"] in app_json
        assert spec["package"] in app_config
        assert spec["name"] in app_config
        assert spec["name"].lower().replace(" ", "-") in package_json
        assert (app / "android/app/build.gradle").exists()
        assert (app / "android/settings.gradle").exists()
        assert (app / "eas.json").exists()
        assert (app / "metro.config.js").exists()
        assert spec["package"] in read(app, "android/app/build.gradle")
        assert spec["package"] in read(app, "android/app/src/main/AndroidManifest.xml")
        assert spec["name"] in read(app, "android/app/src/main/res/values/strings.xml")


def test_novaid_tabs_buttons_and_personal_flows_exist() -> None:
    for key, spec in APPS.items():
        app_config = read(spec["dir"], "src/appConfig.ts")

        for tab in spec["tabs"]:
            assert tab in app_config
        for button in spec["buttons"]:
            assert button in app_config

        if key == "personal":
            for step in spec["flow"]:
                assert step in app_config
            assert "selective-disclosure" in read(spec["dir"], "App.tsx")


def test_novaid_required_services_and_models_exist() -> None:
    personal = APPS["personal"]["dir"]

    models = read(personal, "src/models.ts")
    for type_name in [
        "IdentityProfile",
        "Credential",
        "DigitalCertificate",
        "TrustedDevice",
        "ConsentGrant",
        "IdentityEvent",
        "VerificationRequest",
        "BiometricCheck",
        "DocumentCheck",
        "LivenessCheck",
        "PolicyEvaluation",
        "OrganizationIdentity",
        "EmployeeIdentity",
        "PartnerClient",
        "InspectionRecord",
        "AuditPackage",
        "NovaAIIdentityRecommendation",
    ]:
        assert type_name in models

    for file_name in [
        "src/services/novaid.service.ts",
        "src/services/credential.service.ts",
        "src/services/consent.service.ts",
        "src/services/deviceTrust.service.ts",
        "src/services/certificate.service.ts",
        "src/services/inspection.service.ts",
        "src/services/partner.service.ts",
        "src/services/novaaiIdentity.service.ts",
    ]:
        assert (personal / file_name).exists()


def test_novaid_no_stale_afriride_or_novapay_labels() -> None:
    banned = ("AfriRide", "afriride", "NovaPay", "novapay")
    for spec in APPS.values():
        for path in spec["dir"].rglob("*"):
            if not path.is_file():
                continue
            if any(
                token in part.lower()
                for part in path.parts
                for token in ("dist", "build", ".expo", ".gradle", "node_modules")
            ):
                continue
            if path.suffix.lower() not in {".ts", ".tsx", ".json", ".gradle", ".kt", ".xml", ".js"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for word in banned:
                assert word not in text, f"{word} found in {path}"


def test_novaid_release_build_configs_are_present() -> None:
    for spec in APPS.values():
        app = spec["dir"]
        eas = read(app, "eas.json")
        gradle = read(app, "android/app/build.gradle")
        settings = read(app, "android/settings.gradle")

        assert '"distribution": "internal"' in eas
        assert '"buildType": "apk"' in eas
        assert '"buildType": "app-bundle"' in eas or '"buildType": "apk"' in eas
        assert "versionName \"2026.1.0\"" in gradle
        assert "rootProject.name" in settings
