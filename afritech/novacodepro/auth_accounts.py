from __future__ import annotations

from typing import Any


AUTH_PASSWORD = "NovaCodePro123!"

NOVACODEPRO_ACCOUNTS: list[dict[str, Any]] = [
    {
        "first_name": "Djuma",
        "last_name": "Platform Administrator",
        "username": "djuma.platformadmin",
        "email": "platformadministrator.test@afritechnology.com",
        "role": "ADMIN",
    },
    {
        "first_name": "Djuma",
        "last_name": "Developer",
        "username": "djuma.developer",
        "email": "developer.test@afritechnology.com",
        "role": "DEVELOPER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Product Manager",
        "username": "djuma.productmanager",
        "email": "productmanager.test@afritechnology.com",
        "role": "PRODUCT_MANAGER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Business Analyst",
        "username": "djuma.businessanalyst",
        "email": "businessanalyst.test@afritechnology.com",
        "role": "BUSINESS_ANALYST",
    },
    {
        "first_name": "Djuma",
        "last_name": "UI UX Designer",
        "username": "djuma.uiux",
        "email": "uiuxdesigner.test@afritechnology.com",
        "role": "UI_UX_DESIGNER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Project Manager",
        "username": "djuma.projectmanager",
        "email": "projectmanager.test@afritechnology.com",
        "role": "PROJECT_MANAGER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Architect",
        "username": "djuma.architect",
        "email": "architect.test@afritechnology.com",
        "role": "ARCHITECT",
    },
    {
        "first_name": "Djuma",
        "last_name": "QA Engineer",
        "username": "djuma.qa",
        "email": "qaengineer.test@afritechnology.com",
        "role": "QA_ENGINEER",
    },
    {
        "first_name": "Djuma",
        "last_name": "DevOps Engineer",
        "username": "djuma.devops",
        "email": "devopsengineer.test@afritechnology.com",
        "role": "DEVOPS_ENGINEER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Customer Support",
        "username": "djuma.support",
        "email": "customersupport.test@afritechnology.com",
        "role": "CUSTOMER_SUPPORT",
    },
    {
        "first_name": "Djuma",
        "last_name": "Operations",
        "username": "djuma.operations",
        "email": "operations.test@afritechnology.com",
        "role": "OPERATIONS_TEAM",
    },
    {
        "first_name": "Djuma",
        "last_name": "Brand",
        "username": "djuma.brand",
        "email": "brandteam.test@afritechnology.com",
        "role": "BRAND_TEAM",
    },
    {
        "first_name": "Djuma",
        "last_name": "Compliance",
        "username": "djuma.compliance",
        "email": "compliance.test@afritechnology.com",
        "role": "COMPLIANCE_TEAM",
    },
    {
        "first_name": "Djuma",
        "last_name": "Audit",
        "username": "djuma.audit",
        "email": "audit.test@afritechnology.com",
        "role": "AUDIT_TEAM",
    },
    {
        "first_name": "Djuma",
        "last_name": "Security",
        "username": "djuma.security",
        "email": "securityengineer.test@afritechnology.com",
        "role": "SECURITY_ENGINEER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Incident Response",
        "username": "djuma.incident",
        "email": "incidentresponse.test@afritechnology.com",
        "role": "INCIDENT_RESPONSE_TEAM",
    },
    {
        "first_name": "Djuma",
        "last_name": "Data Architect",
        "username": "djuma.dataarchitect",
        "email": "dataarchitect.test@afritechnology.com",
        "role": "DATA_ARCHITECT",
    },
    {
        "first_name": "Djuma",
        "last_name": "Data Engineer",
        "username": "djuma.dataengineer",
        "email": "dataengineer.test@afritechnology.com",
        "role": "DATA_ENGINEER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Database Engineer",
        "username": "djuma.database",
        "email": "databaseengineer.test@afritechnology.com",
        "role": "DATABASE_ENGINEER",
    },
    {
        "first_name": "Djuma",
        "last_name": "AI ML Engineer",
        "username": "djuma.aiml",
        "email": "aimlengineer.test@afritechnology.com",
        "role": "AI_ML_ENGINEER",
    },
    {
        "first_name": "Djuma",
        "last_name": "Data Scientist",
        "username": "djuma.datascientist",
        "email": "datascientist.test@afritechnology.com",
        "role": "DATA_SCIENTIST",
    },
    {
        "first_name": "Djuma",
        "last_name": "Privacy Compliance",
        "username": "djuma.privacy",
        "email": "privacy.test@afritechnology.com",
        "role": "PRIVACY_COMPLIANCE",
    },
    {
        "first_name": "Djuma",
        "last_name": "Risk Management",
        "username": "djuma.risk",
        "email": "riskmanagement.test@afritechnology.com",
        "role": "RISK_MANAGEMENT",
    },
    {
        "first_name": "Djuma",
        "last_name": "Legal",
        "username": "djuma.legal",
        "email": "legal.test@afritechnology.com",
        "role": "LEGAL",
    },
    {
        "first_name": "Djuma",
        "last_name": "Regulator",
        "username": "djuma.regulator",
        "email": "regulator.test@afritechnology.com",
        "role": "EXTERNAL_REGULATOR",
    },
]

SUPER_TEST_ACCOUNT: dict[str, Any] = {
    "first_name": "Djuma",
    "last_name": "Super Tester",
    "username": "djuma",
    "email": "djstrelly@gmail.com",
    "password": AUTH_PASSWORD,
    "assigned_roles": [account["role"] for account in NOVACODEPRO_ACCOUNTS],
}

ACCOUNT_INDEX: dict[str, dict[str, Any]] = {
    account["email"].strip().lower(): account for account in NOVACODEPRO_ACCOUNTS
}
ACCOUNT_INDEX.update({account["username"].strip().lower(): account for account in NOVACODEPRO_ACCOUNTS})
ACCOUNT_INDEX[SUPER_TEST_ACCOUNT["email"].strip().lower()] = SUPER_TEST_ACCOUNT
ACCOUNT_INDEX[SUPER_TEST_ACCOUNT["username"].strip().lower()] = SUPER_TEST_ACCOUNT


def find_account(identifier: str) -> dict[str, Any] | None:
    key = identifier.strip().lower()
    return ACCOUNT_INDEX.get(key)

