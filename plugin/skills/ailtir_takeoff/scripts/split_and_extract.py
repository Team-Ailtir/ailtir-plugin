#!/usr/bin/env python3
"""Split a multi-page construction drawing PDF and extract per-page JSON.

Top-level orchestrator for the `ailtir_takeoff` skill. Splits the input
PDF into one-page PDFs (via PyMuPDF `Document.insert_pdf`/`select`),
renders each page to PNG (`page.get_pixmap` at `dpi/72` zoom), calls
the sibling `extract.py` (imported in-process) on each single-page PDF,
aggregates a `manifest.json`, and produces a labelled contact-sheet
JPEG (Pillow `Image`/`ImageDraw`).

All intermediate artefacts live under `_working/`; only `manifest.json`
and `contact_sheet.jpg` sit at the top level of `--output`.

Ailtir differentiators (see spec):
    * Bid-folder detection (`.../Bids/<REF>/...` -> `manifest.bid_ref`).
    * ISO 19650-aware `--trade` — code A/S/M/E/P/C/L/F or name.
    * Resumable via `--overwrite` (matches `process_drawing.py`).
    * Contact-sheet labels use extracted sheet numbers, not `p01...`.
    * `--profile` reads `Context/profile.json` and forwards it to extract.
    * `_working/` isolation.

Public references cited in-code: PyMuPDF (Document.select, get_pixmap),
Pillow (Image, ImageDraw), and `research/drawing-conventions.md`
§ Role codes for the ISO 19650 role-letter mapping. Behaviour is
intentionally aligned with `spec_project-indexer_process_drawing.md`.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(f"split_and_extract.py: PyMuPDF is required ({exc})\n")
    sys.exit(2)

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
    _PIL_AVAILABLE = True
except Exception:  # pragma: no cover
    Image = ImageDraw = ImageFont = None  # type: ignore
    _PIL_AVAILABLE = False


# ISO 19650 UK Annex role codes exposed to --trade. Source:
# research/drawing-conventions.md § Role codes.
TRADE_CODE_TO_NAME: dict[str, str] = {
    "A": "Architectural", "S": "Structural", "M": "Mechanical",
    "E": "Electrical", "P": "Plumbing", "C": "Civil",
    "L": "Landscape", "F": "Fire",
}
TRADE_NAME_TO_CODE = {v.lower(): k for k, v in TRADE_CODE_TO_NAME.items()}
TRADE_ALIASES: dict[str, str] = {
    "arch": "A", "architect": "A", "struct": "S",
    "mech": "M", "hvac": "M", "elec": "E", "electric": "E",
    "public health": "P", "ph": "P", "plumb": "P",
    "civ": "C", "land": "L", "fire protection": "F",
}

BID_REF_RE = re.compile(r"^[A-Z]{2,}[-_]?[A-Z0-9\-]{3,}$")
CONTACT_SHEET_JPEG_QUALITY = 85
LOG = logging.getLogger("ailtir.takeoff.split_and_extract")


# --- argument parsing -------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="split_and_extract.py",
        description="Split a construction PDF and run per-page extraction.",
    )
    p.add_argument("input_pdf", help="Path to the multi-page PDF.")
    p.add_argument("-o", "--output", required=True,
                   help="Top-level output directory (created if missing).")
    p.add_argument("--pages", default="all",
                   help="Page selection: '1-5,8,10-12' or 'all'.")
    p.add_argument("--trade", default=None,
                   help="ISO 19650 role code (A/S/M/E/P/C/L/F) or name.")
    p.add_argument("--dpi", type=int, default=150, help="PNG DPI (72..600).")
    p.add_argument("--no-images", action="store_true",
                   help="Skip PNG rendering.")
    p.add_argument("--overwrite", action="store_true",
                   help="Regenerate all per-page artefacts.")
    p.add_argument("--profile", action="store_true",
                   help="Read Context/profile.json and forward it to extract.")
    p.add_argument("--quiet", action="store_true", help="Silence progress logs.")
    return p


# --- --pages parser ---------------------------------------------------------


def parse_pages(spec: str, page_count: int) -> list[int]:
    """Parse a --pages expression. Raises ValueError on any bad input.

    Silent clamping is forbidden by spec — user typos must surface.
    """
    if page_count < 1:
        raise ValueError("PDF reports zero pages")
    text = (spec or "").strip()
    if not text or text.lower() == "all":
        return list(range(1, page_count + 1))

    result: set[int] = set()
    for raw in text.split(","):
        chunk = raw.strip()
        if not chunk:
            continue
        if "-" in chunk:
            l, _, r = chunk.partition("-")
            l, r = l.strip(), r.strip()
            if not (l.isdigit() and r.isdigit()):
                raise ValueError(f"invalid range token: {chunk!r}")
            lo, hi = int(l), int(r)
            if lo < 1 or hi < lo:
                raise ValueError(f"invalid range token: {chunk!r}")
            for n in range(lo, hi + 1):
                if n > page_count:
                    raise ValueError(f"page {n} out of range 1..{page_count}")
                result.add(n)
        else:
            if not chunk.isdigit():
                raise ValueError(f"invalid page token: {chunk!r}")
            n = int(chunk)
            if n < 1 or n > page_count:
                raise ValueError(f"page {n} out of range 1..{page_count}")
            result.add(n)
    if not result:
        raise ValueError(f"no pages selected by {spec!r}")
    return sorted(result)


# --- --trade resolver -------------------------------------------------------


def resolve_trade(value: str | None) -> dict[str, str] | None:
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        raise ValueError("empty --trade value")
    if len(raw) == 1:
        code = raw.upper()
        if code in TRADE_CODE_TO_NAME:
            return {"code": code, "name": TRADE_CODE_TO_NAME[code]}
        raise ValueError(f"unknown trade code: {raw!r}")
    key = " ".join(raw.split()).lower()
    if key in TRADE_NAME_TO_CODE:
        code = TRADE_NAME_TO_CODE[key]
    elif key in TRADE_ALIASES:
        code = TRADE_ALIASES[key]
    else:
        raise ValueError(f"unknown trade name/alias: {raw!r}")
    return {"code": code, "name": TRADE_CODE_TO_NAME[code]}


# --- bid folder + profile ---------------------------------------------------


def detect_bid_ref(output_dir: Path) -> str | None:
    """Walk parents looking for `.../Bids/<REF>/...` (spec differentiator)."""
    parts = output_dir.resolve().parts
    for i, seg in enumerate(parts[:-1]):
        if seg.lower() == "bids":
            candidate = parts[i + 1]
            if BID_REF_RE.match(candidate.upper()):
                return candidate
    return None


def load_profile(output_dir: Path) -> tuple[dict[str, Any] | None, bool]:
    """Search for Context/profile.json up from output_dir; fall back to CWD."""
    search = [output_dir, *output_dir.resolve().parents, Path.cwd()]
    for base in search:
        candidate = base / "Context" / "profile.json"
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    LOG.info("loaded profile from %s", candidate)
                    return data, True
                LOG.warning("profile.json at %s is not a JSON object", candidate)
            except (OSError, json.JSONDecodeError) as exc:
                LOG.warning("cannot read %s: %s", candidate, exc)
            return None, False
    LOG.warning("--profile requested but no Context/profile.json found")
    return None, False


# --- extract.py integration -------------------------------------------------


def import_extract_module():
    """Import the sibling `extract.py` in-process.

    Preferred over subprocess-per-page because the Cowork sandbox pays a
    multi-second Python startup on cold invocations. Subprocess is used
    only as a last-resort fallback.
    """
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import importlib
    return importlib.import_module("extract")


def run_extract(extract_mod: Any, sheet_pdf: Path, sheet_json: Path,
                profile: dict[str, Any] | None) -> tuple[bool, list[str]]:
    """Call extract.py against `sheet_pdf`, writing JSON to `sheet_json`.

    Probes `extract_page(pdf, page=1, profile=None) -> dict` first
    (preferred API), then `run(argv) -> int`, finally a subprocess.
    """
    warnings: list[str] = []
    fn = getattr(extract_mod, "extract_page", None)
    if callable(fn):
        try:
            result = fn(str(sheet_pdf), page=1, profile=profile)
            if isinstance(result, dict):
                _write_json(sheet_json, result)
                return True, _collect_warnings(result)
            warnings.append("extract_page returned non-dict")
        except Exception as exc:
            warnings.append(f"extract_page raised: {exc}")
            LOG.debug("extract_page:\n%s", traceback.format_exc())

    fn = getattr(extract_mod, "run", None)
    if callable(fn):
        argv = [str(sheet_pdf), "-o", str(sheet_json), "--page", "1"]
        try:
            rc = fn(argv)
            if rc == 0 and sheet_json.is_file():
                return True, _collect_warnings(_read_json(sheet_json))
            warnings.append(f"extract.run returned {rc!r}")
        except Exception as exc:
            warnings.append(f"extract.run raised: {exc}")

    import subprocess  # last resort
    env = os.environ.copy()
    if profile is not None:
        env["AILTIR_PROFILE_JSON"] = json.dumps(profile)
    cmd = [sys.executable, str(Path(extract_mod.__file__).resolve()),
           str(sheet_pdf), "-o", str(sheet_json), "--page", "1"]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True,
                            env=env, check=False)
        if cp.returncode == 0 and sheet_json.is_file():
            return True, _collect_warnings(_read_json(sheet_json))
        warnings.append(f"subprocess rc={cp.returncode}: {cp.stderr.strip()[:200]}")
    except OSError as exc:
        warnings.append(f"subprocess failed: {exc}")
    return False, warnings


def _collect_warnings(payload: dict[str, Any] | None) -> list[str]:
    if not isinstance(payload, dict):
        return []
    md = payload.get("ailtir_metadata")
    if isinstance(md, dict):
        warns = md.get("warnings")
        if isinstance(warns, list):
            return [str(w) for w in warns]
    return []


# --- per-page helpers -------------------------------------------------------


def _pad(page_count: int) -> int:
    return max(2, len(str(page_count)))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def split_one_page(src: "fitz.Document", page_index: int, dest: Path) -> None:
    """Emit a single-page PDF preserving vectors (PyMuPDF)."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = fitz.open()
    try:
        out.insert_pdf(src, from_page=page_index, to_page=page_index)
        out.save(str(dest), garbage=3, deflate=True)
    finally:
        out.close()


