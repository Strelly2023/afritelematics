MIN_TRUST_SCORE = 0
MAX_TRUST_SCORE = 100


TRUST_DELTAS = {
    "ride_completed": 2,
    "ride_cancelled": -3,
    "fraud_flag": -20,
    "verified_clean_replay": 5,
}


def calculate_trust_delta(event_type):
    return TRUST_DELTAS.get(event_type, 0)


def clamp_trust_score(score):
    return max(MIN_TRUST_SCORE, min(MAX_TRUST_SCORE, score))
