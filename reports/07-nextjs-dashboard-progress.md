# Feature 07 - Next.js dashboard progress

Status: complete

## Delivered

- Added the App Router dashboard in `dashboard/` with a typed FastAPI client, request composer, domain views, evidence, comparison table, execution details, and raw JSON actions.
- Added explicit empty, validation, loading, partial, failed, and offline-recovery states.
- Applied the requested Slick Carbon default surface: `linear-gradient(180deg, #323232 0%, #3f3f3f 49%, #1c1c1c 100%)`; the accessible light substrate remains available as an alternate theme.
- Reviewed visual hierarchy with real screenshots. The masthead was reduced, validation feedback was placed beside its source field, the primary action was enlarged and grouped, and completed research results now lead the workspace ahead of the follow-up composer.
- Added a local favicon, corrected strict E2E locators, and excluded framework/test artifacts from linting and Git tracking.

## Visual evidence

Meaningful before/after, error, empty, desktop, mobile, and light-mode captures are stored in `artifacts/feature-07/`.

## Verification evidence

```text
dashboard: node node_modules/typescript/bin/tsc --noEmit
pass

dashboard: node node_modules/eslint/bin/eslint.js .
pass

dashboard: node node_modules/vitest/vitest.mjs run
3 test files passed, 9 tests passed

dashboard: npm run test:e2e
2 passed

dashboard: node node_modules/next/dist/bin/next build
pass

root: venv/bin/python -m pytest
72 passed, 1 warning in 6.45s

Lighthouse production audit
performance: 94
accessibility: 100
best practices: 100
```

The browser-driven test now submits a multi-ticker run to the actual deterministic FastAPI application, then verifies the resulting comparison table and narrow viewport domain navigation. The request crosses the graph, executors, FastMCP, synthesizer, and JSON repository. A fresh browser session reported zero console errors after the favicon was added.
