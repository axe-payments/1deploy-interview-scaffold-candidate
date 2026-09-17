# Candidate scaffold implementation handoff

Status: approved implementation direction; **the repository currently contains planning material
only**. This document tells the next agent what to build. It is not a reference solution for the
candidate's interview task. The plan PR must remain a documentation-only change.

## Purpose and source context

Build `axe-payments/1deploy-interview-scaffold-candidate`, a **public** repository a software
engineering candidate can clone, run, and modify during a roughly two-hour pair programming
interview. Their usual AI tools are allowed. The exercise is fleet heartbeat alerting; candidates
may have discussed the domain in an earlier interview but are not required to reproduce their
previous architecture. This is not an ML/model-evaluation exercise.

The old voice-agent scaffold supplied a working email receiver and a working phone-call function,
leaving the connection between them for the candidate. Preserve that division here: working input,
seeded organisational inventory, and working output transport, with consequential behaviour left
unfinished. Reduce setup friction without prescribing the missing-heartbeat solution.

Reference source: https://github.com/axe-payments/axe-interview-scaffold

For agents on the maintainer's machine, the reference checkout is at
`~/conductor/workspaces/axe-interview-scaffold/abu-dhabi-v5`; an additional checkout may exist at
`~/code/axe/axe-interview-scaffold`. Useful references are its README, TASK, Compose configuration,
app entrypoint, models file, inbound route, logging configuration, and tunnel helper. Read code
selectively; do not copy its Git history, real environment files, voice integrations, Vapi keys,
or AI-assistant restrictions. The former interview guide is context, not a binding script; this
handoff contains the decisions needed for implementation without depending on that attachment.

The private companion is `axe-payments/1deploy-interview-scaffold-staff`. It sends synthetic
heartbeats to this application's local or tunnel URL. This public repository must work without
access to that repo. Do not import private interviewer guidance, candidate transcripts, assessments,
contact details, or hiring decisions. There are no application files or runnable services yet.

## Boundary: provide the scaffold, leave the task unfinished

Supply a running HTTP app, the logging-only endpoint, seeded organisations/departments/devices,
a configured database, Slack transport, the unfinished notification wrapper, setup instructions,
and interactive API documentation. The seed tables are intentionally supplied, not a task the
candidate must reconstruct from prose.

**Do not implement a sweep, periodic evaluator, background timer, missing-heartbeat detection,
heartbeat persistence, health-state model, incident model, notification deduplication, or recovery
logic.** Do not add an application dashboard or a status API that forces the candidate to conform
to a preselected health schema. Tests for the starter should prove that the starter works, not
secretly supply the candidate's solution.

The candidate may add tables and fields, alter files and signatures, and choose their implementation
structure. Do not require reproduction of their earlier system design. Do not copy the old
AGENTS instructions that restrict using AI for architectural help or codebase exploration. Any
future contributor instructions must distinguish building this scaffold from solving the exercise.

## Shared contract — identical in both repository plans

### Ownership and compatibility

This section is duplicated intentionally so either implementation agent can work independently.
The future file `fixtures/fleet-v1.json` in the candidate repository is canonical; copy its exact
bytes into the staff repository. Use UTF-8, two-space indentation, and one final newline. The
fixture appears in full below; do not silently rename IDs, keys, or entities. Neither app should
require the other checkout or fetch inventory over the network at startup.

The fixture version describes the inventory, not a heartbeat API version. The staff app checks
that it supports the fixture version on startup. Both repositories validate uniqueness and
relationships in their own fixture tests. When both checkouts are available, also compare their
fixture files directly. A local fixture check does not prove that the other repo has been updated.
Changes to the contract require explicit coordination and updates in both repos and plans.

### Synthetic inventory and seeded database schema

There are two organisations, four departments, and twelve devices. The two organisations both
have departments called Finance and Support; select by IDs and relationships, never by name alone.

