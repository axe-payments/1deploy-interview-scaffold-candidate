# Fleet heartbeat interview scaffold

A small service that receives device heartbeats and (once you build the middle) tells
people on Slack when devices go quiet. Your task is in **[TASK.md](./TASK.md)**.

This README only covers getting it running. Budget about five minutes.

## Prerequisites

- **Docker Desktop** (running). Nothing else needs installing: no Python, no Postgres.
- The **`env.local` contents** the interviewer sends you (a database password and a Slack
  webhook URL).

## Setup

```bash
# 1. Create your env file. Paste in what the interviewer sent you (or fill in the blanks).
cp env.example env.local

# 2. Boot everything: app + database + database browser. First run builds the image (~1-2 min).
docker compose --env-file env.local up --build
```

When uvicorn reports `Application startup complete`, it is ready. The startup log also
shows the seeded inventory: `Startup complete organisations=2 departments=4 devices=12`.

- API: <http://localhost:8000> — interactive docs at <http://localhost:8000/docs>
  (reading view at <http://localhost:8000/redoc>)
- Database browser (Adminer): <http://localhost:8080>

> `--env-file env.local` is needed on **every** `docker compose` command (`up`, `logs`,
> `exec`, `down`). The scripts in `scripts/` add it for you.

## Confirm it works (before you build anything)

```bash
./scripts/verify.sh
```

Checks `/health`, `/docs` and the seed counts: **2 organisations, 4 departments, 12
devices**. (`/health` means this server is up. It says nothing about any device.)

**Send one heartbeat** (this is what the interviewer's simulator will do, many times):

```bash
./scripts/send_heartbeat.sh            # POSTs the example payload for device ns-fin-01
./scripts/send_heartbeat.sh hb-sup-02  # any device id from fixtures/fleet-v1.json
```

You get `{"status":"received"}` with HTTP 201, and the `docker compose up` terminal shows:

```
INFO app.inbound Heartbeat received organisation_id='org-northstar' department_id='dept-northstar-finance' device_id='ns-fin-01' sent_at='...' last_upload_at='...' received_at='...'
```

That log line is all the scaffold does with a heartbeat today. A 201 means "received",
not "stored" and certainly not "healthy".

**Check Slack** (needs `SLACK_WEBHOOK_URL` in `env.local`):

```bash
./scripts/slack_check.sh
```

Posts one labelled test message to the interview channel through the same transport
helper your code will use. This is the only thing in the scaffold that ever sends to Slack
by itself; startup, tests and heartbeats never do.

## Let the interviewer reach your app (tunnel)

The interviewer sends heartbeats from their machine, so your app needs a public URL.
Stop the plain `docker compose up` (Ctrl-C) and start it with a tunnel instead:

```bash
./scripts/tunnel.sh            # Cloudflare quick tunnel: no account, no token
./scripts/tunnel_url.sh        # (another terminal) prints the public https URL
```

Send that URL to the interviewer. Only port 8000 (the app) is exposed; the database and
Adminer stay local. The URL changes every time the tunnel restarts, so re-run
`tunnel_url.sh` and re-send it if you restart. `GET /tunnel/` shows the same thing.

If the Cloudflare URL does not resolve straight away on your machine, give it a minute
(DNS caching); the interviewer's side is usually fine. If it will not work on your network,
use ngrok instead: put the `NGROK_AUTHTOKEN` you were given in `env.local`, then
`./scripts/tunnel.sh ngrok` and `./scripts/tunnel_url.sh ngrok`.

## Your dev loop

The source is mounted into the container with hot-reload: **edit files, save, and the app
restarts**. Watch the `docker compose up` terminal for errors after each save.

| File | What it is |
|------|------------|
| `app/inbound.py` | **Start here.** `POST /inbound/heartbeat/` — receives a heartbeat and currently just logs it. |
| `app/notifications.py` | **Given.** `_send_slack_message(message)` posts to Slack. `notify(...)` is a placeholder wrapper for you to shape. |
| `app/models.py` | The three seeded inventory tables (Tortoise ORM). Add fields, add models, or ignore it. |
| `app/seed.py` | Seeds `fixtures/fleet-v1.json` on startup without touching rows you changed or added. |
| `app/config.py`, `app/main.py`, `app/log.py`, `app/tunnel.py` | Wiring. You should not need to touch these, but you can. |
| `fixtures/fleet-v1.json` | The inventory: 2 organisations → 4 departments → 12 devices. Same file the simulator uses. |
| `tests/` | Tests for the supplied pieces. Add your own alongside. |

You can change any file, model, or function signature. Use whatever AI tools you normally
use. `AGENTS.md` (which `CLAUDE.md` imports) sets the ground rules your assistant will
follow in this repo: it helps fully with orientation, libraries, bugs and code you have
designed, and asks for your thinking on the design decisions. Read it so its pushback
does not surprise you.

### Database

Adminer at <http://localhost:8080>: System `PostgreSQL`, Server `postgres`, and the
username / password / database from your `env.local`.

New models in `app/models.py` get their tables created automatically on restart. Adding or
changing columns on an *existing* table does not alter it. For that, reset the local
database (destructive: it deletes every row and table you added):

```bash
./scripts/reset_db.sh      # asks for confirmation, then removes this project's volume
docker compose --env-file env.local up --build   # recreates + reseeds 2 / 4 / 12
```

### Tests and lint

```bash
./scripts/test.sh            # pytest inside the container (uses SQLite + a fake Slack)
./scripts/test.sh -k inbound # pass any pytest arguments
docker compose --env-file env.local exec app ruff check .
```

### Editor setup (optional)

The app runs in Docker, so your editor needs the packages for import resolution and lint:

- **Attach to the running container (no local Python):** with the stack up, in Cursor/VS Code
  run "Dev Containers: Attach to Running Container…", pick the `app` container and open
  `/code`. The interpreter there already has every dependency.
- **Local venv:** `./scripts/setup_venv.sh` (needs Python 3.12), then pick
  `./.venv/bin/python` as the interpreter. `.vscode/` already points at it. This also lets
  you run `./.venv/bin/pytest` directly.

## Useful commands

```bash
docker compose --env-file env.local up            # start (foreground, shows logs)
docker compose --env-file env.local up -d         # start in the background
docker compose --env-file env.local logs -f app   # follow the app logs
docker compose --env-file env.local down          # stop
./scripts/reset_db.sh                             # stop AND wipe the database
```
