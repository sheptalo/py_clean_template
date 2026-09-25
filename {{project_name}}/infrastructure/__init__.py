"""Infrastructure layer — implementations of application ports.

Imports: application, domain, frameworks and drivers. Forbidden:
presentation.

Belongs here:
- Implementations of ports from application/interfaces.
- Translation between an external format and entities or DTOs.
- An implementation name reflects the technology and the port:
  InMemoryItemRepository, SqlItemRepository.
- Implementation parameters (paths, addresses, timeouts, keys) are a
  BaseSettings subclass from pydantic-settings in the implementation
  module, each class with its own env_prefix. The implementation receives
  the settings in __init__ and does not read os.environ. Every field has a
  default: the container builds the settings with no arguments, so a
  required field fails at the first call instead of at startup.
- An adapter that calls out over HTTP brings its client into the project's
  dependencies (httpx2); urllib of the standard library is refused by the
  linter (S310).
- A client of an external system shared by several implementations is a
  factory in infrastructure that builds the client from its own settings.
  Implementations receive the ready client in __init__ and never create
  it themselves.

DI registration: implementations, settings and client factories from
infrastructure go into the container shared by all entrypoints; they are
registered in composition.

Does not belong here:
- Business rules and "what to do" decisions → domain or application.
- Handling incoming requests, and implementations that need the incoming
  request or the entrypoint context → presentation.
- Choosing a port implementation and building the dependency graph →
  composition.
"""
