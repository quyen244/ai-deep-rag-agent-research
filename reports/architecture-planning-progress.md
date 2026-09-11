# Architecture planning progress

Status: approved; implementation may proceed

## What changed

- Recorded the Phase 2 gap analysis.
- Defined the minimum FastAPI, Next.js, LangGraph, FastMCP, OpenAI, JSON persistence, logging, metrics, and LangSmith architecture.
- Defined run lifecycle, data relationships, failure recovery, and service boundaries.
- Created eight dependency-ordered feature specifications and task lists.
- Recorded a dashboard design contract using the dashboard-specific `industrial-brutalist-ui` skill.

## Files changed

- `features/ARCHITECTURE.md`
- `features/TODO.md`
- `features/01-foundation/spec.md` and `todo.md`
- `features/02-mcp-data-layer/spec.md` and `todo.md`
- `features/03-executor-agents/spec.md` and `todo.md`
- `features/04-orchestration-synthesis/spec.md` and `todo.md`
- `features/05-api-persistence/spec.md` and `todo.md`
- `features/06-observability/spec.md` and `todo.md`
- `features/07-nextjs-dashboard/spec.md` and `todo.md`
- `features/08-verification-documentation/spec.md` and `todo.md`

## Architecture decisions

- Two local user-facing processes: FastAPI backend and Next.js frontend.
- In-process FastMCP client/server transport for the bounded mock-data MVP.
- Explicit LangGraph fan-out instead of model-controlled supervisor handoffs.
- Structured domain outcomes and synthesis result.
- Atomic JSON files and no database.
- Partial-result behavior when at least one domain succeeds.
- In-process metrics and structured logs; no heavy monitoring deployment.
- Validator remains a documented no-op seam.
- Synchronous FastAPI execution (Option A) is approved for the bounded MVP.
- The dashboard commits to the Swiss Industrial Print archetype with one light substrate.

## Tests executed

No application tests were run because this task changed planning artifacts only. Phase 1 diagnostics had already verified the current entrypoint failure, broken legacy graph import, MCP demo import, mock tool behavior, and saved JSON null fields.

## Evidence and results

- All required feature directories, specifications, and task lists now exist.
- No application source file was modified during planning.
- Implementation tasks remain unchecked.

## Known limitations

- The current Python application remains broken and was intentionally not repaired in this planning phase.
- The frontend visual direction has not yet been implemented or rendered.

## Deferred work

- Validator behavior, real providers, database, authentication, alpha generation, heavy observability infrastructure, and LLM-as-a-judge.

## Next recommended step

Implement and verify Feature 01 before touching later features.
