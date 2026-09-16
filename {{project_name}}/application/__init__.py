"""Application layer — use cases and ports.

Imports: domain and the standard library. Forbidden: infrastructure,
presentation, frameworks.

use_cases/ — one class per scenario.
- Subclasses IUseCase[Input, Output] and is decorated with @use_case.
- Input is a dedicated @dto per use case, never None or a primitive.
  The DI key of a use case is IUseCase[Input, Output], so two use cases
  must not share the same pair of types.
- Dependencies are declared as fields typed with ports from interfaces/.
- Orchestrates only: load data through ports, call domain logic, save
  through ports. Contains no business rules.
- Checks whether the current user may run the scenario. A check in
  presentation is bypassed by any other entrypoint. The use case gets the
  data for the decision through ports; the domain makes the decision.

interfaces/ — ports: subclass IPort, the name starts with I (for example,
IItemRepository(IPort)), methods are marked @abstractmethod.
- An implementation subclasses the port.
- A port declares the lifetime of its implementations: scope = "request"
  (default) or "app". An implementation may override it; the choice says
  nothing about the DI library.
- A port lives here even if a domain service needs it: the domain does
  not import ports.
- A port that reads the call context (current user, headers, environment)
  returns primitives or DTOs, not entities. The use case loads entities
  from that data through a repository.

dto/ — use case inputs and outputs, decorated with @dto.
- One type per boundary: a use case DTO is never used as an HTTP schema,
  an ORM model or a broker message.

A service in application is allowed only as a process manager that keeps
state between calls (coordinates events over time).

Domain errors are not wrapped into application errors.
- If an error does not change the flow of the scenario, the use case does
  not catch it: it reaches presentation as is and is turned into a
  response there.
- Catch a domain error only to take a different branch of the scenario:
  except DomainError: handle_error().
- Never re-raise it as an application error:
  except DomainError as error: raise AppError from error.

Does not belong here:
- A rule computed from entities without I/O → domain.
- Format translation for an external system → infrastructure.
- A port implementation → infrastructure. An implementation that needs
  the incoming request or the entrypoint context → presentation.
"""
