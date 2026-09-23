from collections.abc import Iterator
from contextlib import contextmanager

from dishka import Provider, Scope
from fastapi.testclient import TestClient

from composition.api import create_app


def override(key: object, instance: object) -> Provider:
    """Answer `key` with `instance` — for example IUseCase[Input, Output] with a fake use case."""
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: instance, provides=key)
    return provider


@contextmanager
def app_client(*providers: Provider) -> Iterator[TestClient]:
    """The whole application over HTTP, with `providers` replacing what they provide."""
    with TestClient(create_app(*providers)) as client:
        yield client
