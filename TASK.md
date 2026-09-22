# The task

## Start here

Boot the app (see [README.md](./README.md)) and open the interactive API docs at
<http://localhost:8000/docs>. That is the map of what exists.

## The scenario

Two organisations run a fleet of payment devices, grouped into departments. Each device
sends a **heartbeat** to this service every few seconds while it is online, and each
heartbeat may also say when the device last uploaded data.

Right now a heartbeat arrives, gets logged, and… nothing else happens. If a device goes
quiet, nobody finds out.

## What you're given

Both ends of the pipe work:

1. **An inbound heartbeat endpoint:** `POST /inbound/heartbeat/` in `app/inbound.py`.
   The payload is:

   ```json
   {
     "organisation_id": "org-northstar",
     "department_id": "dept-northstar-finance",
     "device_id": "ns-fin-01",
     "sent_at": "2026-09-17T09:00:00Z",
     "last_upload_at": "2026-09-17T08:59:55Z"
   }
   ```

   `sent_at` is a timezone-aware timestamp from the device's own clock. `last_upload_at`
   is optional (it may be `null` or missing): a device can keep heart-beating without
   uploading anything new. The handler validates the payload, logs it, and returns `201`.

2. **The inventory**, seeded into Postgres from `fixtures/fleet-v1.json`: 2 organisations,
   4 departments (each with an IANA timezone), 12 devices. Look at it in Adminer
   (<http://localhost:8080>) or in `app/models.py`. Both organisations have a department
   called Finance and one called Support, so use ids, not names.

3. **A Slack transport:** `_send_slack_message(message)` in `app/notifications.py` posts to
   the interview channel. `notify(...)` next to it is a placeholder wrapper: its
   signature, its message and who calls it are yours to decide. Nothing calls it today.

During the interview, the interviewer's simulator sends heartbeats to your app (through
your tunnel) **every 5 seconds per device**, and can silence devices, bring them back, and
make them misbehave in various ways.

## What to build

**Notify Slack when a device that has been heart-beating stops.** For this exercise, treat
**15 seconds** of silence as "stopped" (the real number would be much larger; the short one
keeps the feedback loop fast).

Concretely, the first objective:

- When a device that has sent at least one heartbeat goes quiet for the threshold, send a
  Slack message about it.
- Send **one** message for that outage, however long it lasts.
- If the device recovers (heartbeats resume) and later goes quiet again, that is a new
  outage and should produce a new message.

Devices that have never sent a heartbeat during the session are out of scope for the
first objective. How you build it and what the message says are your call. Change any
file, model or signature.

## Out of scope

- Slack internals: `_send_slack_message` is a black box you call.
- Anything about *what the device is uploading*. Heartbeats and uploads are different
  things; the first objective is about heartbeats.
- Dashboards, auth, deployment.

## Definition of done

With the simulator sending heartbeats, silencing a device produces exactly one Slack
message for that outage, and a later, separate outage of the same device produces another.
