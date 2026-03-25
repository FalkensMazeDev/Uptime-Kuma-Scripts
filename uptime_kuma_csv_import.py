#!/usr/bin/env python3
"""
uptime_kuma_csv_import.py
--------------------------
Reads a CSV file of hostnames/URLs and checks whether each one already
exists in Uptime Kuma.  If a monitor is not found (accounting for www /
no-www variants) it is added automatically as an HTTP(s) monitor.

Usage:
    python uptime_kuma_csv_import.py --csv monitors.csv \
        --url http://localhost:3001 \
        --username admin \
        --password secret

CSV format (one column, header optional):
    url
    example.com
    subdomain.example.com
    ...
"""

import argparse
import csv
import logging
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from uptime_kuma_api import UptimeKumaApi, MonitorType

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RETRY_ATTEMPTS = 5          # total attempts for API connection
RETRY_DELAY    = 3          # seconds between retries (doubles each attempt)
REQUEST_DELAY  = 0.5        # polite pause between individual monitor checks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def connect_with_retry(url: str, username: str, password: str) -> UptimeKumaApi:
    """Connect to Uptime Kuma with exponential-backoff retries."""
    delay = RETRY_DELAY
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            log.info("Connecting to Uptime Kuma (attempt %d/%d) …", attempt, RETRY_ATTEMPTS)
            api = UptimeKumaApi(url)
            api.login(username, password)
            log.info("Connected successfully.")
            return api
        except Exception as exc:
            log.warning("Connection attempt %d failed: %s", attempt, exc)
            if attempt < RETRY_ATTEMPTS:
                log.info("Retrying in %d seconds …", delay)
                time.sleep(delay)
                delay *= 2          # exponential back-off
            else:
                log.error("All %d connection attempts failed. Exiting.", RETRY_ATTEMPTS)
                sys.exit(1)


def normalise_host(raw: str) -> str:
    """
    Extract just the hostname from a URL or bare hostname string,
    then strip a leading 'www.' so we always compare the root host.

    Examples
        https://www.example.com/path  →  example.com
        www.example.com               →  example.com
        example.com                   →  example.com
        http://sub.example.com        →  sub.example.com
    """
    raw = raw.strip()
    # treat bare hostnames as if they have a scheme so urlparse works properly
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    host = urlparse(raw).hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host.lower()


def monitor_url(monitor: dict) -> str:
    """Return the 'url' field of a monitor, falling back to empty string."""
    return monitor.get("url") or monitor.get("hostname") or ""


def build_www_variants(host: str):
    """Return a set of root and www. variant for a normalised host."""
    return {host, "www." + host}


def fetch_existing_monitors(api: UptimeKumaApi) -> list:
    """Fetch all monitors with retry logic."""
    delay = RETRY_DELAY
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            monitors = api.get_monitors()
            log.info("Fetched %d existing monitors.", len(monitors))
            return monitors
        except Exception as exc:
            log.warning("Failed to fetch monitors (attempt %d): %s", attempt, exc)
            if attempt < RETRY_ATTEMPTS:
                time.sleep(delay)
                delay *= 2
            else:
                log.error("Could not fetch monitors after %d attempts.", RETRY_ATTEMPTS)
                sys.exit(1)


def add_monitor_with_retry(api: UptimeKumaApi, name: str, url: str) -> bool:
    """Add a single HTTP(s) monitor with retry logic. Returns True on success."""
    delay = RETRY_DELAY
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            api.add_monitor(
                type=MonitorType.HTTP,
                name=name,
                url=url,
            )
            return True
        except Exception as exc:
            log.warning("Failed to add '%s' (attempt %d): %s", name, attempt, exc)
            if attempt < RETRY_ATTEMPTS:
                time.sleep(delay)
                delay *= 2
            else:
                log.error("Could not add monitor '%s' after %d attempts.", name, RETRY_ATTEMPTS)
                return False


