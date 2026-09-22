#!/usr/bin/env bash
#
# Send ONE labelled test message to Slack through the app's transport helper.
# Proves SLACK_WEBHOOK_URL in env.local works, independently of anything you build.
# This is the only way the scaffold ever sends to Slack by itself.
#
#   ./scripts/slack_check.sh

source "$(dirname "$0")/_compose.sh"

compose exec app python -m app.slack_check
