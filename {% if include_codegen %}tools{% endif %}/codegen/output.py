"""Format rendered code with the project's ruff settings, and import it before anything is written."""

import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "pyproject.toml"


def format_codes(files: dict[Path, str]) -> dict[Path, str]:
    """Format rendered files with the project's ruff settings, in two ruff runs for all of them."""
    if not files:
        return {}  # ruff with no paths would check and fix the whole repository
    with TemporaryDirectory() as directory:
        copies = {path: Path(directory, path.relative_to(REPO_ROOT)) for path in files}
        for path, copy in copies.items():
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_text(files[path], encoding="utf-8")
        names = [str(copy) for copy in copies.values()]
        run_ruff(["check", "--fix-only", "--config", str(CONFIG), *names])
        run_ruff(["format", "--config", str(CONFIG), *names])
        return {path: copy.read_text(encoding="utf-8") for path, copy in copies.items()}


def run_ruff(arguments: list[str]) -> None:
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "ruff", *arguments],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    if result.returncode:
        raise RuntimeError(f"ruff {arguments[0]} failed: {result.stderr.strip()}")


@contextmanager
def installed(files: dict[Path, str]) -> Iterator[None]:
    """Import the freshly rendered application modules, so routers are checked against the specification.

    The modules they replace are put back on exit: code imported before keeps the classes of the package.
    """
    previous: dict[str, ModuleType | None] = {}
    try:
        for path, text in files.items():
            name = ".".join(path.relative_to(REPO_ROOT).with_suffix("").parts)
            previous[name] = sys.modules.get(name)
            module = ModuleType(name)
            module.__file__ = str(path)
            sys.modules[name] = module
            exec(compile(text, str(path), "exec"), module.__dict__)  # noqa: S102
        yield
    finally:
        for name, original in previous.items():
            if original is None:
                del sys.modules[name]
            else:
                sys.modules[name] = original
