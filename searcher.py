"""
Nueva Compare Tool - Text Search Engine
Recursive full-text search across a folder with regex support.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from utils.logger import get_logger, log_exception

logger = get_logger("nueva_compare.searcher")


@dataclass
class SearchMatch:
    file_path: Path
    relative_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    folder: Path
    query: str
    use_regex: bool
    case_sensitive: bool
    matches: List[SearchMatch] = field(default_factory=list)
    files_searched: int = 0
    files_with_matches: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def total_matches(self) -> int:
        return len(self.matches)


def _read_file_lines(path: Path) -> Optional[List[str]]:
    """Try to read file as text lines."""
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
    return None


def _is_binary(path: Path, sample: int = 8192) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(sample)
    except Exception:
        return True


def search_in_folder(
    folder: str,
    query: str,
    use_regex: bool = False,
    case_sensitive: bool = False,
    file_extensions: Optional[List[str]] = None,
    context_lines: int = 2,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    max_matches: int = 5000,
) -> SearchResult:
    """
    Search for `query` recursively in `folder`.
    Returns a SearchResult with all matches.
    """
    root = Path(folder).resolve()
    logger.info(
        "Search start — folder='%s' query='%s' regex=%s case=%s",
        root, query, use_regex, case_sensitive,
    )

    result = SearchResult(
        folder=root, query=query, use_regex=use_regex, case_sensitive=case_sensitive
    )

    if not root.is_dir():
        result.errors.append(f"Folder not found: {root}")
        logger.error("Folder not found: %s", root)
        return result

    if not query:
        result.errors.append("Query is empty.")
        return result

    # Compile pattern
    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        if use_regex:
            pattern = re.compile(query, flags)
        else:
            pattern = re.compile(re.escape(query), flags)
    except re.error as exc:
        msg = f"Invalid regex: {exc}"
        result.errors.append(msg)
        logger.error(msg)
        return result

    # Collect files
    all_files: List[Path] = []
    try:
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                fp = Path(dirpath) / fname
                if file_extensions:
                    if fp.suffix.lower() not in [e.lower() for e in file_extensions]:
                        continue
                all_files.append(fp)
    except Exception as exc:
        log_exception(logger, exc, "Walking folder for search")

    total = len(all_files)
    logger.info("Files to search: %d", total)

    files_with_matches: set = set()

    for idx, fp in enumerate(all_files):
        if result.total_matches >= max_matches:
            logger.warning("Max matches (%d) reached, stopping early.", max_matches)
            break

        if progress_callback:
            try:
                progress_callback(idx + 1, total, str(fp))
            except Exception:
                pass

        if _is_binary(fp):
            logger.debug("Skipping binary: %s", fp)
            continue

        lines = _read_file_lines(fp)
        if lines is None:
            logger.debug("Could not read: %s", fp)
            continue

        result.files_searched += 1
        stripped = [l.rstrip("\r\n") for l in lines]

        for li, line in enumerate(stripped):
            for m in pattern.finditer(line):
                try:
                    rel = fp.relative_to(root).as_posix()
                except ValueError:
                    rel = str(fp)

                ctx_before = stripped[max(0, li - context_lines): li]
                ctx_after = stripped[li + 1: li + 1 + context_lines]

                match = SearchMatch(
                    file_path=fp,
                    relative_path=rel,
                    line_number=li + 1,
                    line_content=line,
                    match_start=m.start(),
                    match_end=m.end(),
                    context_before=ctx_before,
                    context_after=ctx_after,
                )
                result.matches.append(match)
                files_with_matches.add(str(fp))

                if result.total_matches >= max_matches:
                    break
            if result.total_matches >= max_matches:
                break

    result.files_with_matches = len(files_with_matches)
    logger.info(
        "Search complete — files_searched=%d, files_with_matches=%d, total_matches=%d",
        result.files_searched, result.files_with_matches, result.total_matches,
    )
    return result
