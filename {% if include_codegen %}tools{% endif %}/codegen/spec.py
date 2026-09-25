"""YAML specifications of the application and of the FastAPI presentation layer."""

import importlib
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

METHODS = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


class SpecError(ValueError):
    def __init__(self, path: Path, message: str) -> None:
        super().__init__(f"{path}: {message}")


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UseCaseSpec(Model):
    input: str
    output: str


class RequestSpec(Model):
    """Request sources. A parameter without a type takes it from the mapped DTO field."""

    body: str | None = None
    path: dict[str, str | None] = Field(default_factory=dict)
    query: dict[str, str | None] = Field(default_factory=dict)
    header: dict[str, str | None] = Field(default_factory=dict)


class FileSpec(Model):
    content: str
    filename: str | None = None
    media_type: str = "application/octet-stream"


class ResponseSpec(Model):
    file: FileSpec


class EndpointSpec(Model):
    method: METHODS
    path: str = ""
    status: int | None = None
    auth: Literal["none", "optional", "required"] = "none"
    summary: str | None = None
    use_case: UseCaseSpec
    request: RequestSpec = Field(default_factory=RequestSpec)
    input: dict[str, str] = Field(default_factory=dict)
    response: str | ResponseSpec | None = None
    errors: list[str] = Field(default_factory=list)


class RouterSpec(Model):
    version: Literal[1]
    prefix: str = ""
    tags: list[str] = Field(default_factory=list)
    schemas: dict[str, dict[str, str]] = Field(default_factory=dict)
    errors: dict[str, int] = Field(default_factory=dict)
    endpoints: dict[str, EndpointSpec] = Field(default_factory=dict)


class UseCaseDefinition(Model):
    input: dict[str, str] = Field(default_factory=dict)
    output: str = "none"
    ports: dict[str, str] = Field(default_factory=dict)


class MethodSpec(Model):
    doc: str | None = None
    args: dict[str, str] = Field(default_factory=dict)
    returns: str = "none"


class InterfaceSpec(Model):
    doc: str | None = None
    implementation: str
    scope: Literal["request", "app"] = "request"
    methods: dict[str, MethodSpec] = Field(default_factory=dict)


class ApplicationSpec(Model):
    version: Literal[1]
    enums: dict[str, list[str]] = Field(default_factory=dict)
    dtos: dict[str, dict[str, str]] = Field(default_factory=dict)
    use_cases: dict[str, UseCaseDefinition] = Field(default_factory=dict)
    interfaces: dict[str, InterfaceSpec] = Field(default_factory=dict)


def load_spec[T: Model](path: Path, model: type[T]) -> T:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise SpecError(path, f"is not valid YAML: {error}") from error
    if not isinstance(raw, dict):
        raise SpecError(path, "specification must be a mapping")
    try:
        return model.model_validate(raw)
    except ValidationError as error:
        raise SpecError(path, str(error)) from error


def load_specs[T: Model](directory: Path, model: type[T]) -> dict[Path, T]:
    if not directory.is_dir():
        return {}
    return {path: load_spec(path, model) for path in sorted(directory.glob("*.yaml"))}


def import_object(path: Path, dotted: str) -> Any:
    module_name, _, name = dotted.rpartition(".")
    if not module_name:
        raise SpecError(path, f"{dotted} must be a dotted path to a class")
    try:
        module = importlib.import_module(module_name)
    except ImportError as error:
        raise SpecError(path, f"cannot import {module_name}: {error}") from error
    if not hasattr(module, name):
        raise SpecError(path, f"{module_name} has no {name}")
    return getattr(module, name)
