# clean_template

Copier template for a Python project built on Clean Architecture (in DDD terms): `domain/` → `application/` → `infrastructure/`/`presentation/`, with an explicit Composition Root (`composition/`) outside all rings. Optionally adds FastAPI (`include_fastapi`) and dishka (`include_dishka`); with dishka, auto-wiring of use cases (`auto_wire_use_cases`) and of port implementations with their settings (`auto_wire_ports`) is switched on or off separately.

## Architecture principles

| DDD (Evans) | Clean Architecture (Uncle Bob) | Hexagonal (Cockburn) |
|---|---|---|
| Domain | Entities | core |
| Application | Use Cases | core |
| Presentation | Interface Adapters → Controllers | driving adapters |
| Infrastructure | Interface Adapters → Gateways / Frameworks & Drivers | driven adapters |
| — | Main | Composition Root |

Rules that follow from this and must be respected when adding code:

1. **The domain knows nothing about the outside world.** Entities and domain services in `domain/` are plain Python objects (`dataclass`, not `pydantic`: `pydantic` semantics such as `.model_dump()` are already a dependency on a framework, not on the language). The dependency direction is enforced by the `import-linter` contract in `pyproject.toml.jinja`: `presentation → infrastructure → application → domain`; reverse imports are a linter error.
2. **Interfaces (ports) live in `application/interfaces`, not in `domain/`.** Even if a domain service needs a port, an import from `domain/*.py` into `application/interfaces/*` must be an explicit layer violation, not a "neighbouring file" that slips through review.
3. **A `Service` in application is legitimate only as a process manager that keeps state between calls** (coordinates something over time). If a service actually just translates a format for infrastructure or hides a business rule among side effects, the code is in the wrong layer.
4. **DTO: one type per boundary with an independent reason to change.** Presentation DTOs and Gateway/Repository DTOs for the same data must not be one type, even if their fields currently match. The exception is a Repository: it may receive the Entity itself, that is its job.
5. **The Composition Root (`composition/`) is the only place allowed to know the concrete classes of every layer.** Not a Service Locator: the container is built once at startup (by the entrypoint factory, for example `composition/api.py:create_app`), and nothing resolves it at runtime. Per-layer DI providers (`composition/bootstrap/` with `include_dishka`) may import only their own concrete classes plus abstractions, not the concrete classes of other layers.

## Project structure

```
{{project_name}}/
├── domain/              # entities, value objects, domain services; exceptions.py — domain errors
├── application/
│   ├── spec/            # YAML specification of use cases, DTOs and ports (with include_codegen)
│   ├── use_cases/       # Use Cases — one class per scenario
│   └── interfaces/       # ports (repository, gateway protocols, etc.)
│       ├── use_case.py   # IUseCase[Input, Output] — base use case contract
│       └── port.py       # IPort — base port class, used by auto-wiring of implementations
├── infrastructure/      # port implementations: databases, external APIs, brokers
└── presentation/
    └── fastapi/          # HTTP adapter (with include_fastapi)
        ├── spec/         # YAML specification of the API (with include_codegen)
        └── generated/    # code produced by tools.codegen, never edited by hand

composition/                                  # Composition Root — outside {{project_name}}/
├── api.py                                     # HTTP entrypoint: create_app() factory + main() for [project.scripts]
└── bootstrap/                                  # with include_dishka
    ├── container.py                            # make_container() — provider graph shared by all entrypoints
    ├── use_cases.py.jinja                      # UseCaseProvider; with auto_wire_use_cases scans application.use_cases
    │                                            # and registers every IUseCase subclass, otherwise empty for provide()
    ├── ports.py.jinja                          # InfrastructureProvider; with auto_wire_ports registers port
    │                                            # implementations (IPort), scope REQUEST, and settings (BaseSettings), scope APP:
    │                                            # PortProvider(*packages) — for an entrypoint's presentation subpackage,
    │                                            # InfrastructureProvider — shared by all; provide() in them
    │                                            # overrides the scope or picks an implementation;
    │                                            # without auto_wire_ports InfrastructureProvider is empty for provide()
    └── utils.py                                 # package traversal / subclass lookup for auto-wiring

tools/codegen/       # generator of the presentation layer (with include_codegen)
tests/               # tests; __init__.py — how they are written; the layout mirrors the package
├── fakes/           # in-memory fakes of ports for application tests
└── architecture/    # architecture checks (naming, base classes, @dto, snake_case, tests, generated code)
copier.yaml          # template variables: project_name, include_fastapi, include_dishka,
                     # auto_wire_use_cases, auto_wire_ports, include_codegen
pyproject.toml.jinja  # dependencies + import-linter layer contract
```

