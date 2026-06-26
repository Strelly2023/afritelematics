"""Generate typed client contract artifacts from the canonical version vector."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from afritech.platform_contracts.registry import current_version_vector


GENERATORS: dict[str, tuple[str, Callable[[dict[str, str]], str]]] = {}


def _generator(language: str, filename: str):
    def register(function: Callable[[dict[str, str]], str]):
        GENERATORS[language] = (filename, function)
        return function

    return register


@_generator("python", "novatech_contracts.py")
def render_python(vector: dict[str, str]) -> str:
    return f'''"""Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit."""

VERSION_VECTOR = {vector!r}

TRUST_LEVELS = {{
    "UNVERIFIED": 0,
    "AUTHENTICATED": 1,
    "POLICY_VERIFIED": 2,
    "EVIDENCE_PRODUCED": 3,
    "REPLAY_VERIFIED": 4,
    "FEDERATED_VERIFIED": 5,
    "PUBLICLY_VERIFIABLE": 6,
}}
'''


@_generator("typescript", "novatech-contracts.ts")
def render_typescript(vector: dict[str, str]) -> str:
    values = ", ".join(f'{key}: "{value}"' for key, value in vector.items())
    return (
        "// Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit.\n"
        f"export const versionVector = {{ {values} }} as const;\n"
        "export type TrustLevel = 0 | 1 | 2 | 3 | 4 | 5 | 6;\n"
    )


@_generator("kotlin", "NovaTechContracts.kt")
def render_kotlin(vector: dict[str, str]) -> str:
    constants = "\n".join(
        f'    const val {key} = "{value}"' for key, value in vector.items()
    )
    return (
        "// Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit.\n"
        "package novatech.contracts\n\n"
        "object VersionVector {\n"
        f"{constants}\n"
        "}\n"
    )


@_generator("swift", "NovaTechContracts.swift")
def render_swift(vector: dict[str, str]) -> str:
    constants = "\n".join(
        f'    public static let {key} = "{value}"' for key, value in vector.items()
    )
    return (
        "// Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit.\n"
        "import Foundation\n\n"
        "public enum NovaTechVersion {\n"
        f"{constants}\n"
        "}\n"
    )


def generate_sdks(output_dir: Path, languages: tuple[str, ...] | None = None) -> list[Path]:
    selected = languages or tuple(GENERATORS)
    unknown = set(selected) - set(GENERATORS)
    if unknown:
        raise ValueError(f"unsupported_sdk_languages:{sorted(unknown)}")
    output_dir.mkdir(parents=True, exist_ok=True)
    vector = current_version_vector().canonical()
    written: list[Path] = []
    for language in selected:
        filename, renderer = GENERATORS[language]
        path = output_dir / filename
        path.write_text(renderer(vector), encoding="utf-8")
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate NovaTech contract SDK artifacts")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--language", action="append", choices=sorted(GENERATORS))
    args = parser.parse_args()
    paths = generate_sdks(
        args.output_dir,
        tuple(args.language) if args.language else None,
    )
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