| Table | Supplied columns | Relationship |
| --- | --- | --- |
| `organisations` | `id` (string primary key), `name` (display name) | Parent of departments |
| `departments` | `id` (string primary key), `organisation_id`, `name`, `timezone` (IANA name) | Foreign key to organisation |
| `devices` | `id` (string primary key), `department_id`, `name` (display name) | Foreign key to department |

Resolve a device's organisation through its department. Do not add a second organisation foreign
key to the device model. IDs are explicit fixture values, not generated database IDs. Keep the
schema accessible for the candidate to extend. The timezone is supplied organisational metadata;
it does not establish a working-hours policy.

Do not seed `last_seen`, heartbeat history, health fields, incident or alert tables, or working-hours
rules. Those would pre-implement or unnecessarily constrain the candidate's work. All inventory
is fictional; no employee names, emails, real hostnames, customer data, or production IDs are needed.

Create `fixtures/fleet-v1.json` with exactly this content during implementation:

```json
{
  "fixture_version": 1,
  "organisations": [
    {
      "id": "org-northstar",
      "name": "Northstar Logistics"
    },
    {
      "id": "org-harbour",
      "name": "Harbour Services"
    }
  ],
  "departments": [
    {
      "id": "dept-northstar-finance",
      "organisation_id": "org-northstar",
      "name": "Finance",
      "timezone": "Australia/Sydney"
    },
    {
      "id": "dept-northstar-support",
      "organisation_id": "org-northstar",
      "name": "Support",
      "timezone": "Europe/London"
    },
    {
      "id": "dept-harbour-finance",
      "organisation_id": "org-harbour",
      "name": "Finance",
      "timezone": "Europe/London"
    },
    {
      "id": "dept-harbour-support",
      "organisation_id": "org-harbour",
      "name": "Support",
      "timezone": "America/New_York"
    }
  ],
  "devices": [
    {
      "id": "ns-fin-01",
      "department_id": "dept-northstar-finance",
      "name": "NS-FIN-01"
    },
    {
      "id": "ns-fin-02",
      "department_id": "dept-northstar-finance",
      "name": "NS-FIN-02"
    },
    {
      "id": "ns-fin-03",
      "department_id": "dept-northstar-finance",
      "name": "NS-FIN-03"
    },
    {
      "id": "ns-sup-01",
      "department_id": "dept-northstar-support",
      "name": "NS-SUP-01"
    },
    {
      "id": "ns-sup-02",
      "department_id": "dept-northstar-support",
      "name": "NS-SUP-02"
    },
    {
      "id": "ns-sup-03",
      "department_id": "dept-northstar-support",
      "name": "NS-SUP-03"
    },
    {
      "id": "hb-fin-01",
      "department_id": "dept-harbour-finance",
      "name": "HB-FIN-01"
    },
    {
      "id": "hb-fin-02",
      "department_id": "dept-harbour-finance",
      "name": "HB-FIN-02"
    },
    {
      "id": "hb-fin-03",
      "department_id": "dept-harbour-finance",
      "name": "HB-FIN-03"
    },
    {
      "id": "hb-sup-01",
      "department_id": "dept-harbour-support",
      "name": "HB-SUP-01"
    },
    {
      "id": "hb-sup-02",
      "department_id": "dept-harbour-support",
      "name": "HB-SUP-02"
    },
    {
      "id": "hb-sup-03",
      "department_id": "dept-harbour-support",
      "name": "HB-SUP-03"
    }
  ]
}
```

### HTTP input contract

The staff simulator sends `POST /inbound/heartbeat/` with `Content-Type: application/json`:

```json
{
  "organisation_id": "org-northstar",
  "department_id": "dept-northstar-finance",
  "device_id": "ns-fin-01",
  "sent_at": "2026-09-17T09:00:00Z",
  "last_upload_at": "2026-09-17T08:59:55Z"
}
```

- `organisation_id`, `department_id`, and `device_id` are required nonempty strings. The staff
  simulator derives a valid tuple from the fixture rather than allowing contradictory selections.
- `sent_at` is required and represents a timezone-aware ISO 8601 timestamp. Accept `Z` and numeric
  UTC offsets; reject naive timestamps and malformed values through ordinary request validation.
