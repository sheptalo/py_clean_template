# clean_template

Copier-шаблон Python-проекта на Clean Architecture (в терминах DDD): `domain/` → `application/` → `infrastructure/`/`presentation/`, с явным Composition Root (`composition/`) снаружи всех колец. Опционально подключает FastAPI (`include_fastapi`) и dishka с авто-wiring (`include_dishka`).

## Архитектурные принципы

| DDD (Evans) | Clean Architecture (Uncle Bob) | Hexagonal (Cockburn) |
|---|---|---|
| Domain | Entities | «ядро» |
| Application | Use Cases | «ядро» |
| Presentation | Interface Adapters → Controllers | driving-адаптеры |
| Infrastructure | Interface Adapters → Gateways / Frameworks & Drivers | driven-адаптеры |
| — | Main | Composition Root |

Правила, которые из этого следуют и которые нужно соблюдать при добавлении кода:

1. **Домен не знает о внешнем мире.** Сущности и доменные сервисы в `domain/` — чистые python-объекты (`dataclass`, не `pydantic` — `pydantic`-семантика типа `.model_dump()` это уже зависимость от фреймворка, а не от языка). Направление зависимостей закреплено `import-linter`-контрактом в `pyproject.toml.jinja`: `presentation → infrastructure → application → domain`, обратные импорты — ошибка линтера.
2. **Интерфейсы (порты) лежат в `application/interfaces`, не в `domain/`.** Даже если порт нужен доменному сервису — импорт наружу из `domain/*.py` в `application/interfaces/*` должен быть явным нарушением слоя, а не «соседним файлом», который проскальзывает мимо ревью.
3. **`Service` в application — легитимен только как process manager с состоянием между вызовами** (координирует что-то во времени). Если сервис на деле просто переводит формат в infrastructure или прячет бизнес-правило среди side-effect'ов — это симптом, что код лежит не в том слое.
4. **DTO — один тип на одну границу с независимой причиной изменения.** Presentation-DTO и Gateway/Repository-DTO для одних и тех же данных не должны быть одним типом, даже если сейчас совпадают по полям. Исключение — Repository, ему можно передавать саму Entity, это его прямая работа.
5. **Composition Root (`composition/`) — единственное место, которому разрешено знать про все конкретные классы всех слоёв.** Не Service Locator: контейнер собирается один раз при старте (фабрикой entrypoint'а, например `composition/api.py:create_app`), никто не резолвит его рантайм. Per-layer DI-провайдеры (`composition/bootstrap/` при `include_dishka`) могут импортировать только свои конкретные классы + абстракции — не конкретику соседних слоёв.

## Структура проекта

```
{{project_name}}/
├── domain/              # сущности, объекты-значения, доменные сервисы; exceptions.py — ошибки domain
├── application/
│   ├── use_cases/       # Use Cases — по одному классу на сценарий
│   └── interfaces/       # порты (протоколы репозиториев, шлюзов и т.д.)
│       ├── use_case.py   # IUseCase[Input, Output] — базовый контракт use case'а
│       └── port.py       # IPort — базовый класс портов, по нему работает auto-wiring реализаций
├── infrastructure/      # реализации портов: БД, внешние API, брокеры
└── presentation/
    └── fastapi/          # HTTP-адаптер (если include_fastapi)

composition/                                  # Composition Root — снаружи {{project_name}}/
├── api.py                                     # entrypoint HTTP: фабрика create_app() + main() для [project.scripts]
└── bootstrap/                                  # если include_dishka
    ├── container.py                            # make_container() — общий граф провайдеров для всех entrypoint'ов
    ├── use_cases.py.jinja                      # auto-wiring: сканирует application.use_cases,
    │                                            # регистрирует все подклассы IUseCase в DI-контейнере
    ├── ports.py.jinja                          # auto-wiring реализаций портов (IPort), scope REQUEST, и их
    │                                            # настроек (BaseSettings), scope APP:
    │                                            # PortProvider(*пакеты) — для подпакета presentation entrypoint'а,
    │                                            # InfrastructureProvider — общий для всех; provide() в них
    │                                            # переопределяет scope или выбирает реализацию
    └── utils.py                                 # обход пакетов / поиск подклассов для auto-wiring

tests/               # тесты
└── architecture/    # архитектурные проверки (именование, базовые классы, @dto, snake_case)
copier.yaml          # переменные шаблона: project_name, include_fastapi, include_dishka
pyproject.toml.jinja  # зависимости + import-linter контракт слоёв
```

## Запуск

Проект пакетируется (`uv_build`), entrypoint'ы объявлены в `[project.scripts]`. При `include_fastapi` + `include_dishka` есть команда `api` — обёртка над CLI uvicorn с уже подставленной фабрикой `composition.api:create_app`, поэтому доступны все флаги uvicorn:

```bash
uv run api --reload
```

```bash
uv run api --host 0.0.0.0 --port 8000 --workers 4
```

Новый entrypoint (воркер, CLI) — это модуль в `composition/` со своей функцией `main()` и строка в `[project.scripts]`. Он собирает контейнер как `make_container(<интеграция фреймворка>, PortProvider(<свой подпакет presentation>))`: реализации портов из `infrastructure` общие, а из подпакета `presentation` (например, реализация, которой нужен `Request`) попадают только в контейнер этого entrypoint'а. Выбор реализации или scope только для одного entrypoint'а — `provide()` в подклассе `PortProvider` в его модуле.

Параметры адаптера (пути, URL, таймауты, ключи) описываются классом-наследником `BaseSettings` из `pydantic-settings` рядом с реализацией, со своим `env_prefix`. Реализация принимает его в `__init__`, а `PortProvider` регистрирует класс настроек из того же пакета сам, scope APP:

```python
class ExportSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXPORT_")
    dir: Path


class ExcelItemExporter(IItemExporter):
    def __init__(self, settings: ExportSettings) -> None: ...
```

Правила, какой код к какому слою относится, записаны в docstring `__init__.py` каждого слоя и `composition/__init__.py`. `AGENTS.md` обязывает AI-агентов читать их перед изменениями, а в Claude Code это проверяет хук `.claude/hooks/layer_conventions.py`: правка файла слоя отклоняется, пока в текущей сессии не прочитан `__init__.py` этого слоя.

Проверки из `tests/architecture` (запускаются `pytest tests/architecture` и pre-commit) можно точечно отключить комментарием `# arc: ignore[<правило>]` на строке нарушения: на строке `class` для классов, на строке присваивания для переменных, на первой строке файла для имени файла. Через запятую можно указать несколько правил, правило без имени не действует. Правила: `interfaces-naming`, `use-case-base-class`, `dto-decorator`, `snake-case-file`, `snake-case-variable` (константа `RULE` в каждом тесте). Новая проверка использует `is_ignored(path, line, RULE)` из `tests/architecture/_project.py`. `AGENTS.md` запрещает AI-агентам ставить `arc: ignore`, а в Claude Code это проверяет хук `.claude/hooks/arc_ignore.py`.

Главный пакет всегда называется по `project_name` (задаётся при генерации через copier) — не `app`/`src`/другое generic-имя, чтобы не было дрейфа имени пакета от имени репозитория в разных сгенерированных проектах.

## MCP-серверы

Рекомендуемые MCP-серверы для разработки с AI-ассистентами. Подключаются в настройках вашего харнесса (Claude Code, Codex, Cursor и т.д.).

| Сервер | Назначение | Установка | GitHub |
|---|---|---|---|
| `codebase-memory-mcp` | Граф знаний кода (structural search, call graph, архитектурный обзор) | статический бинарь, положить на `PATH` как `codebase-memory-mcp` | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) |
| `ast-grep` | AST-aware поиск/рефакторинг по структурным паттернам | `uvx --from git+https://github.com/ast-grep/ast-grep-mcp ast-grep-server` | [ast-grep/ast-grep-mcp](https://github.com/ast-grep/ast-grep-mcp) |
| `language-server` | LSP-инструменты (definition, references, rename, diagnostics) поверх `pyright` | `go install github.com/isaacphi/mcp-language-server@latest` → бинарь `mcp-language-server` на `PATH` | [isaacphi/mcp-language-server](https://github.com/isaacphi/mcp-language-server) |

`ast-grep` не требует отдельной установки — `uvx` тянет и запускает его сам. `codebase-memory-mcp` и `mcp-language-server` нужно установить заранее (перейти по ссылке на GitHub — там есть инструкция и релизы для скачивания). `mcp-language-server` работает поверх установленного `pyright`: `mcp-language-server --workspace . --lsp pyright-langserver -- --stdio`.
