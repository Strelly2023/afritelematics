from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class ContractLocatorError(Exception):
    """Raised when contract discovery fails."""


@dataclass(frozen=True)
class ContractFile:
    path: str
    contract_type: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "contract_type": self.contract_type,
        }


class ContractLocator:
    """
    Deterministic repository contract discovery.

    Constitutional properties:
    - read-only
    - deterministic
    - discovery only
    - non-authoritative
    """

    CONTRACT_DIRECTORY_NAMES = frozenset(
        {
            "contracts",
            "contracts_v1",
            "schemas",
        }
    )

    CONTRACT_FILE_PATTERNS = frozenset(
        {
            "contract",
            "schema",
            "receipt",
            "binding",
        }
    )

    def __init__(self, files: Iterable[str]):
        normalized = tuple(
            sorted(str(Path(file_path)) for file_path in files)
        )

        if any(not path for path in normalized):
            raise ContractLocatorError(
                "file paths must not be empty"
            )

        self.files = normalized

    def find_contracts(self) -> tuple[ContractFile, ...]:
        discovered: list[ContractFile] = []

        for file_path in self.files:
            contract_type = self._classify_contract(file_path)

            if contract_type is None:
                continue

            discovered.append(
                ContractFile(
                    path=file_path,
                    contract_type=contract_type,
                )
            )

        return tuple(
            sorted(
                discovered,
                key=lambda item: item.path,
            )
        )

    def contract_count(self) -> int:
        return len(self.find_contracts())

    def canonical_dict(self) -> dict[str, object]:
        return {
            "contract_count": self.contract_count(),
            "contracts": [
                contract.canonical_dict()
                for contract in self.find_contracts()
            ],
        }

    def _classify_contract(
        self,
        file_path: str,
    ) -> str | None:
        path = Path(file_path)

        parts = {
            part.lower()
            for part in path.parts
        }

        stem = path.stem.lower()

        if parts & self.CONTRACT_DIRECTORY_NAMES:
            return "directory_contract"

        if "contract" in stem:
            return "contract"

        if "schema" in stem:
            return "schema"

        if "receipt" in stem:
            return "receipt"

        if "binding" in stem:
            return "binding"

        return None