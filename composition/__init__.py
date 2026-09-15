"""Composition Root — assembling and starting the application, outside all layers.

The only place allowed to know the concrete classes of every layer.

Belongs here:
- Entrypoints: factories of runnable applications (for example, api.py)
  and main() functions for [project.scripts]. Clients of external systems
  needed by port implementations are not entrypoints: their factories
  live in infrastructure.
- DI providers and the choice of port implementations (bootstrap/).
- The provider graph shared by all entrypoints (bootstrap/container): use
  cases, port implementations, settings and client factories from
  infrastructure. A choice of implementation or scope shared by all
  entrypoints is a provide() in InfrastructureProvider.
- Providers of a single entrypoint: the entrypoint passes its framework
  integration and PortProvider(<its presentation subpackage>) to
  make_container(). A choice of implementation or scope for one
  entrypoint only is a provide() in a PortProvider subclass in that
  entrypoint's module.

Does not belong here:
- Any logic other than assembling and starting: business rules → domain,
  scenarios → application, adapters → infrastructure or presentation.
- Resolving dependencies from the container inside layer code (Service
  Locator).
"""
