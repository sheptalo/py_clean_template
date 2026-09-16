# Application specification

`python -m tools.codegen` turns every `*.yaml` in this directory into `application/dto/<file>.py`
and `application/interfaces/<file>.py`, and adds the classes it declares to the skeletons
`application/use_cases/<file>.py` and `infrastructure/<file>.py`.

Keep the first line of the example: `spec.schema.json` lies next to the specification, so the
editor reports a mistake in the structure before the generator does. The field reference is in
the repository README.

```yaml
# yaml-language-server: $schema=./spec.schema.json
version: 1

dtos:                                    # DTOs of this module
  ItemOutput:
    id: uuid                             # str, int, float, bool, uuid, datetime, date, decimal,
    name: str                            # another DTO of this file, list[...];
    quantity: int                        # a trailing ? makes the field optional

use_cases:                               # CreateItemUseCase -> DTO CreateItemInput
  CreateItemUseCase:
    input:
      name: str
      quantity: int
    output: ItemOutput                   # a DTO of this file, list[...] of one, or none

  ListItemsUseCase:
    input:
      limit: int?
    output: list[ItemOutput]

  DeleteItemUseCase:
    input:
      item_id: uuid
    output: none

interfaces:                              # ports, the name starts with I
  IItemRepository:
    implementation: SqlItemRepository     # the class to write in infrastructure/<file>.py
    scope: app                           # lifetime of the implementations: request (default) or app
    methods:                             # every method is async and abstract
      get:
        args:
          item_id: uuid                  # a scalar, a DTO of this file, or a dotted path to a class
        returns: domain.item.Item?
      add:
        args:
          item: domain.item.Item
        returns: none
```
