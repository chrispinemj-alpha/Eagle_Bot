# Eagle Bot Governance

## Core rule
More capability → more responsibility → stronger governance.

## Risk model
- LOW: informational work; no external side effect.
- MEDIUM: bounded work requiring normal permission checks.
- HIGH: consequential external action; human approval required.
- CRITICAL: exceptional impact; explicit approval and additional deployment controls required.

## Human control
The foundation provides explicit permission checks, approval records and an emergency kill switch. Production deployment must add durable authorization, independent audit storage, operator controls and tested incident procedures.

## Truthfulness
The system must distinguish implemented behavior from planned behavior. Documentation must not be treated as evidence that a capability exists.
