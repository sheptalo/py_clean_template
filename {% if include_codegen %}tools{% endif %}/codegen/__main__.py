"""Generate the FastAPI presentation layer from the YAML specification.

python -m tools.codegen            # write generated code
python -m tools.codegen --check    # fail if generated code is out of date
"""

import sys
from argparse import ArgumentParser

from tools.codegen.render import REPO_ROOT, generate, outdated, write
from tools.codegen.spec import SpecError


def main() -> int:
    parser = ArgumentParser(prog="python -m tools.codegen", description=__doc__)
    parser.add_argument("--check", action="store_true", help="do not write, only report changes")
    arguments = parser.parse_args()

    try:
        files = generate()
    except SpecError as error:
        print(error)
        return 2
    changed = outdated(files) if arguments.check else write(files)
    for path in changed:
        print(path.relative_to(REPO_ROOT))
    if arguments.check and changed:
        print("generated code is out of date, run: python -m tools.codegen")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
