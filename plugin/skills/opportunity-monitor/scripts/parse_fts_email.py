#!/usr/bin/env python3
"""
Parses Find a Tender (FTS) and Contracts Finder daily digest emails into structured JSON.

Reads from a file path passed as argv[1], or from stdin if no argument is given.
Prints a JSON array of opportunities to stdout. Missing fields are emitted as empty strings.
"""
import sys
import json
import re


NOTICE_TYPES = [
    "Tender Notice",
    "Preliminary Market Engagement Notice",
    "Pipeline Notice",
    "Transparency Notice",
    "Contract Award Notice",
    "Contract Details Notice",
    "Contract Termination Notice",
    "Contract Performance Notice",
]


def _match_notice_type(block: str) -> str:
    """Return the first NOTICE_TYPES value that appears in the block, or ''."""
    lowered = block.lower()
    for nt in NOTICE_TYPES:
        if nt.lower() in lowered:
            return nt
    return ""


def _extract_value_gbp(line: str) -> str:
    """Extract a GBP value like '£5,300,000' or '£5.3m' as a normalised string.

    Returns the raw string as-is if a currency symbol is found; empty string otherwise.
    """
    match = re.search(r"£\s*[\d,\.]+\s*[MmKk]?", line)
    return match.group(0).strip() if match else ""


def parse_email(text: str):
    opportunities = []

    blocks = re.split(r"\n\s*\n", text)

    for block in blocks:
        if not block.strip():
            continue
        # FTS digest lines often lead with the title in plain text or after a numbered index.
        # Contracts Finder uses similar Title/Authority/Deadline/Link patterns.
        if not any(marker in block for marker in ("Title:", "Tender:", "Notice:", "Contracting Authority:", "Contract Title:")):
            continue

        opp = {
            "title": "",
            "authority": "",
            "authority_type": "",
            "notice_type": _match_notice_type(block),
            "value": "",
            "cpv": "",
            "cpv_desc": "",
            "deadline": "",
            "link": "",
            "location": "",
        }

        for raw_line in block.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            # Strip a leading numeric-list marker like "1. " or "12) " so keyed lines match.
            line = re.sub(r"^\s*\d+[\.\)]\s*", "", line)

            lower = line.lower()

            # Check the more specific "contracting authority" prefix BEFORE the generic
            # "title:" / "contract title:" checks — they would otherwise misfire.
            if lower.startswith(("contracting authority:", "buyer:", "client:")):
                opp["authority"] = line.split(":", 1)[1].strip()
            elif lower.startswith("authority:") and not lower.startswith("authority type:"):
                opp["authority"] = line.split(":", 1)[1].strip()
            elif lower.startswith(("contract title:", "title:", "tender:", "notice:")):
                opp["title"] = line.split(":", 1)[1].strip()
            elif lower.startswith(("authority type:", "buyer type:")):
                opp["authority_type"] = line.split(":", 1)[1].strip()
            elif lower.startswith(("notice type:",)):
                # Explicit Notice Type line overrides the regex match.
                opp["notice_type"] = line.split(":", 1)[1].strip()
            elif lower.startswith(("estimated value:", "value:", "contract value:")):
                raw = line.split(":", 1)[1].strip()
                opp["value"] = _extract_value_gbp(raw) or raw
            elif lower.startswith(("cpv:", "cpv code:")):
                raw = line.split(":", 1)[1].strip()
                # Split first token as code, remainder as description.
                parts = raw.split(None, 1)
                opp["cpv"] = parts[0] if parts else ""
                opp["cpv_desc"] = parts[1] if len(parts) > 1 else ""
            elif lower.startswith(("deadline:", "closing:", "closing date:", "submission deadline:")):
                opp["deadline"] = line.split(":", 1)[1].strip()
            elif lower.startswith(("location:", "region:", "place of performance:")):
                opp["location"] = line.split(":", 1)[1].strip()
            elif lower.startswith(("link:", "url:", "notice link:")):
                url_match = re.search(r"(https?://\S+)", line)
                if url_match:
                    opp["link"] = url_match.group(1)
            elif "http" in line and not opp["link"]:
                url_match = re.search(r"(https?://\S+)", line)
                if url_match:
                    opp["link"] = url_match.group(1)

        if opp["title"]:
            opportunities.append(opp)

    return opportunities


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result = parse_email(text)
    print(json.dumps(result, indent=2))
