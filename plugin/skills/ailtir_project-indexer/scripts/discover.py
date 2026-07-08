"""Project folder inventory for the Ailtir project-indexer workflow.

Walks a construction project directory tree and emits a deterministic JSON
manifest of every file, enriched with lightweight PDF metadata (page count,
media-box dimensions, ISO 216 page-size classification, and a text-layer
probe). Subsequent stages in the project-indexer workflow (``classify.py``,
``process_drawing.py``) consume this manifest instead of re-walking the
tree, so this script is intentionally cheap and side-effect-free.

Public sources referenced by this implementation:

* PyMuPDF documentation for ``fitz.Document``, ``Page.rect`` and
  ``Page.get_text`` -- https://pymupdf.readthedocs.io
* ISO 216 paper-size specification (A-series, US letter, US tabloid),
  values reproducible from any ISO 216 reference table.
* ``pathlib`` POSIX behaviour for cross-platform separators.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# PyMuPDF is an optional runtime dependency. If it is missing we still
# produce a valid manifest but every PDF record is stamped with an error
# marker so the classifier can degrade gracefully.
try:
    import fitz  # type: ignore
    _PYMUPDF_AVAILABLE = True
    _PYMUPDF_IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover - import failure is environmental
    fitz = None  # type: ignore
    _PYMUPDF_AVAILABLE = False
    _PYMUPDF_IMPORT_ERROR = str(exc)


# --- Constants ---------------------------------------------------------------

# Folders that must never be descended into during the walk.
SKIP_FOLDER_NAMES: frozenset[str] = frozenset({
    "__MACOSX",
    "0. AI Context",  # project-indexer's own output folder
})

# Office lock-file / temp-file prefix produced by Word/Excel/PowerPoint.
OFFICE_LOCK_PREFIX = "~$"

# Kind classification driven purely off the extension. This is coarse on
# purpose; deeper classification happens in ``classify.py``.
_KIND_BY_EXT: dict[str, str] = {
    "pdf": "pdf",
    "doc": "office_doc", "docx": "office_doc",
    "xls": "office_doc", "xlsx": "office_doc",
    "ppt": "office_doc", "pptx": "office_doc",
    "csv": "office_doc",
    "jpg": "image", "jpeg": "image",
    "png": "image",
    "tif": "image", "tiff": "image",
    "dwg": "cad", "dxf": "cad",
    "rvt": "cad", "ifc": "cad",
    "nwd": "cad", "nwc": "cad",
    "skp": "cad",
    "md": "text", "txt": "text", "rtf": "text",
}

# ISO 216 page-size detection -- see module docstring for reference.
# Dimensions are (long_axis_pt, short_axis_pt); 1 pt == 1/72".
_PAGE_SIZE_TABLE: tuple[tuple[str, float, float], ...] = (
    ("A0",      3370.0, 2384.0),
    ("A1",      2384.0, 1684.0),
    ("A2",      1684.0, 1191.0),
    ("A3",      1191.0, 842.0),
    ("A4",       842.0, 595.0),
    ("letter",   792.0, 612.0),
    ("tabloid", 1224.0, 792.0),
)
_PAGE_SIZE_TOLERANCE = 0.05  # +/- 5% match band

# Ailtir bid-folder naming convention: YYYY-NNN[N]-<description>.
_BID_FOLDER_RE = re.compile(r"^(\d{4}-\d{3,4})-.*")


# --- Data model --------------------------------------------------------------


@dataclass
class FileRecord:
    """One entry in the ``files`` array of the manifest."""

    path: str
    folder: str
    filename: str
    stem: str
    extension: str
    size_bytes: int
    modified: str
    kind: str
    pdf: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.pdf is None:
            payload.pop("pdf", None)
        return payload


@dataclass
class Manifest:
    """Top-level manifest written to disk (or printed in --dry-run)."""

    project_root: str
    generated_at: str
    bid_ref: str | None
    file_count: int = 0
    folder_count: int = 0
    pdf_count: int = 0
    top_level_folders: list[str] = field(default_factory=list)
    files: list[FileRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": self.project_root,
            "generated_at": self.generated_at,
            "bid_ref": self.bid_ref,
            "file_count": self.file_count,
            "folder_count": self.folder_count,
            "pdf_count": self.pdf_count,
            "top_level_folders": self.top_level_folders,
            "files": [f.to_dict() for f in self.files],
        }


# --- Small helpers -----------------------------------------------------------


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_from_mtime(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _is_hidden_name(name: str) -> bool:
    return name.startswith(".")


def _kind_for(extension: str) -> str:
    return _KIND_BY_EXT.get(extension, "other")


def _extract_bid_ref(root_name: str) -> str | None:
    # Ailtir differentiator: bid-folder-aware manifest.
    match = _BID_FOLDER_RE.match(root_name)
    return match.group(1) if match else None


def _classify_page_size(width_pt: float, height_pt: float) -> str:
    # ISO 216 page-size detection -- see module docstring for reference.
    long_axis = max(width_pt, height_pt)
    short_axis = min(width_pt, height_pt)
    for label, ref_long, ref_short in _PAGE_SIZE_TABLE:
        long_ok = abs(long_axis - ref_long) <= ref_long * _PAGE_SIZE_TOLERANCE
        short_ok = abs(short_axis - ref_short) <= ref_short * _PAGE_SIZE_TOLERANCE
        if long_ok and short_ok:
            return label
    return "other"


def _orientation(width_pt: float, height_pt: float) -> str:
    return "landscape" if width_pt >= height_pt else "portrait"


# --- PDF inspection ----------------------------------------------------------


def probe_pdf(pdf_path: Path) -> dict[str, Any]:
    """Return the lightweight PDF sub-record described in the spec.

    Never raises. When PyMuPDF is missing or the file cannot be opened,
    an ``error`` field is returned instead of measurements.
    """
    if not _PYMUPDF_AVAILABLE:
        return {"error": "pymupdf_unavailable"}

    try:
        doc = fitz.open(pdf_path)  # type: ignore[union-attr]
    except Exception as exc:
        return {"error": "unreadable", "detail": str(exc)}

    try:
        page_count = doc.page_count
        if page_count == 0:
            return {
                "page_count": 0,
                "first_page_width_pt": 0.0,
                "first_page_height_pt": 0.0,
                "first_page_orientation": "portrait",
                "page_size_class": "other",
                "has_text_layer": False,
                "char_count_first_page": 0,
            }

        first_page = doc.load_page(0)
        rect = first_page.rect
        width_pt = float(rect.width)
        height_pt = float(rect.height)

        # Text-layer probe: cheap on page 1, then sample subsequent pages
        # only if page 1 was empty. We deliberately stop as soon as any
        # extractable text is found -- the classifier only needs the flag.
        first_page_text = first_page.get_text() or ""
        char_count_first_page = len(first_page_text)
        has_text_layer = bool(first_page_text.strip())
        if not has_text_layer and page_count > 1:
            for idx in range(1, page_count):
                try:
                    sample = doc.load_page(idx).get_text() or ""
                except Exception:
                    continue
                if sample.strip():
                    has_text_layer = True
                    break

        return {
            "page_count": int(page_count),
            "first_page_width_pt": round(width_pt, 3),
            "first_page_height_pt": round(height_pt, 3),
            "first_page_orientation": _orientation(width_pt, height_pt),
            "page_size_class": _classify_page_size(width_pt, height_pt),
            "has_text_layer": has_text_layer,
            "char_count_first_page": char_count_first_page,
        }
    except Exception as exc:
        return {"error": "unreadable", "detail": str(exc)}
    finally:
        try:
            doc.close()
        except Exception:
            pass


# --- Filesystem walk ---------------------------------------------------------


def _should_skip_dir(name: str) -> bool:
    if _is_hidden_name(name):
        return True
    if name in SKIP_FOLDER_NAMES:
        return True
    return False


def _should_skip_file(name: str) -> bool:
    if _is_hidden_name(name):
        return True
    if name.startswith(OFFICE_LOCK_PREFIX):
        return True
    return False


def _iter_files(root: Path, log: list[str]) -> Iterable[Path]:
    """Yield file paths under ``root`` honouring the traversal rules."""
    # We use os.walk because it lets us prune ``dirs`` in place.
    root_resolved = root.resolve()
    for current_dir, dir_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current_dir)

        # Prune skipped subfolders (mutating ``dir_names`` in place).
        dir_names[:] = sorted(d for d in dir_names if not _should_skip_dir(d))

        for file_name in sorted(file_names):
            if _should_skip_file(file_name):
                continue
            candidate = current_path / file_name

            # Defensive: ignore symlinks pointing outside the tree.
            if candidate.is_symlink():
                try:
                    target = candidate.resolve()
                    root_str = str(root_resolved)
                    if not str(target).startswith(root_str):
                        log.append(f"skip symlink outside root: {candidate}")
                        continue
                except OSError as exc:
                    log.append(f"skip unresolved symlink {candidate}: {exc}")
                    continue

            yield candidate


def _top_level_folders(root: Path) -> list[str]:
    entries: list[str] = []
    try:
        for child in root.iterdir():
            if child.is_dir() and not _should_skip_dir(child.name):
                entries.append(child.name)
    except OSError:
        return []
    return sorted(entries)


def _count_folders(root: Path) -> int:
    total = 0
    for _current, dir_names, _files in os.walk(root, followlinks=False):
        dir_names[:] = [d for d in dir_names if not _should_skip_dir(d)]
        total += len(dir_names)
    return total


# --- Manifest build ----------------------------------------------------------


def build_manifest(project_root: Path) -> tuple[Manifest, list[str]]:
    """Assemble the manifest for ``project_root``.

    Returns the manifest plus a list of informational log lines (used for
    the ``--dry-run`` summary and stderr diagnostics).
    """
    log: list[str] = []
    root_resolved = project_root.resolve()

    manifest = Manifest(
        project_root=str(root_resolved),
        generated_at=_iso_now(),
        bid_ref=_extract_bid_ref(root_resolved.name),
        top_level_folders=_top_level_folders(root_resolved),
        folder_count=_count_folders(root_resolved),
    )

    for file_path in _iter_files(root_resolved, log):
        try:
            stat = file_path.stat()
        except OSError as exc:
            log.append(f"skip unstat-able file {file_path}: {exc}")
            continue

        rel_path = file_path.relative_to(root_resolved)
        rel_posix = rel_path.as_posix()
        parent_posix = rel_path.parent.as_posix() if rel_path.parent != Path(".") else ""
        extension = file_path.suffix.lstrip(".").lower()
        kind = _kind_for(extension)

        record = FileRecord(
            path=rel_posix,
            folder=parent_posix,
            filename=file_path.name,
            stem=file_path.stem,
            extension=extension,
            size_bytes=int(stat.st_size),
            modified=_iso_from_mtime(stat.st_mtime),
            kind=kind,
        )

        if kind == "pdf":
            record.pdf = probe_pdf(file_path)
            manifest.pdf_count += 1

        manifest.files.append(record)

    # Ailtir differentiator: deterministic sort by relative path. Two runs
    # over an unchanged tree produce identical JSON (aside from
    # ``generated_at``), so downstream tests can hash the output.
    manifest.files.sort(key=lambda r: r.path)
    manifest.file_count = len(manifest.files)

    return manifest, log


# --- I/O ---------------------------------------------------------------------


def _write_json(manifest: Manifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest.to_dict(), fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _print_dry_run_summary(manifest: Manifest) -> None:
    counts: Counter[str] = Counter(record.kind for record in manifest.files)
    print(f"project_root:      {manifest.project_root}")
    print(f"bid_ref:           {manifest.bid_ref or '(none)'}")
    print(f"generated_at:      {manifest.generated_at}")
    print(f"top_level_folders: {len(manifest.top_level_folders)}")
    print(f"folder_count:      {manifest.folder_count}")
    print(f"file_count:        {manifest.file_count}")
    print(f"pdf_count:         {manifest.pdf_count}")
    print("kinds:")
    for kind in ("pdf", "office_doc", "image", "cad", "text", "other"):
        print(f"  {kind:11s} {counts.get(kind, 0)}")


# --- Entry point -------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="discover.py",
        description=(
            "Walk a construction project folder tree and write a JSON "
            "inventory used by the ailtir project-indexer workflow."
        ),
    )
    parser.add_argument(
        "project_root",
        type=Path,
        help="Path to the project folder to inventory.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        required=False,
        help="Destination JSON path (required unless --dry-run is set).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Walk the tree and print file counts by kind to stdout. "
            "Does not open the destination JSON for writing."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    project_root: Path = args.project_root
    if not project_root.exists() or not project_root.is_dir():
        print(
            f"error: project_root is not an accessible directory: {project_root}",
            file=sys.stderr,
        )
        return 2
    if not os.access(project_root, os.R_OK):
        print(
            f"error: project_root is not readable: {project_root}",
            file=sys.stderr,
        )
        return 2

    if not args.dry_run:
        if args.output is None:
            print("error: -o/--output is required unless --dry-run is set.", file=sys.stderr)
            return 2
        output_parent = args.output.parent if str(args.output.parent) else Path(".")
        try:
            output_parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(
                f"error: cannot create output parent {output_parent}: {exc}",
                file=sys.stderr,
            )
            return 3
        if not os.access(output_parent, os.W_OK):
            print(
                f"error: output parent is not writable: {output_parent}",
                file=sys.stderr,
            )
            return 3

    if not _PYMUPDF_AVAILABLE:
        print(
            "warning: PyMuPDF (fitz) not importable; PDF stats will be "
            f"marked pymupdf_unavailable. import error: {_PYMUPDF_IMPORT_ERROR}",
            file=sys.stderr,
        )

    manifest, log_lines = build_manifest(project_root)

    for line in log_lines:
        print(f"note: {line}", file=sys.stderr)

    if args.dry_run:
        _print_dry_run_summary(manifest)
        return 0

    try:
        _write_json(manifest, args.output)
    except OSError as exc:
        print(f"error: failed writing manifest: {exc}", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
