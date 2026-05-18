from afritech.ci.level2_formal_model_validator import (
    EXPECTED_THEOREMS,
    MODEL_PATH,
    load_yaml,
    validate_model,
)


def test_level2_formal_model_validates() -> None:
    validate_model(load_yaml(MODEL_PATH))


def test_level2_theorem_set_is_complete() -> None:
    model = load_yaml(MODEL_PATH)

    theorem_ids = {
        theorem["id"]
        for theorem in model["theorems"]
    }

    assert theorem_ids == EXPECTED_THEOREMS
    assert set(model["final_property"]["depends_on"]) == theorem_ids