## Running

The project is packaged (`uv_build`), and entrypoints are declared in `[project.scripts]`. With `include_fastapi` + `include_dishka` there is an `api` command — a wrapper around the uvicorn CLI with the `composition.api:create_app` factory already set, so every uvicorn flag is available:

```bash
uv run api --reload
```

```bash
uv run api --host 0.0.0.0 --port 8000 --workers 4
```

A new entrypoint (worker, CLI) is a module in `composition/` with its own `main()` function plus a line in `[project.scripts]`. With `auto_wire_ports` it builds the container as `make_container(<framework integration>, PortProvider(<its presentation subpackage>))`: port implementations from `infrastructure` are shared, while those from the `presentation` subpackage (for example, an implementation that needs `Request`) go only into this entrypoint's container. A choice of implementation or scope for a single entrypoint is a `provide()` in a `PortProvider` subclass in its module. Without `auto_wire_ports` the entrypoint passes its own provider with explicit `provide()` calls instead of `PortProvider`.

Adapter parameters (paths, URLs, timeouts, keys) are described by a `BaseSettings` subclass from `pydantic-settings` next to the implementation, with its own `env_prefix`. The implementation receives it in `__init__`. With `auto_wire_ports`, `PortProvider` registers the settings class from the same package automatically, scope APP; without it the settings class is registered with `provide()` like any other dependency:

```python
class ExportSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXPORT_")
    dir: Path


class ExcelItemExporter(IItemExporter):
    def __init__(self, settings: ExportSettings) -> None: ...
```

The rules for which code belongs to which layer are written in the docstring of each layer's `__init__.py` and of `composition/__init__.py`. `AGENTS.md` requires AI agents to read them before making changes, and in Claude Code this is enforced by the `.claude/hooks/layer_conventions.py` hook: an edit to a layer file is rejected until that layer's `__init__.py` has been read in the current session.

The rules for tests are the docstring of `tests/__init__.py`, and the same hook requires reading it before a file in `tests/` is changed. In short: a test states a behaviour and asserts a concrete value; `tests/domain` tests plain objects without mocks or async; `tests/application` runs a use case against fakes of its ports from `tests/fakes` (in-memory subclasses of the port, never `Mock`) and checks the result and the state of the fakes; `tests/infrastructure` checks the contract of a port on the real technology; `tests/presentation` checks the HTTP mapping. Async tests use `@pytest.mark.anyio`. A failing test is never weakened, skipped or deleted to make the suite pass — `AGENTS.md` forbids that to AI agents. The mechanical part is checked in `tests/architecture`: no mocks in domain and application tests, no async in domain tests, no test that only asserts `is not None`, `len(...) > 0` or `isinstance`, and no imports of generated routers. With `include_codegen` the generator also adds a `Fake<Port>` skeleton to `tests/fakes/<file>.py` for every port of the application specification.

Pre-commit runs the architecture and unit tests: `pytest -m "not integration"`. Everything in `tests/infrastructure` is marked `integration` by `tests/conftest.py`; these tests need the real services and run in CI, or by hand once the services are up. Coverage is a report, not a gate: it is not part of pre-commit and has no threshold.

```bash
uv run pytest -m "not integration"   # what pre-commit runs
uv run pytest -m integration         # with the services up
uv run pytest --cov                  # everything, with the coverage report
```

