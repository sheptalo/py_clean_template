"""Tests — how they are written, whoever writes them.

The layout mirrors the package: tests/domain, tests/application,
tests/infrastructure, tests/presentation. tests/architecture checks the
structure of the code, tests/fakes holds fakes of ports.

A test states behaviour.
- The name is a claim about it: test_create_item_rejects_negative_quantity,
  not test_create_item_2.
- One scenario per test: arrange, act, assert. parametrize is for a table
  of inputs that share one behaviour.
- Assert a concrete value. "Something came back" (is not None, len > 0,
  isinstance) is not a check.
- A new test fails without the change it covers. A bug fix starts with a
  test that reproduces the bug.

A failing test is a question, not an obstacle.
- First decide which is wrong: the test or the code.
- The expected value changes only when the requirement changed, and the
  change is stated explicitly.
- A test is never weakened, skipped or deleted to make the suite pass.

domain — rules and invariants, edge values, domain errors.
- Plain objects only: no mocks, no I/O, no async.

application — a use case scenario end to end: input and output, the state
of the ports after the call, branches on domain errors, the permission check.
- Ports are replaced by fakes from tests/fakes: an in-memory subclass of
  the port, not a Mock. Assert the result and the state of the fake, never
  which methods were called and with what.
- Domain rules are not tested again here.

infrastructure — the contract of a port on the real technology: what was
written is read back, a missing record gives the answer the port promises.
- No business scenarios.
- These are integration tests: conftest.py marks everything in
  tests/infrastructure as integration. Pre-commit runs pytest -m "not
  integration"; integration tests run in CI, or by hand with the services
  up. Every other test runs without external services.

presentation — the mapping: status codes, the shape of the response,
authentication, an error turned into a status, no extra fields leaving
the service.
- The use case is replaced through DI.
- Generated routers are covered by their specification. Test only what the
  specification does not describe, through the application, without
  importing the generated modules.

Everywhere:
- Async tests are marked @pytest.mark.anyio.
- No sleep, no real time, no unseeded randomness: time and identifiers come
  through ports and are fixed in fakes.
- Frameworks are not tested: request validation, pydantic parsing and
  dependency resolution work without our tests.
- Coverage is a report (pytest --cov), not a goal: a test that exists only
  to raise it is not written.
"""