- `last_upload_at` is an optional timezone-aware timestamp: both explicit JSON null and omission
  are valid. A missing upload time does not make the heartbeat malformed.
- Accept otherwise valid timestamps far ahead of or behind the receiving server. Do not impose
  a timestamp plausibility window or normalise a bad clock into a corrected clock at ingestion.
- The initial handler logs the identifying fields and timestamps, then responds **201** with
  `{"status":"received"}`. The response means HTTP receipt only, not persistence or health.
- The initial handler performs no database writes, ID lookups, notification, or health computation.
  It consequently does not verify that submitted identities exist or belong together; that is
  distinct from the staff simulator's guarantee to emit valid fixture tuples.
- Logging records when the server received the request, but no stored receipt timestamp or
  application-level `last_seen` behaviour is supplied. A log timestamp is not a completed solution.
- Ordinary FastAPI request validation should reject missing required fields, wrong field types,
  naive datetimes, and malformed dates. Tests must cover the actual declared model and route.

Do not add an inventory-discovery protocol, application health-status API, or database access
between the two applications. The fixture and this HTTP contract are the integration boundary.

### Initial candidate-facing behaviour and timing

The interview lasts approximately two hours and permits the candidate's usual AI tools. Initial
traffic runs every **5 seconds**, with a **15-second silence threshold**, so observations do not
consume five minutes at a time. These are exercise defaults, not claims about production timing.

The candidate's first objective is to detect an ongoing outage, notify once for that outage, and
allow another notification if the device recovers and later fails again. The initial task concerns
devices that have already sent at least one heartbeat during the session. Known inventory alone
does not make a never-seen device an immediate alert requirement. Upload activity and heartbeat
receipt are distinct: a device may send heartbeats without new uploads.

The scaffold must not implement this behaviour. The candidate decides how to store heartbeat
information, detect silence, represent health or incident state, recognise recovery, and decide
when to call the notification function. No candidate-facing dashboard is included initially.

## Runtime, development loop, and file organisation

Use Python 3.12, FastAPI, Uvicorn, Tortoise ORM with PostgreSQL, and HTTPX. Reuse the old scaffold's
general approach, but verify and pin supported, compatible dependency versions at implementation
time. Do not blindly preserve old package versions. Include tests and lightweight lint tooling.

Keep the application small and direct. A suitable layout is:

- `app/main.py`: application/lifespan, router registration, database initialisation, seeding hookup.
- `app/config.py`: environment-backed settings; no hard-coded integration credentials.
- `app/models.py` and `app/seed.py`: the three inventory models and idempotent fixture insertion.
- `app/inbound.py`: the visible, editable heartbeat entry point.
- `app/notifications.py`: editable `notify` wrapper and private Slack transport helper.
- `app/tunnel.py`: optional public URL discovery, adapted only as needed.
- `fixtures/fleet-v1.json`: canonical shared inventory.
- `scripts/`: setup/verification/reset commands; `tests/`: supplied-infrastructure checks.

Do not add service layers, worker systems, repository abstractions, or migration frameworks merely
because the application might eventually need them. Ordinary ORM access should be easy to see and
extend during an interview.

### Docker and local services

Docker should be sufficient to run everything. Provide Compose services for:

- The app, port 8000 by default, source-mounted with reload enabled.
- PostgreSQL with a persistent local volume and a readiness check.
- A database browser, port 8080 by default, reachable locally.
- An optional ngrok profile exposing only the app port, never the database/browser port.

Bind host-side development ports to localhost; the application may listen on `0.0.0.0` inside its
container so the tunnel and host port mapping can reach it. Do not publish PostgreSQL to the
internet. The staff simulator reaches only the app's HTTP port through the configured tunnel.

After copying the example and setting a local database password, the normal command is:

```bash
docker compose --env-file env.local up --build
```

Use `env.local` explicitly both for Compose interpolation and for settings passed to the app.
Compose must not accidentally rely on its default `.env` filename. Document a separate tunnel
command using a Compose profile; empty `NGROK_AUTHTOKEN` must not break ordinary local startup.
Empty `SLACK_WEBHOOK_URL` must also permit app/database startup. Fail clearly only when the
optional capability is invoked without its required configuration.

