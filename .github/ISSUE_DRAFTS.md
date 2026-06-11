# Draft Issue Descriptions for Review

Below are detailed drafts for complex feature issues. Review each section and reply with which issue(s) to publish (e.g., `publish: #Group orders`, `publish: all`) or suggest edits.

---

## Group orders: pool tokens to place a single group order

Summary
- Allow multiple festival goers to pool token contributions to place a single group order. Backend will validate each contributor's available balance, atomically reserve contributions, and create a single order record that follows the same stock and acknowledgement rules as single-user orders.

Detailed spec
- API: `POST /group-orders` payload:
  - `items`: array of { `id` | `name`, `quantity` }
  - `contributors`: array of { `festivalier_id`, `contribution`: { `drink_tokens`: int, `food_tokens`: int } }
- Validation rules:
  - Each contributor's offered contribution may not exceed their available tokens.
  - The pooled total must cover the aggregated cost of requested items (drink vs food tokens evaluated separately).
  - All items must be in stock; if any item is out-of-stock, the entire request fails with 409 and no balances change.
- Atomicity and persistence:
  - Reserve contributors' contributions in a transaction-like flow (or application-level reservation + finalize) so partially-applied updates do not remain on failure.
  - Create a single `Order` entity representing the group order with metadata linking to contributors and contribution amounts.
- Side effects:
  - On successful creation (pending acknowledgement) the order is persisted; tokens are only deducted when the order is acknowledged as per existing rules.
- Errors and responses:
  - `400` for malformed requests
  - `402` or `409` for insufficient pooled funds or stock issues
  - `201` with `orderId` on success

Acceptance criteria
- Unit tests for cost aggregation and contributor balance validation
- Integration tests for successful group order and insufficient-pool rejection
- API contract documented with example requests

Gherkin
Scenario: Successful group order
  Given three users contribute drink tokens summing to required total and items are in stock
  When they submit a group order
  Then order is created and contributors' balances are reserved (and later deducted on acknowledgement)

Scenario: Rejected if pooled tokens insufficient
  Given pooled contributions are below required cost
  When group order is attempted
  Then the API returns 402/409 and no balances are changed

Estimated effort: 3–5 days
Labels: feature, group-order

---

## Change order before acknowledgement (and notify bartender on late requests)

Summary
- Support modifying orders while unacknowledged. For already-acknowledged orders, create a review/change-request workflow that notifies bartenders and lets them accept/reject based on prepared items.

Detailed spec
- API:
  - `PATCH /orders/{order_id}` — if order.status == `EN_ATTENTE`, apply change immediately after validating stock and balances.
  - `POST /orders/{order_id}/change-requests` — create a change request when the order is `ACKNOWLEDGED` or beyond; responds with request id.
  - `GET /orders/{order_id}/change-requests` — list pending change requests for bartender UI.
  - `POST /orders/{order_id}/change-requests/{req_id}/resolve` — bartender accepts or rejects the change.
- Business rules:
  - For unacknowledged orders: revalidate token totals and stock; if valid, replace items and return updated order.
  - For acknowledged orders: do not mutate the original order. Instead create a `ChangeRequest` object that records proposed modifications and notifies bartender(s).
  - Bartender resolution:
    - Accept: perform any feasible reuse/transfer of prepared items, update order composition/status, recompute ETA.
    - Reject: record reason and notify festivalier.
- Notifications:
  - On creation of change request, send message to bartender channel (in-app, webhook, or mock adapter).
  - On resolution, notify festivalier with decision and updated ETA if accepted.

Acceptance criteria
- Tests for modifying unacknowledged orders (happy path and failure cases)
- Tests for creating change requests and bartender resolution behaviour
- Clear API examples and error codes

Gherkin
Scenario: Modify unacknowledged order
  Given an unacknowledged order and sufficient tokens/stock
  When festivalier requests modifications via PATCH
  Then modifications are accepted and tokens/stock validated

