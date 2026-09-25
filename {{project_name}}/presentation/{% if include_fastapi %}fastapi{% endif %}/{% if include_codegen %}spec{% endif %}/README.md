# API specification

`python -m tools.codegen` turns every `*.yaml` in this directory into one router in
`../generated/`, and collects the error handlers of all files into `../generated/__init__.py`.
The specification is the source of truth: the generated code is never edited by hand.

Keep the first line of the example: `spec.schema.json` lies next to the specification, so the
editor reports a mistake in the structure before the generator does. Every key and its default
are in that schema; the models it comes from are in `tools/codegen/spec.py`.

```yaml
# yaml-language-server: $schema=./spec.schema.json
version: 1
prefix: /items
tags: [items]

schemas:                                 # wire types: the request body, and a response that
  CreateItemRequest:                     # has to differ from the Output DTO
    name: str
    quantity: int = 1                    # a default value makes the field optional
    note: str?                           # ? is optional too, with None as the default
    state: item.ItemState                # an enum of a DTO module
  RenameItemRequest:
    title: str
  OrderLineRequest:                      # a schema inside a schema fills a DTO of the same shape:
    product: str                         # list[OrderLineRequest] -> list[OrderLineData]
    price: decimal                       # decimal goes on the wire as a string, never a float
  ItemBrief:
    id: uuid
    name: str

errors:                                  # exception class relative to the package -> status;
  domain.exceptions.ItemNotFoundError: 404   # the handlers of all files serve every endpoint
  domain.exceptions.InvalidItemNameError: 422
  domain.exceptions.ItemNotDraftError: 409      # a refused transition of a state machine

endpoints:
  create_item:                           # the name of the generated handler
    method: POST
    path: ""                             # appended to prefix
    status: 201                          # default: 200, or 204 without a response
    auth: required                       # none (default), optional, required:
                                         # credentials only, see the note below
    summary: Create an item              # OpenAPI summary
    use_case:                            # DTOs relative to <package>.application.dto;
      input: item.CreateItemInput        # the DI key is IUseCase[Input, Output]
      output: item.ItemOutput
    request:
      body: CreateItemRequest            # a schema of this file
    errors:                              # documented in OpenAPI with the status from errors
      - domain.exceptions.InvalidItemNameError
    # input is not needed: every Input field comes from the body field of the same name,
    # response is not needed: the schema is built from item.ItemOutput

  list_items:
    method: GET
    use_case:
      input: item.ListItemsInput
      output: list[item.ItemOutput]
    request:
      query:
        state:                           # the type comes from the Input field it feeds
        limit: = 20                      # ...and so does this one, with a default value

  get_item:
    method: GET
    path: /{item_id}                     # path parameters are taken from the URL,
    use_case:                            # their type from the Input field they feed
      input: item.GetItemInput
      output: item.ItemOutput
    errors:
      - domain.exceptions.ItemNotFoundError

  rename_item:
    method: PATCH
    path: /{item_id}
    use_case:
      input: item.RenameItemInput
      output: item.ItemOutput
    request:
      body: RenameItemRequest
      header:
        x_request_id: str?               # a parameter with a type of its own
    input:
      name: body.title                   # map a source by hand to rename it, or to choose
    response: ItemBrief                  # a narrower shape, checked against item.ItemOutput

  export_items:                           # the bytes and the file name come from the Output DTO, so
                                         # rendering the document is an adapter behind a port, and
                                         # the use case asks it for the bytes
    method: GET
    path: /export
    use_case:
      input: item.ExportItemsInput
      output: item.ExportItemsOutput
    response:
      file:
        content: content                 # Output DTO field, must be bytes
        filename: filename               # Output DTO field, must be str; optional
        media_type: text/csv             # default application/octet-stream
```

The message of a mapped error is the body of the response (`{"detail": str(error)}`), so the text of
every exception named in `errors:` is public API, not a note to a developer.

`auth` is about credentials and nothing else: `required` answers 401 when there is no
`Authorization: Bearer` header and draws the lock in OpenAPI, `optional` only draws the lock. The
token never reaches the handler or the Input DTO — an Input field comes from the body, the path, a
query parameter or a header, never from the call context.

`auth` alone is enough while the scenario does not depend on who the caller is — a closed endpoint
that answers the same to every holder of a token. As soon as a rule mentions the caller (his own
records, his permission), the use case needs his identity, and `auth` cannot carry it.

The identity of the caller reaches a use case through a port instead: a port of
`application/interfaces` that reads the call context, implemented where the request is available
(`implementation: presentation.fastapi.caller.BearerCaller` puts its skeleton there), and listed in
the `ports:` of the use cases that need it. Any other entrypoint then provides its own
implementation, and the permission check stays in the use case, as the layer conventions require.