Retain the tracked `env.example` and untracked `env.local` convention already bootstrapped:
`APP_PORT=8000`, `ADMINER_PORT=8080`, `LOG_LEVEL=INFO`, `POSTGRES_DB=interview`,
`POSTGRES_USER=interview`, and blank `POSTGRES_PASSWORD`, `SLACK_WEBHOOK_URL`,
`NGROK_AUTHTOKEN`, and `PUBLIC_BASE_URL`. Explain that the database password must be set locally.
The optional public URL override can bypass tunnel discovery; otherwise show the discovered URL
and/or explain how to read it from ngrok. Never require the staff repo to discover it automatically.

Create `.dockerignore` before building images; exclude `env.local`, conventional `.env` files,
Git state, local data, and credentials so `COPY` does not bake them into an image. Keep the
existing ignore rules for runtime exports and logs. Provide optional dev-container/editor setup
and a host virtualenv helper; neither is a prerequisite for the Docker workflow.

### Database creation, seed preservation, and reset

Use accessible Tortoise model definitions. Preserve the old scaffold's ability to add a model and
restart without operating a production migration toolchain. Document accurately that automatic
creation of new tables does not necessarily migrate existing columns; the candidate may explicitly
reset this disposable local database when changing an existing table shape.

Load the shared fixture, validate relationships, and insert missing seed rows in parent-first
order, using stable IDs. Existing rows must not be updated merely because they differ from the
fixture: a candidate may have deliberately changed names or configuration. Preserve extra rows,
extra tables, and candidate-added data. Seeding must not call truncate, drop tables, or delete a
volume on ordinary startup or code reload.

A separate explicit reset operation may remove the local interview database volume and recreate
it. Explain that it deletes candidate-added database data and requires an intentional action.
The reset must be limited to this Compose project's database, not arbitrary PostgreSQL databases
or all Docker volumes. Verify fresh/reset counts of 2 organisations, 4 departments, and 12 devices.

### HTTP route, API docs, and logging

Implement `POST /inbound/heartbeat/` directly in an obvious candidate-editable function. Its initial
body logs the validated payload and returns the shared 201 response. Do not place a solved engine
behind a short handler. Do not supply a scheduler or persist received timestamps as helpful setup.

Provide `/health` with a simple liveness response and `/docs`/`/redoc` via FastAPI. Make the input
example match the fixture. Distinguish server liveness from fleet health. A healthy server and a
201 heartbeat response do not imply a completed candidate solution.

Ensure structured logging fields are actually visible in container logs: the old scaffold's
formatter is a useful reference because plain logging `extra` fields can otherwise disappear.
Log startup, seed summary, receipt, and explicit transport outcomes without logging settings dumps,
connection strings, webhook URLs, tokens, or local passwords. Heartbeat payloads are synthetic;
do not adapt this convenience into a claim about production customer-data logging policy.

## Slack output boundary

Use a Slack incoming webhook from `SLACK_WEBHOOK_URL`. The webhook is already associated with the
interview channel; no channel ID or Slack OAuth setup belongs in the candidate task. Configure
only dedicated interview credentials locally. A fixed destination is deliberate.

Provide a private async `_send_slack_message(message: str)` helper that sends the webhook request,
and an editable public wrapper initially equivalent to:

```python
from typing import Any

async def notify(*args: Any, **kwargs: Any) -> None:
    await _send_slack_message(message="empty")
```

The placeholder content is intentional. The candidate decides the wrapper's eventual signature,
message, and callers. Do not wire it to incoming heartbeats or a hidden evaluator. They should
be able to discover and call it using normal Python imports and the documentation.

The transport needs a bounded timeout, response-status checking, and comprehensible errors.
Missing configuration must raise only on explicit use. Report exception class/outcome/status as
appropriate, not the exception string or request URL that can reveal the webhook. Avoid exception
chaining that prints a secret-bearing underlying request exception. Do not echo Slack response
bodies indiscriminately. Do not build queues, retries, outboxes, or delivery-durability systems.

