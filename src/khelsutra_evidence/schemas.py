"""Load the versioned JSON Schema registry shipped with the package."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

JsonObject = dict[str, Any]


@lru_cache(maxsize=1)
def load_schemas() -> dict[str, JsonObject]:
    root = resources.files("khelsutra_evidence").joinpath("schemas", "v1")
    if not root.is_dir():
        root = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    loaded: dict[str, JsonObject] = {}
    for path in sorted(root.iterdir(), key=lambda item: item.name):
        if path.name.endswith(".json"):
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema_id = schema.get("$id")
            if not isinstance(schema_id, str):
                raise RuntimeError(f"schema {path.name} has no string $id")
            loaded[schema_id] = schema
    if not loaded:
        raise RuntimeError("no packaged evidence schemas found")
    return loaded


@lru_cache(maxsize=1)
def schema_registry() -> Registry[Any]:
    pairs = [
        (schema_id, Resource.from_contents(schema)) for schema_id, schema in load_schemas().items()
    ]
    return Registry().with_resources(pairs)


@lru_cache(maxsize=1)
def schemas_by_name() -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for schema in load_schemas().values():
        name_schema = schema.get("properties", {}).get("schema_name", {})
        name = name_schema.get("const") if isinstance(name_schema, dict) else None
        if isinstance(name, str):
            result[name] = schema
    return result


def validator_for(schema_name: str) -> Draft202012Validator:
    try:
        schema = schemas_by_name()[schema_name]
    except KeyError as exc:
        raise ValueError(f"unknown schema_name {schema_name!r}") from exc
    return Draft202012Validator(
        schema,
        registry=schema_registry(),
        format_checker=FormatChecker(),
    )
