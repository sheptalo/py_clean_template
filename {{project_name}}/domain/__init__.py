"""Domain layer — business rules that do not depend on how they are invoked.

Imports: standard library only. Forbidden: application, infrastructure,
presentation, frameworks, pydantic.

Entities and value objects are frozen dataclasses: a change returns a new
object (dataclasses.replace), so nothing mutates behind a use case's back.
A mutable entity is a deliberate exception, not the default. A method that
returns its own type annotates it unquoted (def renamed(self) -> Item):
annotations are not evaluated at definition time.
- A rule that concerns a single entity is a method of that entity, not a
  service. This includes access rules that depend on the entity's state.
- Method arguments are entities and values prepared by the use case; raw
  request data is never passed in.

Domain service.
- Exists only when a rule involves several entities and does not
  naturally belong to any one of them.
- A pure function or a stateless class: entities and values in, a result
  out. No I/O and no ports.

Constants and enumerations come from the ubiquitous language.

Errors live in exceptions.py and subclass DomainError, so presentation can
map them to statuses and a use case can catch a whole family at once.

Does not belong here:
- A port (repository, gateway, clock, timer) → application/interfaces.
- A "load, change, save" scenario → application/use_cases.
- A format for the outside world (JSON, ORM, broker message) →
  infrastructure or presentation.
"""
