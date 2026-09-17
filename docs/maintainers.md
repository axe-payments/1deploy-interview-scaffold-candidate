# Maintainer notes

This repository is the **candidate-facing starter** for the fleet heartbeat interview. It
is public. Two rules keep it useful:

## 1. Scaffold, not solution

The candidate's exercise (see `TASK.md`) is to detect silence, notify once per outage and
allow a new notification after recovery. The scaffold must therefore never contain:

- heartbeat persistence, a `last_seen` column, or any stored receipt timestamp;
- a periodic sweep, background timer or scheduler;
- a health or incident model, notification deduplication, or recovery logic;
- a fleet status API or dashboard that presupposes a health schema;
- anything that calls `notify()` / `_send_slack_message()` automatically.

Tests in `tests/` prove the supplied pieces work (route validation, seeding, Slack transport
redaction). They must not smuggle in an example alert engine to pass. A private companion
repository (`1deploy-interview-scaffold-staff`) holds the interviewer's traffic simulator
and guide; nothing from it belongs here.

## 2. The shared contract

`fixtures/fleet-v1.json` and the `POST /inbound/heartbeat/` payload are the integration
boundary with the staff simulator. Both repositories carry a byte-identical copy of the
fixture. Changing ids, fields, the route, the 201 response, or the accepted timestamp forms
requires a coordinated change in both repositories and both plans.

## Layout conventions

- `env.example` is tracked; `env.local` is not (see `.gitignore` and `.dockerignore`).
  Never commit credentials, never bake `env.local` into the image.
- Every `docker compose` call needs `--env-file env.local`; scripts source
  `scripts/_compose.sh` for that.
- The helper scripts need only bash, curl and sed on the host; anything else runs inside
  the app container. Only the app port is ever tunnelled. Postgres has no host port; Adminer binds to
  localhost.
- Logging never prints the webhook URL, connection strings or tokens. The `httpx` and
  `httpcore` loggers are pinned to WARNING for that reason.

## Contributor instructions for AI agents

Building or maintaining this scaffold is not the same as solving the exercise. When
working on this repository as a maintainer, keep the boundary above. When a candidate uses
AI tools during the interview, that is allowed and expected; do not add instruction files
that restrict how they use them.
