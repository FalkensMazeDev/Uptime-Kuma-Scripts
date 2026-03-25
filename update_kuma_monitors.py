#!/usr/bin/env python3
"""
update_kuma_monitors.py

Enforces a standard configuration across every Uptime Kuma HTTP(s) monitor.
All target values live in the CONFIG block below — set any to None to leave
that field untouched on existing monitors.

Install dependency:
    pip install uptime-kuma-api --break-system-packages

Usage:
    python update_kuma_monitors.py
"""

import sys
import time
from uptime_kuma_api import UptimeKumaApi, MonitorType

# ══════════════════════════════════════════════════════════════════
#  CONNECTION
# ══════════════════════════════════════════════════════════════════
KUMA_URL      = "http://localhost:3001"   # e.g. "https://uptime.example.com"
KUMA_USERNAME = "admin"
KUMA_PASSWORD = "your_password_here"

# ══════════════════════════════════════════════════════════════════
#  UNIVERSAL SETTINGS  (applied to every monitor type)
# ══════════════════════════════════════════════════════════════════

# How often to check (seconds). UI label: "Heartbeat Interval"
TARGET_INTERVAL = 300

# How long to wait between retry attempts after a failure (seconds).
# UI label: "Heartbeat Retry Interval"
TARGET_RETRY_INTERVAL = 60

# How many consecutive failures before marking as DOWN and alerting.
# UI label: "Retries"  |  field: maxretries
#   0 = alert on the very first failure
#   1 = alert after 2 failures  <-- your requirement
#   2 = alert after 3 failures  ... and so on
TARGET_MAX_RETRIES = 1

# How many times to re-send the DOWN alert while the monitor stays down.
# UI label: "Resend Notification if still down X times"
#   0 = send the alert once, never resend
#   1 = resend once after the first alert, 2 = resend twice, etc.
TARGET_RESEND_INTERVAL = 0    # set to None to leave untouched

# ══════════════════════════════════════════════════════════════════
#  HTTP-ONLY SETTINGS  (skipped for ping / TCP / DNS / etc.)
# ══════════════════════════════════════════════════════════════════

# HTTP method to use.  "HEAD" is faster (no body download).
# Options: "GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"
TARGET_METHOD = "HEAD"

# Alert when the TLS/SSL certificate is about to expire.
# UI label: "Certificate Expiry Notification"
TARGET_EXPIRY_NOTIFICATION = True

# Alert when the domain name registration is about to expire.
# UI label: "Domain Name Expiry Notification"
TARGET_DOMAIN_EXPIRY_NOTIFICATION = True

# Maximum redirects to follow. 0 = disable redirect following.
TARGET_MAX_REDIRECTS = 10     # set to None to leave untouched

# Request timeout in seconds.
# UI label: "Request Timeout"
TARGET_TIMEOUT = None         # e.g. 30  — set to None to leave untouched

# Ignore TLS/SSL certificate errors (useful for self-signed certs).
TARGET_IGNORE_TLS = None      # True or False — set to None to leave untouched

# Accepted HTTP status code ranges. None = leave untouched.
TARGET_ACCEPTED_STATUSCODES = None   # e.g. ["200-299"]

# ══════════════════════════════════════════════════════════════════
#  SCRIPT BEHAVIOUR
# ══════════════════════════════════════════════════════════════════

# Preview mode — print what would change but do NOT save anything.
DRY_RUN = False

# Seconds to wait when initially connecting (raise if you see timeout errors).
CONNECT_TIMEOUT = 60

# Pause between edits to avoid overwhelming the Socket.IO server.
EDIT_DELAY = 0.5

# How many times to retry an edit if the session drops mid-run.
MAX_RETRIES = 3

# ══════════════════════════════════════════════════════════════════


HTTP_TYPES = {MonitorType.HTTP}


def _changed(monitor: dict, field: str, target) -> bool:
    """Return True if target is not None and differs from the current value."""
    return target is not None and monitor.get(field) != target


def needs_update(monitor: dict) -> bool:
    mtype = monitor.get("type")
    if _changed(monitor, "interval",       TARGET_INTERVAL):          return True
    if _changed(monitor, "retryInterval",  TARGET_RETRY_INTERVAL):    return True
    if _changed(monitor, "maxretries",     TARGET_MAX_RETRIES):       return True
    if _changed(monitor, "resendInterval", TARGET_RESEND_INTERVAL):   return True
    if mtype in HTTP_TYPES:
        if _changed(monitor, "method",                   TARGET_METHOD):                     return True
        if _changed(monitor, "expiryNotification",       TARGET_EXPIRY_NOTIFICATION):        return True
        if _changed(monitor, "domainExpiryNotification", TARGET_DOMAIN_EXPIRY_NOTIFICATION): return True
        if _changed(monitor, "maxredirects",             TARGET_MAX_REDIRECTS):              return True
        if _changed(monitor, "timeout",                  TARGET_TIMEOUT):                    return True
        if _changed(monitor, "ignoreTls",                TARGET_IGNORE_TLS):                 return True
        if _changed(monitor, "accepted_statuscodes",     TARGET_ACCEPTED_STATUSCODES):       return True
    return False


