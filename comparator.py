"""
Nueva Compare Tool - Core Comparison Engine
Handles folder/file diffing across Windows and Unix filesystems.
"""

import difflib
import filecmp
import hashlib
import os
import stat
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

from utils.logger import get_logger, log_exception

logger = get_logger("nueva_compare.comparator")


class DiffStatus(Enum):
    IDENTICAL = "identical"
    MODIFIED = "modified"
    LEFT_ONLY = "left_only"
    RIGHT_ONLY = "right_only"
    BINARY_DIFFER = "binary_differ"
    ERROR = "error"


@dataclass
class LineDiff:
    line_number_left: Optional[int]
    line_number_right: Optional[int]
    tag: str          # 'equal', 'replace', 'insert', 'delete'
    left_line: str
    right_line: str


@dataclass
class FileDiffResult:
    relative_path: str
    status: DiffStatus = DiffStatus.ERROR
    left_path: Optional[Path] = None
    right_path: Optional[Path] = None
    line_diffs: List[LineDiff] = field(default_factory=list)
    error_message: str = ""
    left_size: int = 0
    right_size: int = 0
    left_hash: str = ""
    right_hash: str = ""

    @property
    def changed_lines_count(self) -> int:
        return sum(1 for d in self.line_diffs if d.tag != "equal")

    @property
    def is_binary(self) -> bool:
        return self.status == DiffStatus.BINARY_DIFFER


@dataclass
class FolderCompareResult:
    left_folder: Path
    right_folder: Path
    results: List[FileDiffResult] = field(default_factory=list)
    total_files_scanned: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def identical(self) -> List[FileDiffResult]:
        return [r for r in self.results if r.status == DiffStatus.IDENTICAL]

    @property
    def modified(self) -> List[FileDiffResult]:
        return [r for r in self.results if r.status == DiffStatus.MODIFIED]

    @property
    def left_only(self) -> List[FileDiffResult]:
        return [r for r in self.results if r.status == DiffStatus.LEFT_ONLY]

    @property
    def right_only(self) -> List[FileDiffResult]:
        return [r for r in self.results if r.status == DiffStatus.RIGHT_ONLY]

    @property
    def binary_differ(self) -> List[FileDiffResult]:
        return [r for r in self.results if r.status == DiffStatus.BINARY_DIFFER]

    @property
    def errors_list(self) -> List[FileDiffResult]:
        return [r for r in self.results if r.status == DiffStatus.ERROR]


def _normalise_path(p: Path) -> Path:
    """Resolve and normalise path for cross-platform compat."""
    try:
        return p.resolve()
    except Exception:
        return p.absolute()


def _file_hash(path: Path, chunk: int = 65536) -> str:
    """SHA-256 hash of a file. Returns empty string on error."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                data = f.read(chunk)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()
    except Exception as exc:
        log_exception(logger, exc, f"Hashing {path}")
        return ""


def _is_binary(path: Path, sample: int = 8192) -> bool:
    """Heuristic binary-file detection."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(sample)
        return b"\x00" in chunk
    except Exception:
        return False


def _read_text(path: Path) -> Tuple[Optional[List[str]], Optional[str]]:
    """Try to read a file as text with multiple encodings."""
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.readlines(), None
        except UnicodeDecodeError:
            continue
        except Exception as exc:
            return None, str(exc)
    return None, "Could not decode file with any supported encoding"


