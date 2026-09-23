"""Spec types: parsing, rendering as annotations and matching against DTOs."""

import ast
import dataclasses
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints
from uuid import UUID

OPTIONAL_UNION_ARGS = 2

SCALARS: dict[str, tuple[type, str, tuple[str, str] | None]] = {
    "str": (str, "str", None),
    "int": (int, "int", None),
    "float": (float, "float", None),
    "bool": (bool, "bool", None),
    "uuid": (UUID, "UUID", ("uuid", "UUID")),
    "datetime": (datetime, "datetime", ("datetime", "datetime")),
    "date": (date, "date", ("datetime", "date")),
    "decimal": (Decimal, "Decimal", ("decimal", "Decimal")),
}

SCALAR_BY_TYPE: dict[type, str] = {hint: name for name, (hint, _, _) in SCALARS.items()}

_LIST = re.compile(r"^list\[(?P<item>.+)\]$")
_KEYWORDS = {"true": True, "false": False, "null": None, "none": None}


class SpecTypeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SpecType:
    name: str
    many: bool = False
    optional: bool = False
    default: str | None = None

    @property
    def is_scalar(self) -> bool:
        return self.name in SCALARS


def parse_default(text: str) -> str:
    """The Python source of a default value: a literal, or true, false, null."""
    source = text.strip()
    if source.lower() in _KEYWORDS:
        return repr(_KEYWORDS[source.lower()])
    try:
        return repr(ast.literal_eval(source))
    except (ValueError, SyntaxError) as error:
        raise SpecTypeError(f"a default value must be a literal, got {source!r}") from error


def parse_type(text: str) -> SpecType:
    """Parse `type`, `type?`, `list[type]` with an optional `= default`; `= default` alone keeps the type open."""
    value, has_default, default_text = text.partition("=")
    default = parse_default(default_text) if has_default else None
    value = value.strip()
    optional = value.endswith("?")
    if optional:
        value = value[:-1].strip()
    match = _LIST.match(value)
    if match:
        item = match.group("item").strip()
        if _LIST.match(item) or item.endswith("?"):
            raise SpecTypeError(f"nested list or optional item is not supported: {text}")
        return SpecType(name=item, many=True, optional=optional, default=default)
    return SpecType(name=value, optional=optional, default=default)


def annotation(spec_type: SpecType) -> str:
    text = SCALARS[spec_type.name][1] if spec_type.is_scalar else spec_type.name
    if spec_type.many:
        text = f"list[{text}]"
    if spec_type.optional:
        text = f"{text} | None"
    return text


def imports(spec_type: SpecType) -> set[tuple[str, str]]:
    if not spec_type.is_scalar:
        return set()
    module = SCALARS[spec_type.name][2]
    return {module} if module else set()


def strip_optional(hint: Any) -> tuple[Any, bool]:
    if get_origin(hint) in (Union, UnionType):
        args = [arg for arg in get_args(hint) if arg is not type(None)]
        if len(args) == 1:
            return args[0], len(get_args(hint)) == OPTIONAL_UNION_ARGS
    return hint, False


def matches(
    spec_type: SpecType,
    hint: Any,
    schemas: dict[str, dict[str, str]],
    enums: Mapping[str, type],
) -> bool:
    """Check that a spec type describes the same data as a DTO annotation."""
    hint, hint_optional = strip_optional(hint)
    if hint_optional != spec_type.optional:
        return False
    if spec_type.many:
        if get_origin(hint) is not list:
            return False
        (hint,) = get_args(hint) or (None,)
    if spec_type.is_scalar:
        return hint is SCALARS[spec_type.name][0]
    if spec_type.name in enums:
        return hint is enums[spec_type.name]
    return (
        spec_type.name in schemas
        and dataclasses.is_dataclass(hint)
        and schema_matches(schemas[spec_type.name], hint, schemas, enums)
    )


def schema_matches(
    fields: dict[str, str],
    dto: Any,
    schemas: dict[str, dict[str, str]],
    enums: Mapping[str, type],
) -> bool:
    hints = get_type_hints(dto)
    return all(
        name in hints and matches(parse_type(text), hints[name], schemas, enums) for name, text in fields.items()
    )


def field_hint(dto: Any, name: str) -> Any:
    return get_type_hints(dto).get(name)
