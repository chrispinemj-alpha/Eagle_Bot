# Eagle Bot Architecture

Eagle Core is the product. Channels are doors into the product.

```text
EAGLE BOT
  ├── Identity
  ├── Intelligence
  │   ├── Orchestration
  │   ├── Memory
  │   └── Coworkers
  ├── Governance
  │   ├── Permissions
  │   ├── Approvals
  │   ├── Risk classification
  │   └── Audit
  └── Work state
      ├── Orders
      └── Future Tasks / Projects / Workflows

        ↓ adapters
      Web / Telegram / API / future channels
```

## Boundary Rules
1. Channels never become the source of truth for Eagle state.
2. External AI providers are accessed through `AIGateway`.
3. Real-world information is accessed through `WorldGateway` and must preserve evidence metadata.
4. Tools must be explicitly registered.
5. Unknown actions and tools default to deny.
6. High-impact actions require approval.
7. Critical execution is never silently authorized.
8. Existing legacy code is not removed merely to make the architecture look cleaner.

## Build Order
1. Foundation
2. Intelligence
3. Coworkers
4. Governance
5. Channels
6. Real Work
7. Scale
