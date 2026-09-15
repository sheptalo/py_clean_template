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
  the settings in __init__ and does not read os.environ.
- A client of an external system shared by several implementations is a
  factory in infrastructure that builds the client from its own settings.
  Implementations receive the ready client in __init__ and never create
  it themselves.

DI registration:
- Port implementations (scope REQUEST) and settings classes (scope APP)
  are added to the container shared by all entrypoints automatically.
- Client factories are registered explicitly with provide() in
  InfrastructureProvider (composition/bootstrap/ports.py). The same place
  overrides the scope or picks one of several implementations.

Does not belong here:
- Business rules and "what to do" decisions → domain or application.
- Handling incoming requests, and implementations that need the incoming
  request or the entrypoint context → presentation.
- Choosing a port implementation and building the dependency graph →
  composition.
"""