Supply a dedicated command that explicitly sends a labelled integration-test message using the
transport helper. It proves delivery independently of the candidate's alerting logic. Startup,
seeding, health checks, tests, and documentation generation must never send Slack messages.
Automated tests replace HTTP transport with a stub; any real check is a conscious manual action.

## Candidate-facing README and TASK

Write practical documentation for a person who has never seen the earlier conversation:

1. The scenario and initial behavioural objective in the shared section, including the 5/15-second
   exercise timing, one message per ongoing outage, and a fresh notification after recovery and a
   later outage. No promised exact dispatch instant beyond the agreed threshold behaviour.
2. What is supplied: receiver, seeded inventory, database, transport, and placeholder wrapper.
3. Setup: copy `env.example` to `env.local`, set local database credentials, start Compose, inspect
   `/health` and `/docs`, and verify the expected seed records.
4. How to post one example heartbeat and find the receipt log. All examples use the shared IDs.
5. How to opt into a tunnel, obtain the URL, and give it to the interviewer. No public database UI.
6. How to verify Slack explicitly, where the wrapper lives, and why a 201 alone is not the task done.
7. The edit/reload loop, database browsing, running tests, and intentional destructive local reset.
8. The candidate can change files, models, and signatures and use their usual AI tools.

Do not prescribe a sweep, state machine, database design, or reference answer in the candidate TASK.
Do not publish the staff extension catalogue or evaluation guidance in this repo. The public
maintainer plan necessarily documents which scaffolding is absent; do not mistake that boundary
for permission to ship the missing behaviour. A health dashboard is outside the supplied scope.

## Validation and implementation sequence

Write meaningful infrastructure checks before implementing the relevant infrastructure. State the
failure each check would detect; do not build an example alert engine merely to make tests pass.
Use the actual route and application startup wiring where that is the mechanism under test.

Acceptance checks:

- Fixture JSON has version 1, exact IDs/counts, valid IANA zones, and valid relationships.
- Fresh app startup creates/seeds the three models. The same startup run a second time adds no
  duplicates. Rename a seeded row and add data before restarting: those edits must survive.
- The actual HTTP route accepts the shared example, null/omitted upload time, numeric offsets,
  and large past/future timestamps. It returns 201 and visible log fields with no database writes
  or notification calls. Unknown but syntactically valid IDs do not trigger an identity lookup.
- Missing identifiers, malformed dates, and naive timestamps fail declared request validation.
- `/health` is usable and optional integrations may remain blank at startup.
- Explicit `notify()` sends the placeholder through a fake HTTP transport. Nothing invokes it
  automatically. Missing webhook, timeout, and rejected-response cases produce useful redacted
  errors; use a sentinel secret to prove it is absent from logs and formatted exception chains.
- The explicit reset restores the original inventory and is separate from the normal startup path.
- Compose boots cleanly with documented settings; reload, database browsing, API docs, and optional
  tunnel setup are checked manually. Confirm the tunnel points only to the app port.
- `env.local` is ignored, `env.example` is tracked, and no credentials enter Git or image context.
- Compare the fixture against the staff copy when available and record which revisions were checked.

Suggested build order: environment/configuration and fixture; models/seeding; logging-only route;
Slack helper/wrapper; Docker/tunnel/editor conveniences; candidate docs; end-to-end infrastructure
verification. This order concerns scaffold construction, not a solution path for the candidate.

## Completion boundary for the implementation agent

Deliver a runnable scaffold with the infrastructure checks and documentation above. Report the
commands run and any optional live integrations left untested. Do not count absent candidate
solution behaviour as a scaffold defect. Do not add a health evaluator, reference solution, hidden
answer tests, dashboard, or production alerting framework to make the repo appear more complete.

The present handoff PR creates only this plan on top of README, `.gitignore`, and `env.example`.
Application implementation starts in a later task after the maintainer hands this repository over.
