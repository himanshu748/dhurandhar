# Dhurandhar engineering contract

Dhurandhar is a self-hosting autonomous software company. Preserve the audit trail and the ability to explain every automated action.

## Non-negotiable rules

- Never mutate or delete prior audit events. Corrections are new events.
- Never bypass tests, review, deployment gates, or the emergency stop.
- Treat generated code, prompts, routes, and economy rules as versioned artifacts.
- A self-improvement candidate is promoted only after its benchmark score improves with no critical regression.
- Prefer deterministic, inspectable behavior over agent theatrics.
- Keep the live Codex runtime opt-in. Local demo and tests must not consume credits or require network access.
- Do not expose secrets, raw environment values, or private source content through API responses or logs.

## Verification

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test -- --run && npm run build`
- Integrated demo: `make demo`

## Code conventions

- Python uses explicit types and Pydantic v2 models at API boundaries.
- React code uses focused components, typed API data, accessible controls, and CSS design tokens.
- Every new orchestration state needs a test and a replayable event representation.
