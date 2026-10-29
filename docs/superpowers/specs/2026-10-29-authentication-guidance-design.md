# Authentication and authorization guidance

## Goal

Give projects generated from this template a reusable, transport-neutral guide for implementing authentication and authorization. The guide must capture the useful boundaries in the source skill without carrying over its project name, industry concepts, transport choices, cookie names, class names, or role vocabulary.

This change adds guidance only. It does not implement authentication, choose an identity provider, or change generated application behavior.

## Design

Add `.agents/skills/authentication/SKILL.md.jinja` as a vendor-neutral skill copied into generated projects as `SKILL.md`. Write it in the concise English style used by the existing skills and layer conventions. Describe the workflow in terms of the template's layers and generated-project paths, without naming a particular application or business domain.

The skill will make these boundaries explicit:

- **Presentation** extracts credentials from an incoming transport, asks the authentication boundary to validate them, and handles transport-level responses. Cryptographic validation and checks such as expiry or credential revocation stay outside domain logic.
- **Application** receives an explicit verified identity (or explicit absence of one) and resolves the current principal through ports when needed. Protected use cases enforce business authorization so alternate entry points cannot bypass it.
- **Domain** owns rules that depend on business entities or values. It does not inspect credentials, tokens, requests, or transport metadata.
- **Infrastructure** implements identity, account, and credential ports using the selected storage or provider.
- **Composition** wires the authentication context and port implementations with a lifetime appropriate to the incoming operation.

The guidance will distinguish authentication (establishing who is acting) from authorization (deciding whether that actor may perform a scenario). It will say not to treat mutable identity attributes or permissions carried in a credential as authoritative when they can change; current values must be resolved according to the chosen application policy. It will keep public operations public, put protected-operation checks at the application boundary, centralize transport error mapping, and avoid per-handler permission logic as the only enforcement.

The guide will not prescribe a token format, login mechanism, identity-provider product, revocation strategy, user schema, permission model, transport protocol, or fixed set of ports and DTOs. Those are application decisions. Any examples will use neutral names and be clearly illustrative.

## Template integration

Update the existing layer conventions and AI-agent guidance only where needed to make the new skill discoverable and remove ambiguity:

- Add the skill to `.agents/README.md` and the skill list in `AGENTS.md.jinja`.
- Align `application/__init__.py` and `presentation/__init__.py` with the responsibilities above, especially where they currently describe identity, token expiry, and revocation as belonging to different layers.
- Add authentication-specific test responsibilities to `tests/__init__.py.jinja`: application tests for missing/invalid/stale identity and authorization outcomes as applicable; presentation tests for transport mapping; composition tests for identity/port wiring. Tests remain driven by selected behavior rather than assumed protocols.
- Clarify that `EndpointSpec.auth` / generated `HTTPBearer` checks are transport-level credential-presence handling, not complete authentication or business authorization. Do not expand the generator's authentication behavior in this change.

Keep the changes limited to guidance and its discovery. Do not add generated ports, DTOs, use cases, providers, middleware, exception classes, dependencies, or example business rules.

## Validation

- Review every added rule against the existing layer conventions and ensure each responsibility has one clear home.
- Check that no project, industry, resource, role, credential name, or transport-specific implementation from the source skill is carried into the reusable guidance.
- Check Copier conditionals and paths so the skill is emitted correctly in generated projects.
- Do not change authentication runtime behavior as part of this work.

The guide will describe the authentication flow as: the presentation boundary validates incoming credentials and produces a verified identity; an application authentication workflow resolves current account state through ports and exposes only a safe principal context; the protected use case makes business authorization decisions. The credential and transport never enter domain entities or business use cases.
