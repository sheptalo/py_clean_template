"""Composition Root — assembling and starting the application, outside all layers.

The only place allowed to know the concrete classes of every layer.

Belongs here:
- Entrypoints: factories of runnable applications (for example, api.py)
  and main() functions for [project.scripts]. Clients of external systems
  needed by port implementations are not entrypoints: their factories
  live in infrastructure.
- DI providers, registration and the choice of port implementations
  (bootstrap/).
- The provider graph shared by all entrypoints (bootstrap/container): use
  cases, port implementations, settings and client factories from
  infrastructure.
- Providers of a single entrypoint: its framework integration and the
  registrations from its presentation subpackage, passed by the
  entrypoint to make_container().

An entrypoint that no framework integrates (a CLI, a worker) does the
wiring itself, and only it may touch the container:
- builds it once with make_container(<its own providers>), opens a request
  scope (async with container() as request), resolves the use case the
  command needs and passes it to the adapter of its presentation
  subpackage, then closes the container in a finally.
- turns a domain error into its own transport answer: an exit code and a
  line on stderr for a CLI, a retry or a dead letter for a consumer. A CLI
  parses argv with argparse of the standard library and answers 2 for a
  malformed command, 1 for a refused rule, 0 for done.
- may write to stdout and stderr; no layer below it prints.
- is registered in [project.scripts] as its own command, for example
  stock = "composition.cli:main", and main() is synchronous: it runs the
  async part itself (asyncio.run) and exits with sys.exit(code).

Does not belong here:
- Any logic other than assembling and starting: business rules → domain,
  scenarios → application, adapters → infrastructure or presentation.
- Resolving dependencies from the container inside layer code (Service
  Locator).
"""
