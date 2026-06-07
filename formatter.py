"""
Nueva Compare Tool - Code Formatter
Formats code/text according to file extension / language.
"""

import json
import re
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from utils.logger import get_logger, log_exception

logger = get_logger("nueva_compare.formatter")


class Language(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    HTML = "html"
    CSS = "css"
    XML = "xml"
    SQL = "sql"
    YAML = "yaml"
    MARKDOWN = "markdown"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    RUBY = "ruby"
    PHP = "php"
    BASH = "bash"
    UNKNOWN = "unknown"


EXT_TO_LANG = {
    ".py": Language.PYTHON,
    ".pyw": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".json": Language.JSON,
    ".html": Language.HTML,
    ".htm": Language.HTML,
    ".css": Language.CSS,
    ".scss": Language.CSS,
    ".less": Language.CSS,
    ".xml": Language.XML,
    ".svg": Language.XML,
    ".sql": Language.SQL,
    ".yaml": Language.YAML,
    ".yml": Language.YAML,
    ".md": Language.MARKDOWN,
    ".markdown": Language.MARKDOWN,
    ".java": Language.JAVA,
    ".c": Language.C,
    ".h": Language.C,
    ".cpp": Language.CPP,
    ".cc": Language.CPP,
    ".cxx": Language.CPP,
    ".hpp": Language.CPP,
    ".cs": Language.CSHARP,
    ".go": Language.GO,
    ".rs": Language.RUST,
    ".rb": Language.RUBY,
    ".php": Language.PHP,
    ".sh": Language.BASH,
    ".bash": Language.BASH,
    ".zsh": Language.BASH,
}


def detect_language(file_path: str) -> Language:
    ext = Path(file_path).suffix.lower()
    return EXT_TO_LANG.get(ext, Language.UNKNOWN)


def _tool_available(tool: str) -> bool:
    try:
        subprocess.run(
            [tool, "--version"],
            capture_output=True, timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_formatter(cmd: list, code: str, timeout: int = 30) -> Tuple[str, Optional[str]]:
    """Run external formatter. Returns (formatted_code, error_or_None)."""
    try:
        proc = subprocess.run(
            cmd,
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode == 0:
            return proc.stdout, None
        return code, proc.stderr or "Formatter returned non-zero exit code"
    except subprocess.TimeoutExpired:
        return code, "Formatter timed out"
    except FileNotFoundError:
        return code, f"Formatter not found: {cmd[0]}"
    except Exception as exc:
        return code, str(exc)


# ── Language-specific formatters ──────────────────────────────────────────────

def _format_python(code: str) -> Tuple[str, str]:
    """Try black, fall back to autopep8, fall back to built-in indent fixer."""
    # Try black
    try:
        import black
        mode = black.Mode()
        formatted = black.format_str(code, mode=mode)
        return formatted, "Formatted with black"
    except ImportError:
        pass
    except Exception as exc:
        logger.debug("black failed: %s", exc)

    # Try autopep8
    try:
        import autopep8
        formatted = autopep8.fix_code(code, options={"aggressive": 1})
        return formatted, "Formatted with autopep8"
    except ImportError:
        pass
    except Exception as exc:
        logger.debug("autopep8 failed: %s", exc)

    return code, "No Python formatter available (install black or autopep8)"


def _format_json(code: str) -> Tuple[str, str]:
    try:
        parsed = json.loads(code)
        return json.dumps(parsed, indent=2, ensure_ascii=False) + "\n", "Formatted with json.dumps"
    except json.JSONDecodeError as exc:
        return code, f"Invalid JSON: {exc}"


def _format_xml(code: str) -> Tuple[str, str]:
    try:
        import xml.dom.minidom as minidom
        dom = minidom.parseString(code.encode("utf-8"))
        pretty = dom.toprettyxml(indent="  ", encoding=None)
        # Remove the auto-added XML declaration if not in original
        if not code.strip().startswith("<?xml"):
            pretty = "\n".join(pretty.split("\n")[1:])
        return pretty.strip() + "\n", "Formatted with xml.dom.minidom"
    except Exception as exc:
        return code, f"XML parse error: {exc}"


def _format_yaml(code: str) -> Tuple[str, str]:
    try:
        import yaml
        data = yaml.safe_load(code)
        return yaml.dump(data, default_flow_style=False, allow_unicode=True), "Formatted with PyYAML"
    except ImportError:
        return code, "PyYAML not installed"
    except Exception as exc:
        return code, f"YAML parse error: {exc}"


def _format_sql(code: str) -> Tuple[str, str]:
    try:
        import sqlparse
        formatted = sqlparse.format(
            code, reindent=True, keyword_case="upper", identifier_case="lower"
        )
        return formatted, "Formatted with sqlparse"
    except ImportError:
        # Basic keyword uppercasing fallback
        keywords = [
            "select", "from", "where", "join", "left", "right", "inner",
            "outer", "on", "and", "or", "not", "in", "is", "null",
            "order", "by", "group", "having", "limit", "offset",
            "insert", "into", "values", "update", "set", "delete",
            "create", "table", "drop", "alter", "index",
        ]
        result = code
        for kw in keywords:
            result = re.sub(rf"\b{kw}\b", kw.upper(), result, flags=re.IGNORECASE)
        return result, "Basic SQL keyword formatting (install sqlparse for full support)"
    except Exception as exc:
        return code, f"SQL format error: {exc}"


def _format_js_ts(code: str, lang: Language) -> Tuple[str, str]:
    """Try prettier via CLI."""
    parser = "babel" if lang == Language.JAVASCRIPT else "typescript"
    formatted, err = _run_formatter(
        ["npx", "prettier", "--parser", parser, "--stdin-filepath", "file.js"],
        code,
    )
    if err:
        # Fallback: basic indent normalisation
        return code, f"prettier not available: {err}"
    return formatted, "Formatted with prettier"


def _format_html(code: str) -> Tuple[str, str]:
    formatted, err = _run_formatter(
        ["npx", "prettier", "--parser", "html", "--stdin-filepath", "file.html"],
        code,
    )
    if err:
        return code, f"prettier not available: {err}"
    return formatted, "Formatted with prettier"


def _format_css(code: str) -> Tuple[str, str]:
    formatted, err = _run_formatter(
        ["npx", "prettier", "--parser", "css", "--stdin-filepath", "file.css"],
        code,
    )
    if err:
        return code, f"prettier not available: {err}"
    return formatted, "Formatted with prettier"


def _format_markdown(code: str) -> Tuple[str, str]:
    """Basic markdown normalisation."""
    lines = code.splitlines()
    cleaned = []
    blank_count = 0
    for line in lines:
        stripped = line.rstrip()
        if stripped == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(stripped)
    return "\n".join(cleaned) + "\n", "Basic Markdown normalisation"


# ── Public API ────────────────────────────────────────────────────────────────

def format_code(code: str, file_path: str = "", language: Optional[Language] = None) -> Tuple[str, str, Language]:
    """
    Format `code` for the given file path or explicit language.
    Returns (formatted_code, message, detected_language).
    """
    if language is None:
        language = detect_language(file_path) if file_path else Language.UNKNOWN

    logger.info("Formatting — language=%s, file=%s, len=%d", language.value, file_path, len(code))

    try:
        if language == Language.PYTHON:
            result, msg = _format_python(code)
        elif language == Language.JSON:
            result, msg = _format_json(code)
        elif language == Language.XML:
            result, msg = _format_xml(code)
        elif language == Language.YAML:
            result, msg = _format_yaml(code)
        elif language == Language.SQL:
            result, msg = _format_sql(code)
        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT):
            result, msg = _format_js_ts(code, language)
        elif language == Language.HTML:
            result, msg = _format_html(code)
        elif language == Language.CSS:
            result, msg = _format_css(code)
        elif language == Language.MARKDOWN:
            result, msg = _format_markdown(code)
        else:
            result, msg = code, f"No formatter for language: {language.value}"
    except Exception as exc:
        msg = log_exception(logger, exc, f"Formatting {language.value}")
        result = code

    logger.info("Format result: %s", msg)
    return result, msg, language


def format_file(file_path: str) -> Tuple[str, str, Language]:
    """Read, format and return (formatted_code, message, language). Does NOT write back."""
    path = Path(file_path)
    try:
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                code = path.read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            return "", "Could not decode file", Language.UNKNOWN
    except Exception as exc:
        return "", str(exc), Language.UNKNOWN

    return format_code(code, file_path)