Scenario: Request change on acknowledged order
  Given an acknowledged order
  When festivalier requests changes
  Then a bartender notification is created and the change is pending review

Estimated effort: 2–4 days
Labels: feature, order-change

---

## Bartender acknowledge order and provide ETA (ETA calculation)

Summary
- Bartenders can acknowledge an order and the system calculates an estimated readiness time according to the rules in `FEATURES.md` (per-type durations and special handling for meals).

Detailed spec
- API: `POST /orders/{order_id}/acknowledge` — requires bartender role.
- ETA rules (implement exactly as written in FEATURES.md):
  - Non-alcoholic drinks: 1 minute per distinct drink type
  - Normal alcoholic drinks: 2 minutes per drink
  - Premium alcoholic drinks: 3 minutes per drink
  - Snacks: 2 minutes per snack type
  - Meals: 10 minutes per meal type plus the longest drink preparation time in the order
  - Mixed orders: sum components; items of the same type prepared together (count distinct types where specified)
- Actions on acknowledge:
  - Deduct tokens (drink/food) from the order contributors' balances (or single festivalier) at acknowledgement time
  - Persist ETA and set order.status = `ACKNOWLEDGED` with `eta_minutes` and `acknowledged_at`
  - Trigger notification to festivalier with ETA
- Validation:
  - Ensure stock is still sufficient at acknowledge time; if not, surface errors to bartender and prevent acknowledgement.

Acceptance criteria
- Deterministic unit tests for ETA computations across multiple combos
- Integration test showing token deduction occurs at acknowledgement
- API docs with example payload and response

Gherkin
Scenario: Acknowledge order with mixed items
  Given an order with mixed drinks and meals
  When bartender acknowledges it
  Then order status becomes acknowledged and response contains calculated `eta_minutes`

Estimated effort: 2–3 days
Labels: feature, acknowledge, eta

---

## Mark order as ready and notify festival goer

Summary
- Bartenders mark orders as ready only when prepared item counts meet requested quantities; marking ready triggers a notification to festival goer(s).

Detailed spec
- API: `POST /orders/{order_id}/ready` — transitions order to `READY` if prepared counts are sufficient.
- Preconditions:
  - There must be enough prepared items to fulfil the order (prepared inventory tracking required)
- Effects:
  - Set `status = READY`, set `ready_at` timestamp
  - Trigger pickup notification to festivalier(s) with order id and pickup details
- Errors:
  - 409 Conflict if prepared counts insufficient

Acceptance criteria
- Tests for ready transition only when prepared quantities suffice
- Notification emitted to festivalier on ready

Gherkin
Scenario: Mark ready when prepared
  Given an acknowledged order with prepared items sufficient to fulfil it
  When bartender marks the order as ready
  Then order status becomes READY and user receives a pickup notification

Estimated effort: 1–2 days
Labels: feature, ready

---

## Bartender review of acknowledged-order change requests

Summary
- Enable bartender review/resolve of change requests created by festival goers for acknowledged orders; resolution should account for prepared items reuse.

Detailed spec
- Endpoints:
  - `GET /orders/{order_id}/change-requests` — list pending requests
  - `POST /orders/{order_id}/change-requests/{req_id}/resolve` — payload `{ action: "accept" | "reject", reason?: string }`
- Business logic:
  - When accepting, compute whether prepared items can be transferred to the modified composition. If so, update order items and recompute ETA.
  - When rejecting, leave order unchanged and notify festivalier with reason.
- Notifications and audit:
  - Persist resolution decision, resolver id, and timestamp. Notify festivalier with a human-friendly message and updated ETA when relevant.

Acceptance criteria
- Tests demonstrating acceptance when transfer possible and rejection otherwise
- Audit trail for change requests

Gherkin
Scenario: Accept change when transfer possible
  Given an acknowledged order and at least one prepared item can be transferred
  When bartender accepts the change request
  Then the order is updated and festivalier is notified with a new ETA

