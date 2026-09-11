# Foundation tasks

## Contract

- [x] Draft foundation behavior and acceptance criteria.
- [x] Approve schema names, default model, and configuration boundaries.

## Implementation

- [x] Add package metadata and supported Python version.
- [x] Add validated settings and a LangChain OpenAI model factory.
- [x] Add request, state, domain, evidence, error, and report schemas.
- [x] Add centralized exception classes and safe error serialization.
- [x] Add run ID, clock, and redaction helpers.
- [x] Remove OpenRouter configuration after replacement coverage exists.

## Verification

- [x] Run deterministic configuration and schema tests.
- [x] Verify imports have no side effects.
- [x] Verify no key or secret appears in errors or logs.
- [x] Record test output in `reports/01-foundation-progress.md`.