def read_csv(path: Path) -> list[str]:
    """
    Read URLs/hostnames from a CSV file.

    Expects a header row with a column named 'url', 'hostname', 'host',
    'domain', or 'address' (case-insensitive).  Falls back to the first
    column if none of those names are found.  Works cleanly with
    single-column files that have no trailing comma.
    """
    preferred = {"url", "hostname", "host", "domain", "address"}
    entries = []

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)

        # Identify which column to read
        if reader.fieldnames is None:
            log.error("CSV appears to be empty or has no header row.")
            sys.exit(1)

        normalised_fields = {f.strip().lower(): f for f in reader.fieldnames}
        col_key = next((normalised_fields[k] for k in normalised_fields if k in preferred), None)
        if col_key is None:
            col_key = reader.fieldnames[0]   # fall back to first column
            log.warning("No recognised URL column found; using first column: '%s'", col_key)
        else:
            log.info("Reading URLs from column: '%s'", col_key)

        for row in reader:
            value = (row.get(col_key) or "").strip()
            if value:
                entries.append(value)

    log.info("Read %d entries from %s.", len(entries), path)
    return entries


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Check CSV hosts against Uptime Kuma and add missing monitors."
    )
    parser.add_argument("--csv",      required=True, help="Path to the CSV file")
    parser.add_argument("--url",      required=True, help="Uptime Kuma URL  e.g. http://localhost:3001")
    parser.add_argument("--username", required=True, help="Uptime Kuma username")
    parser.add_argument("--password", required=True, help="Uptime Kuma password")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report what would be added without actually adding anything"
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        log.error("CSV file not found: %s", csv_path)
        sys.exit(1)

    # 1. Connect
    api = connect_with_retry(args.url, args.username, args.password)

    # 2. Load existing monitors once (build a lookup set of normalised hosts)
    existing_monitors = fetch_existing_monitors(api)
    existing_hosts: set[str] = set()
    for m in existing_monitors:
        raw_url = monitor_url(m)
        if raw_url:
            existing_hosts.add(normalise_host(raw_url))

    log.info("Unique normalised hosts already in Uptime Kuma: %d", len(existing_hosts))

    # 3. Read CSV
    csv_entries = read_csv(csv_path)

    # 4. Check each entry
    already_exists = []
    to_add         = []

    for raw in csv_entries:
        norm = normalise_host(raw)
        variants = build_www_variants(norm)

        if variants & existing_hosts:          # intersection — any variant present?
            already_exists.append(raw)
            log.info("  [EXISTS ] %s  (matched as: %s)", raw, norm)
        else:
            to_add.append(raw)
            log.info("  [MISSING] %s  (normalised: %s)", raw, norm)

        time.sleep(REQUEST_DELAY)

    # 5. Summary before acting
    print("\n" + "=" * 60)
    print(f"  Total entries in CSV : {len(csv_entries)}")
    print(f"  Already in Kuma      : {len(already_exists)}")
    print(f"  To be added          : {len(to_add)}")
    print("=" * 60 + "\n")

    if not to_add:
        log.info("Nothing to add. All done.")
        api.disconnect()
        return

    if args.dry_run:
        log.info("DRY RUN — the following would be added:")
        for entry in to_add:
            log.info("  + %s", entry)
        api.disconnect()
        return

    # 6. Add missing monitors
    added   = []
    failed  = []

    for raw in to_add:
        raw = raw.strip()

        # The CSV value is the display name as-is (e.g. "example.com")
        name = raw

        # Prepend https:// for the actual monitor URL
        url_to_add = "https://" + raw

        log.info("Adding monitor: %s  →  %s", name, url_to_add)

        if add_monitor_with_retry(api, name, url_to_add):
            added.append(raw)
            log.info("  [ADDED  ] %s", url_to_add)
        else:
            failed.append(raw)
            log.error("  [FAILED ] %s", url_to_add)

        time.sleep(REQUEST_DELAY)

    # 7. Final report
    print("\n" + "=" * 60)
    print(f"  Successfully added : {len(added)}")
    print(f"  Failed to add      : {len(failed)}")
    print("=" * 60)

    if failed:
        print("\nFailed entries:")
        for f in failed:
            print(f"  - {f}")

    api.disconnect()
    log.info("Disconnected. Done.")


if __name__ == "__main__":
    main()
