import argparse
import json
import sys
from typing import Any, Dict

from afritech.services.audit_proof_verifier import (
    verify_audit_proof,
    verify_log_proof,
)


# =====================================================
# ✅ LOAD JSON FILE
# =====================================================

def load_json(filepath: str) -> Dict[str, Any]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ ERROR: Invalid JSON format in file: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: Failed to read file: {e}")
        sys.exit(1)


# =====================================================
# ✅ OUTPUT HANDLER
# =====================================================

def output_result(is_valid: bool, mode: str, filepath: str, json_mode: bool, verbose: bool):
    if json_mode:
        print(json.dumps({"valid": is_valid}))
    else:
        if verbose:
            print(f"File: {filepath}")
            print(f"Mode: {mode}")

        if is_valid:
            print("✅ VALID")
        else:
            print("❌ INVALID")

    sys.exit(0 if is_valid else 1)


# =====================================================
# ✅ VERIFY FULL PROOF
# =====================================================

def verify_full_proof(filepath: str, json_mode: bool, verbose: bool):
    proof = load_json(filepath)

    if verbose:
        print("🔍 Verifying full audit proof...")

    is_valid = verify_audit_proof(proof)

    output_result(is_valid, "full-proof", filepath, json_mode, verbose)


# =====================================================
# ✅ VERIFY SINGLE LOG PROOF
# =====================================================

def verify_single_log(filepath: str, json_mode: bool, verbose: bool):
    proof = load_json(filepath)

    if verbose:
        print("🔍 Verifying single log inclusion proof...")

    is_valid = verify_log_proof(proof)

    output_result(is_valid, "log-proof", filepath, json_mode, verbose)


# =====================================================
# ✅ MAIN ENTRYPOINT
# =====================================================

def main():
    parser = argparse.ArgumentParser(
        prog="audit",
        description="Cryptographic Audit Proof Verifier (CLI)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    subparsers = parser.add_subparsers(dest="command")

    # ✅ verify full proof
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify full audit proof",
    )
    verify_parser.add_argument("file", help="Path to proof JSON file")

    # ✅ verify single log proof
    verify_log_parser = subparsers.add_parser(
        "verify-log",
        help="Verify inclusion proof for a single log",
    )
    verify_log_parser.add_argument("file", help="Path to log proof JSON file")

    args = parser.parse_args()

    if args.command == "verify":
        verify_full_proof(args.file, args.json, args.verbose)

    elif args.command == "verify-log":
        verify_single_log(args.file, args.json, args.verbose)

    else:
        parser.print_help()
        sys.exit(1)


# =====================================================
# ✅ ENTRYPOINT
# =====================================================

if __name__ == "__main__":
    main()
