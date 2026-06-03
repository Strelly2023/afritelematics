def build_submission_payload(partner, report):
    """Build an outbound payload without transmitting it.

    Live API transmission requires credentials, jurisdictional approval, and an
    audit policy. This scaffold prepares the approved data shape only.
    """

    return {
        "authority": "external_submission_payload_only",
        "partner_id": partner.id,
        "partner_name": partner.name,
        "country": partner.country,
        "endpoint_url": partner.endpoint_url,
        "report_id": report.id,
        "report_type": report.report_type,
        "report_hash": report.report_hash,
        "replay_verified": report.replay_verified,
    }


def submit_to_partner(partner, report):
    payload = build_submission_payload(partner, report)
    return {
        "status": "prepared",
        "transmitted": False,
        "payload": payload,
    }