Checks in `tests/architecture` (run by `pytest tests/architecture` and pre-commit) can be disabled selectively with a `# arc: ignore[<rule>]` comment on the violating line: the `class` line for classes, the assignment line for variables, the first line of the file for the file name. Several rules can be listed separated by commas; a comment without a rule name has no effect. Rules: `interfaces-naming`, `use-case-base-class`, `dto-decorator`, `snake-case-file`, `snake-case-variable`, `use-case-decorator` (the `RULE` constant in each test). A new check uses `is_ignored(path, line, RULE)` from `tests/architecture/_project.py`. `AGENTS.md` forbids AI agents from adding `arc: ignore`, and in Claude Code this is enforced by the `.claude/hooks/arc_ignore.py` hook.

## Generated application layer (`include_codegen`)

Use cases, their DTOs and the ports they need are described in `<package>/application/spec/*.yaml`; a copyable example with comments lies in that directory, and `spec.schema.json` next to it validates the YAML in the editor. One specification file produces one DTO module, one port module and two skeletons:

```yaml
version: 1

dtos:
  ItemOutput:
    id: uuid
    name: str
    quantity: int

use_cases:
  CreateItemUseCase:
    input:
      name: str
      quantity: int
    output: ItemOutput

  ListItemsUseCase:
    input:
      limit: int?
    output: list[ItemOutput]

  DeleteItemUseCase:
    input:
      item_id: uuid
    output: none

interfaces:
  IItemRepository:
    implementation: InMemoryItemRepository
    scope: app
    methods:
      get:
        args:
          item_id: uuid
        returns: domain.item.Item?
      add:
        args:
          item: domain.item.Item
        returns: none
```

- **`application/dto/<file>.py`** is generated and must not be edited: every DTO from `dtos` plus one Input DTO per use case, named after it (`CreateItemUseCase` → `CreateItemInput`). Handwritten DTOs may live in the same package; the generator only owns files with its header.
- **`application/interfaces/<file>.py`** is generated too: one `IPort` subclass per entry of `interfaces`, every method `async` and `@abstractmethod`. `scope` (`request` by default) is written into the port, so the lifetime of its implementations is declared next to the port itself.
- **`application/use_cases/<file>.py`** and **`infrastructure/<file>.py`** are skeletons: a class the specification declares is added when the file has no class with that name, and a class that is already there is never touched again, so a use case or a port added to an existing specification gets its skeleton too. The classes, the `@use_case` decorator and the signatures come from the specification; the business logic, the port fields and the implementation are written by hand. `implementation` is the name of the class in infrastructure, so it reflects the technology as the layer conventions require.
- **Field types** are the same as in the presentation specification: `str`, `int`, `float`, `bool`, `uuid`, `datetime`, `date`, `decimal`, another DTO from the same file, `list[...]`, and a trailing `?` for optional. The output of a use case is a DTO of the same file, a list of one, or `none` — a primitive there is rejected, as the `dto-decorator` check requires.
- **In `interfaces`** a type may also be a dotted path to a class of the project (`domain.item.Item`), which is how a port takes and returns entities.
- The presentation specification refers to these DTOs as usual: `input: item.CreateItemInput`.

## Generated presentation layer (`include_codegen`)

With `include_codegen` the FastAPI presentation layer is generated from YAML. The specification in `<package>/presentation/fastapi/spec/*.yaml` is the source of truth; the code in `<package>/presentation/fastapi/generated/` is written by the generator and must not be edited by hand. That directory also holds a copyable example with comments and `spec.schema.json`; start every specification with the line that points to it, and the editor reports an unknown or missing key without running the generator:

```yaml
# yaml-language-server: $schema=./spec.schema.json
```

```bash
python -m tools.codegen          # write generated code
python -m tools.codegen --check  # fail if the generated code is out of date
```

One file per router:

```yaml
version: 1
prefix: /items
tags: [items]

schemas:
  CreateItemRequest:
    name: str
    quantity: int

errors:
  domain.exceptions.ItemNotFoundError: 404

endpoints:
  create_item:
    method: POST
    path: ""
    status: 201
    auth: required
    use_case:
      input: item.CreateItemInput
      output: item.ItemOutput
    request:
      body: CreateItemRequest

  get_item:
    method: GET
    path: /{item_id}
    use_case:
      input: item.GetItemInput
      output: item.ItemOutput

  list_items:
    method: GET
    use_case:
      input: item.ListItemsInput
      output: list[item.ItemOutput]
    request:
      query:
        limit:
```