Estimated effort: 2–3 days
Labels: feature, change-review

---

## Transfer tokens between festival goers with confirmation

Summary
- Allow secure transfers of up to 3 tokens of each type per transfer; transfers require recipient confirmation.

Detailed spec
- API:
  - `POST /transfers` — create transfer request: `{ from_id, to_id, food_tokens, drink_tokens }`.
  - `GET /transfers/{id}` — get transfer status.
  - `POST /transfers/{id}/confirm` — recipient confirms and finalizes the transfer.
- Business rules:
  - Sender cannot offer more than 3 tokens per type and must have sufficient available tokens at request time (reservation pattern recommended).
  - Recipient confirmation finalizes the movement of tokens; if recipient denies or timeout expires, the reservation is released.
  - Transfers must not leave sender with negative balances.
- Notifications:
  - Notify recipient on transfer creation; notify both parties on finalize or rejection.

Gherkin
Scenario: Successful transfer with confirmation
  Given user A has at least 3 drink tokens and user B accepts transfer
  When A transfers 3 drink tokens to B
  Then A's balance decreases and B's increases accordingly

Scenario: Prevent over-transfer
  Given A has only 1 snack token and attempts to transfer 3
  When transfer is requested
  Then the system rejects the transfer

Acceptance criteria
- Tests for reservation + finalize flow, expiry behavior, and over-transfer prevention

Estimated effort: 2–3 days
Labels: feature, transfer

---

## Hydration notifications scheduler (hourly, or 30min for heavy drinkers)

Summary
- Scheduled reminders to festival goers to hydrate. Frequency is hourly by default during 11:00–19:00, and every 30 minutes for users who've consumed >3 alcoholic drinks in the last hour.

Detailed spec
- Implementation:
  - Background scheduled task runs every 30 minutes and computes recipients and frequency per-user.
  - For each festivalier:
    - Determine alcoholic drinks consumed in the last hour via order history.
    - If >3 drinks in last hour: candidate frequency is 30min; otherwise 60min.
    - Ensure notifications are only sent between 11:00 and 19:00 local festival time.
- Notification payload: friendly message, optional tips for responsible drinking.
- Config/adapters:
  - Plug-in notification adapter (no-op/mock for tests; SMTP/push for production integration).
- Tests:
  - Unit tests for heavy-drinker detection logic
  - Integration test for scheduler decisioning

Gherkin
Scenario: Hourly hydration reminders
  Given current time within 11:00–19:00 and user consumed <=3 alcoholic drinks in last hour
  When scheduler runs
  Then user receives a hydration reminder every hour

Scenario: Heavy-drinker gets 30-minute reminders
  Given user consumed 4 alcoholic drinks in last hour
  When scheduler runs
  Then user receives a hydration reminder every 30 minutes

Estimated effort: 2–4 days
Labels: feature, notifications, hydration

---

## Inventory admin endpoints (PATCH /inventory/{item_id})

Summary
- Admin API to set/update stock quantities for items; rejects negative values.

Detailed spec
- API: `PATCH /inventory/{item_id}` body `{ quantity: int }`.
- Validation: quantity must be integer >= 0.
- Effects: update StockRepository and emit an audit log entry.
- Access: document admin-only access; basic auth/role gating can be added later.

Gherkin
Scenario: Update stock quantity
  Given a bartender updates an item stock to 10
  When the PATCH request is accepted
  Then the system stores stock=10 and it cannot be negative

Estimated effort: 1 day
Labels: feature, inventory

---

# How to respond
- To publish a single draft: `publish: <section title>` (exact title or short unique fragment)
- To publish all drafts: `publish: all`
- To edit a section: `edit: <section title>` and include your changes
- To skip publishing and keep drafts: `keep: drafts`

I'll wait for your validation before creating/updating the corresponding GitHub issues.