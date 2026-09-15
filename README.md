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
│   ├── use_cases/       # Use Cases — one class per scenario
│   └── interfaces/       # ports (repository, gateway protocols, etc.)
│       ├── use_case.py   # IUseCase[Input, Output] — base use case contract
│       └── port.py       # IPort — base port class, used by auto-wiring of implementations
├── infrastructure/      # port implementations: databases, external APIs, brokers
└── presentation/
    └── fastapi/          # HTTP adapter (with include_fastapi)

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

tests/               # tests
└── architecture/    # architecture checks (naming, base classes, @dto, snake_case)
copier.yaml          # template variables: project_name, include_fastapi, include_dishka, auto_wire_use_cases, auto_wire_ports
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

Checks in `tests/architecture` (run by `pytest tests/architecture` and pre-commit) can be disabled selectively with a `# arc: ignore[<rule>]` comment on the violating line: the `class` line for classes, the assignment line for variables, the first line of the file for the file name. Several rules can be listed separated by commas; a comment without a rule name has no effect. Rules: `interfaces-naming`, `use-case-base-class`, `dto-decorator`, `snake-case-file`, `snake-case-variable` (the `RULE` constant in each test). A new check uses `is_ignored(path, line, RULE)` from `tests/architecture/_project.py`. `AGENTS.md` forbids AI agents from adding `arc: ignore`, and in Claude Code this is enforced by the `.claude/hooks/arc_ignore.py` hook.

The main package is always named after `project_name` (set when generating with copier), not `app`/`src`/another generic name, so the package name does not drift from the repository name across generated projects.

## MCP servers

Recommended MCP servers for development with AI assistants. Configure them in your harness settings (Claude Code, Codex, Cursor, etc.).

| Server | Purpose | Installation | GitHub |
|---|---|---|---|
| `codebase-memory-mcp` | Code knowledge graph (structural search, call graph, architecture overview) | static binary, put it on `PATH` as `codebase-memory-mcp` | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) |
| `ast-grep` | AST-aware search/refactoring by structural patterns | `uvx --from git+https://github.com/ast-grep/ast-grep-mcp ast-grep-server` | [ast-grep/ast-grep-mcp](https://github.com/ast-grep/ast-grep-mcp) |
| `language-server` | LSP tools (definition, references, rename, diagnostics) on top of `pyright` | `go install github.com/isaacphi/mcp-language-server@latest` → `mcp-language-server` binary on `PATH` | [isaacphi/mcp-language-server](https://github.com/isaacphi/mcp-language-server) |

`ast-grep` needs no separate installation: `uvx` fetches and runs it. `codebase-memory-mcp` and `mcp-language-server` must be installed beforehand (follow the GitHub link for instructions and release downloads). `mcp-language-server` runs on top of an installed `pyright`: `mcp-language-server --workspace . --lsp pyright-langserver -- --stdio`.