def render_png(page: "fitz.Page", dpi: int, dest: Path) -> None:
    """Render `page` to PNG at `dpi` (PyMuPDF Matrix(dpi/72, dpi/72))."""
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    dest.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(dest))


def summarise_page(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Roll up per-page extract JSON into manifest summary fields."""
    summary: dict[str, Any] = {
        "sheet_number": None, "sheet_title": None, "scale": None,
        "discipline": None, "tag_counts": {}, "shape_counts": {},
    }
    if not isinstance(payload, dict):
        return summary
    pi = payload.get("page_info")
    if isinstance(pi, dict):
        for k in ("sheet_number", "sheet_title", "scale", "discipline"):
            if pi.get(k) is not None:
                summary[k] = pi.get(k)
    if summary["scale"] is None:
        scale = payload.get("scale")
        if isinstance(scale, dict):
            summary["scale"] = scale.get("nominal") or scale.get("value")
    tags = payload.get("tags")
    if isinstance(tags, list):
        counts: dict[str, int] = {}
        for t in tags:
            if isinstance(t, dict):
                key = str(t.get("category") or t.get("kind") or t.get("type") or "other")
                counts[key] = counts.get(key, 0) + 1
        summary["tag_counts"] = counts
    geom = payload.get("geometry")
    if isinstance(geom, dict):
        shapes: dict[str, int] = {}
        for k, v in geom.items():
            if isinstance(v, list):
                shapes[k] = len(v)
            elif isinstance(v, int):
                shapes[k] = v
        summary["shape_counts"] = shapes
    return summary


# --- contact sheet ----------------------------------------------------------


def build_contact_sheet(pages: list[dict[str, Any]], output_dir: Path,
                        out_path: Path) -> bool:
    """Labelled thumbnail grid. Returns False (with stderr warning) if skipped."""
    if not _PIL_AVAILABLE:
        sys.stderr.write("warning: Pillow unavailable; skipping contact_sheet.jpg\n")
        return False

    entries: list[tuple[Path, str]] = []
    for p in pages:
        rel = p.get("sheet_png")
        if not rel:
            continue
        png = output_dir / rel
        if not png.is_file():
            continue
        label = p.get("sheet_number") or f"p{p['page']:02d}"
        entries.append((png, str(label)))
    if not entries:
        sys.stderr.write("warning: no PNGs; skipping contact_sheet.jpg\n")
        return False

    thumbs: list[tuple[Any, str]] = []
    max_w = max_h = 1
    try:
        for path, label in entries:
            with Image.open(path) as im:
                im = im.convert("RGB")
                # Spec: 25% of --dpi's pixel dimensions.
                im.thumbnail((max(1, im.width // 4), max(1, im.height // 4)))
                thumb = im.copy()
                thumbs.append((thumb, label))
                max_w = max(max_w, thumb.width)
                max_h = max(max_h, thumb.height)
    except Exception as exc:
        sys.stderr.write(f"warning: failed loading thumbnails: {exc}\n")
        return False

    gutter, label_band, target_w = 4, 28, 2000
    cols = max(1, min(len(thumbs), target_w // max(1, max_w + gutter)))
    rows = (len(thumbs) + cols - 1) // cols
    cell_w, cell_h = max_w + gutter, max_h + label_band + gutter
    sheet_w, sheet_h = cols * cell_w + gutter, rows * cell_h + gutter

    canvas = Image.new("RGB", (sheet_w, sheet_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    for idx, (thumb, label) in enumerate(thumbs):
        r, c = divmod(idx, cols)
        x, y = gutter + c * cell_w, gutter + r * cell_h
        canvas.paste(thumb, (x + (max_w - thumb.width) // 2,
                             y + (max_h - thumb.height) // 2))
        try:
            bbox = draw.textbbox((0, 0), label, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw = int(draw.textlength(label, font=font)) if font else len(label) * 6
            th = 12
        draw.text((x + (max_w - tw) // 2, y + max_h + (label_band - th) // 2),
                  label, fill=(0, 0, 0), font=font)

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(str(out_path), "JPEG", quality=CONTACT_SHEET_JPEG_QUALITY)
    except OSError as exc:
        sys.stderr.write(f"warning: cannot save contact sheet: {exc}\n")
        return False
    return True


# --- orchestration ----------------------------------------------------------


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(target: Path, base: Path) -> str:
    try:
        return target.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(target)


def _validate_paths(input_pdf: Path, output_dir: Path) -> None:
    if not input_pdf.is_file():
        sys.stderr.write(f"error: input PDF not found: {input_pdf}\n")
        sys.exit(2)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".ailtir_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        sys.stderr.write(f"error: output dir not writable: {exc}\n")
        sys.exit(3)


def orchestrate(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    input_pdf = Path(args.input_pdf).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    working_dir = output_dir / "_working"
    _validate_paths(input_pdf, output_dir)

    if not (72 <= args.dpi <= 600):
        sys.stderr.write(f"error: --dpi {args.dpi} out of range 72..600\n")
        return 4
    try:
        trade = resolve_trade(args.trade)
    except ValueError as exc:
        sys.stderr.write(f"error: --trade {exc}\n")
        return 4

    try:
        src = fitz.open(str(input_pdf))
    except Exception as exc:
        sys.stderr.write(f"error: cannot open PDF: {exc}\n")
        return 2

    try:
        page_count = src.page_count
        if page_count < 1:
            sys.stderr.write("error: PDF has no pages\n")
            return 2
        try:
            requested = parse_pages(args.pages, page_count)
        except ValueError as exc:
            sys.stderr.write(f"error: --pages {exc}\n")
            return 4

        pad = _pad(page_count)
        stem = input_pdf.stem
        working_dir.mkdir(parents=True, exist_ok=True)

        profile, profile_applied = (None, False)
        if args.profile:
            profile, profile_applied = load_profile(output_dir)

        try:
            extract_mod = import_extract_module()
        except Exception as exc:
            LOG.warning("cannot import extract.py: %s", exc)
            extract_mod = None

        pages_out: list[dict[str, Any]] = []
        produced = skipped_existing = failed = 0

        for page_num in requested:
            idx = page_num - 1
            tag = f"p{page_num:0{pad}d}"
            sheet_pdf = working_dir / f"{stem}_{tag}.pdf"
            sheet_png = working_dir / f"{stem}_{tag}.png"
            sheet_json = working_dir / f"{stem}_{tag}.json"

            LOG.info("page %d/%d %s", page_num, page_count, tag)
            status = "ok"
            warnings: list[str] = []
            payload: dict[str, Any] | None = None

            existing = None if args.overwrite else _read_json(sheet_json)
            if existing is not None:
                status, payload = "skipped_existing", existing
                skipped_existing += 1
            else:
                try:
                    split_one_page(src, idx, sheet_pdf)
                except Exception as exc:
                    LOG.error("split page %d: %s", page_num, exc)
                    status = "failed"
                    warnings.append(f"split failed: {exc}")
                    failed += 1

                if status != "failed" and not args.no_images:
                    try:
                        render_png(src.load_page(idx), args.dpi, sheet_png)
                    except Exception as exc:
                        LOG.warning("PNG page %d: %s", page_num, exc)
                        warnings.append(f"png render failed: {exc}")

                if status != "failed":
                    if extract_mod is None:
                        warnings.append("extract module unavailable")
                        status = "failed"
                        failed += 1
                    else:
                        ok, ewarn = run_extract(extract_mod, sheet_pdf,
                                                sheet_json, profile)
                        warnings.extend(ewarn)
                        payload = _read_json(sheet_json)
                        if not ok:
                            status = "failed"
                            failed += 1
                        else:
                            produced += 1
                            if ewarn:
                                status = "partial"

            summary = summarise_page(payload)
            entry: dict[str, Any] = {
                "page": page_num,
                "sheet_pdf": _rel(sheet_pdf, output_dir),
                "sheet_png": _rel(sheet_png, output_dir) if sheet_png.is_file() else None,
                "sheet_json": _rel(sheet_json, output_dir),
                **summary,
                "status": status,
            }
            if warnings:
                entry["warnings"] = warnings
            pages_out.append(entry)
    finally:
        src.close()

    manifest: dict[str, Any] = {
        "source_pdf": str(input_pdf),
        "output_dir": str(output_dir),
        "dpi": args.dpi,
        "trade": trade,
        "processed_at": _iso_now(),
        "page_count": page_count,
        "pages_requested": requested,
        "pages_produced": produced,
        "pages_skipped_existing": skipped_existing,
        "pages_failed": failed,
        "profile_applied": profile_applied,
        "pages": pages_out,
    }
    bid_ref = detect_bid_ref(output_dir)
    if bid_ref is not None:
        manifest["bid_ref"] = bid_ref  # only when detected; never write null.

    _write_json(output_dir / "manifest.json", manifest)
    LOG.info("wrote %s", output_dir / "manifest.json")

    build_contact_sheet(
        [p for p in pages_out if p.get("sheet_png")],
        output_dir, output_dir / "contact_sheet.jpg",
    )

    if requested and (produced + skipped_existing) == 0:
        return 5  # every requested page failed
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        return orchestrate(args)
    except SystemExit:
        raise
    except Exception:  # pragma: no cover
        traceback.print_exc()
        return 5


if __name__ == "__main__":
    sys.exit(main())