def build_patch(monitor: dict) -> dict:
    mtype = monitor.get("type")
    patch: dict = {}

    def add(field, target):
        if target is not None:
            patch[field] = target

    add("interval",       TARGET_INTERVAL)
    add("retryInterval",  TARGET_RETRY_INTERVAL)
    add("maxretries",     TARGET_MAX_RETRIES)
    add("resendInterval", TARGET_RESEND_INTERVAL)

    if mtype in HTTP_TYPES:
        add("method",                   TARGET_METHOD)
        add("expiryNotification",       TARGET_EXPIRY_NOTIFICATION)
        add("domainExpiryNotification", TARGET_DOMAIN_EXPIRY_NOTIFICATION)
        add("maxredirects",             TARGET_MAX_REDIRECTS)
        add("timeout",                  TARGET_TIMEOUT)
        add("ignoreTls",                TARGET_IGNORE_TLS)
        add("accepted_statuscodes",     TARGET_ACCEPTED_STATUSCODES)

    return patch


def build_diff(monitor: dict) -> str:
    """Human-readable summary of what will change."""
    mtype = monitor.get("type")
    parts = []

    def diff(label, field, target):
        if target is not None and monitor.get(field) != target:
            parts.append(f"{label}: {monitor.get(field)!r} -> {target!r}")

    diff("interval",        "interval",                   TARGET_INTERVAL)
    diff("retryInterval",   "retryInterval",              TARGET_RETRY_INTERVAL)
    diff("maxretries",      "maxretries",                 TARGET_MAX_RETRIES)
    diff("resendInterval",  "resendInterval",             TARGET_RESEND_INTERVAL)

    if mtype in HTTP_TYPES:
        diff("method",                   "method",                   TARGET_METHOD)
        diff("expiryNotification",       "expiryNotification",       TARGET_EXPIRY_NOTIFICATION)
        diff("domainExpiryNotification", "domainExpiryNotification", TARGET_DOMAIN_EXPIRY_NOTIFICATION)
        diff("maxredirects",             "maxredirects",             TARGET_MAX_REDIRECTS)
        diff("timeout",                  "timeout",                  TARGET_TIMEOUT)
        diff("ignoreTls",                "ignoreTls",                TARGET_IGNORE_TLS)
        diff("accepted_statuscodes",     "accepted_statuscodes",     TARGET_ACCEPTED_STATUSCODES)

    return ", ".join(parts)


def connect() -> UptimeKumaApi:
    api = UptimeKumaApi(KUMA_URL, timeout=CONNECT_TIMEOUT)
    api.login(KUMA_USERNAME, KUMA_PASSWORD)
    return api


def edit_with_retry(api: UptimeKumaApi, mid: int, patch: dict) -> UptimeKumaApi:
    """Edit a monitor, reconnecting and retrying if the session drops."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            api.edit_monitor(mid, **patch)
            return api
        except Exception as exc:
            err = str(exc).lower()
            is_auth_error = any(k in err for k in ("logout", "not logged", "unauthorized"))
            if is_auth_error and attempt < MAX_RETRIES:
                print(f"      Reconnecting (attempt {attempt}/{MAX_RETRIES}) …")
                try:
                    api.disconnect()
                except Exception:
                    pass
                time.sleep(2)
                api = connect()
            else:
                raise
    return api


def main():
    print(f"Connecting to {KUMA_URL} …")
    try:
        api = connect()
    except Exception as exc:
        print(f"[ERROR] Could not connect / login: {exc}")
        sys.exit(1)

    try:
        monitors = api.get_monitors()
    except Exception as exc:
        print(f"[ERROR] Failed to retrieve monitors: {exc}")
        api.disconnect()
        sys.exit(1)

    if not monitors:
        print("No monitors found. Nothing to do.")
        api.disconnect()
        return

    # Skip group containers — they are not real monitors
    monitors = [m for m in monitors if m.get("type") != MonitorType.GROUP]

    print(f"Found {len(monitors)} monitor(s).\n")

    updated = 0
    skipped = 0
    errors  = 0

    for monitor in monitors:
        mid  = monitor["id"]
        name = monitor.get("name", f"ID {mid}")

        if not needs_update(monitor):
            print(f"  [OK]      {name!r:50s}  (no changes needed)")
            skipped += 1
            continue

        diff_str = build_diff(monitor)
        patch    = build_patch(monitor)

        if DRY_RUN:
            print(f"  [DRY-RUN] {name!r:50s}  {diff_str}")
            updated += 1
            continue

        try:
            api = edit_with_retry(api, mid, patch)
            print(f"  [UPDATED] {name!r:50s}  {diff_str}")
            updated += 1
        except Exception as exc:
            print(f"  [ERROR]   {name!r:50s}  failed after {MAX_RETRIES} attempt(s): {exc}")
            errors += 1

        time.sleep(EDIT_DELAY)

    api.disconnect()

    print(f"\n{'─'*60}")
    print(f"  Monitors checked : {len(monitors)}")
    print(f"  Already correct  : {skipped}")
    print(f"  {'Would update' if DRY_RUN else 'Updated'}       : {updated}")
    if errors:
        print(f"  Errors           : {errors}")
    print(f"{'─'*60}")
    if DRY_RUN:
        print("\nDry-run mode — no changes were saved.")


if __name__ == "__main__":
    main()
