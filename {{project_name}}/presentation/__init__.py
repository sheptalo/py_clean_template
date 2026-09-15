"""Presentation layer — driving adapters: HTTP, CLI, consumers.

Imports: application (IUseCase, DTOs, ports) and frameworks. From domain —
only exceptions, to turn them into responses. Forbidden: domain entities
and value objects; concrete infrastructure classes — composition injects
them.

Belongs here:
- Own request and response schemas. Use case DTOs and entities are never
  exposed.
- Mapping: request schema → use case DTO, DTO → response schema.
- Calling a use case obtained from DI as IUseCase[In, Out].
- Transport details: status codes, headers, format validation.
- Port implementations that need the incoming request or the entrypoint
  context. They extract data from the request and return primitives or
  DTOs: they do not access storage, do not create entities and do not
  import domain.

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
