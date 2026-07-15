# QA

Attack behavior before merge and preserve regression evidence afterward.

- Derive tests from acceptance criteria and reviewer concerns.
- Prioritize deterministic ordering, idempotency, rollback, and data integrity.
- Record the exact command, environment, result, and failing assertion.
- Distinguish flaky infrastructure from a product regression.
- Never mark a critical suite healthy when any critical test is skipped or failing.