- **`use_case`** names the Input and Output DTOs relative to `<package>.application.dto`; the DI key is `IUseCase[Input, Output]`. `output: none` means the use case returns nothing, `output: list[item.ItemOutput]` a list.
- **`request`** declares `body` (a schema) and `query` and `header` parameters; path parameters are taken from the URL. A parameter written without a type (`limit:`) takes it from the Input field it feeds.
- **`input`** maps a field of the Input DTO to a source: `body.name`, `path.item_id`, `query.limit`. A field whose name matches exactly one source is mapped without `input`; write it there to rename a source or to choose between several of them.
- **`response`** is optional: without it the schema is built from the Output DTO and named after it, nested DTOs included. To send a different shape, declare a schema in `schemas` and name it in `response` — the generator checks that the Output DTO can fill it. A list output produces a list response.
- **`schemas`** are the wire types of this router: the request body always, a response that has to differ from the Output DTO.
- **Field types:** `str`, `int`, `float`, `bool`, `uuid`, `datetime`, `date`, `decimal`, another schema, `list[...]`; a trailing `?` makes the field optional.
- **`errors`** is a section of its own: exception class relative to the package → status code. Handlers are collected from all files into `generated/__init__.py` and passed to `FastAPI(exception_handlers=...)`.
- **`auth`** is `none`, `optional` or `required`. It only requires credentials: `required` answers 401 without an `Authorization: Bearer` header and adds the lock in OpenAPI. Permissions stay in the use case, as the layer conventions require.

Returning a file is described by a `file` response instead of a schema. The use case returns a DTO with the bytes; HTTP details stay in the specification:

```yaml
    response:
      file:
        content: content          # Output DTO field, must be bytes
        filename: filename        # Output DTO field, must be str; optional
        media_type: text/csv      # constant; default application/octet-stream
```

The generated handler returns `Response` with that media type and a `Content-Disposition` header, and the media type is written into the OpenAPI response. Streaming is not supported yet: `content` must be `bytes`.

The application specification is rendered first and the routers are checked against its result, so a change that touches both specifications needs one run. Before writing anything the generator checks the specification against the code: the DTOs exist, every Input field is mapped exactly once, the types of the sources match the DTO fields, a hand-written response schema is filled by the Output DTO, and the error classes exist. A mismatch is a generation error, not a runtime failure. The architecture test `tests/architecture/test_generated_code.py` fails when the generated code differs from the specification, so pre-commit catches edits made by hand.

The main package is always named after `project_name` (set when generating with copier), not `app`/`src`/another generic name, so the package name does not drift from the repository name across generated projects.

## MCP servers

Recommended MCP servers for development with AI assistants. Configure them in your harness settings (Claude Code, Codex, Cursor, etc.).

| Server | Purpose | Installation | GitHub |
|---|---|---|---|
| `codebase-memory-mcp` | Code knowledge graph (structural search, call graph, architecture overview) | static binary, put it on `PATH` as `codebase-memory-mcp` | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) |
| `ast-grep` | AST-aware search/refactoring by structural patterns | `uvx --from git+https://github.com/ast-grep/ast-grep-mcp ast-grep-server` | [ast-grep/ast-grep-mcp](https://github.com/ast-grep/ast-grep-mcp) |
| `language-server` | LSP tools (definition, references, rename, diagnostics) on top of `pyright` | `go install github.com/isaacphi/mcp-language-server@latest` → `mcp-language-server` binary on `PATH` | [isaacphi/mcp-language-server](https://github.com/isaacphi/mcp-language-server) |

`ast-grep` needs no separate installation: `uvx` fetches and runs it. `codebase-memory-mcp` and `mcp-language-server` must be installed beforehand (follow the GitHub link for instructions and release downloads). `mcp-language-server` runs on top of an installed `pyright`: `mcp-language-server --workspace . --lsp pyright-langserver -- --stdio`.
