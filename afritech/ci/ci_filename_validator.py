import os
import re
import sys

CI_DIR = os.path.dirname(__file__)

# ✅ Canonical naming pattern
# - lowercase
# - snake_case
# - ends with .py
VALID_PATTERN = re.compile(r"^[a-z0-9_]+\.py$")

# ✅ Allowed semantic suffixes for governance clarity
ALLOWED_SUFFIXES = (
    "validator.py",
    "enforcement.py",
    "guard.py",
    "resolver.py",
    "engine.py",
    "pipeline.py"
)

# ✅ Explicit allowed special files
WHITELIST = {
    "__init__.py",
}


def validate_filename(name: str):
    if name in WHITELIST:
        return True, None

    if not VALID_PATTERN.match(name):
        return False, f"❌ Invalid format: {name}"

    if not name.endswith(ALLOWED_SUFFIXES):
        return False, (
            f"❌ Invalid semantic suffix: {name}\n"
            f"   Allowed suffixes: {ALLOWED_SUFFIXES}"
        )

    return True, None


def run():
    print("🔍 Running CI filename validator...")

    errors = []

    for filename in os.listdir(CI_DIR):
        path = os.path.join(CI_DIR, filename)

        if os.path.isfile(path):
            valid, error = validate_filename(filename)
            if not valid:
                errors.append(error)

    if errors:
        print("\n🚫 CI filename validation FAILED\n")
        for e in errors:
            print(e)
        sys.exit(1)

    print("✅ CI filename validation passed — naming is canonical")


if __name__ == "__main__":
    run()