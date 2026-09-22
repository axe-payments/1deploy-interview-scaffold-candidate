# The task

Boot the app ([README.md](./README.md)), then:

- API docs: <http://localhost:8000/docs>
- Heartbeats come in at `POST /inbound/heartbeat/` (`app/inbound.py`).
- Slack messages are sent by `_send_slack_message` in `app/notifications.py`.

## What to build

- When a device that has sent at least one heartbeat goes quiet, send a Slack message
  about it.
- Send **one** message for that outage, however long it lasts.
- If the device recovers (heartbeats resume) and later goes quiet again, that is a new
  outage and should produce a new message.
