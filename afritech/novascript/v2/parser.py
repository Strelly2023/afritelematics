from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedOutput:
    data: dict[str, Any]
    raw: str
    parser_name: str = "structured_output_parser"


class StructuredOutputParser:
    def parse(self, payload: Any) -> ParsedOutput:
        if isinstance(payload, dict):
            return ParsedOutput(data=payload, raw=json.dumps(payload, sort_keys=True))

        text = str(payload).strip()
        if not text:
            return ParsedOutput(data={}, raw="")

        json_blob = self._extract_json(text)
        if json_blob is not None:
            return ParsedOutput(data=self._coerce_mapping(json.loads(json_blob)), raw=text)

        mapping = self._parse_key_value_lines(text)
        if mapping:
            return ParsedOutput(data=mapping, raw=text)

        return ParsedOutput(data={"text": text}, raw=text)

    def _extract_json(self, text: str) -> str | None:
        if text.startswith("{") and text.endswith("}"):
            return text
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if fenced:
            return fenced.group(1)
        return None

    def _parse_key_value_lines(self, text: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower().replace(" ", "_")
            value = value.strip()
            if not key:
                continue
            result[key] = self._coerce_scalar(value)
        return result

    def _coerce_mapping(self, mapping: Any) -> dict[str, Any]:
        if not isinstance(mapping, dict):
            return {"value": mapping}
        return mapping

    def _coerce_scalar(self, value: str) -> Any:
        lowered = value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value


_DEFAULT_PARSER = StructuredOutputParser()


def get_structured_output_parser() -> StructuredOutputParser:
    return _DEFAULT_PARSER
