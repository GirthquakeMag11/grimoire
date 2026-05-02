from __future__ import annotations

import re
from typing import Final

field_type_value: Final[re.Pattern] = re.compile(
    r"(?m)^\s*(?P<field>\w+:)\s*(?P<type>[^=\n]+?)(?:\s*(?P<value>=\s*.+?))?\s*$"
)


def orthogonize(text: str) -> str:
    lines: list[str] = text.splitlines()

    match_results: dict[int, re.Match | None] = {
        line_no: field_type_value.match(line) for line_no, line in enumerate(lines)
    }
    matches: dict[int, dict[str, str]] = {
        line_no: match.groupdict(default="")
        for line_no, match in match_results.items()
        if match is not None
    }
    misses: dict[int, str] = {
        line_no: lines[line_no] for line_no, match in match_results.items() if match is None
    }

    margin_size: int = max(
        (len(line) - len(line.lstrip())) for line in lines if line not in misses.values()
    )
    margin: str = " " * margin_size

    field_length: int = max(len(m["field"]) for m in matches.values()) + 1
    type_length: int = max(len(m["type"]) for m in matches.values()) + 1
    value_length: int = max(len(m["value"]) for m in matches.values()) + 1

    formatted_fields: dict[int, str] = {}
    formatted_types: dict[int, str] = {}
    formatted_values: dict[int, str] = {}
    formatted_lines: dict[int, str] = {}

    for index, match_dict in matches.items():
        formatted_fields[index] = match_dict["field"].ljust(field_length)
        formatted_types[index] = match_dict["type"].ljust(type_length)
        formatted_values[index] = match_dict["value"].ljust(value_length)

    for index in range(len(lines)):
        if index in matches:
            formatted_lines[index] = margin + "".join(
                (formatted_fields[index], formatted_types[index], formatted_values[index])
            )
        else:
            if misses[index].lstrip().startswith("#"):
                formatted_lines[index] = "\n" + misses[index]
                continue
            formatted_lines[index] = misses[index]

    return "\n".join([formatted_lines[index] for index in range(len(formatted_lines))])
