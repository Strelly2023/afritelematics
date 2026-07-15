"""GA guard."""

GA_ALLOWED = False
GA_APPROVAL = "PENDING"


def assert_ga_blocked() -> dict[str, object]:
    return {"GA_ALLOWED": GA_ALLOWED, "GA_APPROVAL": GA_APPROVAL}
