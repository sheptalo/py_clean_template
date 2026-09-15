# clean_template

Copier-шаблон Python-проекта на Clean Architecture (в терминах DDD): `domain/` → `application/` → `infrastructure/`/`presentation/`, с явным Composition Root (`composition/`) снаружи всех колец. Опционально подключает FastAPI (`include_fastapi`) и dishka с авто-wiring (`include_dishka`).

## Архитектурные принципы

Три конвергентные традиции для одних и тех же слоёв — используем словарь DDD, но решения ближе к Uncle Bob:

| DDD (Evans) | Clean Architecture (Uncle Bob) | Hexagonal (Cockburn) |
|---|---|---|
| Domain | Entities | «ядро» |
| Application | Use Cases (Interactor) | «ядро» |
| Presentation | Interface Adapters → Controllers | driving-адаптеры |
| Infrastructure | Interface Adapters → Gateways / Frameworks & Drivers | driven-адаптеры |
| — | Main | Composition Root |

Правила, которые из этого следуют и которые нужно соблюдать при добавлении кода:

1. **Домен не знает о внешнем мире.** `domain/model` и `domain/services` — чистые python-объекты (`dataclass`, не `pydantic` — `pydantic`-семантика типа `.model_dump()` это уже зависимость от фреймворка, а не от языка). Направление зависимостей закреплено `import-linter`-контрактом в `pyproject.toml.jinja`: `presentation → infrastructure → application → domain`, обратные импорты — ошибка линтера.
2. **Интерфейсы (порты) лежат в `application/interfaces`, не в `domain/`.** Даже если порт нужен доменному сервису — импорт наружу из `domain/services/*.py` в `application/interfaces/*` должен быть явным нарушением слоя, а не «соседним файлом», который проскальзывает мимо ревью.
3. **`Service` в application — легитимен только как process manager с состоянием между вызовами** (координирует что-то во времени). Если сервис на деле просто переводит формат в infrastructure или прячет бизнес-правило среди side-effect'ов — это симптом, что код лежит не в том слое.
4. **DTO — один тип на одну границу с независимой причиной изменения.** Presentation-DTO и Gateway/Repository-DTO для одних и тех же данных не должны быть одним типом, даже если сейчас совпадают по полям. Исключение — Repository, ему можно передавать саму Entity, это его прямая работа.
5. **Composition Root (`composition/`) — единственное место, которому разрешено знать про все конкретные классы всех слоёв.** Не Service Locator: контейнер собирается один раз при старте (фабрикой entrypoint'а, например `composition/api.py:create_app`), никто не резолвит его рантайм. Per-layer DI-провайдеры (`composition/bootstrap/` при `include_dishka`) могут импортировать только свои конкретные классы + абстракции — не конкретику соседних слоёв.

## Структура проекта

```
{{project_name}}/
├── domain/
│   ├── model/          # Entities — dataclass, без внешних зависимостей
│   └── services/       # доменные сервисы (чистые функции/классы, без портов)
├── application/
│   ├── interactors/     # Use Cases — по одному классу на сценарий
│   └── interfaces/       # порты (протоколы репозиториев, шлюзов и т.д.)
│       ├── interactor.py # IInteractor[Input, Output] — базовый контракт use case'а
│       └── port.py       # IPort — базовый класс портов, по нему работает auto-wiring реализаций
├── infrastructure/      # реализации портов: БД, внешние API, брокеры
└── presentation/
    └── fastapi/          # HTTP-адаптер (если include_fastapi)

composition/                                  # Composition Root — снаружи {{project_name}}/
├── api.py                                     # entrypoint HTTP: фабрика create_app() + main() для [project.scripts]
└── bootstrap/                                  # если include_dishka
    ├── container.py                            # make_container() — общий граф провайдеров для всех entrypoint'ов
    ├── interactors.py.jinja                    # auto-wiring: сканирует application.interactors,
    │                                            # регистрирует все подклассы IInteractor в DI-контейнере
    ├── ports.py.jinja                          # auto-wiring: регистрирует реализации портов (IPort) из
    │                                            # infrastructure и presentation, scope REQUEST; provide() в
    │                                            # PortProvider переопределяет scope или выбирает реализацию
    └── utils.py                                 # обход пакетов / поиск подклассов для auto-wiring

scripts/            # служебные скрипты
tests/               # тесты
copier.yaml          # переменные шаблона: project_name, include_fastapi, include_dishka, include_example
pyproject.toml.jinja  # зависимости + import-linter контракт слоёв
```

`include_example` (спрашивается только при `include_fastapi` + `include_dishka`) добавляет рабочий вертикальный срез `Item` — по одному файлу на слой: Entity → порт `IItemRepository` → DTO с `@dto` → интеракторы → `InMemoryItemRepository` → FastAPI-роутер `/items` со своими pydantic-схемами запроса/ответа и маппингом в/из DTO интерактора, плюс явный `provide()` в `PortProvider`, который переводит `InMemoryItemRepository` в scope APP (иначе данные терялись бы между запросами).

## Запуск

Проект пакетируется (`uv_build`), entrypoint'ы объявлены в `[project.scripts]`. При `include_fastapi` + `include_dishka` есть команда `api` — обёртка над CLI uvicorn с уже подставленной фабрикой `composition.api:create_app`, поэтому доступны все флаги uvicorn:

```bash
uv run api --reload
```

```bash
uv run api --host 0.0.0.0 --port 8000 --workers 4
```

Новый entrypoint (воркер, CLI) — это модуль в `composition/` со своей функцией `main()`, использующий `make_container()`, и строка в `[project.scripts]`.

Правила, какой код к какому слою относится, записаны в docstring `__init__.py` каждого слоя и `composition/__init__.py`. `AGENTS.md` обязывает AI-агентов читать их перед изменениями, а в Claude Code это проверяет хук `.claude/hooks/layer_conventions.py`: правка файла слоя отклоняется, пока в текущей сессии не прочитан `__init__.py` этого слоя.

Проверки из `scripts/` (запускаются `pytest scripts` и pre-commit) можно точечно отключить комментарием `# arc: ignore[<правило>]` на строке нарушения: на строке `class` для классов, на строке присваивания для переменных, на первой строке файла для имени файла. Через запятую можно указать несколько правил, правило без имени не действует. Правила: `interfaces-naming`, `interactor-base-class`, `dto-decorator`, `snake-case-file`, `snake-case-variable` (константа `RULE` в каждом тесте). Новая проверка использует `is_ignored(path, line, RULE)` из `scripts/_project.py`. `AGENTS.md` запрещает AI-агентам ставить `arc: ignore`, а в Claude Code это проверяет хук `.claude/hooks/arc_ignore.py`.

Главный пакет всегда называется по `project_name` (задаётся при генерации через copier) — не `app`/`src`/другое generic-имя, чтобы не было дрейфа имени пакета от имени репозитория в разных сгенерированных проектах.

## MCP-серверы

Рекомендуемые MCP-серверы для разработки с AI-ассистентами. Подключаются в настройках вашего харнесса (Claude Code, Codex, Cursor и т.д.).

| Сервер | Назначение | Установка | GitHub |
|---|---|---|---|
| `codebase-memory-mcp` | Граф знаний кода (structural search, call graph, архитектурный обзор) | статический бинарь, положить на `PATH` как `codebase-memory-mcp` | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) |
| `ast-grep` | AST-aware поиск/рефакторинг по структурным паттернам | `uvx --from git+https://github.com/ast-grep/ast-grep-mcp ast-grep-server` | [ast-grep/ast-grep-mcp](https://github.com/ast-grep/ast-grep-mcp) |
| `language-server` | LSP-инструменты (definition, references, rename, diagnostics) поверх `pyright` | `go install github.com/isaacphi/mcp-language-server@latest` → бинарь `mcp-language-server` на `PATH` | [isaacphi/mcp-language-server](https://github.com/isaacphi/mcp-language-server) |

`ast-grep` не требует отдельной установки — `uvx` тянет и запускает его сам. `codebase-memory-mcp` и `mcp-language-server` нужно установить заранее (перейти по ссылке на GitHub — там есть инструкция и релизы для скачивания). `mcp-language-server` работает поверх установленного `pyright`: `mcp-language-server --workspace . --lsp pyright-langserver -- --stdio`.
