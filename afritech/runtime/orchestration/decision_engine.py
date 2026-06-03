"""
AfriTech Decision Engine

PURPOSE:
--------
Applies deterministic routing and branching decisions to events.

Responsibilities:
- apply safe decision rules
- control workflow branching
- enrich routing metadata (non-semantic)
- ensure deterministic behavior

CRITICAL LAW:
-------------
Decision Engine MAY:
- route events
- attach execution metadata

Decision Engine may NOT:
- modify payload semantics
- alter business truth
- introduce randomness
"""

# ============================================================
# ✅ MAIN DECISION FUNCTION
# ============================================================

def make_decision(event: dict, decisions: dict):
    """
    Apply decision logic to an event.

    Allowed decisions:
    - route (string)
    - tags (list)
    - priority (int or string)
    - flags (dict)

    Returns:
        new event with metadata (safe extension)
    """

    if not isinstance(event, dict):
        raise TypeError("Event must be a dictionary")

    if not isinstance(decisions, dict):
        raise TypeError("Decisions must be a dictionary")

    # --------------------------------------------------------
    # ✅ Start from safe shallow copy
    # --------------------------------------------------------
    routed_event = dict(event)

    # --------------------------------------------------------
    # ✅ ROUTE (primary flow control)
    # --------------------------------------------------------
    route = decisions.get("route")
    if route:
        routed_event["_route"] = _normalize_route(route)

    # --------------------------------------------------------
    # ✅ TAGS (classification)
    # --------------------------------------------------------
    tags = decisions.get("tags")
    if tags:
        if not isinstance(tags, list):
            raise TypeError("tags must be a list")

        routed_event["_tags"] = list(tags)

    # --------------------------------------------------------
    # ✅ PRIORITY (scheduling hint)
    # --------------------------------------------------------
    priority = decisions.get("priority")
    if priority is not None:
        routed_event["_priority"] = priority

    # --------------------------------------------------------
    # ✅ FLAGS (generic metadata)
    # --------------------------------------------------------
    flags = decisions.get("flags")
    if flags:
        if not isinstance(flags, dict):
            raise TypeError("flags must be a dict")

        routed_event["_flags"] = dict(flags)

    # --------------------------------------------------------
    # ✅ USER-DEFINED METADATA (SAFE NAMESPACE)
    # --------------------------------------------------------
    extras = decisions.get("metadata")
    if extras:
        if not isinstance(extras, dict):
            raise TypeError("metadata must be a dict")

        routed_event["_meta"] = dict(extras)

    return routed_event


# ============================================================
# ✅ ROUTE NORMALIZATION
# ============================================================

def _normalize_route(route: str):
    """
    Normalize route string.
    """

    if not isinstance(route, str):
        raise TypeError("Route must be a string")

    return route.strip().lower()


# ============================================================
# ✅ CONDITIONAL DECISION EXECUTION
# ============================================================

def apply_conditional_decision(event: dict, rules: list):
    """
    Apply first matching rule.

    rules:
        [
            {
                "condition": fn(event) -> bool,
                "decision": dict
            }
        ]
    """

    if not isinstance(rules, list):
        raise TypeError("Rules must be a list")

    for index, rule in enumerate(rules):
        condition = rule.get("condition")
        decision = rule.get("decision")

        if not callable(condition):
            raise Exception(
                f"[DECISION ERROR] Rule {index} missing callable condition"
            )

        if not isinstance(decision, dict):
            raise Exception(
                f"[DECISION ERROR] Rule {index} invalid decision"
            )

        if condition(event):
            return make_decision(event, decision)

    return event


# ============================================================
# ✅ MULTI-DECISION MERGE
# ============================================================

def merge_decisions(*decisions_list):
    """
    Merge multiple decision dicts safely.

    Later decisions override earlier ones.
    """

    result = {}

    for decisions in decisions_list:
        if not isinstance(decisions, dict):
            raise TypeError("All decisions must be dicts")

        result.update(decisions)

    return result


# ============================================================
# ✅ BULK DECISION APPLICATION
# ============================================================

def apply_decisions_bulk(events: list, decisions_map: dict):
    """
    Apply decisions to multiple events.

    decisions_map:
        {event_id: decisions}
    """

    if not isinstance(events, list):
        raise TypeError("Events must be a list")

    results = []

    for event in events:
        eid = event.get("event_id")
        decision = decisions_map.get(eid, {})

        results.append(make_decision(event, decision))

    return results


# ============================================================
# ✅ VALIDATION
# ============================================================

def validate_decisions(decisions: dict):
    """
    Validate decision structure.
    """

    if not isinstance(decisions, dict):
        raise TypeError("Decisions must be a dict")

    allowed_keys = {"route", "tags", "priority", "flags", "metadata"}

    for key in decisions.keys():
        if key not in allowed_keys:
            raise Exception(
                f"[DECISION ERROR] Invalid decision key: {key}"
            )

    return True


# ============================================================
# ✅ DETERMINISM CHECK
# ============================================================

def validate_decision_determinism(event: dict, decisions: dict):
    """
    Ensure deterministic routing.
    """

    r1 = make_decision(event, decisions)
    r2 = make_decision(event, decisions)

    if r1 != r2:
        raise Exception(
            "[DECISION ERROR] Non-deterministic decision output"
        )

    return True


# ============================================================
# ✅ TRACE (OBSERVABILITY)
# ============================================================

def trace_decision(event: dict, decisions: dict):
    """
    Debug helper.
    """

    result = make_decision(event, decisions)

    return {
        "event_id": event.get("event_id"),
        "input": event,
        "decisions": decisions,
        "output": result,
    }