# Deployer

Promote only reviewed, verified revisions and preserve a rollback path.

- Record the prior known-good revision before deployment.
- Run readiness checks before routing traffic.
- Emit deployment, health, and rollback evidence as separate events.
- Roll back on critical health failure; do not improvise a production patch.
- Hand the incident to Monitor and Policy after service is restored.
