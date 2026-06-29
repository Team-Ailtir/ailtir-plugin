#!/usr/bin/env python3
"""Diagnostic probe: can a Cowork-sandboxed skill reach PostHog?

Tests three failure surfaces independently:
  1. DNS — can we resolve eu.i.posthog.com?
  2. TCP/TLS — can we open a socket and complete the handshake?
  3. HTTP — does PostHog accept a real (dry-run) capture event?

Prints a structured verdict so stdout (the only thing Claude sees) carries the result.
"""

from __future__ import annotations

import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request

POSTHOG_HOST = "eu.i.posthog.com"
POSTHOG_URL = f"https://{POSTHOG_HOST}/capture/"
POSTHOG_TOKEN = "phc_9gC5EKe7JulA1RKMs8AwlnaLiKHaI6l3mFyWf1XklO7"
TIMEOUT = 3.0


def probe_dns() -> tuple[bool, str]:
    try:
        addr = socket.gethostbyname(POSTHOG_HOST)
        return True, f"resolved to {addr}"
    except socket.gaierror as exc:
        return False, f"gaierror: {exc}"
    except OSError as exc:
        return False, f"oserror: {exc}"


def probe_tcp_tls() -> tuple[bool, str]:
    try:
        ctx = ssl.create_default_context()
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        with socket.create_connection((POSTHOG_HOST, 443), timeout=TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=POSTHOG_HOST) as tls:
                cipher = tls.cipher()
                return True, f"tls ok ({cipher[0] if cipher else 'unknown cipher'})"
    except socket.timeout:
        return False, "tcp timeout (egress likely blocked)"
    except ssl.SSLError as exc:
        return False, f"ssl error: {exc}"
    except OSError as exc:
        return False, f"oserror: {exc}"


def probe_http_capture() -> tuple[bool, str]:
    event = {
        "api_key": POSTHOG_TOKEN,
        "event": "ailtir_cowork_probe",
        "distinct_id": "telemetry-test-probe",
        "properties": {
            "source": "cowork-probe",
            "$process_person_profile": False,
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    body = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        POSTHOG_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            status = resp.status
            preview = resp.read(200).decode("utf-8", errors="replace")
            return (200 <= status < 300, f"http {status}: {preview}")
    except urllib.error.HTTPError as exc:
        return False, f"http {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return False, f"urlerror: {exc.reason}"
    except (OSError, ssl.SSLError) as exc:
        return False, f"oserror/ssl: {exc}"


def main() -> int:
    print("=== Ailtir Cowork telemetry probe ===")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Target: {POSTHOG_URL}")
    print()

    results = {}
    for name, probe in (("dns", probe_dns), ("tcp_tls", probe_tcp_tls), ("http_capture", probe_http_capture)):
        ok, detail = probe()
        results[name] = {"ok": ok, "detail": detail}
        marker = "PASS" if ok else "FAIL"
        print(f"[{marker}] {name}: {detail}")

    print()
    print("=== Verdict ===")
    if all(r["ok"] for r in results.values()):
        print("VERDICT: PostHog is reachable from this Cowork session. Telemetry will work.")
    elif not results["dns"]["ok"]:
        print("VERDICT: DNS blocked or unavailable. Telemetry cannot work without admin egress changes.")
    elif not results["tcp_tls"]["ok"]:
        print("VERDICT: TCP/TLS egress to PostHog is blocked. Telemetry cannot work without admin egress changes.")
    elif not results["http_capture"]["ok"]:
        print("VERDICT: Network reachable but PostHog rejected the capture. Token or payload issue, not a sandbox issue.")
    else:
        print("VERDICT: unknown.")

    print()
    print("=== Machine-readable ===")
    print(json.dumps(results, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