def _diff_text_files(left: Path, right: Path, context_lines: int = 3) -> List[LineDiff]:
    """Generate a structured line-level diff between two text files."""
    left_lines, err_l = _read_text(left)
    right_lines, err_r = _read_text(right)

    if err_l or err_r:
        raise ValueError(f"Read error — left: {err_l}, right: {err_r}")

    left_lines = left_lines or []
    right_lines = right_lines or []

    left_norm = [l.rstrip("\r\n") for l in left_lines]
    right_norm = [r.rstrip("\r\n") for r in right_lines]

    matcher = difflib.SequenceMatcher(None, left_norm, right_norm, autojunk=False)
    diffs: List[LineDiff] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                diffs.append(LineDiff(
                    line_number_left=i1 + offset + 1,
                    line_number_right=j1 + offset + 1,
                    tag="equal",
                    left_line=left_norm[i1 + offset],
                    right_line=right_norm[j1 + offset],
                ))
        elif tag == "replace":
            left_block = left_norm[i1:i2]
            right_block = right_norm[j1:j2]
            max_len = max(len(left_block), len(right_block))
            for offset in range(max_len):
                ll = left_block[offset] if offset < len(left_block) else ""
                rl = right_block[offset] if offset < len(right_block) else ""
                ln = (i1 + offset + 1) if offset < len(left_block) else None
                rn = (j1 + offset + 1) if offset < len(right_block) else None
                diffs.append(LineDiff(
                    line_number_left=ln, line_number_right=rn,
                    tag="replace", left_line=ll, right_line=rl,
                ))
        elif tag == "delete":
            for offset in range(i2 - i1):
                diffs.append(LineDiff(
                    line_number_left=i1 + offset + 1, line_number_right=None,
                    tag="delete", left_line=left_norm[i1 + offset], right_line="",
                ))
        elif tag == "insert":
            for offset in range(j2 - j1):
                diffs.append(LineDiff(
                    line_number_left=None, line_number_right=j1 + offset + 1,
                    tag="insert", left_line="", right_line=right_norm[j1 + offset],
                ))

    return diffs


def _collect_relative_paths(folder: Path) -> Dict[str, Path]:
    paths: Dict[str, Path] = {}
    try:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                abs_path = Path(root) / fname
                try:
                    rel = abs_path.relative_to(folder)
                    paths[rel.as_posix()] = abs_path
                except ValueError:
                    pass
    except PermissionError as exc:
        log_exception(logger, exc, f"Walking {folder}")
    return paths


def compare_folders(
    left_folder: str,
    right_folder: str,
    progress_callback=None,
    ignore_patterns: Optional[List[str]] = None,
) -> FolderCompareResult:
    left = _normalise_path(Path(left_folder))
    right = _normalise_path(Path(right_folder))

    result = FolderCompareResult(left_folder=left, right_folder=right)

    if not left.is_dir() or not right.is_dir():
        return result

    left_paths = _collect_relative_paths(left)
    right_paths = _collect_relative_paths(right)

    all_keys = sorted(set(left_paths) | set(right_paths))
    total = len(all_keys)
    result.total_files_scanned = total

    ignore_patterns = ignore_patterns or []

    for idx, rel_key in enumerate(all_keys):
        if any(pat in rel_key for pat in ignore_patterns):
            continue

        if progress_callback:
            try: progress_callback(idx + 1, total, rel_key)
            except: pass

        in_left = rel_key in left_paths
        in_right = rel_key in right_paths

        diff_result = FileDiffResult(relative_path=rel_key)

        try:
            if in_left and not in_right:
                diff_result.status = DiffStatus.LEFT_ONLY
                diff_result.left_path = left_paths[rel_key]
                diff_result.left_size = left_paths[rel_key].stat().st_size
            elif in_right and not in_left:
                diff_result.status = DiffStatus.RIGHT_ONLY
                diff_result.right_path = right_paths[rel_key]
                diff_result.right_size = right_paths[rel_key].stat().st_size
            else:
                lp = left_paths[rel_key]
                rp = right_paths[rel_key]
                diff_result.left_path = lp
                diff_result.right_path = rp
                diff_result.left_size = lp.stat().st_size
                diff_result.right_size = rp.stat().st_size

                lh = _file_hash(lp)
                rh = _file_hash(rp)
                diff_result.left_hash = lh
                diff_result.right_hash = rh

                if lh == rh:
                    diff_result.status = DiffStatus.IDENTICAL
                else:
                    if _is_binary(lp) or _is_binary(rp):
                        diff_result.status = DiffStatus.BINARY_DIFFER
                    else:
                        diff_result.line_diffs = _diff_text_files(lp, rp)
                        diff_result.status = DiffStatus.MODIFIED
        except Exception as exc:
            msg = log_exception(logger, exc, f"Comparing {rel_key}")
            diff_result.status = DiffStatus.ERROR
            diff_result.error_message = msg

        result.results.append(diff_result)

    return result