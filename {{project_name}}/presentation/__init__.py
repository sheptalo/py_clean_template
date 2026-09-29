"""Presentation layer — driving adapters: HTTP, CLI, consumers.

Imports: application (IUseCase, DTOs, ports) and frameworks. From domain —
exceptions, to turn them into responses, and enumerations, when a schema
names the same set of values. Forbidden: domain entities and value objects;
concrete infrastructure classes — composition injects them.

Belongs here:
- Own request and response schemas. Use case DTOs and entities are never
  exposed.
- Mapping: request schema → use case DTO, DTO → response schema.
- Calling a use case obtained from DI as IUseCase[In, Out].
- Transport details: status codes, headers, format validation.
- Port implementations that need the incoming request or the entrypoint
  context. They extract data from the request and return primitives or
  DTOs: they do not access storage, do not create entities and do not
  import domain. Such an implementation takes what it reads in __init__
  (def __init__(self, request: Request)): the framework integration the
  entrypoint registers is what makes the request resolvable.

A handwritten FastAPI adapter, when the code generator is not used:
- One module per resource in presentation/fastapi (items.py), holding its
  schemas and its router: APIRouter(route_class=DishkaRoute) from
  dishka.integrations.fastapi, so a handler can declare a dependency.
- A handler takes use_case: FromDishka[IUseCase[Input, Output]], builds the
  Input DTO from its schema, and returns its own response schema.
- A domain error becomes a status in one table, not in a try/except per
  handler. The table lives in this package, next to the routers, and the
  entrypoint only hands it to FastAPI. FastAPI types it strictly, so both
  the table and the handlers are annotated:

      type Handlers = dict[
          int | type[Exception],
          Callable[[Request, Any], Coroutine[Any, Any, Response]],
      ]

      async def _not_found(_request: Request, _error: Exception) -> Response:
          return JSONResponse(status_code=404, content={"detail": "..."})

      EXCEPTION_HANDLERS: Handlers = {ItemNotFoundError: _not_found}

  A handler returns Response (JSONResponse is one): annotating the return
  as JSONResponse makes the table incompatible with FastAPI.
- The entrypoint wires this package in, and is the only place that knows
  which of it the entrypoint serves: in composition/api.py add
  app.include_router(...) for every router it serves, and pass
  exception_handlers=EXCEPTION_HANDLERS to FastAPI.

DI registration: port implementations and their settings (BaseSettings)
live in the subpackage of their entrypoint (presentation/fastapi,
presentation/cli) and go only into that entrypoint's container.

Does not belong here:
- Business rules and branching on domain logic → domain or application.
- Loading entities and checking permissions → use case in application.
- Access to storage and external systems → infrastructure, through a port.
- Creating the application and the container, starting the server →
  composition.
"""
