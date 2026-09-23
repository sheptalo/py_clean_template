# Application specification

`python -m tools.codegen` turns every `*.yaml` in this directory into `application/dto/<file>.py`
and `application/interfaces/<file>.py`, and adds the classes it declares to the skeletons
`application/use_cases/<file>.py`, `infrastructure/<file>.py` and `tests/fakes/<file>.py`.

Keep the first line of the example: `spec.schema.json` lies next to the specification, so the
editor reports a mistake in the structure before the generator does. The field reference is in
the repository README.

```yaml
# yaml-language-server: $schema=./spec.schema.json
version: 1

enums:                                   # StrEnum in application/dto/<file>.py: OPEN = "open"
  ItemState: [open, archived]

dtos:                                    # DTOs of this module
  ItemOutput:
    id: uuid                             # str, int, float, bool, uuid, datetime, date, decimal,
    name: str                            # an enum or another DTO of this file, list[...];
    quantity: int                        # a trailing ? makes the field optional
    state: ItemState

use_cases:                               # CreateItemUseCase -> DTO CreateItemInput
  CreateItemUseCase:
    input:
      name: str
      quantity: int
    output: ItemOutput                   # a DTO of this file, list[...] of one, or none
    ports:                               # fields of the skeleton: a port of this file,
      items: IItemRepository             # or a dotted path like application.interfaces.clock.IClock

  ListItemsUseCase:
    input:
      state: ItemState?
      limit: int
    output: list[ItemOutput]
    ports:
      items: IItemRepository

  DeleteItemUseCase:
    input:
      item_id: uuid
    output: none
    ports:
      items: IItemRepository

interfaces:                              # ports, the name starts with I
  IItemRepository:
    doc: Items, kept between requests.   # docstrings: the contract every implementation keeps
    implementation: SqlItemRepository     # the class to write in infrastructure/<file>.py
    scope: app                           # lifetime of the implementations: request (default) or app
    methods:                             # every method is async and abstract
      get:
        doc: The item with this id, or None if there is none.
        args:
          item_id: uuid                  # a scalar, an enum or DTO of this file, or a dotted path
        returns: domain.item.Item?       # to a class relative to the package
      find:
        doc: |
          Items in creation order.
          state=None returns every item.
        args:
          state: ItemState?
        returns: list[domain.item.Item]
      add:
        args:
          item: domain.item.Item
        returns: none
```

A file with only `interfaces` produces no DTO module.
