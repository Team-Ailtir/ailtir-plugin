#!/usr/bin/env python3
"""Probe #2: what CAN reach out from Cowork, and how do paths resolve?

Investigates two questions left open by the PostHog probe:
  1. Path resolution — does ${CLAUDE_SKILL_DIR} substitute? Does sys.argv[0] give
     us a reliable absolute path? What's the working directory?
  2. Egress allowlist — which common SaaS / cloud hostnames does the proxy
     actually allow outbound to? Tested independently so a single allowed host
     unlocks an architecture option.
"""

from __future__ import annotations

import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request

TIMEOUT = 3.0

EGRESS_TARGETS = [
    ("anthropic.com", "https://www.anthropic.com/"),
    ("api.anthropic.com", "https://api.anthropic.com/"),
    ("github.com", "https://github.com/"),
    ("raw.githubusercontent.com", "https://raw.githubusercontent.com/"),
    ("api.github.com", "https://api.github.com/"),
    ("pypi.org", "https://pypi.org/simple/"),
    ("cloudflare.com", "https://www.cloudflare.com/"),
    ("workers.dev", "https://workers.dev/"),
    ("vercel.com", "https://vercel.com/"),
    ("vercel.app", "https://vercel.app/"),
    ("notion.com", "https://www.notion.com/"),
    ("api.notion.com", "https://api.notion.com/"),
    ("ailtir.ai", "https://ailtir.ai/"),
]


def banner(title: str) -> None:
    print()
    print(f"=== {title} ===")


def probe_paths() -> dict:
    out = {}
    out["cwd"] = os.getcwd()
    out["sys_argv_0"] = sys.argv[0]
    out["abs_argv_0"] = os.path.abspath(sys.argv[0])
    out["__file__"] = os.path.abspath(__file__)
    out["script_dirname"] = os.path.dirname(os.path.abspath(__file__))
    out["env_CLAUDE_SKILL_DIR"] = os.environ.get("CLAUDE_SKILL_DIR")
    out["env_CLAUDE_PLUGIN_ROOT"] = os.environ.get("CLAUDE_PLUGIN_ROOT")
    out["env_AILTIR_PLUGIN_DATA"] = os.environ.get("AILTIR_PLUGIN_DATA")
    out["env_HOME"] = os.environ.get("HOME")
    out["env_USER"] = os.environ.get("USER")
    out["claude_env_keys"] = sorted(k for k in os.environ if "CLAUDE" in k.upper())
    out["all_env_keys_sample"] = sorted(os.environ.keys())[:50]
    return out


def probe_egress_host(host: str, url: str) -> tuple[bool, str]:
    # DNS first — cheap and tells us which hosts the proxy refuses to even resolve.
    try:
        socket.gethostbyname(host)
    except (socket.gaierror, OSError) as exc:
        return False, f"dns-fail: {exc}"

    ctx = ssl.create_default_context()
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            return True, f"http {resp.status}"
    except urllib.error.HTTPError as exc:
        # A real HTTP response (even 4xx/5xx) means egress works.
        return True, f"http {exc.code} (egress ok)"
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if "403" in reason or "Forbidden" in reason or "Tunnel" in reason:
            return False, f"proxy-block: {reason}"
        return False, f"urlerror: {reason}"
    except (OSError, ssl.SSLError) as exc:
        return False, f"oserror/ssl: {exc}"


def main() -> int:
    print("=== Ailtir Cowork sandbox probe #2 ===")
    print(f"Python: {sys.version.split()[0]}")

    banner("Path resolution")
    paths = probe_paths()
    for key, val in paths.items():
        if isinstance(val, list):
            print(f"  {key}: {val}")
        else:
            print(f"  {key}: {val!r}")

    banner("Egress allowlist test")
    egress_results = {}
    for host, url in EGRESS_TARGETS:
        ok, detail = probe_egress_host(host, url)
        egress_results[host] = {"ok": ok, "detail": detail}
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {host}: {detail}")

    banner("Verdict")
    reachable = [h for h, r in egress_results.items() if r["ok"]]
    if reachable:
        print(f"REACHABLE HOSTS: {', '.join(reachable)}")
        print("=> A proxy-friendly telemetry relay on one of these domains is viable.")
    else:
        print("NO HOSTS REACHABLE. Egress is fully locked down in this sandbox.")
        print("=> Outbound telemetry of any kind is infeasible without an admin allowlist change.")

    print()
    if paths["env_CLAUDE_SKILL_DIR"]:
        print(f"${{CLAUDE_SKILL_DIR}} IS exported as an env var: {paths['env_CLAUDE_SKILL_DIR']!r}")
    else:
        print("${CLAUDE_SKILL_DIR} is NOT exported as an env var.")
    if paths["env_CLAUDE_PLUGIN_ROOT"]:
        print(f"${{CLAUDE_PLUGIN_ROOT}} IS exported as an env var: {paths['env_CLAUDE_PLUGIN_ROOT']!r}")
    else:
        print("${CLAUDE_PLUGIN_ROOT} is NOT exported as an env var.")
    print()
    print(f"cwd at script start: {paths['cwd']}")
    print(f"script's own dir (reliable absolute):  {paths['script_dirname']}")
    print("=> If cwd != script dir, the 'relative paths' guidance is broken in Cowork;")
    print("   use the script's own dirname or an env var to anchor bundled-file refs.")

    banner("Machine-readable")
    print(json.dumps({"paths": paths, "egress": egress_results}, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
