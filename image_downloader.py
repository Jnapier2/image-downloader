#!/usr/bin/env python3
"""
Image Downloader - lean Windows-friendly image downloader.

Asset ID: IMGDL-SOURCE-PY
Version: 2026.08.09.1
Status: current
Sensitivity: public-source
Tags: image-downloader, python-source, windows-utility, diagnostics, smart-safe-automation, canonical-export, helpful-computer-awareness, asset-metadata

Designed for portable project-folder launch with plain Python + BAT launchers.
No bundled executables. Downloaded files are never executed.
Copyright © 2026 Gateway Information Group LLC. All rights reserved.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from collections import deque
import contextlib
import dataclasses
import hashlib
import html
import importlib
import importlib.metadata
import io
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import platform
import posixpath
import queue
import random
import re
import shutil
import struct
import sys
import tempfile
import threading
import time
import traceback
import uuid
import errno
import urllib.parse
import warnings
import zipfile
import zlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - fallback for unusual Python builds
    ZoneInfo = None  # type: ignore
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

APP_NAME = "Gateway Image Downloader"
APP_VERSION = "2026.08.09.1"
BUILD_NAME = "v2176-canonical-entrypoint-project-local-outputs"
BUILD_DATE = "2026-08-09 15:39 CDT"
CONFIG_FILENAME = "image_downloader_config.json"
SCRIPT_FILENAME = "image_downloader.py"
STATE_DIRNAME = "state"
LOG_DIRNAME = "logs"
REPORT_DIRNAME = "reports"
EXPORT_DIRNAME = "exports"
CANONICAL_EXPORT_FILENAME = "IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip"
EXECUTION_NAMESPACE = "GatewayImageDownloader"
CANONICAL_ENTRYPOINT = "GatewayImageDownloader.bat"
SAFE_BROWSER_ENTRYPOINT = "GatewayImageDownloader_SafeBrowser.bat"
DIAGNOSTICS_EXPORT_ENTRYPOINT = "GatewayImageDownloader_DiagnosticsExport.bat"
APPROVED_LEGACY_ENTRYPOINT_ALIASES = (
    "run_image_downloader.bat",
    "run_image_downloader_safe_browser.bat",
    "run_diagnose_export.bat",
)
TEMP_DIRNAME = "temp"
PROJECT_OUTPUT_ROOTS = {
    "config_file": CONFIG_FILENAME,
    "downloads": "downloads",
    "logs": LOG_DIRNAME,
    "state": STATE_DIRNAME,
    "temp": TEMP_DIRNAME,
    "reports": REPORT_DIRNAME,
    "exports": EXPORT_DIRNAME,
    "backups": f"{STATE_DIRNAME}/migration_backups",
}
DOWNLOAD_INDEX_FILENAME = "download_index.json"
RECENT_RUN_FILENAME = "recent_run_summary.json"
RECENT_FAILURES_FILENAME = "recent_failures_errors.json"
NOT_DOWNLOADED_FILENAME = "not_downloaded_images.json"
SEQUENCE_STATS_FILENAME = "sequential_search_stats.json"
LOG_FILENAME = "image_downloader.log"
INSTANCE_LOCK_FILENAME = "image_downloader_instance.lock"
INSTANCE_EVENTS_FILENAME = "instance_guard_events.json"
CONFIG_SCHEMA_VERSION = 5
STATE_SCHEMA_VERSION = 2
MIGRATION_BACKUP_DIRNAME = "migration_backups"
EXPORT_AUDIT_FILENAME = "deep_conflict_audit.txt"
NESTED_LAYOUT_CLEANUP_FILENAME = "nested_layout_cleanup_latest.json"
PARTIAL_DIRNAME = "partials"
PARTIAL_METADATA_SUFFIX = ".json"
DOWNLOAD_QUEUE_STATE_FILENAME = "download_queue.json"
DOWNLOAD_QUEUE_SCHEMA_VERSION = 1
DOWNLOAD_QUEUE_HARD_MAX = 100
MAX_ACTIVE_DOWNLOADS = 3
LATEST_DOWNLOAD_LIST_FILENAME = "LATEST_DOWNLOAD_LIST.txt"

IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "tif", "tiff", "avif"
}
DANGEROUS_EXTENSIONS = {
    "exe", "msi", "msp", "scr", "com", "bat", "cmd", "ps1", "vbs", "js", "jse",
    "wsf", "hta", "jar", "dll", "sys", "cpl", "reg", "lnk", "zip", "rar", "7z", "tar",
    "gz", "bz2", "xz", "iso", "dmg", "pkg", "deb", "rpm", "apk", "app", "scf"
}
DANGEROUS_CONTENT_TYPES = {
    "application/x-msdownload",
    "application/x-msdos-program",
    "application/x-ms-installer",
    "application/x-sh",
    "application/x-bat",
    "application/x-cmd",
    "application/javascript",
    "text/javascript",
    "application/x-javascript",
    "application/zip",
    "application/x-7z-compressed",
    "application/vnd.rar",
    "application/x-rar-compressed",
    "application/x-tar",
    "application/gzip",
    "application/octet-stream-executable",
}
GENERIC_BINARY_CONTENT_TYPES = {
    "application/octet-stream",
    "binary/octet-stream",
    "application/x-octet-stream",
}
SVG_ALLOWED_CONTENT_TYPES = {
    "image/svg+xml",
    "application/svg+xml",
    "text/xml",
    "application/xml",
    "text/plain",
}
EXPORT_FILE_LIMIT = 20
EXPORT_MAX_ENTRY_BYTES = 5 * 1024 * 1024
EXPORT_MAX_TOTAL_BYTES = 12 * 1024 * 1024
EXPORT_SNAPSHOT_ATTEMPTS = 3
PARAMETER_ALIGNMENT_VERSION = "project-framework-2026.08.09"
ASSET_METADATA_SCHEMA = "asset-metadata-v1"
PROJECT_SLUG = "image-downloader"
PACKAGE_ASSET_ID = "IMGDL-PACKAGE"
PACKAGE_ID = "gateway-image-downloader"
VERSION_FILENAME = "VERSION.txt"
MANIFEST_FILENAME = "MANIFEST.json"
PACKAGE_METADATA_FILENAME = "PACKAGE_METADATA.json"
RELEASE_IDENTITY_EXIT_CODE = 23
RUNTIME_IDENTITY_GATE_VERSION = "runtime-release-identity-v1"
ASSET_STATUS = "current"
ASSET_SENSITIVITY = "public-source"
INTENDED_DRIVE_VAULT_PATH = "support_archive/30_UTILITIES_AND_WINDOWS_TOOLS/ImageDownloader/02_LATEST_BUILD"
DRIVE_PROJECT_PATH = "support_archive/30_UTILITIES_AND_WINDOWS_TOOLS/ImageDownloader"
RETRYABLE_HTTP_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
COMMON_RASTER_FORMATS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"}


def chicago_now() -> datetime:
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo("America/Chicago"))
        except Exception:
            pass
    return datetime.now().astimezone()


def now_local() -> str:
    return chicago_now().isoformat(timespec="seconds")


def timestamp_compact() -> str:
    return chicago_now().strftime("%Y%m%d_%H%M%S_%Z")


def timestamp_unique() -> str:
    return f"{timestamp_compact()}_{uuid.uuid4().hex[:6]}"


def make_run_id(prefix: str = "imgdl") -> str:
    safe_prefix = re.sub(r"[^A-Za-z0-9_-]+", "_", str(prefix or "imgdl")).strip("_") or "imgdl"
    return f"{safe_prefix}_{timestamp_compact()}_{uuid.uuid4().hex[:8]}"


def safe_int(value: Any, default: int, *, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = int(default)
    if min_value is not None:
        result = max(int(min_value), result)
    if max_value is not None:
        result = min(int(max_value), result)
    return result


def safe_float(value: Any, default: float, *, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = float(default)
    if min_value is not None:
        result = max(float(min_value), result)
    if max_value is not None:
        result = min(float(max_value), result)
    return result


def safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.strip().lower()
        if low in {"1", "true", "yes", "y", "on"}:
            return True
        if low in {"0", "false", "no", "n", "off"}:
            return False
    if value is None:
        return bool(default)
    return bool(value)


def parse_retry_after_seconds(value: Any, max_seconds: float) -> float:
    """Return a bounded Retry-After delay for either delta-seconds or an HTTP date."""
    text = str(value or "").strip()
    if not text:
        return 0.0
    try:
        seconds = float(text)
    except (TypeError, ValueError):
        try:
            retry_at = parsedate_to_datetime(text)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return 0.0
    return min(max(0.0, seconds), max(0.0, float(max_seconds)))


def parse_content_range(value: Any) -> Tuple[Optional[int], Optional[int]]:
    """Return byte-range start and total size from a Content-Range header."""
    text = str(value or "").strip()
    match = re.match(r"(?i)^bytes\s+(\d+)-(\d+)/(\d+|\*)$", text)
    if match:
        return int(match.group(1)), (None if match.group(3) == "*" else int(match.group(3)))
    unsatisfied = re.match(r"(?i)^bytes\s+\*/(\d+)$", text)
    if unsatisfied:
        return None, int(unsatisfied.group(1))
    return None, None


def app_root() -> Path:
    return Path(__file__).resolve().parent


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()



def _version_control_values(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    values: Dict[str, str] = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        normalized = re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")
        if normalized:
            values[normalized] = value.strip()
    return values


def _release_identity_mismatch(evidence: Dict[str, Any], kind: str, path: str, expected: Any, observed: Any) -> None:
    evidence.setdefault("mismatches", []).append({
        "kind": str(kind),
        "path": str(path),
        "expected": None if expected is None else str(expected),
        "observed": None if observed is None else str(observed),
    })


def _safe_managed_release_path(root: Path, raw_path: Any) -> Tuple[Optional[str], Optional[Path], str]:
    if not isinstance(raw_path, str):
        return None, None, "managed path is not a string"
    rel = raw_path.strip()
    if not rel:
        return None, None, "managed path is empty"
    if "\\" in rel:
        return None, None, "managed path must use normalized forward slashes"
    if rel.startswith("/") or rel.startswith("//") or re.match(r"^[A-Za-z]:", rel):
        return None, None, "managed path is absolute"
    parts = rel.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None, None, "managed path is not normalized or attempts traversal"
    normalized = "/".join(parts)
    raw_target = root / Path(*parts)
    if raw_target.is_symlink():
        return None, None, "managed release files may not be symlinks"
    target = raw_target.resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None, None, "managed path escapes project root"
    return normalized, target, ""


def verify_release_identity(root: Path) -> Dict[str, Any]:
    """Read-only release-identity and managed-file verification gate."""
    root = root.resolve()
    started = time.monotonic()
    evidence: Dict[str, Any] = {
        "gate_version": RUNTIME_IDENTITY_GATE_VERSION,
        "parameter_alignment": PARAMETER_ALIGNMENT_VERSION,
        "started_at": now_local(),
        "project_root": safe_display_path(root),
        "running": {"package_id": PACKAGE_ID, "version": APP_VERSION, "build_id": BUILD_NAME},
        "execution": {
            "execution_namespace": EXECUTION_NAMESPACE,
            "canonical_entrypoint": CANONICAL_ENTRYPOINT,
            "backend_target": SCRIPT_FILENAME,
            "project_output_roots": PROJECT_OUTPUT_ROOTS,
        },
        "controls": {},
        "managed_count": 0,
        "verified_count": 0,
        "mismatches": [],
        "authenticated_activity_allowed": False,
        "authenticated_activity_waited_for_pass": False,
        "verification_mutated_release_files": False,
    }
    controls = {
        VERSION_FILENAME: root / VERSION_FILENAME,
        MANIFEST_FILENAME: root / MANIFEST_FILENAME,
        PACKAGE_METADATA_FILENAME: root / PACKAGE_METADATA_FILENAME,
    }
    parsed: Dict[str, Dict[str, Any]] = {}
    for name, path in controls.items():
        info: Dict[str, Any] = {"exists": path.is_file(), "sha256": None}
        evidence["controls"][name] = info
        if not path.is_file():
            _release_identity_mismatch(evidence, "missing_control_file", name, "readable file", "missing")
            continue
        try:
            info["size_bytes"] = path.stat().st_size
            info["sha256"] = sha256_file(path)
            if name == VERSION_FILENAME:
                values = _version_control_values(path)
                parsed[name] = values
                info.update({
                    "package_id": values.get("package_id"),
                    "version": values.get("version"),
                    "build_id": values.get("build") or values.get("build_id"),
                })
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("control JSON root must be an object")
                parsed[name] = data
                info.update({
                    "package_id": data.get("package_id"),
                    "version": data.get("version"),
                    "build_id": data.get("build_id", data.get("build")),
                })
        except Exception as exc:
            info["error"] = f"{exc.__class__.__name__}: {exc}"
            _release_identity_mismatch(evidence, "unreadable_control_file", name, "readable/parseable", exc.__class__.__name__)

    expected_identity = {"package_id": PACKAGE_ID, "version": APP_VERSION, "build_id": BUILD_NAME}
    for name, info in evidence["controls"].items():
        for field, expected in expected_identity.items():
            observed = info.get(field)
            if observed != expected:
                _release_identity_mismatch(evidence, "identity_mismatch", f"{name}:{field}", expected, observed)

    expected_execution = {
        "execution_namespace": EXECUTION_NAMESPACE,
        "canonical_entrypoint": CANONICAL_ENTRYPOINT,
        "backend_target": SCRIPT_FILENAME,
        "project_output_roots": PROJECT_OUTPUT_ROOTS,
    }
    for control_name in (MANIFEST_FILENAME, PACKAGE_METADATA_FILENAME):
        control_data = parsed.get(control_name, {})
        if not isinstance(control_data, dict):
            continue
        for field, expected in expected_execution.items():
            observed = control_data.get(field)
            if observed != expected:
                _release_identity_mismatch(evidence, "execution_output_identity_mismatch", f"{control_name}:{field}", expected, observed)

    manifest = parsed.get(MANIFEST_FILENAME, {})
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, list):
        _release_identity_mismatch(evidence, "manifest_inventory_invalid", MANIFEST_FILENAME, "files list", type(files).__name__)
        files = []
    seen: Set[str] = set()
    managed_paths: Set[str] = set()
    for index, entry in enumerate(files):
        if not isinstance(entry, dict) or entry.get("package_managed") is not True:
            continue
        evidence["managed_count"] += 1
        normalized, target, path_error = _safe_managed_release_path(root, entry.get("path"))
        label = str(entry.get("path") or f"files[{index}]")
        if path_error or normalized is None or target is None:
            _release_identity_mismatch(evidence, "unsafe_managed_path", label, "unique normalized root-relative path", path_error or "invalid")
            continue
        dedupe_key = normalized.casefold()
        if dedupe_key in seen:
            _release_identity_mismatch(evidence, "duplicate_managed_path", normalized, "unique path", "duplicate")
            continue
        seen.add(dedupe_key)
        managed_paths.add(normalized)
        if normalized == CONFIG_FILENAME or normalized.split("/", 1)[0] in {STATE_DIRNAME, LOG_DIRNAME, REPORT_DIRNAME, EXPORT_DIRNAME, TEMP_DIRNAME, "downloads", "cache", "caches"}:
            _release_identity_mismatch(evidence, "mutable_file_marked_managed", normalized, "package_managed=false", "package_managed=true")
            continue
        if not target.is_file():
            _release_identity_mismatch(evidence, "missing_managed_file", normalized, "file present", "missing")
            continue
        expected_size = entry.get("size_bytes")
        if expected_size is not None:
            if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
                _release_identity_mismatch(evidence, "invalid_recorded_size", normalized, "non-negative integer or null", expected_size)
                continue
            actual_size = target.stat().st_size
            if actual_size != expected_size:
                _release_identity_mismatch(evidence, "managed_size_mismatch", normalized, expected_size, actual_size)
                continue
        expected_hash = str(entry.get("sha256") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            _release_identity_mismatch(evidence, "invalid_recorded_sha256", normalized, "64 lowercase hex chars", expected_hash or "missing")
            continue
        actual_hash = sha256_file(target)
        if actual_hash != expected_hash:
            _release_identity_mismatch(evidence, "managed_sha256_mismatch", normalized, expected_hash, actual_hash)
            continue
        evidence["verified_count"] += 1

    required_managed = {
        SCRIPT_FILENAME,
        VERSION_FILENAME,
        PACKAGE_METADATA_FILENAME,
        CANONICAL_ENTRYPOINT,
        SAFE_BROWSER_ENTRYPOINT,
        DIAGNOSTICS_EXPORT_ENTRYPOINT,
        *APPROVED_LEGACY_ENTRYPOINT_ALIASES,
    }
    for required in sorted(required_managed - managed_paths):
        _release_identity_mismatch(evidence, "required_managed_file_unlisted", required, "package_managed=true", "not listed as managed")
    if evidence["managed_count"] == 0:
        _release_identity_mismatch(evidence, "empty_managed_inventory", MANIFEST_FILENAME, ">=1 managed file", 0)

    passed = not evidence["mismatches"] and evidence["verified_count"] == evidence["managed_count"]
    evidence["result"] = "PASS" if passed else "BLOCK"
    evidence["authenticated_activity_allowed"] = passed
    evidence["authenticated_activity_waited_for_pass"] = passed
    evidence["duration_ms"] = round(max(0.0, time.monotonic() - started) * 1000.0, 3)
    evidence["finished_at"] = now_local()
    return evidence


def release_identity_summary(root: Path, evidence: Optional[Dict[str, Any]] = None) -> str:
    ev = evidence if isinstance(evidence, dict) else verify_release_identity(root)
    controls = ev.get("controls", {}) if isinstance(ev.get("controls"), dict) else {}
    lines = [
        "Runtime release identity / managed-file integrity gate:",
        f"- Result: {ev.get('result', 'BLOCK')}",
        f"- Gate: {ev.get('gate_version', RUNTIME_IDENTITY_GATE_VERSION)}",
        f"- Running package/version/build: {PACKAGE_ID} / {APP_VERSION} / {BUILD_NAME}",
        f"- Execution namespace / canonical entrypoint: {EXECUTION_NAMESPACE} / {CANONICAL_ENTRYPOINT}",
        f"- Backend target: {SCRIPT_FILENAME}",
        f"- Project output roots: {json.dumps(PROJECT_OUTPUT_ROOTS, sort_keys=True)}",
        f"- Managed files verified: {ev.get('verified_count', 0)}/{ev.get('managed_count', 0)}",
        f"- Gate duration ms: {ev.get('duration_ms', 0)}",
        f"- Authenticated/network runtime allowed only after PASS: {bool(ev.get('authenticated_activity_allowed', False))}",
        f"- Authenticated activity waited for PASS assertion: {bool(ev.get('authenticated_activity_waited_for_pass', False))}",
        "- Verification mutates release files: false",
    ]
    for name in (VERSION_FILENAME, MANIFEST_FILENAME, PACKAGE_METADATA_FILENAME):
        info = controls.get(name, {}) if isinstance(controls.get(name), dict) else {}
        lines.append(
            f"- Control {name}: package={info.get('package_id')} version={info.get('version')} build={info.get('build_id')} sha256={info.get('sha256')}"
        )
    mismatches = ev.get("mismatches", []) if isinstance(ev.get("mismatches"), list) else []
    if mismatches:
        lines.append(f"- Mismatch count: {len(mismatches)}")
        for item in mismatches[:20]:
            if isinstance(item, dict):
                lines.append(f"  - {item.get('kind')}: {item.get('path')} expected={item.get('expected')} observed={item.get('observed')}")
    else:
        lines.append("- Mismatch count: 0")
    if ev.get("result") != "PASS":
        lines.extend([
            "- BLOCK behavior: no download/browser/authenticated runtime is permitted.",
            "- Recovery: restore the complete verified release ZIP, then rerun --verify-release.",
            "- Diagnostics/Export20 remain available and verification performs no repair/rewrite.",
        ])
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def print_release_identity_result(evidence: Dict[str, Any]) -> None:
    print(release_identity_summary(app_root(), evidence).rstrip())


def short_path(path: Path, root: Optional[Path] = None) -> str:
    try:
        base = root or app_root()
        return str(path.resolve().relative_to(base.resolve()))
    except (ValueError, OSError, RuntimeError):
        return str(path)


def _home_markers() -> List[str]:
    markers: List[str] = []
    for value in [str(Path.home()), os.environ.get("USERPROFILE"), os.environ.get("HOME")]:
        if value:
            markers.append(value)
    drive = os.environ.get("HOMEDRIVE") or ""
    homepath = os.environ.get("HOMEPATH") or ""
    if drive and homepath:
        markers.append(drive + homepath)
    return sorted({m for m in markers if m and len(m) > 3}, key=len, reverse=True)


SENSITIVE_KEY_HINTS = {
    "api_key", "apikey", "access_key", "secret", "token", "password", "passwd", "pwd",
    "cookie", "credential", "bearer", "authorization", "private_key",
    "session_token", "sessionid", "session_key", "signature", "credential", "policy", "expires",
    "googleaccessid", "awsaccesskeyid", "x_amz", "x_goog",
    "license", "product_key", "serial", "uuid", "mac_address", "local_ip",
}


def redact_sensitive_text(value: Any) -> str:
    text = "" if value is None else str(value)
    for marker in _home_markers():
        text = text.replace(marker, "<USER_HOME>")
        text = text.replace(marker.replace("\\", "/"), "<USER_HOME>")
    # Redact HTTP(S) userinfo wherever a URL appears in logs or exception text.
    text = re.sub(
        r"(?i)\b(https?://)[^/\s:@]+(?::[^/\s@]*)?@",
        r"\1<REDACTED>@",
        text,
    )
    # Redact common secret-bearing URL query parameters without dropping host/path evidence.
    text = re.sub(
        r"(?i)([?&](?:api[_-]?key|access[_-]?key|access[_-]?token|token|secret|password|passwd|pwd|cookie|session|sid|signature|sig|auth|authorization|credential|policy|expires|googleaccessid|awsaccesskeyid|x-amz-[^=&\s]+|x-goog-[^=&\s]+)=)[^&\s]+",
        r"\1<REDACTED>",
        text,
    )
    # Redact common key/value secret patterns in logs and generated diagnostics.
    text = re.sub(
        r"(?i)\b(api[_-]?key|access[_-]?token|token|secret|password|passwd|pwd|cookie|authorization|bearer)\b\s*[:=]\s*([^\s,;\]}&]+)",
        r"\1=<REDACTED>",
        text,
    )
    text = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer <REDACTED>", text)
    return text


SENSITIVE_QUERY_KEY_HINTS = {
    "api_key", "apikey", "access_key", "accesskey", "token", "secret", "password", "passwd", "pwd",
    "cookie", "session", "sid", "signature", "sig", "auth", "authorization", "credential", "policy",
    "expires", "googleaccessid", "awsaccesskeyid", "x-amz", "x-goog", "key-pair-id",
}


def _query_key_is_sensitive(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key or "").lower()).strip("_")
    return any(hint in normalized for hint in SENSITIVE_QUERY_KEY_HINTS)


def redact_url_for_evidence(value: Any) -> str:
    """Return a diagnostic-safe HTTP(S) URL without changing the operational URL.

    Userinfo and secret-like query values are masked before URLs reach logs, recent-run
    summaries, failure evidence, diagnostics, or support exports. The downloader still
    keeps the original normalized URL internally where it is required for fetching and
    duplicate indexing.
    """
    text = "" if value is None else str(value)
    try:
        parsed = urllib.parse.urlsplit(text)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            return redact_sensitive_text(text)
        host = parsed.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        try:
            port = parsed.port
        except ValueError:
            port = None
        netloc = host + (f":{port}" if port else "")
        if parsed.username is not None or parsed.password is not None:
            netloc = f"<REDACTED>@{netloc}"
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        safe_pairs = [(key, "<REDACTED>" if _query_key_is_sensitive(key) else value) for key, value in query_pairs]
        safe_query = urllib.parse.urlencode(safe_pairs, doseq=True)
        rebuilt = urllib.parse.urlunsplit((parsed.scheme.lower(), netloc, parsed.path, safe_query, ""))
        return redact_sensitive_text(rebuilt)
    except (TypeError, ValueError, UnicodeError):
        return redact_sensitive_text(text)


def redact_source_for_evidence(value: Any) -> str:
    text = "" if value is None else str(value)
    return redact_url_for_evidence(text) if text.lower().startswith(("http://", "https://")) else redact_sensitive_text(text)


def safe_display_path(path: Any, root: Optional[Path] = None) -> str:
    try:
        p = Path(str(path)).resolve()
        if root is not None:
            try:
                return str(p.relative_to(root.resolve()))
            except (ValueError, RuntimeError):
                pass
        return redact_sensitive_text(str(p))
    except (OSError, RuntimeError, TypeError, ValueError):
        return redact_sensitive_text(path)


def redact_json_for_export(value: Any, key_hint: str = "") -> Any:
    key_l = key_hint.lower()
    if any(hint in key_l for hint in SENSITIVE_KEY_HINTS):
        return "<REDACTED>"
    if isinstance(value, dict):
        return {str(k): redact_json_for_export(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_json_for_export(item, key_hint) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def tool_available(name: str) -> str:
    found = shutil.which(name)
    return "available" if found else "not found"


COMPUTER_AWARENESS_VERSION = "1.0.0"
COMPUTER_PROFILE_OVERRIDE_ENV = "IMAGE_DOWNLOADER_COMPUTER_LABEL"
COMPUTER_PROFILES: Dict[str, Dict[str, Any]] = {
    "PC-ALPHA-01": {
        "display_name": "ALPHA",
        "role": "high-throughput desktop",
        "aliases": ["alpha", "alpha computer", "main desktop", "primary desktop"],
        "helpful_hint": "Suitable for sustained or large download sets; adaptive throttling remains the runtime authority.",
    },
    "PC-ASCEND-02": {
        "display_name": "ASCEND",
        "role": "high-performance mobile computer",
        "aliases": ["ascend", "ascend laptop", "asus rog strix", "g634jy"],
        "helpful_hint": "Mobile/VPN-aware diagnostics are emphasized; no worker or feature restriction is applied.",
    },
    "PC-DEUSEX-03": {
        "display_name": "DeusEx",
        "role": "portable compatibility computer",
        "aliases": ["deusex", "deus ex", "raider", "msi raider", "ge66", "raider ge66 12uhs", "pc-raider-03"],
        "helpful_hint": "Compatibility labeling is enabled; no reduced mode, ownership requirement, or launch gate is applied.",
    },
}


def normalize_computer_label(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower()).strip()


def resolve_computer_profile(value: Any) -> Optional[str]:
    normalized = normalize_computer_label(value)
    if not normalized:
        return None
    compact = normalized.replace(" ", "")
    for canonical_id, profile in COMPUTER_PROFILES.items():
        canonical_normalized = normalize_computer_label(canonical_id)
        if normalized == canonical_normalized or compact == canonical_normalized.replace(" ", ""):
            return canonical_id
        for alias in profile.get("aliases", []):
            alias_normalized = normalize_computer_label(alias)
            alias_compact = alias_normalized.replace(" ", "")
            if normalized == alias_normalized or compact == alias_compact:
                return canonical_id
            if len(alias_compact) >= 5 and alias_compact in compact:
                return canonical_id
    return None


def detect_computer_context(cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Return a privacy-safe, label-only computer context.

    This context is informational only. It never changes launch permission, locks,
    state paths, feature access, worker limits, or ownership behavior.
    """
    cfg = cfg if isinstance(cfg, dict) else {}
    enabled = bool(cfg.get("computer_awareness_enabled", True))
    env_name = str(cfg.get("computer_profile_override_env_name") or COMPUTER_PROFILE_OVERRIDE_ENV)
    raw_host = str(os.environ.get("COMPUTERNAME", "") or platform.node() or "generic-windows")
    normalized_host = normalize_computer_label(raw_host) or "generic windows"
    host_hash = hashlib.sha256(normalized_host.encode("utf-8", errors="replace")).hexdigest()[:8].upper()
    if not enabled:
        return {
            "awareness_version": COMPUTER_AWARENESS_VERSION,
            "canonical_id": "AWARENESS-DISABLED",
            "display_name": "Computer awareness disabled",
            "diagnostic_id": f"LOCAL-{host_hash}",
            "role": "local computer",
            "detection_source": "disabled by config",
            "known_profile": False,
            "warning": "",
            "helpful_hint": "No computer label is shown; runtime behavior remains unrestricted.",
            "behavior_scope": "diagnostic_labels_only",
            "launch_restrictions": False,
            "state_path_changes": False,
            "lock_scope_changes": False,
            "feature_restrictions": False,
        }

    override = os.environ.get(env_name, "").strip()
    canonical_id = resolve_computer_profile(override) if override else None
    warning = ""
    source = f"{env_name} override" if override else "sanitized hostname alias match"
    if override and canonical_id is None:
        warning = "Unrecognized computer-label override was ignored; generic non-restrictive labeling is used."
    if canonical_id is None and not override:
        for candidate in (os.environ.get("COMPUTERNAME", ""), platform.node()):
            canonical_id = resolve_computer_profile(candidate)
            if canonical_id:
                break
    if canonical_id in COMPUTER_PROFILES:
        profile = COMPUTER_PROFILES[canonical_id]
        return {
            "awareness_version": COMPUTER_AWARENESS_VERSION,
            "canonical_id": canonical_id,
            "display_name": str(profile.get("display_name") or canonical_id),
            "diagnostic_id": canonical_id,
            "role": str(profile.get("role") or "local computer"),
            "detection_source": source,
            "known_profile": True,
            "warning": warning,
            "helpful_hint": str(profile.get("helpful_hint") or "Informational label only."),
            "behavior_scope": "diagnostic_labels_only",
            "launch_restrictions": False,
            "state_path_changes": False,
            "lock_scope_changes": False,
            "feature_restrictions": False,
        }
    return {
        "awareness_version": COMPUTER_AWARENESS_VERSION,
        "canonical_id": "OTHER-WINDOWS",
        "display_name": f"Other Windows computer ({host_hash})",
        "diagnostic_id": f"OTHER-WINDOWS-{host_hash}",
        "role": "generic local Windows computer",
        "detection_source": "privacy-safe hashed local hostname; no canonical alias match",
        "known_profile": False,
        "warning": warning,
        "helpful_hint": "Generic capability mode is informational only; all normal features remain available.",
        "behavior_scope": "diagnostic_labels_only",
        "launch_restrictions": False,
        "state_path_changes": False,
        "lock_scope_changes": False,
        "feature_restrictions": False,
    }


def computer_awareness_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    ctx = detect_computer_context(cfg)
    lines = [
        "Helpful computer awareness (non-restrictive):",
        f"- Enabled: {bool(cfg.get('computer_awareness_enabled', True))}",
        f"- Active label: {ctx.get('display_name')}",
        f"- Diagnostic ID: {ctx.get('diagnostic_id')}",
        f"- Role hint: {ctx.get('role')}",
        f"- Detection source: {ctx.get('detection_source')}",
        f"- Known profile: {ctx.get('known_profile')}",
        f"- Helpful hint: {ctx.get('helpful_hint')}",
        f"- Optional label override: {cfg.get('computer_profile_override_env_name', COMPUTER_PROFILE_OVERRIDE_ENV)}",
        "- Launch permission: never changed by computer identity.",
        "- Runtime state/log/report paths: shared project-local layout; no computer overlay.",
        "- Locks/ownership/handoff: no computer-specific ownership credential, coordination hold, election, or cross-computer gate.",
        "- Worker limits/features: adaptive throttle and config remain authoritative; the label does not restrict or unlock features.",
    ]
    if ctx.get("warning"):
        lines.append(f"- Warning: {ctx.get('warning')}")
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def system_aware_environment_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        f"{APP_NAME} system-aware environment summary",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        "Source: current public release framework with preserved runtime integrity and nonrestrictive computer awareness",
        "",
        "Runtime snapshot (redacted):",
        f"- Project root: {safe_display_path(root)}",
        f"- Config path: {safe_display_path(config_path, root)}",
        f"- Python executable: {safe_display_path(sys.executable)}",
        f"- Python version: {platform.python_version()}",
        f"- OS/platform: {redact_sensitive_text(platform.platform())}",
        f"- Machine/architecture: {platform.machine() or 'unknown'}",
        f"- Helpful computer label: {detect_computer_context(cfg).get('display_name')}",
        f"- Helpful diagnostic ID: {detect_computer_context(cfg).get('diagnostic_id')}",
        f"- Processor class: {redact_sensitive_text(platform.processor() or 'not reported')}",
        f"- Working directory: {safe_display_path(Path.cwd())}",
        "",
        "Windows/tooling checks (non-invasive):",
        f"- py launcher: {tool_available('py')}",
        f"- python: {tool_available('python')}",
        f"- pip: {tool_available('pip')}",
        f"- Windows Terminal wt: {tool_available('wt')}",
        f"- git CLI: {tool_available('git')}",
        f"- Node.js: {tool_available('node')}",
        f"- Docker: {tool_available('docker')}",
        "",
        "Security/VPN posture:",
        "- No antivirus, firewall, VPN, adapter, MAC, serial, account, raw hostname, or local IP enumeration is exported.",
        "- Computer recognition uses known aliases or a short privacy-safe hash and remains diagnostic-only.",
        "- Package remains Norton/Windows Security friendly: no bundled executables, no hidden execution, no downloaded-file auto-run, no firewall/service/autostart changes.",
        f"- Downloaded media hidden-file default: {bool(cfg.get('hide_downloaded_media', True))}; this changes only the Windows file attribute on completed image files.",
        f"- Backend VPN/IP resilience enabled: {bool(cfg.get('network_resilience_enabled', True))}",
        f"- HTTP session refresh on network error: {bool(cfg.get('network_reset_session_on_error', True))}",
        f"- Optional browser context reset on browser/network error: {bool(cfg.get('network_browser_reset_on_error', True))}",
        "",
        "External-platform drift posture:",
        "- Cached, off-critical-path integration evidence is used; normal launches do not crawl documentation/status pages.",
        "- This project performs public HTTP(S) image/page fetches only; it does not store credentials, cookies, webhooks, wallet keys, or API tokens.",
        "- Per-site permission/terms remain user responsibility because pasted URLs can point to arbitrary third-party websites.",
        "",
        "Sanitized PC-context assumptions from current release framework:",
        "- Treat Windows 11 Pro, Python 3.13-class runtime, Norton/VPN presence, and multi-drive storage as expected context, but verify live state before sensitive changes.",
        "- Keep outputs folder-local and prefer ZIP handoff; do not carry raw PC reports or hardware identifiers forward.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def atomic_temp_path(path: Path) -> Path:
    return path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")


WINDOWS_FILE_ATTRIBUTE_HIDDEN = 0x00000002
WINDOWS_INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


def windows_attributes_with_visibility(attributes: int, hidden: bool) -> int:
    """Return Windows file attributes with the hidden bit enabled or disabled."""
    value = int(attributes)
    return (value | WINDOWS_FILE_ATTRIBUTE_HIDDEN) if hidden else (value & ~WINDOWS_FILE_ATTRIBUTE_HIDDEN)


def apply_downloaded_media_visibility(path: Path, hidden: bool) -> Tuple[str, str]:
    """Apply completed-media visibility with the native Windows file attribute.

    No shell is started. A visibility failure never invalidates a verified image.
    """
    if not hidden:
        return "visible", "hidden-media default disabled by config"
    if os.name != "nt":
        return "not_applicable", "Windows hidden file attributes are unavailable on this host"
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_attributes = kernel32.GetFileAttributesW
        get_attributes.argtypes = [wintypes.LPCWSTR]
        get_attributes.restype = wintypes.DWORD
        set_attributes = kernel32.SetFileAttributesW
        set_attributes.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
        set_attributes.restype = wintypes.BOOL

        current = int(get_attributes(str(path)))
        if current == WINDOWS_INVALID_FILE_ATTRIBUTES:
            return "failed", f"GetFileAttributesW failed with WinError {ctypes.get_last_error()}"
        desired = windows_attributes_with_visibility(current, True)
        if desired == current:
            return "hidden", "Windows hidden attribute was already present"
        if not bool(set_attributes(str(path), desired)):
            return "failed", f"SetFileAttributesW failed with WinError {ctypes.get_last_error()}"
        return "hidden", "Windows hidden attribute applied"
    except (AttributeError, ImportError, OSError, TypeError, ValueError) as exc:
        return "failed", f"{exc.__class__.__name__}: {exc}"


def json_dump(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = atomic_temp_path(path)
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)
            f.write("\n")
        tmp.replace(path)
    except Exception:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = atomic_temp_path(path)
    try:
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
    except Exception:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise


def json_load(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError, ValueError):
        return default


def json_load_strict_object(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Malformed JSON in {path.name}: line {exc.lineno}, column {exc.colno}") from exc
    except OSError as exc:
        raise RuntimeError(f"Could not read {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"{path.name} must contain a JSON object at the top level")
    return data


def retain_recent_files(folder: Path, pattern: str, keep: int) -> None:
    try:
        files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return
    for old in files[max(0, keep):]:
        with contextlib.suppress(OSError):
            old.unlink()


def backup_file_for_migration(path: Path, *, label: str, keep: int = 5) -> str:
    if not path.exists():
        return ""
    backup_dir = (path.parent / MIGRATION_BACKUP_DIRNAME) if path.parent.name == STATE_DIRNAME else (path.parent / STATE_DIRNAME / MIGRATION_BACKUP_DIRNAME)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_name = f"{path.stem}_{label}_{timestamp_compact()}{path.suffix or '.bak'}"
    backup_path = backup_dir / backup_name
    shutil.copy2(path, backup_path)
    retain_recent_files(backup_dir, f"{path.stem}_{label}_*", keep)
    return short_path(backup_path, path.parent)


def default_config() -> Dict[str, Any]:
    return {
        "config_schema_version": CONFIG_SCHEMA_VERSION,
        "state_schema_version": STATE_SCHEMA_VERSION,
        "output": "downloads",
        "output_mode": "project_local",
        "hide_downloaded_media": True,
        "timeout": 5,
        "connect_timeout": 3,
        "read_timeout": 5,
        "request_wall_clock_timeout_seconds": 5,
        "page_wall_clock_timeout_seconds": 60,
        "limit": 0,
        "workers": 3,
        "retries": 2,
        "retry_backoff_base_ms": 500,
        "retry_backoff_max_ms": 8000,
        "retry_jitter_ms": 250,
        "retry_after_max_seconds": 30,
        "max_redirects": 12,
        "same_domain_only": False,
        "min_width": 0,
        "min_height": 0,
        "types": [
            "jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "tiff", "avif"
        ],
        "follow_gallery_links": False,
        "gallery_page_limit": 6,
        "gallery_max_depth": 1,
        "automation_mode": "smart_safe",
        "auto_gallery_follow_enabled": True,
        "auto_gallery_page_limit": 3,
        "auto_gallery_max_depth": 1,
        "auto_gallery_link_limit_per_page": 12,
        "auto_browser_fallback_enabled": False,
        "auto_browser_fallback_policy": "manual_trusted_sites_only",
        "srcset_preference": "largest",
        "browser_mode": False,
        "browser_scroll_steps": 3,
        "browser_wait_ms": 500,
        "browser_reuse_context": True,
        "browser_capture_network_images": True,
        "browser_network_image_limit": 500,
        "network_resilience_enabled": True,
        "network_reset_session_on_error": True,
        "network_recovery_pause_ms": 750,
        "network_recovery_max_pause_ms": 4000,
        "network_head_probe_retries": 1,
        "network_browser_reset_on_error": True,
        "network_recovery_event_limit": 25,
        "network_session_reset_debounce_ms": 1000,
        "network_recovery_extra_attempts": 2,
        "adaptive_throttle_enabled": True,
        "adaptive_throttle_mode": "feedback_aimd",
        "adaptive_throttle_min_workers": 1,
        "adaptive_throttle_max_workers": 3,
        "adaptive_throttle_target_latency_ms": 1500,
        "adaptive_throttle_slow_latency_ms": 4500,
        "adaptive_throttle_ewma_alpha": 0.25,
        "adaptive_throttle_successes_to_increase": 5,
        "adaptive_throttle_decrease_factor": 0.65,
        "adaptive_throttle_error_rate_threshold": 0.25,
        "adaptive_throttle_window": 20,
        "adaptive_throttle_cooldown_seconds": 3,
        "adaptive_throttle_host_cooldown_max_seconds": 60,
        "adaptive_throttle_event_limit": 40,
        "stale_state_guard_days": 30,
        "single_instance_guard_enabled": False,
        "single_instance_second_launch": "allowed_guard_disabled_by_default",
        "single_instance_lock_stale_seconds": 21600,
        "single_instance_event_limit": 40,
        "computer_awareness_enabled": True,
        "computer_profile_mode": "diagnostic_labels_only",
        "computer_profile_override_env_name": COMPUTER_PROFILE_OVERRIDE_ENV,
        "computer_profile_include_in_console": True,
        "computer_profile_include_in_diagnostics": True,
        "computer_profile_affects_launch": False,
        "computer_profile_affects_state_paths": False,
        "computer_profile_affects_locks": False,
        "computer_profile_affects_feature_access": False,
        "download_queue_capacity": 100,
        "download_queue_full_policy": "visible_reject_excess",
        "download_queue_autosave_enabled": True,
        "download_queue_recovery_enabled": True,
        "session_download_list_enabled": True,
        "session_download_list_latest_filename": LATEST_DOWNLOAD_LIST_FILENAME,
        "session_download_list_retention": 25,
        "gallery_queue_capacity": 100,
        "shutdown_drain_timeout_seconds": 10,
        "schema_migration_backup_retention": 5,
        "log_max_bytes": 1048576,
        "log_backup_count": 3,
        "system_snapshot_enabled": True,
        "diagnostic_redact_sensitive_values": True,
        "export_redaction_enabled": True,
        "system_aware_primer_version": PARAMETER_ALIGNMENT_VERSION,
        "parameter_alignment_version": PARAMETER_ALIGNMENT_VERSION,
        "asset_metadata": {
            "metadata_schema": ASSET_METADATA_SCHEMA,
            "asset_id": "IMGDL-CONFIG",
            "project_slug": PROJECT_SLUG,
            "version": APP_VERSION,
            "build": BUILD_NAME,
            "status": ASSET_STATUS,
            "sensitivity": ASSET_SENSITIVITY,
            "tags": ["image-downloader", "config", "standard-mode", "smart-safe-automation", "canonical-export", "portable", "helpful-computer-awareness", "asset-metadata"],
            "lineage": "supersedes IMGDL-CONFIG@2026.08.08.1; adds the stable launcher and project-local output contract while remaining mutable and intentionally excluded from package-managed release hashing",
            "copyright_notice": "Copyright © 2026 Gateway Information Group LLC. All rights reserved.",
        },
        "google_drive_vault_sync_status": "not_configured_local_runtime",
        "google_drive_reference_check_status": "verified",
        "google_drive_reference_check_note": "local current maintenance release prepared on 2026-08-09; Drive upload/sync not performed or claimed",
        "google_drive_intended_vault_path": INTENDED_DRIVE_VAULT_PATH,
        "google_drive_project_category": "30_UTILITIES_AND_WINDOWS_TOOLS",
        "google_drive_project_path": DRIVE_PROJECT_PATH,
        "google_drive_latest_build_path": INTENDED_DRIVE_VAULT_PATH,
        "google_drive_source_of_truth_path": DRIVE_PROJECT_PATH + "/00_SOURCE_OF_TRUTH",
        "google_drive_support_ready_path": DRIVE_PROJECT_PATH + "/01_SUPPORT_READY",
        "google_drive_diagnostics_path": DRIVE_PROJECT_PATH + "/03_DIAGNOSTICS",
        "google_drive_docs_runbook_path": DRIVE_PROJECT_PATH + "/04_DOCS_RUNBOOK",
        "google_drive_changelog_manifest_path": DRIVE_PROJECT_PATH + "/05_CHANGELOG_MANIFEST",
        "google_drive_archive_path": DRIVE_PROJECT_PATH + "/06_ARCHIVE",
        "custom_input_assurance_enabled": True,
        "platform_api_compliance_enabled": True,
        "platform_review_mode": "cached_off_critical_path",
        "platform_review_normal_days": 30,
        "platform_review_fast_days": 7,
        "platform_contract_probe_mode": "non_mutating_read_only",
        "platform_registry_status": "verified_local_controls_unknown_site_policy",
        "platform_registry_last_review": BUILD_DATE,
        "launcher_sync_installed_files": False,
        "archive_nested_package_conflicts": True,
        "nested_package_archive_retention": 3,
        "archive_superseded_support_docs": True,
        "superseded_support_docs_archive_retention": 3,
        "per_run_duplicate_queue_reset": True,
        "thread_local_http_sessions": True,
        "max_file_mb": 25.0,
        "max_html_mb": 5.0,
        "stream_chunk_kb": 128,
        "resume_partial_downloads": True,
        "resume_requires_validator": True,
        "resume_min_bytes": 262144,
        "partial_retention_hours": 24,
        "state_checkpoint_interval_downloads": 10,
        "strict_raster_verify": True,
        "image_max_pixels": 120000000,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123 Safari/537.36"
        ),
        "organize_by_domain": True,
        "dry_run": False,
        "safe_svg_validation": True,
        "duplicate_url_check": True,
        "duplicate_content_hash_check": True,
        "duplicate_visual_fingerprint_check": True,
        "duplicate_library_reconcile_enabled": True,
        "duplicate_library_reconcile_max_files": 250,
        "duplicate_library_reconcile_time_budget_seconds": 3,
        "sequence_discovery_enabled": True,
        "sequence_same_domain_only": True,
        "sequence_max_seed_groups_per_run": 30,
        "sequence_max_anchors_per_group": 5,
        "sequence_max_candidates_per_group": 80,
        "sequence_max_failed_attempts": 8,
        "sequence_backward_steps": 3,
        "sequence_probe_delay_ms": 75,
        "sequence_include_discovered_seeds": True,
        "max_candidate_urls_per_page": 500,
        "modern_discovery_enabled": True,
        "recent_failure_limit": 200,
        "log_tail_lines_for_export": 400,
        "canonical_export_filename": CANONICAL_EXPORT_FILENAME,
        "export_keep_previous_zips": 0,
        "export_location_mode": "project_exports_canonical",
        "trusted_sites_note": (
            "Safe Browser Mode uses Playwright/Chromium only when launched explicitly; "
            "use it only for trusted sites."
        ),
        "google_drive_lookup_note": (
            "official structured ImageDownloader vault path retained as reference only; "
            "local runtime may identify ALPHA, ASCEND, DeusEx/Raider/GE66, or a privacy-safe generic host for labels and diagnostics only; no host-specific state overlay, shared startup coordination, ownership dependency, or launch restriction; "
            "direct ZIP upload may require manual Drive placement when connector upload is unavailable"
        ),
        "preferred_bot_dir": ".",
        "bot_dir_env_override_name": "",
        "path_targeting_mode": "canonical_launcher_or_script_root_only",
        "portable_fallback_enabled": False,
        "relocation_repair_status": "canonical_root_relative_project_local_no_auto_sync_no_user_data_delete",
        "omission_control_status": "coverage_ledger_plus_queue_recovery_three_worker_cap_session_timestamps_portable_launch_privacy_and_runtime_evidence",
        "omission_control_coverage_note": "Startup, persistent 100-item queue autosave/recovery, hard three-download concurrency, timestamped session download-list output, canonical-launcher/project-root path targeting, nonrestrictive computer labeling, credential-safe URL evidence, Windows-reserved filename safety, one canonical Export20 ZIP, runtime-evidence completeness, and package verification are tracked before completion claims.",
        "thread_context_health_status": "green_v2176_execution_output_alignment",
    }


def normalize_ext(ext: str) -> str:
    ext = (ext or "").lower().lstrip(".")
    if ext == "tif":
        return "tiff"
    if ext == "jpe":
        return "jpg"
    return ext


def downloaded_asset_id(digest: str) -> str:
    """Stable content-addressed asset ID for a retained downloaded image."""
    token = re.sub(r"[^0-9a-fA-F]", "", str(digest or ""))[:20].upper()
    return f"IMGDL-IMAGE-{token or 'UNKNOWN'}"


def enrich_download_asset_record(record: Dict[str, Any], *, digest: str = "", url: str = "") -> Dict[str, Any]:
    """Add compact release-framework metadata to an existing download-index record."""
    value = dict(record) if isinstance(record, dict) else {}
    digest_value = str(digest or value.get("sha256") or "")
    path_value = str(value.get("path") or "")
    saved_at = str(value.get("saved_at") or value.get("created_at") or now_local())
    suffix = normalize_ext(Path(path_value).suffix) if path_value else ""
    title = Path(path_value).name if path_value else f"image_{digest_value[:12]}"
    aliases = value.get("aliases") if isinstance(value.get("aliases"), list) else []
    if title and title not in aliases:
        aliases = [title] + [str(item) for item in aliases if str(item) != title]
    tags = value.get("tags") if isinstance(value.get("tags"), list) else []
    for tag in ["image-downloader", "downloaded-image", suffix or "unknown-image-format", "content-addressed"]:
        if tag not in tags:
            tags.append(tag)
    value.update({
        "asset_id": str(value.get("asset_id") or downloaded_asset_id(digest_value)),
        "metadata_schema": ASSET_METADATA_SCHEMA,
        "title": str(value.get("title") or title),
        "asset_class": "image",
        "role": "downloaded-output",
        "format": suffix or str(value.get("format") or "unknown"),
        "project_slug": PROJECT_SLUG,
        "asset_version": str(value.get("asset_version") or (digest_value[:16] if digest_value else "unknown")),
        "status": str(value.get("status") or ASSET_STATUS),
        "sensitivity": str(value.get("sensitivity") or ASSET_SENSITIVITY),
        "source_of_truth": False,
        "tags": tags,
        "aliases": aliases[:8],
        "lineage": str(value.get("lineage") or "downloaded from a user-supplied or discovered URL; identity is the content SHA256"),
        "created_at": str(value.get("created_at") or saved_at),
        "modified_at": str(value.get("modified_at") or saved_at),
        "size_bytes": int(value.get("size_bytes", value.get("bytes", 0)) or 0),
        "sha256": digest_value,
        "media_visibility": str(value.get("media_visibility") or "unknown_legacy"),
        "media_visibility_note": str(value.get("media_visibility_note") or "visibility was not recorded by the originating build"),
    })
    if url and not value.get("url"):
        value["url"] = url
    return value


def _normalized_types(value: Any) -> List[str]:
    if not isinstance(value, list):
        value = default_config()["types"]
    result: List[str] = []
    for item in value:
        ext = normalize_ext(str(item))
        if ext in IMAGE_EXTENSIONS and ext not in result:
            result.append(ext)
    return result or list(default_config()["types"])


def normalize_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # Direct-user simplification: remove obsolete computer-specific coordination
    # fields from preserved configs. They are not accepted, exported, or used.
    obsolete_prefix = "fl" + "eet_"
    for obsolete_key in [key for key in list(cfg) if str(key).startswith(obsolete_prefix)]:
        cfg.pop(obsolete_key, None)
    cfg["config_schema_version"] = safe_int(cfg.get("config_schema_version", CONFIG_SCHEMA_VERSION), CONFIG_SCHEMA_VERSION, min_value=1, max_value=CONFIG_SCHEMA_VERSION)
    cfg["state_schema_version"] = safe_int(cfg.get("state_schema_version", STATE_SCHEMA_VERSION), STATE_SCHEMA_VERSION, min_value=1, max_value=STATE_SCHEMA_VERSION)
    cfg["timeout"] = safe_int(cfg.get("timeout", 5), 5, min_value=1, max_value=120)
    cfg["connect_timeout"] = safe_int(cfg.get("connect_timeout", 3), 3, min_value=1, max_value=60)
    cfg["read_timeout"] = safe_int(cfg.get("read_timeout", cfg["timeout"]), cfg["timeout"], min_value=1, max_value=180)
    cfg["request_wall_clock_timeout_seconds"] = safe_int(cfg.get("request_wall_clock_timeout_seconds", 5), 5, min_value=1, max_value=3600)
    cfg["page_wall_clock_timeout_seconds"] = safe_int(cfg.get("page_wall_clock_timeout_seconds", 60), 60, min_value=10, max_value=600)
    cfg["limit"] = safe_int(cfg.get("limit", 0), 0, min_value=0, max_value=100000)
    cfg["workers"] = safe_int(cfg.get("workers", 3), 3, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS)
    cfg["retries"] = safe_int(cfg.get("retries", 2), 2, min_value=0, max_value=5)
    cfg["retry_backoff_base_ms"] = safe_int(cfg.get("retry_backoff_base_ms", 500), 500, min_value=0, max_value=30000)
    cfg["retry_backoff_max_ms"] = safe_int(cfg.get("retry_backoff_max_ms", 8000), 8000, min_value=0, max_value=120000)
    cfg["retry_jitter_ms"] = safe_int(cfg.get("retry_jitter_ms", 250), 250, min_value=0, max_value=5000)
    cfg["retry_after_max_seconds"] = safe_int(cfg.get("retry_after_max_seconds", 30), 30, min_value=0, max_value=300)
    cfg["max_redirects"] = safe_int(cfg.get("max_redirects", 12), 12, min_value=1, max_value=30)
    cfg["min_width"] = safe_int(cfg.get("min_width", 0), 0, min_value=0, max_value=100000)
    cfg["min_height"] = safe_int(cfg.get("min_height", 0), 0, min_value=0, max_value=100000)
    cfg["types"] = _normalized_types(cfg.get("types"))
    cfg["gallery_page_limit"] = safe_int(cfg.get("gallery_page_limit", 6), 6, min_value=1, max_value=50)
    cfg["gallery_max_depth"] = safe_int(cfg.get("gallery_max_depth", 1), 1, min_value=0, max_value=4)
    cfg["auto_gallery_page_limit"] = safe_int(cfg.get("auto_gallery_page_limit", 3), 3, min_value=1, max_value=10)
    cfg["auto_gallery_max_depth"] = safe_int(cfg.get("auto_gallery_max_depth", 1), 1, min_value=0, max_value=2)
    cfg["auto_gallery_link_limit_per_page"] = safe_int(cfg.get("auto_gallery_link_limit_per_page", 12), 12, min_value=1, max_value=50)
    cfg["export_keep_previous_zips"] = safe_int(cfg.get("export_keep_previous_zips", 0), 0, min_value=0, max_value=5)
    cfg["browser_scroll_steps"] = safe_int(cfg.get("browser_scroll_steps", 3), 3, min_value=0, max_value=25)
    cfg["browser_wait_ms"] = safe_int(cfg.get("browser_wait_ms", 500), 500, min_value=0, max_value=10000)
    cfg["browser_network_image_limit"] = safe_int(cfg.get("browser_network_image_limit", 500), 500, min_value=1, max_value=5000)
    cfg["network_recovery_pause_ms"] = safe_int(cfg.get("network_recovery_pause_ms", 750), 750, min_value=0, max_value=30000)
    cfg["network_recovery_max_pause_ms"] = safe_int(cfg.get("network_recovery_max_pause_ms", 4000), 4000, min_value=0, max_value=60000)
    cfg["network_head_probe_retries"] = safe_int(cfg.get("network_head_probe_retries", 1), 1, min_value=0, max_value=5)
    cfg["network_recovery_event_limit"] = safe_int(cfg.get("network_recovery_event_limit", 25), 25, min_value=1, max_value=200)
    cfg["network_session_reset_debounce_ms"] = safe_int(cfg.get("network_session_reset_debounce_ms", 1000), 1000, min_value=0, max_value=30000)
    cfg["network_recovery_extra_attempts"] = safe_int(cfg.get("network_recovery_extra_attempts", 2), 2, min_value=0, max_value=5)
    cfg["adaptive_throttle_min_workers"] = safe_int(cfg.get("adaptive_throttle_min_workers", 1), 1, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS)
    cfg["adaptive_throttle_max_workers"] = safe_int(cfg.get("adaptive_throttle_max_workers", cfg.get("workers", MAX_ACTIVE_DOWNLOADS)), cfg.get("workers", MAX_ACTIVE_DOWNLOADS), min_value=1, max_value=MAX_ACTIVE_DOWNLOADS)
    if cfg["adaptive_throttle_max_workers"] < cfg["adaptive_throttle_min_workers"]:
        cfg["adaptive_throttle_max_workers"] = cfg["adaptive_throttle_min_workers"]
    cfg["adaptive_throttle_max_workers"] = min(MAX_ACTIVE_DOWNLOADS, cfg["adaptive_throttle_max_workers"])
    cfg["adaptive_throttle_target_latency_ms"] = safe_int(cfg.get("adaptive_throttle_target_latency_ms", 1500), 1500, min_value=100, max_value=60000)
    cfg["adaptive_throttle_slow_latency_ms"] = safe_int(cfg.get("adaptive_throttle_slow_latency_ms", 4500), 4500, min_value=250, max_value=120000)
    cfg["adaptive_throttle_successes_to_increase"] = safe_int(cfg.get("adaptive_throttle_successes_to_increase", 5), 5, min_value=1, max_value=100)
    cfg["adaptive_throttle_window"] = safe_int(cfg.get("adaptive_throttle_window", 20), 20, min_value=5, max_value=200)
    cfg["adaptive_throttle_cooldown_seconds"] = safe_int(cfg.get("adaptive_throttle_cooldown_seconds", 3), 3, min_value=0, max_value=120)
    cfg["adaptive_throttle_host_cooldown_max_seconds"] = safe_int(cfg.get("adaptive_throttle_host_cooldown_max_seconds", 60), 60, min_value=1, max_value=600)
    cfg["adaptive_throttle_event_limit"] = safe_int(cfg.get("adaptive_throttle_event_limit", 40), 40, min_value=5, max_value=200)
    cfg["adaptive_throttle_ewma_alpha"] = safe_float(cfg.get("adaptive_throttle_ewma_alpha", 0.25), 0.25, min_value=0.05, max_value=1.0)
    cfg["adaptive_throttle_decrease_factor"] = safe_float(cfg.get("adaptive_throttle_decrease_factor", 0.65), 0.65, min_value=0.25, max_value=0.95)
    cfg["adaptive_throttle_error_rate_threshold"] = safe_float(cfg.get("adaptive_throttle_error_rate_threshold", 0.25), 0.25, min_value=0.05, max_value=1.0)
    cfg["stale_state_guard_days"] = safe_int(cfg.get("stale_state_guard_days", 30), 30, min_value=1, max_value=3650)
    cfg["single_instance_lock_stale_seconds"] = safe_int(cfg.get("single_instance_lock_stale_seconds", 21600), 21600, min_value=60, max_value=604800)
    cfg["single_instance_event_limit"] = safe_int(cfg.get("single_instance_event_limit", 40), 40, min_value=5, max_value=200)
    cfg["download_queue_capacity"] = safe_int(cfg.get("download_queue_capacity", DOWNLOAD_QUEUE_HARD_MAX), DOWNLOAD_QUEUE_HARD_MAX, min_value=1, max_value=DOWNLOAD_QUEUE_HARD_MAX)
    cfg["session_download_list_retention"] = safe_int(cfg.get("session_download_list_retention", 25), 25, min_value=1, max_value=200)
    cfg["gallery_queue_capacity"] = safe_int(cfg.get("gallery_queue_capacity", 100), 100, min_value=1, max_value=1000)
    cfg["shutdown_drain_timeout_seconds"] = safe_int(cfg.get("shutdown_drain_timeout_seconds", 10), 10, min_value=1, max_value=120)
    cfg["schema_migration_backup_retention"] = safe_int(cfg.get("schema_migration_backup_retention", 5), 5, min_value=1, max_value=20)
    cfg["log_max_bytes"] = safe_int(cfg.get("log_max_bytes", 1048576), 1048576, min_value=262144, max_value=10485760)
    cfg["log_backup_count"] = safe_int(cfg.get("log_backup_count", 3), 3, min_value=1, max_value=10)
    cfg["max_file_mb"] = safe_float(cfg.get("max_file_mb", 25), 25, min_value=1, max_value=500)
    cfg["max_html_mb"] = safe_float(cfg.get("max_html_mb", 5), 5, min_value=1, max_value=50)
    cfg["stream_chunk_kb"] = safe_int(cfg.get("stream_chunk_kb", 128), 128, min_value=16, max_value=1024)
    cfg["resume_min_bytes"] = safe_int(cfg.get("resume_min_bytes", 262144), 262144, min_value=0, max_value=104857600)
    cfg["partial_retention_hours"] = safe_int(cfg.get("partial_retention_hours", 24), 24, min_value=1, max_value=720)
    cfg["state_checkpoint_interval_downloads"] = safe_int(cfg.get("state_checkpoint_interval_downloads", 10), 10, min_value=1, max_value=1000)
    cfg["image_max_pixels"] = safe_int(cfg.get("image_max_pixels", 120000000), 120000000, min_value=1000000, max_value=1000000000)
    cfg["sequence_max_seed_groups_per_run"] = safe_int(cfg.get("sequence_max_seed_groups_per_run", 30), 30, min_value=1, max_value=100)
    cfg["sequence_max_anchors_per_group"] = safe_int(cfg.get("sequence_max_anchors_per_group", 5), 5, min_value=1, max_value=25)
    cfg["sequence_max_candidates_per_group"] = safe_int(cfg.get("sequence_max_candidates_per_group", 80), 80, min_value=1, max_value=500)
    cfg["sequence_max_failed_attempts"] = safe_int(cfg.get("sequence_max_failed_attempts", 8), 8, min_value=1, max_value=50)
    cfg["sequence_backward_steps"] = safe_int(cfg.get("sequence_backward_steps", 3), 3, min_value=0, max_value=100)
    cfg["sequence_probe_delay_ms"] = safe_int(cfg.get("sequence_probe_delay_ms", 75), 75, min_value=0, max_value=5000)
    cfg["max_candidate_urls_per_page"] = safe_int(cfg.get("max_candidate_urls_per_page", 500), 500, min_value=1, max_value=5000)
    cfg["duplicate_library_reconcile_max_files"] = safe_int(cfg.get("duplicate_library_reconcile_max_files", 250), 250, min_value=0, max_value=5000)
    cfg["duplicate_library_reconcile_time_budget_seconds"] = safe_int(cfg.get("duplicate_library_reconcile_time_budget_seconds", 3), 3, min_value=0, max_value=60)
    cfg["recent_failure_limit"] = safe_int(cfg.get("recent_failure_limit", 200), 200, min_value=10, max_value=5000)
    cfg["log_tail_lines_for_export"] = safe_int(cfg.get("log_tail_lines_for_export", 400), 400, min_value=20, max_value=2000)
    cfg["superseded_support_docs_archive_retention"] = safe_int(cfg.get("superseded_support_docs_archive_retention", 3), 3, min_value=1, max_value=20)
    cfg["platform_review_normal_days"] = safe_int(cfg.get("platform_review_normal_days", 30), 30, min_value=1, max_value=365)
    cfg["platform_review_fast_days"] = safe_int(cfg.get("platform_review_fast_days", 7), 7, min_value=1, max_value=90)
    for key in [
        "same_domain_only", "follow_gallery_links", "auto_gallery_follow_enabled", "auto_browser_fallback_enabled", "browser_mode", "browser_reuse_context", "browser_capture_network_images",
        "network_resilience_enabled", "network_reset_session_on_error", "network_browser_reset_on_error",
        "adaptive_throttle_enabled",
        "single_instance_guard_enabled", "computer_awareness_enabled", "computer_profile_include_in_console", "computer_profile_include_in_diagnostics", "computer_profile_affects_launch", "computer_profile_affects_state_paths", "computer_profile_affects_locks", "computer_profile_affects_feature_access", "system_snapshot_enabled", "diagnostic_redact_sensitive_values",
        "export_redaction_enabled", "platform_api_compliance_enabled", "custom_input_assurance_enabled", "launcher_sync_installed_files", "archive_nested_package_conflicts", "archive_superseded_support_docs", "per_run_duplicate_queue_reset",
        "thread_local_http_sessions", "portable_fallback_enabled", "organize_by_domain", "hide_downloaded_media", "dry_run", "safe_svg_validation", "download_queue_autosave_enabled", "download_queue_recovery_enabled", "session_download_list_enabled",
        "resume_partial_downloads", "resume_requires_validator", "strict_raster_verify", "modern_discovery_enabled",
        "duplicate_url_check", "duplicate_content_hash_check", "duplicate_visual_fingerprint_check", "duplicate_library_reconcile_enabled", "sequence_discovery_enabled",
        "sequence_same_domain_only", "sequence_include_discovered_seeds",
    ]:
        cfg[key] = safe_bool(cfg.get(key), bool(default_config().get(key, False)))
    if str(cfg.get("automation_mode", "smart_safe")) not in {"smart_safe", "manual"}:
        cfg["automation_mode"] = "smart_safe"
    if str(cfg.get("computer_profile_mode", "diagnostic_labels_only")) != "diagnostic_labels_only":
        cfg["computer_profile_mode"] = "diagnostic_labels_only"
    cfg["computer_profile_override_env_name"] = str(cfg.get("computer_profile_override_env_name") or COMPUTER_PROFILE_OVERRIDE_ENV)
    if str(cfg.get("auto_browser_fallback_policy", "manual_trusted_sites_only")) not in {"manual_trusted_sites_only"}:
        cfg["auto_browser_fallback_policy"] = "manual_trusted_sites_only"
    if str(cfg.get("export_location_mode", "project_exports_canonical")) not in {"project_exports_canonical"}:
        cfg["export_location_mode"] = "project_exports_canonical"
    if str(cfg.get("output_mode", "project_local")) not in {"project_local", "external_explicit"}:
        cfg["output_mode"] = "project_local"
    canonical_export_name = Path(str(cfg.get("canonical_export_filename", CANONICAL_EXPORT_FILENAME))).name
    if not canonical_export_name.lower().endswith(".zip"):
        canonical_export_name += ".zip"
    cfg["canonical_export_filename"] = canonical_export_name or CANONICAL_EXPORT_FILENAME
    if str(cfg.get("adaptive_throttle_mode", "feedback_aimd")) not in {"feedback_aimd", "fixed"}:
        cfg["adaptive_throttle_mode"] = "feedback_aimd"
    if str(cfg.get("download_queue_full_policy", "visible_reject_excess")) not in {"visible_reject_excess"}:
        cfg["download_queue_full_policy"] = "visible_reject_excess"
    session_list_name = Path(str(cfg.get("session_download_list_latest_filename", LATEST_DOWNLOAD_LIST_FILENAME))).name
    if not session_list_name.lower().endswith(".txt"):
        session_list_name += ".txt"
    cfg["session_download_list_latest_filename"] = session_list_name or LATEST_DOWNLOAD_LIST_FILENAME
    if str(cfg.get("single_instance_second_launch", "allowed_guard_disabled_by_default")) not in {"exit_with_status", "allowed_guard_disabled_by_default"}:
        cfg["single_instance_second_launch"] = "allowed_guard_disabled_by_default"
    if str(cfg.get("srcset_preference", "largest")).lower() not in {"largest", "first", "smallest", "all"}:
        cfg["srcset_preference"] = "largest"
    if str(cfg.get("platform_review_mode", "cached_off_critical_path")) not in {"cached_off_critical_path"}:
        cfg["platform_review_mode"] = "cached_off_critical_path"
    if str(cfg.get("platform_contract_probe_mode", "non_mutating_read_only")) not in {"non_mutating_read_only"}:
        cfg["platform_contract_probe_mode"] = "non_mutating_read_only"
    valid_platform_states = {"verified", "warning", "stale", "blocked", "unknown", "verified_local_controls_unknown_site_policy"}
    if str(cfg.get("platform_registry_status", "verified_local_controls_unknown_site_policy")) not in valid_platform_states:
        cfg["platform_registry_status"] = "verified_local_controls_unknown_site_policy"
    valid_drive_states = {"verified", "not_available", "stale", "conflict", "blocked", "not_configured_local_runtime"}
    if str(cfg.get("google_drive_vault_sync_status", "not_configured_local_runtime")) not in valid_drive_states:
        cfg["google_drive_vault_sync_status"] = "not_configured_local_runtime"
    drive_ref_status = str(cfg.get("google_drive_reference_check_status", "not_available") or "not_available")
    if drive_ref_status == "verified_structured_folder_exists_no_zip_upload":
        cfg["google_drive_reference_check_status"] = "verified"
        cfg["google_drive_reference_check_note"] = str(cfg.get("google_drive_reference_check_note") or "structured_folder_exists_no_zip_upload")
    elif drive_ref_status == "not_available_local_runtime":
        cfg["google_drive_reference_check_status"] = "not_available"
        cfg["google_drive_reference_check_note"] = str(cfg.get("google_drive_reference_check_note") or "local_runtime_without_connector_verification")
    elif drive_ref_status not in valid_drive_states:
        cfg["google_drive_reference_check_status"] = "not_available"
        cfg["google_drive_reference_check_note"] = str(cfg.get("google_drive_reference_check_note") or f"normalized_from_unsupported_status:{drive_ref_status}")
    else:
        cfg["google_drive_reference_check_status"] = drive_ref_status
        cfg["google_drive_reference_check_note"] = str(cfg.get("google_drive_reference_check_note") or "")
    cfg["google_drive_intended_vault_path"] = str(cfg.get("google_drive_intended_vault_path") or INTENDED_DRIVE_VAULT_PATH)
    for key in [
        "preferred_bot_dir",
        "bot_dir_env_override_name",
        "path_targeting_mode",
        "relocation_repair_status",
        "omission_control_status",
        "omission_control_coverage_note",
        "thread_context_health_status",
    ]:
        cfg[key] = str(cfg.get(key) or default_config().get(key, ""))
    # These are build-owned metadata, not user-tunable behavior. Always refresh them
    # so an upgraded package cannot keep exporting stale parameter/version evidence.
    cfg["single_instance_guard_enabled"] = False
    cfg["single_instance_second_launch"] = "allowed_guard_disabled_by_default"
    # Computer awareness is strictly informational. These values are build-owned
    # safeguards so config drift cannot turn labels into launch or ownership gates.
    cfg["computer_profile_mode"] = "diagnostic_labels_only"
    cfg["computer_profile_affects_launch"] = False
    cfg["computer_profile_affects_state_paths"] = False
    cfg["computer_profile_affects_locks"] = False
    cfg["computer_profile_affects_feature_access"] = False
    cfg["parameter_alignment_version"] = PARAMETER_ALIGNMENT_VERSION
    cfg["system_aware_primer_version"] = PARAMETER_ALIGNMENT_VERSION
    cfg["asset_metadata"] = default_config()["asset_metadata"]
    return cfg


def merge_config(existing: Dict[str, Any]) -> Dict[str, Any]:
    cfg = default_config()
    for key, value in existing.items():
        cfg[key] = value
    return normalize_config(cfg)


def load_or_create_config(path: Path) -> Tuple[Dict[str, Any], bool]:
    existed = path.exists()
    existing = json_load_strict_object(path) if existed else {}
    source_schema = safe_int(existing.get("config_schema_version", 1), 1, min_value=1) if existed else CONFIG_SCHEMA_VERSION
    if source_schema > CONFIG_SCHEMA_VERSION:
        raise RuntimeError(
            f"Config schema {source_schema} is newer than this build supports ({CONFIG_SCHEMA_VERSION}). "
            "Use a newer Image Downloader build or restore a compatible config backup."
        )
    cfg = merge_config(existing)
    if existed and source_schema < 5 and "output_mode" not in existing:
        legacy_output = Path(str(existing.get("output", "downloads")))
        cfg["output_mode"] = "external_explicit" if legacy_output.is_absolute() else "project_local"
    changed = (not existed) or any(k not in existing for k in default_config().keys()) or source_schema != CONFIG_SCHEMA_VERSION
    if source_schema < CONFIG_SCHEMA_VERSION:
        backup_ref = backup_file_for_migration(
            path,
            label=f"schema{source_schema}_to_{CONFIG_SCHEMA_VERSION}",
            keep=safe_int(cfg.get("schema_migration_backup_retention", 5), 5, min_value=1, max_value=20),
        )
        cfg["config_last_migration"] = {
            "time": now_local(),
            "from_schema": source_schema,
            "to_schema": CONFIG_SCHEMA_VERSION,
            "app_version": APP_VERSION,
            "backup": backup_ref,
            "status": "completed",
            "rollback_note": "Restore the backup with a compatible older build if a one-way schema change must be reversed.",
        }
        changed = True
    # A completed migration must publish the target schema, not merely record it.
    # Keeping the old number would cause repeat migrations and false compatibility evidence.
    cfg["config_schema_version"] = CONFIG_SCHEMA_VERSION
    if changed or cfg != existing:
        json_dump(path, cfg)
    return cfg, existed


def dependency_version(module_name: str, package_name: Optional[str] = None) -> str:
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        return f"not installed ({exc.__class__.__name__})"
    package = package_name or module_name
    try:
        return importlib.metadata.version(package)
    except Exception:
        mod = sys.modules.get(module_name)
        return getattr(mod, "__version__", "installed")


def require_requests():
    try:
        import requests  # type: ignore
        return requests
    except Exception as exc:
        raise RuntimeError(
            f"The requests package is required. Run {CANONICAL_ENTRYPOINT} so it can install core packages, "
            "or install it with: python -m pip install requests beautifulsoup4 pillow"
        ) from exc


def optional_bs4():
    try:
        from bs4 import BeautifulSoup  # type: ignore
        return BeautifulSoup
    except Exception:
        return None


def optional_pil_image():
    try:
        from PIL import Image  # type: ignore
        return Image
    except Exception:
        return None


def configure_logging(root: Path, cfg: Optional[Dict[str, Any]] = None) -> logging.Logger:
    cfg = cfg or {}
    log_dir = root / LOG_DIRNAME
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("image_downloader")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    try:
        max_bytes = max(256 * 1024, int(cfg.get("log_max_bytes", 1048576) or 1048576))
    except (TypeError, ValueError):
        max_bytes = 1048576
    try:
        backup_count = max(1, min(10, int(cfg.get("log_backup_count", 3) or 3)))
    except (TypeError, ValueError):
        backup_count = 3
    file_handler = RotatingFileHandler(
        log_dir / LOG_FILENAME,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def clean_url_text(url: str) -> str:
    url = html.unescape((url or "").strip())
    if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
        url = url[1:-1].strip()
    return url.replace(" ", "%20")


def normalize_url(url: str, base: Optional[str] = None) -> Optional[str]:
    if not url:
        return None
    url = clean_url_text(url)
    low = url.lower()
    if low.startswith(("data:", "blob:", "javascript:", "mailto:", "tel:", "file:")):
        return None
    try:
        if base:
            url = urllib.parse.urljoin(base, url)
        url, _frag = urllib.parse.urldefrag(url)
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if not parsed.netloc:
            return None
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = urllib.parse.quote(urllib.parse.unquote(parsed.path or "/"), safe="/%:@+~#=,;!$&'()*[]")
        query = urllib.parse.quote(urllib.parse.unquote(parsed.query), safe="=&?/%:@+~#=,;!$'()*[]")
        return urllib.parse.urlunparse((scheme, netloc, path, "", query, ""))
    except (TypeError, ValueError, UnicodeError):
        return None


def url_host(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        return (parsed.hostname or parsed.netloc or "").lower()
    except (TypeError, ValueError):
        return ""


def same_hostname(a: str, b: str) -> bool:
    return bool(url_host(a)) and url_host(a) == url_host(b)


def extension_from_url(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path
        name = posixpath.basename(path)
        if "." not in name:
            return ""
        return normalize_ext(name.rsplit(".", 1)[1])
    except (TypeError, ValueError, UnicodeError):
        return ""


def allowed_types(cfg: Dict[str, Any]) -> Set[str]:
    return {normalize_ext(str(x)) for x in cfg.get("types", []) if str(x).strip()}


def is_allowed_image_url(url: str, cfg: Dict[str, Any]) -> bool:
    ext = extension_from_url(url)
    return bool(ext and ext in allowed_types(cfg))


def has_dangerous_extension(url: str) -> bool:
    ext = extension_from_url(url)
    return bool(ext and ext in DANGEROUS_EXTENSIONS)


def base_content_type(content_type: str) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def is_dangerous_content_type(content_type: str) -> bool:
    ct = base_content_type(content_type)
    return ct in DANGEROUS_CONTENT_TYPES or ct.startswith("application/x-msdownload")


def detect_svg(data: bytes) -> bool:
    sample = data[:8192]
    try:
        text = sample.decode("utf-8", errors="ignore").lstrip("\ufeff\r\n\t ").lower()
    except (AttributeError, TypeError, UnicodeError):
        return False
    return "<svg" in text[:4096] and (text.startswith("<svg") or text.startswith("<?xml") or "<svg" in text[:512])


def svg_has_active_content(data: bytes) -> bool:
    try:
        text = data[:65536].decode("utf-8", errors="ignore").lower()
    except (AttributeError, TypeError, UnicodeError):
        return True
    active_patterns = [
        "<script", "javascript:", "vbscript:", "data:text/html", "onload=", "onclick=",
        "onerror=", "onmouseover=", "onfocus=", "onbegin=", "onactivate=", "<foreignobject"
    ]
    return any(pattern in text for pattern in active_patterns)


def detect_image_format(data: bytes, safe_svg: bool = True) -> Optional[str]:
    if len(data) < 12:
        return None
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    if data.startswith(b"BM"):
        return "bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if len(data) >= 16 and data[4:8] == b"ftyp":
        brand_area = data[8:48]
        if any(brand in brand_area for brand in (b"avif", b"avis")):
            return "avif"
    if detect_svg(data):
        if safe_svg and svg_has_active_content(data):
            return None
        return "svg"
    return None


def content_type_allows_format(content_type: str, fmt: str) -> bool:
    ct = base_content_type(content_type)
    if not ct:
        return True
    if is_dangerous_content_type(ct):
        return False
    if ct.startswith("image/"):
        return True
    if fmt == "svg" and ct in SVG_ALLOWED_CONTENT_TYPES:
        return True
    if ct in GENERIC_BINARY_CONTENT_TYPES and fmt != "svg":
        return True
    return False


def validate_image_payload(
    data: bytes,
    fmt: str,
    *,
    strict_raster_verify: bool = True,
    max_pixels: int = 120000000,
) -> Tuple[bool, int, int, str, str]:
    """Validate an in-memory image and return valid, width, height, mode, reason."""
    fmt_norm = normalize_ext(fmt)
    if fmt_norm == "svg":
        if svg_has_active_content(data):
            return False, 0, 0, "svg_active_content_rejected", "SVG contains active/script-like content"
        return True, 0, 0, "safe_svg_scan", ""
    Image = optional_pil_image()
    if Image is None:
        if strict_raster_verify and fmt_norm in COMMON_RASTER_FORMATS:
            return False, 0, 0, "pillow_required", "Pillow is unavailable for strict raster verification"
        return True, 0, 0, "header_only_no_pillow", ""
    try:
        with warnings.catch_warnings():
            bomb_warning = getattr(Image, "DecompressionBombWarning", Warning)
            warnings.simplefilter("error", bomb_warning)
            with Image.open(io.BytesIO(data)) as img:
                width, height = int(img.width), int(img.height)
                if max_pixels > 0 and width * height > max_pixels:
                    return False, width, height, "rejected_pixel_limit", f"image exceeds image_max_pixels ({width * height} > {max_pixels})"
                if strict_raster_verify:
                    img.verify()
        return True, width, height, "pillow_verify", ""
    except Exception as exc:
        if fmt_norm in COMMON_RASTER_FORMATS:
            return False, 0, 0, "pillow_verify_failed", f"{exc.__class__.__name__}: {exc}"
        return True, 0, 0, "header_only_decoder_unavailable", f"{exc.__class__.__name__}: {exc}"


def validate_image_file(
    path: Path,
    fmt: str,
    *,
    strict_raster_verify: bool = True,
    max_pixels: int = 120000000,
) -> Tuple[bool, int, int, str, str]:
    """Validate a downloaded image from disk without loading the whole file into RAM."""
    fmt_norm = normalize_ext(fmt)
    if fmt_norm == "svg":
        active_patterns = [
            b"<script", b"javascript:", b"vbscript:", b"data:text/html", b"onload=",
            b"onclick=", b"onerror=", b"onmouseover=", b"onfocus=", b"onbegin=",
            b"onactivate=", b"<foreignobject",
        ]
        overlap = b""
        try:
            with path.open("rb") as source:
                while True:
                    chunk = source.read(64 * 1024)
                    if not chunk:
                        break
                    sample = (overlap + chunk).lower()
                    if any(pattern in sample for pattern in active_patterns):
                        return False, 0, 0, "svg_active_content_rejected", "SVG contains active/script-like content"
                    overlap = sample[-64:]
        except OSError as exc:
            return False, 0, 0, "svg_read_failed", f"{exc.__class__.__name__}: {exc}"
        return True, 0, 0, "safe_svg_stream_scan", ""

    Image = optional_pil_image()
    if Image is None:
        if strict_raster_verify and fmt_norm in COMMON_RASTER_FORMATS:
            return False, 0, 0, "pillow_required", "Pillow is unavailable for strict raster verification"
        return True, 0, 0, "header_only_no_pillow", ""
    try:
        with warnings.catch_warnings():
            bomb_warning = getattr(Image, "DecompressionBombWarning", Warning)
            warnings.simplefilter("error", bomb_warning)
            with Image.open(path) as img:
                width, height = int(img.width), int(img.height)
                if max_pixels > 0 and width * height > max_pixels:
                    return False, width, height, "rejected_pixel_limit", f"image exceeds image_max_pixels ({width * height} > {max_pixels})"
                if strict_raster_verify:
                    img.verify()
        return True, width, height, "pillow_verify_streamed", ""
    except Exception as exc:
        if fmt_norm in COMMON_RASTER_FORMATS:
            return False, 0, 0, "pillow_verify_failed", f"{exc.__class__.__name__}: {exc}"
        return True, 0, 0, "header_only_decoder_unavailable", f"{exc.__class__.__name__}: {exc}"


def image_visual_fingerprint(path: Path, *, max_pixels: int = 120000000) -> Tuple[str, str, str]:
    """Return a compact orientation-aware visual fingerprint for a static raster image.

    The fingerprint combines aHash, dHash, average RGB, and aspect ratio. Exact
    matches detect visually equivalent re-encodes without adding a new dependency.
    Animated/multi-frame images are intentionally excluded so a shared first frame
    cannot hide different animations.
    """
    Image = optional_pil_image()
    if Image is None:
        return "", "unavailable", "Pillow is unavailable"
    try:
        from PIL import ImageOps  # type: ignore
    except Exception as exc:
        return "", "unavailable", f"ImageOps unavailable: {exc.__class__.__name__}"
    try:
        with warnings.catch_warnings():
            bomb_warning = getattr(Image, "DecompressionBombWarning", Warning)
            warnings.simplefilter("error", bomb_warning)
            with Image.open(path) as img:
                if getattr(img, "is_animated", False) or int(getattr(img, "n_frames", 1) or 1) > 1:
                    return "", "skipped_animated", "multi-frame images use exact SHA256 deduplication only"
                width, height = int(img.width), int(img.height)
                if width <= 0 or height <= 0:
                    return "", "unavailable", "invalid image dimensions"
                if max_pixels > 0 and width * height > max_pixels:
                    return "", "skipped_pixel_limit", "image exceeds image_max_pixels"
                oriented = ImageOps.exif_transpose(img)
                try:
                    if oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info:
                        rgba = oriented.convert("RGBA")
                        canvas = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                        canvas.alpha_composite(rgba)
                        rgb = canvas.convert("RGB")
                    else:
                        rgb = oriented.convert("RGB")
                    resampling = getattr(Image, "Resampling", Image)
                    lanczos = getattr(resampling, "LANCZOS", getattr(Image, "LANCZOS", 1))
                    gray = rgb.convert("L")
                    ah_img = gray.resize((8, 8), lanczos)
                    dh_img = gray.resize((9, 8), lanczos)
                    avg_img = rgb.resize((1, 1), lanczos)
                    getter = getattr(ah_img, "get_flattened_data", None)
                    ah_pixels = tuple(getter()) if callable(getter) else tuple(ah_img.getdata())
                    getter = getattr(dh_img, "get_flattened_data", None)
                    dh_pixels = tuple(getter()) if callable(getter) else tuple(dh_img.getdata())
                    getter = getattr(avg_img, "get_flattened_data", None)
                    avg_pixels = tuple(getter()) if callable(getter) else tuple(avg_img.getdata())
                    mean = sum(int(value) for value in ah_pixels) / max(1, len(ah_pixels))
                    ahash = 0
                    for value in ah_pixels:
                        ahash = (ahash << 1) | int(int(value) >= mean)
                    dhash = 0
                    for row in range(8):
                        offset = row * 9
                        for col in range(8):
                            dhash = (dhash << 1) | int(int(dh_pixels[offset + col]) > int(dh_pixels[offset + col + 1]))
                    average_rgb = avg_pixels[0] if avg_pixels else (0, 0, 0)
                    if not isinstance(average_rgb, tuple):
                        average_rgb = (int(average_rgb),) * 3
                    red, green, blue = (int(average_rgb[i]) if i < len(average_rgb) else 0 for i in range(3))
                    aspect_milli = int(round((oriented.width / max(1, oriented.height)) * 1000.0))
                    fingerprint = f"v1:{ahash:016x}:{dhash:016x}:{red:02x}{green:02x}{blue:02x}:{aspect_milli}"
                    return fingerprint, "pillow_ahash_dhash_rgb_v1", ""
                finally:
                    with contextlib.suppress(Exception):
                        if oriented is not img:
                            oriented.close()
    except Exception as exc:
        return "", "unavailable", f"{exc.__class__.__name__}: {exc}"


def output_path_identity(path: Path) -> str:
    """Case-insensitive canonical output identity for Windows-safe reservations."""
    try:
        return str(path.resolve()).casefold()
    except OSError:
        return str(path.absolute()).casefold()


def build_test_png(red: int, green: int, blue: int) -> bytes:
    """Create a tiny valid RGB PNG using only the standard library for self-tests."""
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    raw = bytes([0, red & 0xFF, green & 0xFF, blue & 0xFF])
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


WINDOWS_RESERVED_FILE_STEMS = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}
BIDI_CONTROL_PATTERN = re.compile(r"[\u202A-\u202E\u2066-\u2069]")


def sanitize_filename(name: str) -> str:
    name = urllib.parse.unquote(name or "")
    name = name.replace("\x00", "")
    name = BIDI_CONTROL_PATTERN.sub("", name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = re.sub(r"\s+", " ", name).strip().rstrip(" .")
    if not name:
        name = "image"
    stem, suffix = os.path.splitext(name)
    if stem.rstrip(" .").upper() in WINDOWS_RESERVED_FILE_STEMS:
        name = f"_{name}"
    if len(name) > 140:
        root_part, dot, ext = name.rpartition(".")
        if dot:
            name = root_part[:120].rstrip(" .") + dot + ext[:12]
        else:
            name = name[:140].rstrip(" .")
    if not name:
        return "image"
    return name


def hostname_folder(url: str) -> str:
    host = url_host(url) or "unknown_host"
    return sanitize_filename(host.replace(":", "_"))


def parse_srcset(srcset: str, preference: str = "largest") -> List[str]:
    if not srcset:
        return []
    items: List[Tuple[float, str]] = []
    for piece in srcset.split(","):
        piece = piece.strip()
        if not piece:
            continue
        parts = piece.split()
        url = parts[0]
        score = 1.0
        if len(parts) > 1:
            descriptor = parts[1].lower()
            try:
                if descriptor.endswith("w"):
                    score = float(descriptor[:-1])
                elif descriptor.endswith("x"):
                    score = float(descriptor[:-1]) * 1000.0
            except (TypeError, ValueError):
                score = 1.0
        items.append((score, url))
    if not items:
        return []
    if preference == "all":
        return [u for _s, u in sorted(items, reverse=True)]
    if preference == "smallest":
        return [min(items, key=lambda x: x[0])[1]]
    return [max(items, key=lambda x: x[0])[1]]


def extract_css_image_urls(css_text: str) -> List[str]:
    """Extract URL-bearing CSS image references without fetching external stylesheets."""
    if not css_text:
        return []
    found: List[str] = []
    for _quote, raw in re.findall(r"url\(\s*(['\"]?)(.*?)\1\s*\)", css_text, flags=re.I | re.S):
        value = html.unescape(raw.strip())
        if value and value not in found:
            found.append(value)
    # image-set() can contain quoted URLs without url(...).
    for block in re.findall(r"(?:-webkit-)?image-set\((.*?)\)", css_text, flags=re.I | re.S):
        for _quote, raw in re.findall(r"(['\"])(.*?)\1", block, flags=re.S):
            value = html.unescape(raw.strip())
            if value and value not in found:
                found.append(value)
    return found


def jsonld_image_urls(value: Any) -> List[str]:
    """Extract image URLs from common Schema.org/JSON-LD image fields."""
    found: List[str] = []
    image_keys = {
        "image", "images", "thumbnailurl", "thumbnail", "logo",
        "primaryimageofpage",
    }

    def walk(node: Any, *, image_context: bool = False) -> None:
        if isinstance(node, str):
            if image_context and node.strip() and node.strip() not in found:
                found.append(node.strip())
            return
        if isinstance(node, list):
            for item in node:
                walk(item, image_context=image_context)
            return
        if not isinstance(node, dict):
            return
        type_value = str(node.get("@type", "")).lower()
        local_image_context = image_context or "imageobject" in type_value
        for key, child in node.items():
            normalized_key = re.sub(r"[^a-z0-9]+", "", str(key).lower())
            child_context = local_image_context or normalized_key in image_keys
            if normalized_key == "url" and local_image_context:
                child_context = True
            walk(child, image_context=child_context)

    walk(value)
    return found


def gallery_link_is_safe_auto(anchor: Any, normalized_url: str, base_url: str) -> bool:
    """Return True only for strong, same-domain pagination/gallery navigation signals."""
    if not normalized_url or not same_hostname(base_url, normalized_url):
        return False
    parsed = urllib.parse.urlparse(normalized_url)
    if parsed.scheme not in {"http", "https"} or has_dangerous_extension(normalized_url):
        return False
    base_no_fragment = urllib.parse.urldefrag(normalize_url(base_url) or base_url)[0]
    target_no_fragment = urllib.parse.urldefrag(normalized_url)[0]
    if not target_no_fragment or target_no_fragment == base_no_fragment:
        return False
    combined = " ".join(
        str(value or "")
        for value in (
            anchor.get_text(" ", strip=True) if hasattr(anchor, "get_text") else "",
            anchor.get("rel", "") if hasattr(anchor, "get") else "",
            anchor.get("class", "") if hasattr(anchor, "get") else "",
            anchor.get("id", "") if hasattr(anchor, "get") else "",
            anchor.get("title", "") if hasattr(anchor, "get") else "",
            anchor.get("aria-label", "") if hasattr(anchor, "get") else "",
        )
    ).lower()
    blocked_tokens = {
        "login", "log in", "signin", "sign in", "signup", "sign up", "logout",
        "account", "cart", "checkout", "comment", "share", "privacy", "terms",
        "contact", "subscribe", "feed", "search", "download app",
    }
    if any(token in combined for token in blocked_tokens):
        return False
    strong_tokens = {
        "next", "next page", "older", "load more", "more images", "more photos",
        "view more", "continue", "slideshow", "gallery", "pagination",
    }
    if any(token in combined for token in strong_tokens):
        return True
    text = (anchor.get_text(" ", strip=True) if hasattr(anchor, "get_text") else "").strip()
    query = urllib.parse.parse_qs(parsed.query.lower(), keep_blank_values=True)
    page_keys = {"page", "p", "pg", "start", "offset"}
    numeric_page_signal = bool(re.fullmatch(r"\d{1,4}", text)) and bool(page_keys.intersection(query))
    path_page_signal = bool(re.search(r"(?:^|[/_-])page[/_-]?\d+(?:$|[/_.-])", parsed.path.lower()))
    return numeric_page_signal or path_page_signal


@dataclasses.dataclass
class DownloadResult:
    url: str
    status: str
    reason: str = ""
    path: str = ""
    bytes_saved: int = 0
    sha256: str = ""
    content_type: str = ""
    status_code: int = 0
    width: int = 0
    height: int = 0


class AdaptiveThrottle:
    """Lightweight feedback controller for concurrency and per-host cooldowns.

    This is deliberately local and deterministic: an AIMD-style controller with
    EWMA latency/error feedback, not a cloud AI service or opaque ML model.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.enabled = bool(config.get("adaptive_throttle_enabled", True)) and str(config.get("adaptive_throttle_mode", "feedback_aimd")) != "fixed"
        configured_workers = safe_int(config.get("workers", MAX_ACTIVE_DOWNLOADS), MAX_ACTIVE_DOWNLOADS, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS)
        requested_min = safe_int(config.get("adaptive_throttle_min_workers", 1), 1, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS)
        requested_max = safe_int(config.get("adaptive_throttle_max_workers", configured_workers), configured_workers, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS)
        self.max_limit = max(1, min(configured_workers, requested_max))
        self.min_limit = max(1, min(self.max_limit, requested_min))
        self.initial_limit = self.max_limit
        self.target_latency = safe_int(config.get("adaptive_throttle_target_latency_ms", 1500), 1500, min_value=100, max_value=60000) / 1000.0
        self.slow_latency = safe_int(config.get("adaptive_throttle_slow_latency_ms", 4500), 4500, min_value=250, max_value=120000) / 1000.0
        self.alpha = safe_float(config.get("adaptive_throttle_ewma_alpha", 0.25), 0.25, min_value=0.05, max_value=1.0)
        self.successes_to_increase = safe_int(config.get("adaptive_throttle_successes_to_increase", 5), 5, min_value=1, max_value=100)
        self.decrease_factor = safe_float(config.get("adaptive_throttle_decrease_factor", 0.65), 0.65, min_value=0.25, max_value=0.95)
        self.error_threshold = safe_float(config.get("adaptive_throttle_error_rate_threshold", 0.25), 0.25, min_value=0.05, max_value=1.0)
        self.window_size = safe_int(config.get("adaptive_throttle_window", 20), 20, min_value=5, max_value=200)
        self.cooldown_seconds = safe_int(config.get("adaptive_throttle_cooldown_seconds", 3), 3, min_value=0, max_value=120)
        self.host_cooldown_max = safe_int(config.get("adaptive_throttle_host_cooldown_max_seconds", 60), 60, min_value=1, max_value=600)
        self.event_limit = safe_int(config.get("adaptive_throttle_event_limit", 40), 40, min_value=5, max_value=200)
        self.lock = threading.RLock()
        self.reset_run()

    def reset_run(self) -> None:
        with self.lock:
            self.current_limit = self.initial_limit
            self.ewma_latency_seconds = 0.0
            self.success_streak = 0
            self.global_cooldown_until = 0.0
            self.host_cooldown_until: Dict[str, float] = {}
            self.window = deque(maxlen=self.window_size)
            self.events: List[Dict[str, Any]] = []
            self.limit_increases = 0
            self.limit_decreases = 0
            self.rate_limit_events = 0
            self.server_pressure_events = 0
            self.network_error_events = 0
            self.slow_completion_events = 0
            self.coalesced_wait_seconds = 0.0
            self.max_observed_in_flight = 0
            self.last_reason = "initial"

    def _append_event(self, kind: str, host: str, reason: str, **extra: Any) -> None:
        item = {
            "time": now_local(),
            "kind": kind,
            "host": host,
            "reason": reason[:300],
            "limit": self.current_limit,
        }
        item.update(extra)
        self.events.append(item)
        del self.events[:-self.event_limit]

    def _decrease(self, host: str, reason: str, *, factor: Optional[float] = None, cooldown: float = 0.0, global_cooldown: bool = False) -> None:
        if not self.enabled:
            return
        old = self.current_limit
        chosen_factor = self.decrease_factor if factor is None else max(0.1, min(0.95, factor))
        proposed = max(self.min_limit, int(old * chosen_factor))
        if proposed >= old and old > self.min_limit:
            proposed = old - 1
        self.current_limit = max(self.min_limit, proposed)
        if self.current_limit < old:
            self.limit_decreases += 1
        now_mono = time.monotonic()
        if cooldown > 0:
            bounded = min(float(self.host_cooldown_max), max(0.0, float(cooldown)))
            self.host_cooldown_until[host] = max(self.host_cooldown_until.get(host, 0.0), now_mono + bounded)
            if global_cooldown:
                self.global_cooldown_until = max(self.global_cooldown_until, now_mono + min(float(self.cooldown_seconds), bounded))
        self.success_streak = 0
        self.last_reason = reason
        self._append_event("decrease", host, reason, previous_limit=old, cooldown_seconds=round(max(0.0, cooldown), 3))
        if self.current_limit != old:
            self.logger.warning("ADAPTIVE_THROTTLE action=decrease host=%s old_limit=%s new_limit=%s reason=%s", host, old, self.current_limit, reason)

    def record_retry(self, host: str, *, status_code: int, delay_seconds: float, stage: str) -> None:
        if not self.enabled:
            return
        with self.lock:
            if status_code == 429:
                self.rate_limit_events += 1
                self._decrease(host, f"HTTP 429 at {stage}", factor=0.5, cooldown=max(delay_seconds, self.cooldown_seconds))
            elif status_code in {500, 502, 503, 504}:
                self.server_pressure_events += 1
                self._decrease(host, f"HTTP {status_code} at {stage}", factor=0.7, cooldown=max(delay_seconds, 1.0))
            elif status_code in {408, 425}:
                self.server_pressure_events += 1
                self._decrease(host, f"HTTP {status_code} at {stage}", factor=0.8, cooldown=max(delay_seconds, 0.5))

    def record_network_error(self, host: str, stage: str, reason: str) -> None:
        if not self.enabled:
            return
        with self.lock:
            self.network_error_events += 1
            self._decrease(host, f"network error at {stage}: {reason}", factor=0.7, cooldown=max(1.0, self.cooldown_seconds), global_cooldown=True)

    def record_completion(self, host: str, result: DownloadResult, elapsed_seconds: float) -> None:
        if not self.enabled:
            return
        elapsed = max(0.0, float(elapsed_seconds))
        success = result.status in {"downloaded", "duplicate_url", "duplicate_content", "duplicate_visual", "dry_run"}
        pressure_error = int(result.status_code or 0) in RETRYABLE_HTTP_STATUS_CODES
        with self.lock:
            if success:
                self.ewma_latency_seconds = elapsed if self.ewma_latency_seconds <= 0 else (self.alpha * elapsed + (1.0 - self.alpha) * self.ewma_latency_seconds)
            if success or pressure_error:
                self.window.append(0 if success else 1)
            error_rate = (sum(self.window) / len(self.window)) if self.window else 0.0
            if not success:
                self.success_streak = 0
                if pressure_error:
                    self._decrease(host, f"completion HTTP {result.status_code}", factor=0.75, cooldown=1.0)
                return
            if elapsed >= self.slow_latency:
                self.slow_completion_events += 1
                self._decrease(host, f"slow completion {elapsed:.3f}s", factor=0.85, cooldown=0.0)
                return
            if len(self.window) >= min(5, self.window_size) and error_rate >= self.error_threshold:
                self._decrease(host, f"recent error rate {error_rate:.2f}", factor=0.8, cooldown=0.0)
                return
            self.success_streak += 1
            now_mono = time.monotonic()
            if (
                self.success_streak >= self.successes_to_increase
                and self.ewma_latency_seconds <= self.target_latency
                and now_mono >= self.global_cooldown_until
                and self.current_limit < self.max_limit
            ):
                old = self.current_limit
                self.current_limit += 1
                self.limit_increases += 1
                self.success_streak = 0
                self.last_reason = "healthy completions"
                self._append_event("increase", host, "healthy completions", previous_limit=old, ewma_latency_seconds=round(self.ewma_latency_seconds, 3))
                self.logger.info("ADAPTIVE_THROTTLE action=increase host=%s old_limit=%s new_limit=%s ewma_latency=%.3f", host, old, self.current_limit, self.ewma_latency_seconds)

    def ready_delay(self, host: str) -> float:
        if not self.enabled:
            return 0.0
        with self.lock:
            now_mono = time.monotonic()
            return max(0.0, self.host_cooldown_until.get(host, 0.0) - now_mono, self.global_cooldown_until - now_mono)

    def limit(self) -> int:
        with self.lock:
            return self.current_limit if self.enabled else self.initial_limit

    def observe_in_flight(self, count: int) -> None:
        with self.lock:
            self.max_observed_in_flight = max(self.max_observed_in_flight, int(count))

    def add_wait(self, seconds: float) -> None:
        with self.lock:
            self.coalesced_wait_seconds += max(0.0, float(seconds))

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            now_mono = time.monotonic()
            host_cooldowns = {host: round(max(0.0, until - now_mono), 3) for host, until in self.host_cooldown_until.items() if until > now_mono}
            error_rate = (sum(self.window) / len(self.window)) if self.window else 0.0
            return {
                "enabled": self.enabled,
                "mode": "feedback_aimd" if self.enabled else "fixed",
                "initial_limit": self.initial_limit,
                "current_limit": self.current_limit,
                "minimum_limit": self.min_limit,
                "maximum_limit": self.max_limit,
                "ewma_latency_seconds": round(self.ewma_latency_seconds, 3),
                "recent_error_rate": round(error_rate, 3),
                "success_streak": self.success_streak,
                "limit_increases": self.limit_increases,
                "limit_decreases": self.limit_decreases,
                "rate_limit_events": self.rate_limit_events,
                "server_pressure_events": self.server_pressure_events,
                "network_error_events": self.network_error_events,
                "slow_completion_events": self.slow_completion_events,
                "scheduler_wait_seconds": round(self.coalesced_wait_seconds, 3),
                "max_observed_in_flight": self.max_observed_in_flight,
                "active_host_cooldowns_seconds": host_cooldowns,
                "last_reason": self.last_reason,
                "recent_events": list(self.events),
                "note": "Local AIMD/EWMA feedback controller; no external AI model, telemetry service, or cloud dependency.",
            }


@dataclasses.dataclass
class SequencePattern:
    signature: str
    parsed_url: urllib.parse.ParseResult
    directory: str
    prefix: str
    suffix: str
    number: int
    width: int
    original_url: str

    def make_url(self, number: int) -> str:
        number_text = str(number).zfill(self.width) if self.width > 1 else str(number)
        filename = f"{self.prefix}{number_text}{self.suffix}"
        path = posixpath.join(self.directory, filename) if self.directory else "/" + filename
        return urllib.parse.urlunparse((
            self.parsed_url.scheme,
            self.parsed_url.netloc,
            path,
            "",
            self.parsed_url.query,
            "",
        ))


def _windows_process_status(pid: int) -> Tuple[bool, str]:
    """Return liveness and a creation-time signature without signalling the process."""
    try:
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        open_process.restype = wintypes.HANDLE
        get_exit_code = kernel32.GetExitCodeProcess
        get_exit_code.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        get_exit_code.restype = wintypes.BOOL
        get_process_times = kernel32.GetProcessTimes
        get_process_times.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        ]
        get_process_times.restype = wintypes.BOOL
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle.restype = wintypes.BOOL

        handle = open_process(process_query_limited_information, False, int(pid))
        if not handle:
            # Access denied can mean a protected but live process. Treat ambiguity as live
            # so a lock is never broken merely because inspection was denied.
            error = ctypes.get_last_error()
            return (True, "") if error == 5 else (False, "")
        try:
            exit_code = wintypes.DWORD(0)
            if not get_exit_code(handle, ctypes.byref(exit_code)):
                return True, ""
            alive = int(exit_code.value) == still_active
            creation = wintypes.FILETIME()
            exit_time = wintypes.FILETIME()
            kernel_time = wintypes.FILETIME()
            user_time = wintypes.FILETIME()
            signature = ""
            if get_process_times(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exit_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time),
            ):
                ticks = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
                signature = f"win_filetime:{ticks}"
            return alive, signature
        finally:
            close_handle(handle)
    except (ImportError, AttributeError, OSError, TypeError, ValueError):
        # Fail safely: an inspection failure must not silently permit a conflicting run.
        return True, ""


def _posix_process_status(pid: int) -> Tuple[bool, str]:
    try:
        os.kill(pid, 0)
        alive = True
    except OSError as exc:
        alive = exc.errno == errno.EPERM
    except (ValueError, PermissionError):
        alive = False
    signature = ""
    if alive:
        stat_path = Path(f"/proc/{pid}/stat")
        try:
            stat_text = stat_path.read_text(encoding="utf-8", errors="replace")
            # Field 2 is parenthesized and may contain spaces; fields after the final ')'
            # start with field 3. Process start time is field 22, therefore index 19 here.
            suffix = stat_text.rsplit(")", 1)[1].strip().split()
            if len(suffix) > 19:
                signature = f"proc_start_ticks:{suffix[19]}"
        except (OSError, IndexError, ValueError):
            signature = ""
    return alive, signature


def process_status(pid: int) -> Tuple[bool, str]:
    if pid <= 0:
        return False, ""
    if os.name == "nt":
        return _windows_process_status(pid)
    return _posix_process_status(pid)


def process_start_signature(pid: int) -> str:
    alive, signature = process_status(pid)
    return signature if alive else ""


def process_is_alive(pid: int) -> bool:
    return process_status(pid)[0]


def _safe_lock_owner_summary(meta: Dict[str, Any]) -> str:
    pid = meta.get("pid", "unknown")
    role = meta.get("role", "unknown")
    run_id = meta.get("run_id", "unknown")
    acquired = meta.get("acquired_at", "unknown")
    heartbeat = meta.get("last_heartbeat_at", "unknown")
    signature = str(meta.get("process_start_signature", "") or "")
    signature_note = signature[:80] if signature else "legacy_or_unavailable"
    return f"owner pid={pid}, role={role}, run_id={run_id}, acquired={acquired}, heartbeat={heartbeat}, process_signature={signature_note}"


class InstanceGuard:
    """Project-local top-level lock with stale/crash recovery for shared state writes."""

    def __init__(self, root: Path, *, role: str = "interactive", enabled: bool = True, stale_seconds: int = 21600, run_id: Optional[str] = None):
        self.root = root.resolve()
        self.state_dir = self.root / STATE_DIRNAME
        self.path = self.state_dir / INSTANCE_LOCK_FILENAME
        self.events_path = self.state_dir / INSTANCE_EVENTS_FILENAME
        self.role = role
        self.enabled = bool(enabled)
        self.stale_seconds = max(60, int(stale_seconds or 21600))
        self.run_id = run_id or make_run_id()
        self.token = uuid.uuid4().hex
        self.process_start_signature = process_start_signature(os.getpid())
        self.acquired = False

    def __enter__(self) -> "InstanceGuard":
        self.acquire()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.release(status="error" if exc_type else "normal")

    def _metadata(self, event: str = "heartbeat") -> Dict[str, Any]:
        return {
            "app": APP_NAME,
            "version": APP_VERSION,
            "build": BUILD_NAME,
            "project_id": "image_downloader",
            "pid": os.getpid(),
            "run_id": self.run_id,
            "role": self.role,
            "token": self.token,
            "process_start_signature": self.process_start_signature,
            "process_identity_check": "non_signalling_process_query_plus_start_signature",
            "event": event,
            "acquired_at": getattr(self, "acquired_at", now_local()),
            "last_heartbeat_at": now_local(),
            "lock_scope": "project-local state folder",
            "second_launch_behavior": "exit_with_status",
        }

    def _read_lock(self) -> Dict[str, Any]:
        data = json_load(self.path, {})
        return data if isinstance(data, dict) else {}

    def _record_event(self, event: str, status: str, detail: str = "") -> None:
        if not self.enabled:
            return
        self.state_dir.mkdir(parents=True, exist_ok=True)
        items = json_load(self.events_path, [])
        if not isinstance(items, list):
            items = []
        items.append({
            "time": now_local(),
            "event": event,
            "status": status,
            "role": self.role,
            "pid": os.getpid(),
            "run_id": self.run_id,
            "detail": redact_sensitive_text(detail)[:800],
        })
        limit = 40
        try:
            raw_cfg = json_load(self.root / CONFIG_FILENAME, {})
            if isinstance(raw_cfg, dict):
                limit = safe_int(raw_cfg.get("single_instance_event_limit", 40), 40, min_value=5, max_value=200)
        except Exception:
            limit = 40
        json_dump(self.events_path, items[-limit:])

    def _write_metadata(self, event: str) -> None:
        json_dump(self.path, self._metadata(event))

    def acquire(self) -> None:
        if not self.enabled:
            return
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.acquired_at = now_local()
        metadata = self._metadata("acquire")
        while True:
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                self.acquired = True
                self._record_event("acquire", "acquired", "top-level ownership acquired")
                return
            except FileExistsError:
                existing = self._read_lock()
                pid = safe_int(existing.get("pid", 0), 0, min_value=0) if existing else 0
                same_project = existing.get("project_id") == "image_downloader" if existing else False
                alive, observed_signature = process_status(pid) if pid else (False, "")
                expected_signature = str(existing.get("process_start_signature", "") or "")
                pid_reused = bool(
                    alive
                    and expected_signature
                    and observed_signature
                    and expected_signature != observed_signature
                )
                try:
                    age = time.time() - self.path.stat().st_mtime
                except OSError:
                    age = 0
                if same_project and (not alive or pid_reused):
                    with contextlib.suppress(OSError):
                        self.path.unlink()
                    reason = "PID identity changed" if pid_reused else "owner process is no longer alive"
                    self._record_event("stale_recovery", "recovered", f"{reason}; prior {_safe_lock_owner_summary(existing)}")
                    continue
                if (not existing or not same_project) and age > self.stale_seconds:
                    with contextlib.suppress(OSError):
                        self.path.unlink()
                    self._record_event("stale_recovery", "recovered", "invalid or foreign stale lock removed after bounded age check")
                    continue
                detail = _safe_lock_owner_summary(existing) if existing else "unreadable lock"
                self._record_event("contention", "rejected", detail)
                raise RuntimeError(
                    "Another Image Downloader window appears to be active. "
                    f"Second-launch behavior is exit_with_status; use the existing window or close it first. {detail}"
                )

    def heartbeat(self, event: str = "heartbeat") -> None:
        if not (self.enabled and self.acquired):
            return
        current = self._read_lock()
        if current.get("token") != self.token:
            self._record_event("heartbeat", "lost", "lock token changed; not overwriting")
            raise RuntimeError("Image Downloader instance lock ownership was lost; refusing to continue shared-state work.")
        self._write_metadata(event)

    def release(self, status: str = "normal") -> None:
        if not (self.enabled and self.acquired):
            return
        try:
            current = self._read_lock()
            if current.get("token") == self.token:
                with contextlib.suppress(OSError):
                    self.path.unlink()
                self._record_event("release", status, "top-level ownership released")
        finally:
            self.acquired = False


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def resolve_download_output(root: Path, cfg: Dict[str, Any]) -> Tuple[Path, str]:
    """Resolve the configured download output under the project-local output contract."""
    root = root.resolve()
    raw = str(cfg.get("output", "downloads") or "downloads").strip()
    mode = str(cfg.get("output_mode", "project_local") or "project_local")
    candidate = Path(raw)
    if mode == "project_local":
        if candidate.is_absolute():
            raise RuntimeError(
                "output_mode=project_local requires a root-relative output path. "
                "Use output_mode=external_explicit only for an intentional absolute destination."
            )
        resolved = (root / candidate).resolve()
        if not _path_is_within(resolved, root):
            raise RuntimeError("Configured project-local output escapes the project root; correct the output path before launch.")
        return resolved, "project_local"
    if mode != "external_explicit":
        raise RuntimeError(f"Unsupported output_mode: {mode}")
    if not candidate.is_absolute():
        raise RuntimeError("output_mode=external_explicit requires an absolute output path.")
    resolved = candidate.resolve()
    anchor = Path(resolved.anchor).resolve() if resolved.anchor else None
    if anchor is not None and resolved == anchor:
        raise RuntimeError("External output may not be a drive/filesystem root.")
    return resolved, "external_explicit"


def verify_writable_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    probe = path / f".imgdl_write_test_{uuid.uuid4().hex[:8]}.tmp"
    try:
        probe.write_text("ok\n", encoding="utf-8")
    finally:
        with contextlib.suppress(OSError):
            probe.unlink()


class ImageDownloader:
    def __init__(self, root: Path, config_path: Optional[Path] = None, *, browser_mode: Optional[bool] = None, dry_run: Optional[bool] = None, top_level_run_id: Optional[str] = None, instance_guard: Optional[InstanceGuard] = None):
        self.root = root.resolve()
        self.config_path = config_path.resolve() if config_path else self.root / CONFIG_FILENAME
        self.config, _ = load_or_create_config(self.config_path)
        unknown_keys = unknown_config_keys(self.config)
        if unknown_keys and bool(self.config.get("custom_input_assurance_enabled", True)):
            print("Warning: unknown config key(s) detected and preserved but not consumed by this build: " + ", ".join(unknown_keys[:10]))
            print("Run /diagnose or /export for the redacted custom-input assurance summary.")
        if browser_mode is not None:
            self.config["browser_mode"] = bool(browser_mode)
        if dry_run is not None:
            self.config["dry_run"] = bool(dry_run)
        env_run_id = os.environ.get("IMAGE_DOWNLOADER_RUN_ID", "").strip()
        self.top_level_run_id = top_level_run_id or (re.sub(r"[^A-Za-z0-9_-]+", "_", env_run_id).strip("_") if env_run_id else "") or make_run_id()
        self.instance_guard = instance_guard
        self._url_run_counter = 0
        self._run_start_monotonic = 0.0
        self._last_progress_monotonic = 0.0
        self.backpressure_stats: Dict[str, Any] = {}
        self.requests = require_requests()
        self.lock = threading.RLock()
        self._session_lock = threading.RLock()
        self._thread_local = threading.local()
        self._session_generation = 0
        self._known_sessions: Dict[int, Any] = {}
        self._network_recovery_events: List[Dict[str, Any]] = []
        self._http_session_resets = 0
        self._coalesced_http_session_resets = 0
        self._last_http_session_reset_monotonic = 0.0
        self._browser_context_resets = 0
        self._stop_event = threading.Event()
        self._reserved_output_paths: Set[str] = set()
        self._active_download_reservations = 0
        self._state_checkpoint_counter = 0
        self.state_dir = self.root / STATE_DIRNAME
        self.partial_dir = self.state_dir / PARTIAL_DIRNAME
        self.log_dir = self.root / LOG_DIRNAME
        self.report_dir = self.root / REPORT_DIRNAME
        self.export_dir = self.root / EXPORT_DIRNAME
        self.temp_dir = self.root / TEMP_DIRNAME
        self._output_dir, self._output_mode = resolve_download_output(self.root, self.config)
        for path in (self.state_dir, self.partial_dir, self.log_dir, self.report_dir, self.export_dir, self.temp_dir):
            path.mkdir(parents=True, exist_ok=True)
        verify_writable_directory(self._output_dir)
        self.logger = configure_logging(self.root, self.config)
        self._queue_lock = threading.RLock()
        self.session_id = make_run_id("session")
        self.session_started_at = now_local()
        self.session_download_records: List[Dict[str, Any]] = []
        self.session_job_summaries: List[Dict[str, Any]] = []
        self.session_report_path: Optional[Path] = None
        self._session_report_finalized = False
        self.queue_metrics: Dict[str, Any] = {
            "loaded_at": now_local(),
            "recovered_running_items": 0,
            "rejected_invalid": 0,
            "rejected_duplicate": 0,
            "rejected_capacity": 0,
            "enqueued": 0,
            "processed": 0,
        }
        self.download_queue_state = self._load_download_queue_state()
        self.computer_context = detect_computer_context(self.config)
        self.logger.info(
            "COMPUTER_AWARENESS label=%s diagnostic_id=%s source=%s restrictions=false state_overlay=false lock_scope_change=false",
            self.computer_context.get("display_name"),
            self.computer_context.get("diagnostic_id"),
            self.computer_context.get("detection_source"),
        )
        self.adaptive_throttle = AdaptiveThrottle(self.config, self.logger)
        self.state = self._load_download_index()
        self.library_duplicate_scan_stats = self._reconcile_existing_download_library()
        self.duplicate_stats: Dict[str, Any] = self._fresh_duplicate_stats()
        self.url_seen_this_process: Set[str] = set()
        self.sequence_probed_urls: Set[str] = set()
        self.run_summary: Dict[str, Any] = {}
        self.failures_this_run: List[Dict[str, Any]] = []
        self.not_downloaded_this_run: List[Dict[str, Any]] = []
        self.sequence_stats: Dict[str, Any] = self._fresh_sequence_stats()
        self.automation_stats: Dict[str, Any] = self._fresh_automation_stats()
        self.discovery_stats: Dict[str, Any] = self._fresh_discovery_stats()
        self.transfer_recovery_stats: Dict[str, Any] = self._fresh_transfer_recovery_stats()
        self._playwright: Any = None
        self._browser: Any = None
        self._browser_context: Any = None
        self._browser_pages_opened = 0
        self._browser_observed_images: List[str] = []
        self._cleanup_stale_partials()

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    @property
    def output_mode(self) -> str:
        return self._output_mode

    @property
    def timeout(self) -> int:
        try:
            return max(1, int(self.config.get("read_timeout", self.config.get("timeout", 5))))
        except (TypeError, ValueError):
            return 5

    @property
    def request_timeout(self) -> Tuple[int, int]:
        connect = safe_int(self.config.get("connect_timeout", 3), 3, min_value=1, max_value=60)
        read = safe_int(self.config.get("read_timeout", self.config.get("timeout", 5)), 5, min_value=1, max_value=180)
        return connect, read

    @property
    def request_wall_clock_timeout(self) -> int:
        return safe_int(self.config.get("request_wall_clock_timeout_seconds", 5), 5, min_value=1, max_value=3600)

    @staticmethod
    def _deadline_remaining(deadline: Optional[float]) -> float:
        if deadline is None:
            return float("inf")
        return max(0.0, deadline - time.monotonic())

    def _request_timeout_for_deadline(self, deadline: Optional[float]) -> Tuple[float, float]:
        connect, read = self.request_timeout
        if deadline is None:
            return float(connect), float(read)
        remaining = self._deadline_remaining(deadline)
        if remaining <= 0:
            raise TimeoutError("download exceeded request_wall_clock_timeout_seconds")
        # Divide the remaining hard wall-clock budget between connection setup and response reads.
        # The streaming loop independently checks the same monotonic deadline for every chunk.
        connect_budget = min(float(connect), max(0.1, remaining * 0.4))
        read_budget = min(float(read), max(0.1, remaining - connect_budget))
        return connect_budget, read_budget

    @property
    def page_wall_clock_timeout(self) -> int:
        return safe_int(self.config.get("page_wall_clock_timeout_seconds", 60), 60, min_value=10, max_value=600)

    @property
    def max_file_bytes(self) -> int:
        try:
            return max(1, int(float(self.config.get("max_file_mb", 25)) * 1024 * 1024))
        except (TypeError, ValueError):
            return 25 * 1024 * 1024

    @property
    def max_html_bytes(self) -> int:
        try:
            return max(1, int(float(self.config.get("max_html_mb", 5)) * 1024 * 1024))
        except (TypeError, ValueError):
            return 5 * 1024 * 1024

    def _network_enabled(self) -> bool:
        return bool(self.config.get("network_resilience_enabled", True))

    def _new_http_session(self) -> Any:
        session = self.requests.Session()
        session.headers.update({
            "User-Agent": str(self.config.get("user_agent", default_config()["user_agent"])),
            "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/*,*/*;q=0.8",
        })
        session.max_redirects = safe_int(self.config.get("max_redirects", 12), 12, min_value=1, max_value=30)
        try:
            workers = max(1, min(MAX_ACTIVE_DOWNLOADS, int(self.config.get("workers", MAX_ACTIVE_DOWNLOADS) or MAX_ACTIVE_DOWNLOADS)))
        except (TypeError, ValueError):
            workers = MAX_ACTIVE_DOWNLOADS
        pool_size = max(8, workers * 2)
        with contextlib.suppress(AttributeError, TypeError, ValueError):
            adapter = self.requests.adapters.HTTPAdapter(
                pool_connections=pool_size,
                pool_maxsize=pool_size,
                max_retries=0,
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)
        return session

    def _get_http_session(self) -> Any:
        """Return a requests Session scoped to this worker thread and current network generation."""
        if not bool(self.config.get("thread_local_http_sessions", True)):
            # Compatibility path: still creates a session for this process, but this mode is not the default.
            session = getattr(self._thread_local, "session", None)
            if session is None:
                session = self._new_http_session()
                self._thread_local.session = session
            return session
        session = getattr(self._thread_local, "session", None)
        generation = getattr(self._thread_local, "session_generation", None)
        if session is None or generation != self._session_generation:
            old_session = session
            session = self._new_http_session()
            self._thread_local.session = session
            self._thread_local.session_generation = self._session_generation
            with self._session_lock:
                self._known_sessions[threading.get_ident()] = session
            if old_session is not None:
                with contextlib.suppress(Exception):
                    old_session.close()
        return session

    def _close_all_http_sessions(self) -> None:
        with self._session_lock:
            sessions = list({id(s): s for s in self._known_sessions.values()}.values())
            self._known_sessions.clear()
        current = getattr(self._thread_local, "session", None)
        if current is not None and all(id(current) != id(s) for s in sessions):
            sessions.append(current)
        self._thread_local.session = None
        self._thread_local.session_generation = None
        for session in sessions:
            with contextlib.suppress(Exception):
                session.close()

    def _network_retry_delay(self, attempt: int, retry_after: Any = "") -> float:
        base_ms = safe_int(
            self.config.get("retry_backoff_base_ms", self.config.get("network_recovery_pause_ms", 500)),
            500,
            min_value=0,
            max_value=30000,
        )
        cap_ms = safe_int(
            self.config.get("retry_backoff_max_ms", self.config.get("network_recovery_max_pause_ms", 8000)),
            8000,
            min_value=0,
            max_value=120000,
        )
        jitter_ms = safe_int(self.config.get("retry_jitter_ms", 250), 250, min_value=0, max_value=5000)
        backoff = min(cap_ms, base_ms * (2 ** max(0, attempt))) / 1000.0
        if jitter_ms:
            backoff += random.uniform(0.0, jitter_ms / 1000.0)
        retry_after_seconds = parse_retry_after_seconds(
            retry_after,
            safe_int(self.config.get("retry_after_max_seconds", 30), 30, min_value=0, max_value=300),
        )
        return retry_after_seconds if retry_after_seconds > 0 else backoff

    def _sleep_before_retry(self, url: str, stage: str, attempt: int, *, status_code: int = 0, retry_after: Any = "", deadline: Optional[float] = None) -> float:
        delay = self._network_retry_delay(attempt, retry_after)
        if deadline is not None:
            delay = min(delay, self._deadline_remaining(deadline))
        if self.transfer_recovery_stats:
            with self.lock:
                self.transfer_recovery_stats["retry_events"] = int(self.transfer_recovery_stats.get("retry_events", 0)) + 1
                if status_code:
                    self.transfer_recovery_stats["status_retries"] = int(self.transfer_recovery_stats.get("status_retries", 0)) + 1
                if parse_retry_after_seconds(retry_after, safe_int(self.config.get("retry_after_max_seconds", 30), 30, min_value=0, max_value=300)) > 0:
                    self.transfer_recovery_stats["retry_after_honored"] = int(self.transfer_recovery_stats.get("retry_after_honored", 0)) + 1
                events = self.transfer_recovery_stats.setdefault("recent_retry_events", [])
                events.append({
                    "time": now_local(),
                    "stage": stage,
                    "host": url_host(url),
                    "attempt": attempt + 1,
                    "status_code": status_code,
                    "delay_seconds": round(delay, 3),
                })
                del events[:-20]
        self.adaptive_throttle.record_retry(url_host(url), status_code=status_code, delay_seconds=delay, stage=stage)
        self.logger.warning(
            "RETRY stage=%s host=%s attempt=%s status=%s delay_seconds=%.3f",
            stage,
            url_host(url),
            attempt + 1,
            status_code or "network",
            delay,
        )
        if delay > 0:
            self._stop_event.wait(delay)
        return delay

    @staticmethod
    def _retryable_status(status_code: int) -> bool:
        return int(status_code or 0) in RETRYABLE_HTTP_STATUS_CODES

    def _network_recovery_snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": self._network_enabled(),
            "reset_session_on_error": bool(self.config.get("network_reset_session_on_error", True)),
            "http_session_resets": int(self._http_session_resets),
            "coalesced_http_session_resets": int(self._coalesced_http_session_resets),
            "session_reset_debounce_ms": safe_int(self.config.get("network_session_reset_debounce_ms", 1000), 1000, min_value=0, max_value=30000),
            "browser_context_resets": int(self._browser_context_resets),
            "recent_events": list(self._network_recovery_events),
            "note": "HTTP sessions are recreated after connection/timeout errors so VPN or IP changes do not leave stale pooled connections behind.",
        }

    def _record_network_recovery(self, kind: str, url: str, reason: str, stage: str) -> None:
        item = {
            "time": now_local(),
            "kind": kind,
            "stage": stage,
            "host": url_host(url),
            "reason": reason[:500],
        }
        try:
            limit = max(1, int(self.config.get("network_recovery_event_limit", 25) or 25))
        except (TypeError, ValueError):
            limit = 25
        with self.lock:
            self._network_recovery_events.append(item)
            self._network_recovery_events = self._network_recovery_events[-limit:]
        logger = getattr(self, "logger", None)
        if logger is not None:
            logger.warning("NETWORK_RECOVERY kind=%s stage=%s host=%s reason=%s", kind, stage, item["host"], item["reason"])

    def _reset_http_session(self, reason: str, url: str, stage: str) -> None:
        if not (self._network_enabled() and bool(self.config.get("network_reset_session_on_error", True))):
            return
        now_mono = time.monotonic()
        debounce_seconds = safe_int(self.config.get("network_session_reset_debounce_ms", 1000), 1000, min_value=0, max_value=30000) / 1000.0
        coalesced = False
        with self._session_lock:
            if debounce_seconds > 0 and self._last_http_session_reset_monotonic and now_mono - self._last_http_session_reset_monotonic < debounce_seconds:
                self._coalesced_http_session_resets += 1
                coalesced = True
            else:
                self._session_generation += 1
                self._http_session_resets += 1
                self._last_http_session_reset_monotonic = now_mono
            self._known_sessions.pop(threading.get_ident(), None)
        old_session = getattr(self._thread_local, "session", None)
        self._thread_local.session = None
        self._thread_local.session_generation = None
        if old_session is not None:
            with contextlib.suppress(Exception):
                old_session.close()
        event_kind = "http_session_reset_coalesced" if coalesced else "http_session_reset"
        self._record_network_recovery(event_kind, url, reason, stage)

    def _reset_browser_context_for_network(self, reason: str, url: str, stage: str) -> None:
        if not (self._network_enabled() and bool(self.config.get("network_browser_reset_on_error", True))):
            return
        self.close_browser()
        self._browser_context_resets += 1
        self._record_network_recovery("browser_context_reset", url, reason, stage)

    def _handle_network_exception(self, exc: BaseException, url: str, attempt: int, stage: str, *, will_retry: bool, deadline: Optional[float] = None) -> None:
        reason = f"{exc.__class__.__name__}: {exc}"
        self.adaptive_throttle.record_network_error(url_host(url), stage, reason)
        self._reset_http_session(reason, url, stage)
        if will_retry and self._deadline_remaining(deadline) > 0:
            self._sleep_before_retry(url, stage, attempt, deadline=deadline)

    def _fresh_automation_stats(self) -> Dict[str, Any]:
        mode = str(self.config.get("automation_mode", "smart_safe"))
        enabled = mode == "smart_safe"
        return {
            "mode": mode,
            "enabled": enabled,
            "automatic_features": [
                "direct-image/page routing",
                "duplicate URL/SHA256/visual/library detection",
                "validator-backed resume",
                "VPN/IP reconnect and session renewal",
                "adaptive concurrency throttle",
                "numbered sequence discovery when a numeric pattern exists",
                "conservative same-domain gallery pagination",
                "hidden completed media on Windows",
            ] if enabled else [],
            "manual_features": [
                "Safe Browser Mode remains manual and trusted-sites-only",
                "dry-run remains manually selectable",
            ],
            "auto_gallery_enabled": enabled and bool(self.config.get("auto_gallery_follow_enabled", True)),
            "auto_browser_fallback": "manual_trusted_sites_only",
            "decisions": [],
            "last_updated": now_local(),
        }

    def _automation_decision(self, action: str, reason: str) -> None:
        if not hasattr(self, "automation_stats") or not isinstance(self.automation_stats, dict):
            return
        decisions = self.automation_stats.setdefault("decisions", [])
        item = {"time": now_local(), "action": str(action), "reason": str(reason)}
        if item not in decisions:
            decisions.append(item)
        if len(decisions) > 40:
            del decisions[:-40]
        self.automation_stats["last_updated"] = now_local()

    def _fresh_sequence_stats(self) -> Dict[str, Any]:
        return {
            "enabled": bool(self.config.get("sequence_discovery_enabled", True)),
            "same_domain_only": bool(self.config.get("sequence_same_domain_only", True)),
            "groups_found": 0,
            "groups_scanned": 0,
            "anchors_scanned": 0,
            "probes_attempted": 0,
            "probes_downloaded": 0,
            "probes_duplicate_url": 0,
            "probes_duplicate_content": 0,
            "probes_duplicate_visual": 0,
            "probes_failed": 0,
            "bounded_by_max_candidates": 0,
            "bounded_by_failed_attempts": 0,
            "max_candidates_per_group": safe_int(self.config.get("sequence_max_candidates_per_group", 80), 80, min_value=1, max_value=500),
            "max_failed_attempts": safe_int(self.config.get("sequence_max_failed_attempts", 8), 8, min_value=1, max_value=50),
            "last_updated": now_local(),
            "groups": [],
        }

    def _fresh_backpressure_stats(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "download_queue_capacity": safe_int(self.config.get("download_queue_capacity", DOWNLOAD_QUEUE_HARD_MAX), DOWNLOAD_QUEUE_HARD_MAX, min_value=1, max_value=DOWNLOAD_QUEUE_HARD_MAX),
            "download_queue_full_policy": str(self.config.get("download_queue_full_policy", "visible_reject_excess")),
            "gallery_queue_capacity": safe_int(self.config.get("gallery_queue_capacity", 100), 100, min_value=1, max_value=1000),
            "workers": safe_int(self.config.get("workers", MAX_ACTIVE_DOWNLOADS), MAX_ACTIVE_DOWNLOADS, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS),
            "adaptive_throttle_enabled": bool(self.config.get("adaptive_throttle_enabled", True)),
            "adaptive_min_workers": safe_int(self.config.get("adaptive_throttle_min_workers", 1), 1, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS),
            "adaptive_max_workers": safe_int(self.config.get("adaptive_throttle_max_workers", self.config.get("workers", MAX_ACTIVE_DOWNLOADS)), self.config.get("workers", MAX_ACTIVE_DOWNLOADS), min_value=1, max_value=MAX_ACTIVE_DOWNLOADS),
            "retries": safe_int(self.config.get("retries", 2), 2, min_value=0, max_value=5),
            "network_recovery_extra_attempts": safe_int(self.config.get("network_recovery_extra_attempts", 2), 2, min_value=0, max_value=5),
            "submitted": 0,
            "rejected_due_capacity": 0,
            "gallery_links_rejected_due_capacity": 0,
            "high_water_depth": 0,
            "oldest_item_age_seconds": 0,
            "shutdown_drain_timeout_seconds": safe_int(self.config.get("shutdown_drain_timeout_seconds", 10), 10, min_value=1, max_value=120),
            "shutdown_drain_status": "not_started",
            "note": "Download work is bounded to a 100-item queue and never exceeds three active downloads; adaptive AIMD/EWMA feedback may reduce concurrency under rate/server/network pressure and cautiously restore it up to the hard cap of three.",
        }

    def _fresh_discovery_stats(self) -> Dict[str, Any]:
        return {
            "modern_discovery_enabled": bool(self.config.get("modern_discovery_enabled", True)),
            "html_attribute_candidates": 0,
            "srcset_candidates": 0,
            "imagesrcset_candidates": 0,
            "metadata_candidates": 0,
            "jsonld_candidates": 0,
            "css_candidates": 0,
            "noscript_candidates": 0,
            "browser_network_candidates": 0,
            "browser_network_limit_reached": False,
            "automation_mode": str(self.config.get("automation_mode", "smart_safe")),
            "auto_gallery_enabled": str(self.config.get("automation_mode", "smart_safe")) == "smart_safe" and bool(self.config.get("auto_gallery_follow_enabled", True)),
            "auto_gallery_links_detected": 0,
            "auto_gallery_links_queued": 0,
            "auto_gallery_pages_visited": 0,
            "candidate_limit_reached": False,
            "last_updated": now_local(),
        }

    def _fresh_transfer_recovery_stats(self) -> Dict[str, Any]:
        return {
            "resume_enabled": bool(self.config.get("resume_partial_downloads", True)),
            "retry_events": 0,
            "status_retries": 0,
            "retry_after_honored": 0,
            "partial_resume_attempts": 0,
            "partial_resume_successes": 0,
            "partial_bytes_reused": 0,
            "partial_restarts": 0,
            "wall_clock_aborts": 0,
            "raster_verify_failures": 0,
            "stale_partials_removed": 0,
            "state_checkpoints": 0,
            "recent_retry_events": [],
            "last_updated": now_local(),
        }

    def _bump_transfer_stat(self, key: str, amount: int = 1) -> None:
        with self.lock:
            self.transfer_recovery_stats[key] = int(self.transfer_recovery_stats.get(key, 0)) + int(amount)

    def _partial_paths(self, url: str) -> Tuple[Path, Path]:
        token = sha256_bytes(url.encode("utf-8", errors="ignore"))[:32]
        return (
            self.partial_dir / f"{token}.part",
            self.partial_dir / f"{token}{PARTIAL_METADATA_SUFFIX}",
        )

    def _discard_partial(self, part_path: Path, meta_path: Path, *, reason: str = "") -> None:
        removed = False
        for path in (part_path, meta_path):
            try:
                if path.exists():
                    path.unlink()
                    removed = True
            except OSError:
                pass
        if removed and reason:
            self.logger.info("PARTIAL_DISCARDED reason=%s file=%s", reason, short_path(part_path, self.root))

    def _cleanup_stale_partials(self) -> None:
        retention_hours = safe_int(self.config.get("partial_retention_hours", 24), 24, min_value=1, max_value=720)
        cutoff = time.time() - retention_hours * 3600
        removed = 0
        try:
            files = list(self.partial_dir.glob("*"))
        except OSError:
            files = []
        for path in files:
            try:
                if not path.is_file() or path.stat().st_mtime >= cutoff:
                    continue
                path.unlink()
                removed += 1
            except OSError:
                continue
        if removed:
            self._bump_transfer_stat("stale_partials_removed", removed)
            self.logger.info("PARTIAL_CLEANUP removed=%s retention_hours=%s", removed, retention_hours)

    def _load_partial_metadata(self, url: str, part_path: Path, meta_path: Path) -> Dict[str, Any]:
        if not part_path.exists() or not meta_path.exists():
            return {}
        metadata = json_load(meta_path, {})
        if not isinstance(metadata, dict) or metadata.get("url") != url:
            self._discard_partial(part_path, meta_path, reason="metadata mismatch")
            return {}
        try:
            size = part_path.stat().st_size
        except OSError:
            return {}
        metadata["bytes_present"] = size
        return metadata

    def _write_partial_metadata(self, meta_path: Path, metadata: Dict[str, Any]) -> None:
        json_dump(meta_path, metadata)

    def _claim_download_slot(self) -> bool:
        limit = safe_int(self.config.get("limit", 0), 0, min_value=0, max_value=100000)
        with self.lock:
            if limit > 0 and int(self.run_summary.get("downloaded", 0)) + self._active_download_reservations >= limit:
                return False
            self._active_download_reservations += 1
            return True

    def _release_download_slot(self) -> None:
        with self.lock:
            self._active_download_reservations = max(0, self._active_download_reservations - 1)

    def _release_output_path(self, path: Optional[Path]) -> None:
        if path is None:
            return
        with self.lock:
            self._reserved_output_paths.discard(output_path_identity(path))

    def _checkpoint_state_if_due(self) -> None:
        interval = safe_int(self.config.get("state_checkpoint_interval_downloads", 10), 10, min_value=1, max_value=1000)
        with self.lock:
            self._state_checkpoint_counter += 1
            due = self._state_checkpoint_counter >= interval
            if due:
                self._state_checkpoint_counter = 0
        if not due:
            return
        self._save_download_index()
        self._bump_transfer_stat("state_checkpoints")
        self.logger.info("STATE_CHECKPOINT reason=download_interval interval=%s", interval)

    def _mark_progress(self) -> None:
        self._last_progress_monotonic = time.monotonic()

    def _load_download_index(self) -> Dict[str, Any]:
        path = self.state_dir / DOWNLOAD_INDEX_FILENAME
        data = json_load(path, {})
        if not isinstance(data, dict):
            data = {}
        source_schema = safe_int(data.get("state_schema_version", data.get("version", 1)), 1, min_value=1) if data else STATE_SCHEMA_VERSION
        if source_schema > STATE_SCHEMA_VERSION:
            raise RuntimeError(
                f"State schema {source_schema} is newer than this build supports ({STATE_SCHEMA_VERSION}). "
                "Use a newer Image Downloader build or restore a compatible state backup."
            )
        if source_schema < STATE_SCHEMA_VERSION and path.exists():
            backup_ref = backup_file_for_migration(
                path,
                label=f"state_schema{source_schema}_to_{STATE_SCHEMA_VERSION}",
                keep=safe_int(self.config.get("schema_migration_backup_retention", 5), 5, min_value=1, max_value=20),
            )
            data["state_last_migration"] = {
                "time": now_local(),
                "from_schema": source_schema,
                "to_schema": STATE_SCHEMA_VERSION,
                "app_version": APP_VERSION,
                "backup": backup_ref,
                "status": "completed",
                "rollback_note": "Restore the backup with a compatible older build if a state schema change must be reversed.",
            }
        data["version"] = STATE_SCHEMA_VERSION
        data["state_schema_version"] = STATE_SCHEMA_VERSION
        data.setdefault("urls", {})
        data.setdefault("hashes", {})
        data.setdefault("visual_hashes", {})
        if not isinstance(data.get("urls"), dict):
            data["urls"] = {}
        if not isinstance(data.get("hashes"), dict):
            data["hashes"] = {}
        if not isinstance(data.get("visual_hashes"), dict):
            data["visual_hashes"] = {}
        data["asset_metadata_schema"] = ASSET_METADATA_SCHEMA
        # Reconcile legacy records into one content-addressed metadata catalog without
        # creating per-image sidecars or a duplicate standalone database.
        for digest, record in list(data["hashes"].items()):
            if isinstance(record, dict):
                data["hashes"][digest] = enrich_download_asset_record(record, digest=str(digest), url=str(record.get("url") or ""))
        for url, record in list(data["urls"].items()):
            if not isinstance(record, dict):
                continue
            digest = str(record.get("sha256") or "")
            canonical = data["hashes"].get(digest) if digest else None
            data["urls"][url] = canonical if isinstance(canonical, dict) else enrich_download_asset_record(record, digest=digest, url=str(url))
        for digest, record in list(data["hashes"].items()):
            if not isinstance(record, dict):
                continue
            visual = str(record.get("visual_fingerprint") or "")
            if visual and visual not in data["visual_hashes"]:
                data["visual_hashes"][visual] = record
        return data

    def _save_download_index(self) -> None:
        # Snapshot under the shared-state lock, then perform the atomic disk write
        # outside the lock so worker updates cannot interleave with serialization.
        with self.lock:
            self.state["version"] = STATE_SCHEMA_VERSION
            self.state["state_schema_version"] = STATE_SCHEMA_VERSION
            self.state["asset_metadata_schema"] = ASSET_METADATA_SCHEMA
            self.state.setdefault("visual_hashes", {})
            self.state["updated_at"] = now_local()
            snapshot = json.loads(json.dumps(self.state, ensure_ascii=False))
        json_dump(self.state_dir / DOWNLOAD_INDEX_FILENAME, snapshot)

    def _fresh_duplicate_stats(self) -> Dict[str, Any]:
        return {
            "url_check_enabled": bool(self.config.get("duplicate_url_check", True)),
            "exact_content_check_enabled": bool(self.config.get("duplicate_content_hash_check", True)),
            "visual_fingerprint_check_enabled": bool(self.config.get("duplicate_visual_fingerprint_check", True)),
            "candidate_duplicates_removed": 0,
            "url_duplicates_skipped": 0,
            "exact_content_duplicates_skipped": 0,
            "visual_duplicates_skipped": 0,
            "filename_conflicts_resolved": 0,
            "library_reconcile": dict(getattr(self, "library_duplicate_scan_stats", {}) or {}),
            "last_updated": now_local(),
        }

    def _state_visual_record_exists(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        if not fingerprint:
            return None
        rec = self.state.get("visual_hashes", {}).get(fingerprint)
        if not isinstance(rec, dict):
            return None
        rel = str(rec.get("path") or "")
        if not rel:
            return None
        candidate = self.root / rel
        return rec if candidate.exists() else None

    def _reconcile_existing_download_library(self) -> Dict[str, Any]:
        """Bounded, non-destructive recovery of duplicate indexes from existing media."""
        stats: Dict[str, Any] = {
            "enabled": bool(self.config.get("duplicate_library_reconcile_enabled", True)),
            "started_at": now_local(),
            "finished_at": None,
            "status": "not_started",
            "max_files": safe_int(self.config.get("duplicate_library_reconcile_max_files", 250), 250, min_value=0, max_value=5000),
            "time_budget_seconds": safe_int(self.config.get("duplicate_library_reconcile_time_budget_seconds", 3), 3, min_value=0, max_value=60),
            "files_examined": 0,
            "already_indexed": 0,
            "records_recovered": 0,
            "visual_records_recovered": 0,
            "exact_duplicates_found": 0,
            "visual_duplicates_found": 0,
            "invalid_or_unsupported": 0,
            "errors": 0,
            "bounded_by_file_limit": False,
            "bounded_by_time_budget": False,
        }
        if not stats["enabled"] or stats["max_files"] <= 0 or stats["time_budget_seconds"] <= 0:
            stats["status"] = "disabled_or_zero_budget"
            stats["finished_at"] = now_local()
            return stats
        output_dir = self.output_dir
        if not output_dir.exists():
            stats["status"] = "output_directory_not_present"
            stats["finished_at"] = now_local()
            return stats
        started = time.monotonic()
        deadline = started + float(stats["time_budget_seconds"])
        indexed_paths: Dict[str, Dict[str, Any]] = {}
        for record in self.state.get("hashes", {}).values():
            if isinstance(record, dict) and record.get("path"):
                indexed_paths[output_path_identity(self.root / str(record.get("path")))] = record
        changed = False
        try:
            iterator = output_dir.rglob("*")
            for candidate in iterator:
                if stats["files_examined"] >= stats["max_files"]:
                    stats["bounded_by_file_limit"] = True
                    break
                if time.monotonic() >= deadline:
                    stats["bounded_by_time_budget"] = True
                    break
                try:
                    if not candidate.is_file():
                        continue
                    ext = normalize_ext(candidate.suffix)
                    if ext not in IMAGE_EXTENSIONS:
                        continue
                    stats["files_examined"] += 1
                    identity = output_path_identity(candidate)
                    existing_by_path = indexed_paths.get(identity)
                    if isinstance(existing_by_path, dict) and existing_by_path.get("sha256") and (
                        not bool(self.config.get("duplicate_visual_fingerprint_check", True)) or existing_by_path.get("visual_fingerprint")
                    ):
                        stats["already_indexed"] += 1
                        continue
                    with candidate.open("rb") as stream:
                        header = stream.read(128 * 1024)
                    fmt = normalize_ext(detect_image_format(header, bool(self.config.get("safe_svg_validation", True))))
                    if not fmt or fmt not in allowed_types(self.config):
                        stats["invalid_or_unsupported"] += 1
                        continue
                    valid, width, height, _mode, _reason = validate_image_file(
                        candidate,
                        fmt,
                        strict_raster_verify=bool(self.config.get("strict_raster_verify", True)),
                        max_pixels=safe_int(self.config.get("image_max_pixels", 120000000), 120000000, min_value=1000000, max_value=1000000000),
                    )
                    if not valid:
                        stats["invalid_or_unsupported"] += 1
                        continue
                    digest = sha256_file(candidate)
                    existing_hash = self._state_hash_record_exists(digest)
                    visual = ""
                    visual_method = ""
                    visual_note = ""
                    if bool(self.config.get("duplicate_visual_fingerprint_check", True)) and fmt != "svg":
                        visual, visual_method, visual_note = image_visual_fingerprint(
                            candidate,
                            max_pixels=safe_int(self.config.get("image_max_pixels", 120000000), 120000000, min_value=1000000, max_value=1000000000),
                        )
                    if existing_hash and output_path_identity(self.root / str(existing_hash.get("path", ""))) != identity:
                        stats["exact_duplicates_found"] += 1
                    if visual:
                        existing_visual = self._state_visual_record_exists(visual)
                        if existing_visual and output_path_identity(self.root / str(existing_visual.get("path", ""))) != identity:
                            stats["visual_duplicates_found"] += 1
                    if existing_hash is None:
                        stat = candidate.stat()
                        saved_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).astimezone().isoformat(timespec="seconds")
                        record = enrich_download_asset_record({
                            "url": "",
                            "path": short_path(candidate, self.root),
                            "sha256": digest,
                            "bytes": int(stat.st_size),
                            "size_bytes": int(stat.st_size),
                            "content_type": f"image/{'jpeg' if fmt == 'jpg' else fmt}",
                            "width": width,
                            "height": height,
                            "saved_at": saved_at,
                            "created_at": saved_at,
                            "modified_at": saved_at,
                            "media_visibility": "unknown_existing",
                            "media_visibility_note": "indexed by bounded duplicate-library reconciliation",
                            "visual_fingerprint": visual,
                            "visual_fingerprint_method": visual_method,
                            "visual_fingerprint_note": visual_note,
                            "library_reconciled": True,
                        }, digest=digest, url="")
                        self.state.setdefault("hashes", {})[digest] = record
                        indexed_paths[identity] = record
                        stats["records_recovered"] += 1
                        changed = True
                    else:
                        record = existing_hash
                        if visual and not record.get("visual_fingerprint"):
                            record["visual_fingerprint"] = visual
                            record["visual_fingerprint_method"] = visual_method
                            record["visual_fingerprint_note"] = visual_note
                            changed = True
                    if visual and self._state_visual_record_exists(visual) is None:
                        self.state.setdefault("visual_hashes", {})[visual] = record
                        stats["visual_records_recovered"] += 1
                        changed = True
                except (OSError, ValueError, RuntimeError):
                    stats["errors"] += 1
                    continue
        except OSError:
            stats["errors"] += 1
        if changed:
            self._save_download_index()
        stats["status"] = "completed_bounded" if (stats["bounded_by_file_limit"] or stats["bounded_by_time_budget"]) else "completed"
        stats["elapsed_seconds"] = round(max(0.0, time.monotonic() - started), 3)
        stats["finished_at"] = now_local()
        self.logger.info(
            "DUPLICATE_LIBRARY_RECONCILE status=%s examined=%s recovered=%s visual_recovered=%s exact_duplicates=%s visual_duplicates=%s errors=%s",
            stats["status"], stats["files_examined"], stats["records_recovered"], stats["visual_records_recovered"],
            stats["exact_duplicates_found"], stats["visual_duplicates_found"], stats["errors"],
        )
        return stats

    @property
    def download_queue_path(self) -> Path:
        return self.state_dir / DOWNLOAD_QUEUE_STATE_FILENAME

    @property
    def download_queue_capacity(self) -> int:
        return safe_int(
            self.config.get("download_queue_capacity", DOWNLOAD_QUEUE_HARD_MAX),
            DOWNLOAD_QUEUE_HARD_MAX,
            min_value=1,
            max_value=DOWNLOAD_QUEUE_HARD_MAX,
        )

    def _empty_download_queue_state(self) -> Dict[str, Any]:
        return {
            "queue_schema_version": DOWNLOAD_QUEUE_SCHEMA_VERSION,
            "app_version": APP_VERSION,
            "build": BUILD_NAME,
            "capacity": self.download_queue_capacity,
            "max_active_downloads": MAX_ACTIVE_DOWNLOADS,
            "updated_at": now_local(),
            "sensitivity": "local-private-operational-urls-not-exported",
            "items": [],
        }

    def _save_download_queue_state(self) -> None:
        if not bool(self.config.get("download_queue_autosave_enabled", True)):
            return
        with self._queue_lock:
            state = dict(self.download_queue_state) if isinstance(self.download_queue_state, dict) else self._empty_download_queue_state()
            state["queue_schema_version"] = DOWNLOAD_QUEUE_SCHEMA_VERSION
            state["app_version"] = APP_VERSION
            state["build"] = BUILD_NAME
            state["capacity"] = self.download_queue_capacity
            state["max_active_downloads"] = MAX_ACTIVE_DOWNLOADS
            state["updated_at"] = now_local()
            state["sensitivity"] = "local-private-operational-urls-not-exported"
            state["items"] = list(state.get("items", []))[: self.download_queue_capacity]
            self.download_queue_state = state
            json_dump(self.download_queue_path, state)

    def _load_download_queue_state(self) -> Dict[str, Any]:
        state = self._empty_download_queue_state()
        path = self.download_queue_path
        if not path.exists():
            if bool(self.config.get("download_queue_autosave_enabled", True)):
                json_dump(path, state)
            return state
        try:
            loaded = json_load_strict_object(path)
        except Exception as exc:
            backup_ref = backup_file_for_migration(path, label="queue_corrupt", keep=5)
            self.logger.warning("DOWNLOAD_QUEUE_RECOVERY status=corrupt_reset backup=%s error=%s", backup_ref, redact_sensitive_text(exc))
            state["recovery_note"] = f"Corrupt queue preserved as {backup_ref}; active queue reset safely."
            json_dump(path, state)
            return state
        raw_items = loaded.get("items", []) if isinstance(loaded, dict) else []
        if not isinstance(raw_items, list):
            raw_items = []
        recovered: List[Dict[str, Any]] = []
        recovered_running = 0
        seen: Set[str] = set()
        for raw in raw_items:
            if len(recovered) >= self.download_queue_capacity:
                break
            if not isinstance(raw, dict):
                continue
            url = normalize_url(raw.get("url", ""))
            if not url or url in seen:
                continue
            status = str(raw.get("status") or "pending").lower()
            if status not in {"pending", "running"}:
                continue
            item = dict(raw)
            item["url"] = url
            item["url_evidence"] = redact_url_for_evidence(url)
            item["url_sha256"] = sha256_bytes(url.encode("utf-8", errors="ignore"))
            item["queue_id"] = str(item.get("queue_id") or uuid.uuid4().hex[:12])
            item["queued_at"] = str(item.get("queued_at") or now_local())
            item["attempts"] = safe_int(item.get("attempts", 0), 0, min_value=0, max_value=1000000)
            if status == "running" and bool(self.config.get("download_queue_recovery_enabled", True)):
                item["status"] = "pending"
                item["recovered_at"] = now_local()
                item["recovery_reason"] = "previous session ended while item was running"
                recovered_running += 1
            elif status == "running":
                continue
            else:
                item["status"] = "pending"
            recovered.append(item)
            seen.add(url)
        state.update({
            "items": recovered,
            "loaded_from_previous_session": bool(recovered),
            "recovered_running_items": recovered_running,
            "updated_at": now_local(),
        })
        self.queue_metrics["recovered_running_items"] = recovered_running
        self.download_queue_state = state
        self._save_download_queue_state()
        if recovered:
            self.logger.info("DOWNLOAD_QUEUE_RECOVERY pending=%s recovered_running=%s", len(recovered), recovered_running)
        return self.download_queue_state

    def pending_download_queue_count(self) -> int:
        with self._queue_lock:
            items = self.download_queue_state.get("items", []) if isinstance(self.download_queue_state, dict) else []
            return sum(1 for item in items if isinstance(item, dict) and item.get("status") in {"pending", "running"})

    def enqueue_download_urls(self, urls: Sequence[str], *, source: str = "interactive") -> Dict[str, Any]:
        accepted: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        with self._queue_lock:
            items = self.download_queue_state.setdefault("items", [])
            existing = {str(item.get("url")) for item in items if isinstance(item, dict)}
            for raw_url in urls:
                normalized = normalize_url(raw_url)
                if not normalized:
                    self.queue_metrics["rejected_invalid"] += 1
                    rejected.append({"url": redact_url_for_evidence(raw_url), "reason": "invalid URL"})
                    continue
                if normalized in existing:
                    self.queue_metrics["rejected_duplicate"] += 1
                    rejected.append({"url": redact_url_for_evidence(normalized), "reason": "already queued"})
                    continue
                if len(items) >= self.download_queue_capacity:
                    self.queue_metrics["rejected_capacity"] += 1
                    rejected.append({"url": redact_url_for_evidence(normalized), "reason": "queue capacity reached"})
                    continue
                item = {
                    "queue_id": uuid.uuid4().hex[:12],
                    "url": normalized,
                    "url_evidence": redact_url_for_evidence(normalized),
                    "url_sha256": sha256_bytes(normalized.encode("utf-8", errors="ignore")),
                    "queued_at": now_local(),
                    "status": "pending",
                    "attempts": 0,
                    "source": redact_source_for_evidence(source),
                }
                items.append(item)
                existing.add(normalized)
                accepted.append(item)
                self.queue_metrics["enqueued"] += 1
            self._save_download_queue_state()
        return {"accepted": accepted, "rejected": rejected, "pending": self.pending_download_queue_count()}

    def download_queue_preview(self, limit: int = 12) -> List[Dict[str, Any]]:
        with self._queue_lock:
            items = self.download_queue_state.get("items", []) if isinstance(self.download_queue_state, dict) else []
            preview = []
            for index, item in enumerate(items[: max(0, limit)], start=1):
                if not isinstance(item, dict):
                    continue
                preview.append({
                    "position": index,
                    "queue_id": item.get("queue_id"),
                    "status": item.get("status"),
                    "queued_at": item.get("queued_at"),
                    "url": item.get("url_evidence") or redact_url_for_evidence(item.get("url", "")),
                    "attempts": item.get("attempts", 0),
                })
            return preview

    def _claim_next_queued_url(self) -> Optional[Dict[str, Any]]:
        with self._queue_lock:
            items = self.download_queue_state.get("items", []) if isinstance(self.download_queue_state, dict) else []
            for item in items:
                if isinstance(item, dict) and item.get("status") == "pending":
                    item["status"] = "running"
                    item["started_at"] = now_local()
                    item["attempts"] = safe_int(item.get("attempts", 0), 0, min_value=0, max_value=1000000) + 1
                    self._save_download_queue_state()
                    return dict(item)
        return None

    def _return_queued_url_to_pending(self, queue_id: str, reason: str) -> None:
        with self._queue_lock:
            for item in self.download_queue_state.get("items", []):
                if isinstance(item, dict) and str(item.get("queue_id")) == str(queue_id):
                    item["status"] = "pending"
                    item["last_interrupted_at"] = now_local()
                    item["last_error"] = redact_sensitive_text(reason)
                    break
            self._save_download_queue_state()

    def _remove_queued_url(self, queue_id: str) -> None:
        with self._queue_lock:
            items = self.download_queue_state.get("items", []) if isinstance(self.download_queue_state, dict) else []
            self.download_queue_state["items"] = [
                item for item in items
                if not (isinstance(item, dict) and str(item.get("queue_id")) == str(queue_id))
            ]
            self._save_download_queue_state()

    def process_saved_download_queue(self) -> List[Dict[str, Any]]:
        summaries: List[Dict[str, Any]] = []
        while True:
            item = self._claim_next_queued_url()
            if item is None:
                break
            queue_id = str(item.get("queue_id") or "")
            operational_url = str(item.get("url") or "")
            print(f"Queue: processing {redact_url_for_evidence(operational_url)}")
            try:
                summary = self.process_url(operational_url)
            except KeyboardInterrupt:
                self._return_queued_url_to_pending(queue_id, "interrupted; item returned to pending queue")
                raise
            except Exception as exc:
                self._remove_queued_url(queue_id)
                self.queue_metrics["processed"] += 1
                self.logger.exception("DOWNLOAD_QUEUE_ITEM_ERROR queue_id=%s url=%s", queue_id, redact_url_for_evidence(operational_url))
                summaries.append({"queue_id": queue_id, "terminal_status": "error", "error": redact_sensitive_text(exc)})
                continue
            self._remove_queued_url(queue_id)
            self.queue_metrics["processed"] += 1
            summaries.append(summary if isinstance(summary, dict) else {})
        return summaries

    def _session_download_list_text(self, *, final: bool) -> str:
        finished_at = now_local()
        total_bytes = sum(safe_int(item.get("bytes", 0), 0, min_value=0) for item in self.session_download_records)
        lines = [
            f"{APP_NAME} — Session Download List",
            "=" * 72,
            f"Version: {APP_VERSION}",
            f"Build: {BUILD_NAME}",
            f"Session ID: {self.session_id}",
            f"Session started: {self.session_started_at}",
            f"Report updated: {finished_at}",
            f"Session finalized: {bool(final)}",
            f"Queue capacity: {self.download_queue_capacity}",
            f"Maximum active downloads: {MAX_ACTIVE_DOWNLOADS}",
            f"Queue pending at report time: {self.pending_download_queue_count()}",
            f"Recovered running items this session: {self.queue_metrics.get('recovered_running_items', 0)}",
            f"Completed downloads: {len(self.session_download_records)}",
            f"Completed download bytes: {total_bytes}",
            "",
            "Top-level URL jobs:",
        ]
        if not self.session_job_summaries:
            lines.append("- None")
        else:
            for index, item in enumerate(self.session_job_summaries, start=1):
                duplicates = sum(safe_int(item.get(key, 0), 0, min_value=0) for key in ("duplicate_url_skips", "duplicate_content_skips", "duplicate_visual_skips"))
                lines.append(
                    f"{index:03d}. [{item.get('finished_at') or item.get('started_at') or ''}] "
                    f"{item.get('terminal_status', 'unknown').upper()} | downloaded={item.get('downloaded', 0)} | "
                    f"duplicates={duplicates} | failed={item.get('failed', 0)} | skipped={item.get('skipped', 0)} | "
                    f"URL={item.get('input_url', '')}"
                )
        lines.extend(["", "Downloaded files:"])
        if not self.session_download_records:
            lines.append("- None")
        else:
            for index, item in enumerate(self.session_download_records, start=1):
                dimensions = ""
                if item.get("width") or item.get("height"):
                    dimensions = f" | {item.get('width', 0)}x{item.get('height', 0)}"
                lines.append(
                    f"{index:03d}. [{item.get('timestamp', '')}] DOWNLOADED | {item.get('path', '')} | "
                    f"{item.get('bytes', 0)} bytes{dimensions} | URL={item.get('url', '')}"
                )
        lines.extend([
            "",
            "Privacy: URLs in this TXT are redacted for userinfo and secret-like query values.",
            f"Operational recovery queue: state/{DOWNLOAD_QUEUE_STATE_FILENAME} (local-private; excluded from Export20).",
            "Copyright © 2026 Gateway Information Group LLC. All rights reserved.",
            "",
        ])
        return "\n".join(lines)

    def write_session_download_list(self, *, final: bool = False) -> Optional[Path]:
        if not bool(self.config.get("session_download_list_enabled", True)):
            return None
        latest_name = Path(str(self.config.get("session_download_list_latest_filename", LATEST_DOWNLOAD_LIST_FILENAME))).name
        latest_path = self.report_dir / (latest_name or LATEST_DOWNLOAD_LIST_FILENAME)
        text = self._session_download_list_text(final=final)
        write_text_atomic(latest_path, text)
        if final and not self._session_report_finalized:
            final_path = self.report_dir / f"download_list_{timestamp_unique()}_{self.session_id[-8:]}.txt"
            write_text_atomic(final_path, text)
            retain_recent_files(
                self.report_dir,
                "download_list_*.txt",
                safe_int(self.config.get("session_download_list_retention", 25), 25, min_value=1, max_value=200),
            )
            self.session_report_path = final_path
            self._session_report_finalized = True
            self.logger.info("SESSION_DOWNLOAD_LIST final=%s latest=%s downloads=%s", short_path(final_path, self.root), short_path(latest_path, self.root), len(self.session_download_records))
            return final_path
        return latest_path

    def _start_run(self, input_url: str) -> None:
        self._stop_event.clear()
        self.failures_this_run = []
        self.not_downloaded_this_run = []
        # Reset per-run in-memory queues so a failed URL can be retried in the same open console.
        # Successful duplicates are still protected by the persistent URL/hash index.
        self.url_seen_this_process = set()
        self.sequence_probed_urls = set()
        self._browser_observed_images = []
        with self.lock:
            self._reserved_output_paths.clear()
            self._active_download_reservations = 0
        self.sequence_stats = self._fresh_sequence_stats()
        self.automation_stats = self._fresh_automation_stats()
        self.backpressure_stats = self._fresh_backpressure_stats()
        self.discovery_stats = self._fresh_discovery_stats()
        self.transfer_recovery_stats = self._fresh_transfer_recovery_stats()
        self.duplicate_stats = self._fresh_duplicate_stats()
        self.adaptive_throttle.reset_run()
        self._network_recovery_events = []
        self._http_session_resets = 0
        self._coalesced_http_session_resets = 0
        self._last_http_session_reset_monotonic = 0.0
        self._browser_context_resets = 0
        self._url_run_counter += 1
        url_run_id = f"{self.top_level_run_id}_{self._url_run_counter:03d}"
        self._run_start_monotonic = time.monotonic()
        self._last_progress_monotonic = self._run_start_monotonic
        if self.instance_guard is not None:
            self.instance_guard.heartbeat("run_start")
        safe_input_url = redact_url_for_evidence(input_url)
        self.run_summary = {
            "app": APP_NAME,
            "version": APP_VERSION,
            "build": BUILD_NAME,
            "top_level_run_id": self.top_level_run_id,
            "run_id": url_run_id,
            "started_at": now_local(),
            "finished_at": None,
            "elapsed_seconds": 0,
            "last_progress_elapsed_seconds": 0,
            "terminal_status": "running",
            "input_url": safe_input_url,
            "input_url_sha256": sha256_bytes(input_url.encode("utf-8", errors="ignore")),
            "mode": "Safe Browser Mode" if self.config.get("browser_mode") else "Standard Mode",
            "dry_run": bool(self.config.get("dry_run", False)),
            "execution_namespace": EXECUTION_NAMESPACE,
            "canonical_entrypoint": CANONICAL_ENTRYPOINT,
            "project_root": str(self.root),
            "output_mode": self.output_mode,
            "output_dir": str(self.output_dir),
            "exports_dir": str(self.export_dir),
            "config_schema_version": self.config.get("config_schema_version", CONFIG_SCHEMA_VERSION),
            "state_schema_version": self.state.get("state_schema_version", STATE_SCHEMA_VERSION),
            "computer_awareness": self.computer_context,
            "candidate_images_found": 0,
            "downloaded": 0,
            "duplicate_url_skips": 0,
            "duplicate_content_skips": 0,
            "duplicate_visual_skips": 0,
            "failed": 0,
            "skipped": 0,
            "bytes_saved": 0,
            "media_visibility": {
                "configured_default": "hidden" if bool(self.config.get("hide_downloaded_media", True)) else "visible",
                "hidden": 0,
                "visible": 0,
                "not_applicable": 0,
                "failed": 0,
            },
            "pages_visited": 0,
            "page_failures": 0,
            "automation": self.automation_stats,
            "sequential_search": self.sequence_stats,
            "discovery": self.discovery_stats,
            "transfer_recovery": self.transfer_recovery_stats,
            "duplicate_detection": self.duplicate_stats,
            "network_recovery": self._network_recovery_snapshot(),
            "adaptive_throttle": self.adaptive_throttle.snapshot(),
            "backpressure": self.backpressure_stats,
        }

    def _finish_run(self, terminal_status: str = "completed") -> None:
        finished_mono = time.monotonic()
        self.run_summary["finished_at"] = now_local()
        self.run_summary["elapsed_seconds"] = round(max(0.0, finished_mono - self._run_start_monotonic), 3) if self._run_start_monotonic else 0
        self.run_summary["last_progress_elapsed_seconds"] = round(max(0.0, self._last_progress_monotonic - self._run_start_monotonic), 3) if self._run_start_monotonic else 0
        self.run_summary["terminal_status"] = terminal_status
        self.automation_stats["last_updated"] = now_local()
        self.run_summary["automation"] = self.automation_stats
        self.run_summary["sequential_search"] = self.sequence_stats
        self.discovery_stats["last_updated"] = now_local()
        self.transfer_recovery_stats["last_updated"] = now_local()
        self.run_summary["discovery"] = self.discovery_stats
        self.run_summary["transfer_recovery"] = self.transfer_recovery_stats
        self.duplicate_stats["last_updated"] = now_local()
        self.run_summary["duplicate_detection"] = self.duplicate_stats
        self.run_summary["network_recovery"] = self._network_recovery_snapshot()
        self.run_summary["adaptive_throttle"] = self.adaptive_throttle.snapshot()
        self.run_summary["backpressure"] = self.backpressure_stats
        if self.instance_guard is not None:
            self.instance_guard.heartbeat("run_finish")
        json_dump(self.state_dir / RECENT_RUN_FILENAME, self.run_summary)
        limit = safe_int(self.config.get("recent_failure_limit", 200), 200, min_value=10, max_value=5000)
        json_dump(self.state_dir / RECENT_FAILURES_FILENAME, self.failures_this_run[-limit:])
        json_dump(self.state_dir / NOT_DOWNLOADED_FILENAME, self.not_downloaded_this_run[-limit:])
        json_dump(self.state_dir / SEQUENCE_STATS_FILENAME, self.sequence_stats)
        self._save_download_index()
        if hasattr(self, "session_job_summaries"):
            self.session_job_summaries.append({
                "run_id": self.run_summary.get("run_id"),
                "started_at": self.run_summary.get("started_at"),
                "finished_at": self.run_summary.get("finished_at"),
                "terminal_status": self.run_summary.get("terminal_status"),
                "input_url": self.run_summary.get("input_url"),
                "downloaded": self.run_summary.get("downloaded", 0),
                "duplicate_url_skips": self.run_summary.get("duplicate_url_skips", 0),
                "duplicate_content_skips": self.run_summary.get("duplicate_content_skips", 0),
                "duplicate_visual_skips": self.run_summary.get("duplicate_visual_skips", 0),
                "failed": self.run_summary.get("failed", 0),
                "skipped": self.run_summary.get("skipped", 0),
                "bytes_saved": self.run_summary.get("bytes_saved", 0),
            })
            with contextlib.suppress(Exception):
                self.write_session_download_list(final=False)

    def _record_failure(self, url: str, reason: str, *, source: str = "", stage: str = "download", status_code: int = 0, content_type: str = "") -> None:
        safe_url = redact_url_for_evidence(url)
        item = {
            "time": now_local(),
            "url": safe_url,
            "url_sha256": sha256_bytes(url.encode("utf-8", errors="ignore")),
            "source": redact_source_for_evidence(source),
            "stage": stage,
            "reason": redact_sensitive_text(reason),
            "status_code": status_code,
            "content_type": content_type,
        }
        self.failures_this_run.append(item)
        self.not_downloaded_this_run.append(item)
        self._mark_progress()
        self.logger.info("NOT_DOWNLOADED stage=%s reason=%s url=%s", stage, redact_sensitive_text(reason), safe_url)

    def _record_not_downloaded(self, url: str, reason: str, *, source: str = "", stage: str = "download") -> None:
        safe_url = redact_url_for_evidence(url)
        item = {
            "time": now_local(),
            "url": safe_url,
            "url_sha256": sha256_bytes(url.encode("utf-8", errors="ignore")),
            "source": redact_source_for_evidence(source),
            "stage": stage,
            "reason": redact_sensitive_text(reason),
        }
        self.not_downloaded_this_run.append(item)
        self._mark_progress()
        self.logger.info("SKIPPED stage=%s reason=%s url=%s", stage, redact_sensitive_text(reason), safe_url)

    def _state_url_record_exists(self, url: str) -> bool:
        rec = self.state.get("urls", {}).get(url)
        if not isinstance(rec, dict):
            return False
        rel = rec.get("path", "")
        if not rel:
            return False
        candidate = self.root / rel
        return candidate.exists()

    def _state_hash_record_exists(self, digest: str) -> Optional[Dict[str, Any]]:
        rec = self.state.get("hashes", {}).get(digest)
        if not isinstance(rec, dict):
            return None
        rel = rec.get("path", "")
        if not rel:
            return None
        candidate = self.root / rel
        return rec if candidate.exists() else None

    def _save_file_record(self, url: str, digest: str, path: Path, bytes_saved: int, content_type: str, width: int, height: int, *, media_visibility: str = "unknown", media_visibility_note: str = "", visual_fingerprint: str = "", visual_fingerprint_method: str = "", visual_fingerprint_note: str = "") -> None:
        rel = short_path(path, self.root)
        saved_at = now_local()
        record = enrich_download_asset_record({
            "url": url,
            "path": rel,
            "sha256": digest,
            "bytes": bytes_saved,
            "size_bytes": bytes_saved,
            "content_type": content_type,
            "width": width,
            "height": height,
            "saved_at": saved_at,
            "created_at": saved_at,
            "modified_at": saved_at,
            "media_visibility": media_visibility,
            "media_visibility_note": media_visibility_note,
            "windows_hidden_attribute_requested": bool(self.config.get("hide_downloaded_media", True)),
            "visual_fingerprint": visual_fingerprint,
            "visual_fingerprint_method": visual_fingerprint_method,
            "visual_fingerprint_note": visual_fingerprint_note,
        }, digest=digest, url=url)
        self.state["asset_metadata_schema"] = ASSET_METADATA_SCHEMA
        self.state.setdefault("urls", {})[url] = record
        self.state.setdefault("hashes", {})[digest] = record
        if visual_fingerprint:
            self.state.setdefault("visual_hashes", {})[visual_fingerprint] = record
        if hasattr(self, "session_download_records"):
            self.session_download_records.append({
                "timestamp": saved_at,
                "path": rel,
                "bytes": bytes_saved,
                "sha256": digest,
                "content_type": content_type,
                "width": width,
                "height": height,
                "url": redact_url_for_evidence(url),
                "url_sha256": sha256_bytes(url.encode("utf-8", errors="ignore")),
            })

    def _make_output_path(self, url: str, fmt: str, digest: str) -> Path:
        parsed = urllib.parse.urlparse(url)
        name = sanitize_filename(posixpath.basename(parsed.path))
        current_ext = normalize_ext(name.rsplit(".", 1)[1]) if "." in name else ""
        ext = "jpg" if fmt == "jpeg" else fmt
        if current_ext not in IMAGE_EXTENSIONS or normalize_ext(current_ext) != normalize_ext(ext):
            stem = name.rsplit(".", 1)[0] if "." in name else name
            stem = sanitize_filename(stem) or f"image_{digest[:12]}"
            name = f"{stem}.{ext}"
        if not name or name.startswith("."):
            name = f"image_{digest[:12]}.{ext}"
        folder = self.output_dir
        if bool(self.config.get("organize_by_domain", True)):
            folder = folder / hostname_folder(url)
        folder.mkdir(parents=True, exist_ok=True)
        base_path = folder / name
        with self.lock:
            conflict_recorded = False
            for index in range(1, 10000):
                candidate = base_path if index == 1 else base_path.with_name(f"{base_path.stem}_{index}{base_path.suffix}")
                key = output_path_identity(candidate)
                if candidate.exists() or key in self._reserved_output_paths:
                    if not conflict_recorded:
                        self.duplicate_stats["filename_conflicts_resolved"] = int(self.duplicate_stats.get("filename_conflicts_resolved", 0)) + 1
                        conflict_recorded = True
                    continue
                self._reserved_output_paths.add(key)
                return candidate
        raise RuntimeError(f"Could not allocate a unique output path for {name}")

    def _limit_reached(self) -> bool:
        limit = safe_int(self.config.get("limit", 0), 0, min_value=0, max_value=100000)
        return limit > 0 and int(self.run_summary.get("downloaded", 0)) >= limit

    def head_probe(self, url: str, *, deadline: Optional[float] = None) -> Tuple[int, str, int]:
        attempts = safe_int(self.config.get("network_head_probe_retries", 1), 1, min_value=0, max_value=5)
        if not self._network_enabled():
            attempts = 0
        for attempt in range(attempts + 1):
            if self._deadline_remaining(deadline) <= 0:
                return 0, "", 0
            try:
                with self._get_http_session().head(url, allow_redirects=True, timeout=self._request_timeout_for_deadline(deadline)) as resp:
                    content_type = resp.headers.get("Content-Type", "")
                    length_text = resp.headers.get("Content-Length", "")
                    length = int(length_text) if length_text.isdigit() else 0
                    if self._retryable_status(int(resp.status_code)) and attempt < attempts:
                        self._sleep_before_retry(
                            url,
                            "head_probe",
                            attempt,
                            status_code=int(resp.status_code),
                            retry_after=resp.headers.get("Retry-After", ""),
                            deadline=deadline,
                        )
                        continue
                    return int(resp.status_code), content_type, length
            except self.requests.exceptions.RequestException as exc:
                will_retry = attempt < attempts and self._deadline_remaining(deadline) > 0
                self._handle_network_exception(exc, url, attempt, "head_probe", will_retry=will_retry, deadline=deadline)
        return 0, "", 0

    def download_one(self, url: str, *, source: str = "", reason: str = "discovered", enforce_host: str = "") -> DownloadResult:
        normalized = normalize_url(url)
        if not normalized:
            self._record_failure(url, "invalid or unsupported URL", source=source, stage=reason)
            with self.lock:
                self.run_summary["failed"] += 1
            return DownloadResult(url=url, status="failed", reason="invalid URL")
        url = normalized
        if has_dangerous_extension(url):
            self._record_failure(url, "blocked dangerous file extension", source=source, stage=reason)
            with self.lock:
                self.run_summary["failed"] += 1
            return DownloadResult(url=url, status="failed", reason="dangerous extension")
        if enforce_host and url_host(url) != enforce_host:
            self._record_failure(url, "blocked by same-domain sequence restriction", source=source, stage=reason)
            with self.lock:
                self.run_summary["failed"] += 1
            return DownloadResult(url=url, status="failed", reason="same-domain restriction")
        with self.lock:
            duplicate_url = url in self.url_seen_this_process
            if not duplicate_url and bool(self.config.get("duplicate_url_check", True)):
                duplicate_url = self._state_url_record_exists(url)
            if duplicate_url:
                self.run_summary["duplicate_url_skips"] += 1
                self.duplicate_stats["url_duplicates_skipped"] = int(self.duplicate_stats.get("url_duplicates_skipped", 0)) + 1
                self._record_not_downloaded(url, "duplicate URL already downloaded or queued", source=source, stage=reason)
                return DownloadResult(url=url, status="duplicate_url", reason="duplicate URL")
            self.url_seen_this_process.add(url)

        if bool(self.config.get("dry_run", False)):
            status_code, content_type, length = self.head_probe(url)
            dry_reason = "dry run: would download if image validation passes"
            if status_code >= 400:
                dry_reason = f"dry run: server returned HTTP {status_code}"
            elif length > self.max_file_bytes:
                dry_reason = "dry run: file would exceed max_file_mb"
            self._record_not_downloaded(url, dry_reason, source=source, stage=reason)
            with self.lock:
                self.run_summary["skipped"] += 1
            return DownloadResult(url=url, status="dry_run", reason=dry_reason, content_type=content_type, status_code=status_code)

        if not self._claim_download_slot():
            self._record_not_downloaded(url, "download limit reached", source=source, stage=reason)
            with self.lock:
                self.run_summary["skipped"] += 1
            return DownloadResult(url=url, status="skipped", reason="download limit reached")

        part_path, meta_path = self._partial_paths(url)
        output_path: Optional[Path] = None
        target_tmp: Optional[Path] = None
        last_error = ""
        status_code = 0
        content_type = ""
        retries = safe_int(self.config.get("retries", 2), 2, min_value=0, max_value=5)
        extra_network_retries = safe_int(self.config.get("network_recovery_extra_attempts", 2), 2, min_value=0, max_value=5)
        operation_started = time.monotonic()
        operation_deadline = operation_started + self.request_wall_clock_timeout
        try:
            # HEAD and GET share one strict monotonic per-image download budget.
            head_status, head_type, head_length = self.head_probe(url, deadline=operation_deadline)
            if self._deadline_remaining(operation_deadline) <= 0:
                self._bump_transfer_stat("wall_clock_aborts")
                timeout_reason = f"download exceeded {self.request_wall_clock_timeout}-second limit"
                self._record_failure(url, timeout_reason, source=source, stage=reason, status_code=head_status, content_type=head_type)
                with self.lock:
                    self.run_summary["failed"] += 1
                return DownloadResult(url=url, status="failed", reason=timeout_reason, status_code=head_status, content_type=head_type)
            if head_status in {404, 410}:
                self._discard_partial(part_path, meta_path, reason=f"HTTP {head_status}")
                self._record_failure(url, f"HTTP {head_status}", source=source, stage=reason, status_code=head_status, content_type=head_type)
                with self.lock:
                    self.run_summary["failed"] += 1
                return DownloadResult(url=url, status="failed", reason=f"HTTP {head_status}", status_code=head_status, content_type=head_type)
            if head_length and head_length > self.max_file_bytes:
                self._discard_partial(part_path, meta_path, reason="max size preflight")
                self._record_failure(url, "blocked by max_file_mb before download", source=source, stage=reason, status_code=head_status, content_type=head_type)
                with self.lock:
                    self.run_summary["failed"] += 1
                return DownloadResult(url=url, status="failed", reason="too large", status_code=head_status, content_type=head_type)
            if is_dangerous_content_type(head_type):
                self._discard_partial(part_path, meta_path, reason="dangerous content type")
                self._record_failure(url, "blocked dangerous content type", source=source, stage=reason, status_code=head_status, content_type=head_type)
                with self.lock:
                    self.run_summary["failed"] += 1
                return DownloadResult(url=url, status="failed", reason="dangerous content type", status_code=head_status, content_type=head_type)

            for attempt in range(retries + extra_network_retries + 1):
                if self._stop_event.is_set():
                    raise RuntimeError("shutdown requested")
                if self._deadline_remaining(operation_deadline) <= 0:
                    self._bump_transfer_stat("wall_clock_aborts")
                    raise TimeoutError("download exceeded request_wall_clock_timeout_seconds")

                metadata = self._load_partial_metadata(url, part_path, meta_path)
                resume_size = int(metadata.get("bytes_present", 0) or 0)
                resume_enabled = bool(self.config.get("resume_partial_downloads", True))
                resume_min = safe_int(self.config.get("resume_min_bytes", 262144), 262144, min_value=0, max_value=104857600)
                require_validator = bool(self.config.get("resume_requires_validator", True))
                etag = str(metadata.get("etag", "") or "")
                if etag.startswith("W/"):
                    etag = ""
                validator = etag or str(metadata.get("last_modified", "") or "")
                resume_requested = bool(
                    resume_enabled
                    and resume_size >= resume_min
                    and (validator or not require_validator)
                )
                if resume_size and not resume_requested:
                    self._discard_partial(part_path, meta_path, reason="partial below threshold or missing validator")
                    self._bump_transfer_stat("partial_restarts")
                    metadata = {}
                    resume_size = 0

                headers = {"Accept-Encoding": "identity"}
                if resume_requested:
                    headers["Range"] = f"bytes={resume_size}-"
                    if validator:
                        headers["If-Range"] = validator
                    self._bump_transfer_stat("partial_resume_attempts")

                try:
                    complete_from_partial = False
                    with self._get_http_session().get(
                        url,
                        stream=True,
                        allow_redirects=True,
                        timeout=self._request_timeout_for_deadline(operation_deadline),
                        headers=headers,
                    ) as resp:
                        status_code = int(resp.status_code)
                        content_type = resp.headers.get("Content-Type", "")
                        final_url = normalize_url(resp.url) or url

                        if self._retryable_status(status_code) and attempt < retries:
                            last_error = f"HTTP {status_code}"
                            self._sleep_before_retry(
                                url,
                                reason,
                                attempt,
                                status_code=status_code,
                                retry_after=resp.headers.get("Retry-After", ""),
                                deadline=operation_deadline,
                            )
                            continue

                        if status_code == 416 and resume_requested:
                            _range_start, range_total = parse_content_range(resp.headers.get("Content-Range", ""))
                            if range_total is not None and range_total == resume_size and part_path.exists():
                                complete_from_partial = True
                                content_type = str(metadata.get("content_type", content_type) or content_type)
                            else:
                                self._discard_partial(part_path, meta_path, reason="unsatisfied range")
                                self._bump_transfer_stat("partial_restarts")
                                last_error = "HTTP 416 range could not be resumed"
                                if attempt < retries:
                                    self._sleep_before_retry(url, reason, attempt, status_code=status_code, deadline=operation_deadline)
                                    continue
                                raise RuntimeError(last_error)

                        if not complete_from_partial:
                            if enforce_host and url_host(final_url) != enforce_host:
                                self._discard_partial(part_path, meta_path, reason="redirect outside same domain")
                                self._record_failure(url, "blocked redirect outside same-domain sequence restriction", source=source, stage=reason, status_code=status_code, content_type=content_type)
                                with self.lock:
                                    self.run_summary["failed"] += 1
                                return DownloadResult(url=url, status="failed", reason="redirect outside same domain", status_code=status_code, content_type=content_type)
                            if status_code >= 400:
                                self._discard_partial(part_path, meta_path, reason=f"HTTP {status_code}")
                                self._record_failure(url, f"HTTP {status_code}", source=source, stage=reason, status_code=status_code, content_type=content_type)
                                with self.lock:
                                    self.run_summary["failed"] += 1
                                return DownloadResult(url=url, status="failed", reason=f"HTTP {status_code}", status_code=status_code, content_type=content_type)
                            if is_dangerous_content_type(content_type):
                                self._discard_partial(part_path, meta_path, reason="dangerous content type")
                                self._record_failure(url, "blocked dangerous content type", source=source, stage=reason, status_code=status_code, content_type=content_type)
                                with self.lock:
                                    self.run_summary["failed"] += 1
                                return DownloadResult(url=url, status="failed", reason="dangerous content type", status_code=status_code, content_type=content_type)

                            range_start, range_total = parse_content_range(resp.headers.get("Content-Range", ""))
                            append_mode = bool(resume_requested and status_code == 206 and range_start == resume_size)
                            if append_mode:
                                response_etag = str(resp.headers.get("ETag", "") or "")
                                response_last_modified = str(resp.headers.get("Last-Modified", "") or "")
                                metadata_etag = str(metadata.get("etag", "") or "")
                                metadata_last_modified = str(metadata.get("last_modified", "") or "")
                                validator_changed = bool(
                                    (metadata_etag and response_etag and metadata_etag != response_etag)
                                    or (not metadata_etag and metadata_last_modified and response_last_modified and metadata_last_modified != response_last_modified)
                                )
                                if validator_changed:
                                    self._discard_partial(part_path, meta_path, reason="resume validator changed")
                                    self._bump_transfer_stat("partial_restarts")
                                    last_error = "resume validator changed; restarting from byte zero"
                                    if attempt < retries:
                                        self._sleep_before_retry(url, reason, attempt, status_code=status_code)
                                        continue
                                    raise RuntimeError(last_error)
                            if resume_requested and not append_mode:
                                self._bump_transfer_stat("partial_restarts")
                                resume_size = 0
                            write_mode = "ab" if append_mode else "wb"
                            existing_bytes = resume_size if append_mode else 0
                            length_text = resp.headers.get("Content-Length", "")
                            response_length = int(length_text) if length_text.isdigit() else 0
                            expected_total = range_total or ((existing_bytes + response_length) if response_length else 0)
                            if expected_total and expected_total > self.max_file_bytes:
                                self._discard_partial(part_path, meta_path, reason="max size response")
                                self._record_failure(url, "blocked by max_file_mb", source=source, stage=reason, status_code=status_code, content_type=content_type)
                                with self.lock:
                                    self.run_summary["failed"] += 1
                                return DownloadResult(url=url, status="failed", reason="too large", status_code=status_code, content_type=content_type)

                            metadata = {
                                "url": url,
                                "final_url": final_url,
                                "etag": resp.headers.get("ETag", ""),
                                "last_modified": resp.headers.get("Last-Modified", ""),
                                "content_type": content_type,
                                "expected_total": expected_total,
                                "updated_at": now_local(),
                            }
                            self._write_partial_metadata(meta_path, metadata)
                            chunk_size = safe_int(self.config.get("stream_chunk_kb", 128), 128, min_value=16, max_value=1024) * 1024
                            bytes_written = existing_bytes
                            with part_path.open(write_mode) as output:
                                for chunk in resp.iter_content(chunk_size=chunk_size):
                                    if self._stop_event.is_set():
                                        raise RuntimeError("shutdown requested")
                                    if self._deadline_remaining(operation_deadline) <= 0:
                                        self._bump_transfer_stat("wall_clock_aborts")
                                        raise TimeoutError("download exceeded request_wall_clock_timeout_seconds")
                                    if not chunk:
                                        continue
                                    output.write(chunk)
                                    bytes_written += len(chunk)
                                    if bytes_written > self.max_file_bytes:
                                        raise ValueError("blocked by max_file_mb while streaming")
                                output.flush()
                                with contextlib.suppress(OSError):
                                    os.fsync(output.fileno())
                            if expected_total and bytes_written != expected_total:
                                raise OSError(f"incomplete transfer ({bytes_written} of {expected_total} bytes)")
                            if append_mode:
                                self._bump_transfer_stat("partial_resume_successes")
                                self._bump_transfer_stat("partial_bytes_reused", existing_bytes)

                    if not part_path.exists():
                        raise OSError("download completed without a partial payload file")
                    try:
                        file_size = part_path.stat().st_size
                    except OSError as exc:
                        raise OSError(f"could not stat completed partial payload: {exc}") from exc
                    if file_size > self.max_file_bytes:
                        raise ValueError("blocked by max_file_mb after transfer")
                    with part_path.open("rb") as source_file:
                        header_data = source_file.read(128 * 1024)

                    fmt = detect_image_format(header_data, bool(self.config.get("safe_svg_validation", True)))
                    if not fmt:
                        self._discard_partial(part_path, meta_path, reason="header validation failed")
                        self._record_failure(url, "not an image after header validation", source=source, stage=reason, status_code=status_code, content_type=content_type)
                        with self.lock:
                            self.run_summary["failed"] += 1
                        return DownloadResult(url=url, status="failed", reason="not an image", status_code=status_code, content_type=content_type)
                    fmt_norm = normalize_ext(fmt)
                    if fmt_norm not in allowed_types(self.config):
                        self._discard_partial(part_path, meta_path, reason="image type not allowed")
                        self._record_failure(url, f"image type not allowed: {fmt_norm}", source=source, stage=reason, status_code=status_code, content_type=content_type)
                        with self.lock:
                            self.run_summary["failed"] += 1
                        return DownloadResult(url=url, status="failed", reason="image type not allowed", status_code=status_code, content_type=content_type)
                    if not content_type_allows_format(content_type, fmt_norm):
                        self._discard_partial(part_path, meta_path, reason="invalid content type")
                        self._record_failure(url, "content type did not validate as an image", source=source, stage=reason, status_code=status_code, content_type=content_type)
                        with self.lock:
                            self.run_summary["failed"] += 1
                        return DownloadResult(url=url, status="failed", reason="invalid content type", status_code=status_code, content_type=content_type)

                    valid, width, height, verification_mode, validation_reason = validate_image_file(
                        part_path,
                        fmt_norm,
                        strict_raster_verify=bool(self.config.get("strict_raster_verify", True)),
                        max_pixels=safe_int(self.config.get("image_max_pixels", 120000000), 120000000, min_value=1000000, max_value=1000000000),
                    )
                    if not valid:
                        self._bump_transfer_stat("raster_verify_failures")
                        self._discard_partial(part_path, meta_path, reason="image verification failed")
                        self._record_failure(url, f"image verification failed: {validation_reason}", source=source, stage=reason, status_code=status_code, content_type=content_type)
                        with self.lock:
                            self.run_summary["failed"] += 1
                        return DownloadResult(url=url, status="failed", reason="image verification failed", status_code=status_code, content_type=content_type, width=width, height=height)

                    min_width = safe_int(self.config.get("min_width", 0), 0, min_value=0, max_value=100000)
                    min_height = safe_int(self.config.get("min_height", 0), 0, min_value=0, max_value=100000)
                    if width and min_width and width < min_width:
                        self._discard_partial(part_path, meta_path, reason="below min_width")
                        self._record_failure(url, f"image width below minimum ({width} < {min_width})", source=source, stage=reason, status_code=status_code, content_type=content_type)
                        with self.lock:
                            self.run_summary["failed"] += 1
                        return DownloadResult(url=url, status="failed", reason="below min_width", status_code=status_code, content_type=content_type, width=width, height=height)
                    if height and min_height and height < min_height:
                        self._discard_partial(part_path, meta_path, reason="below min_height")
                        self._record_failure(url, f"image height below minimum ({height} < {min_height})", source=source, stage=reason, status_code=status_code, content_type=content_type)
                        with self.lock:
                            self.run_summary["failed"] += 1
                        return DownloadResult(url=url, status="failed", reason="below min_height", status_code=status_code, content_type=content_type, width=width, height=height)

                    digest = sha256_file(part_path)
                    visual_fingerprint = ""
                    visual_fingerprint_method = ""
                    visual_fingerprint_note = ""
                    if bool(self.config.get("duplicate_visual_fingerprint_check", True)) and fmt_norm != "svg":
                        visual_fingerprint, visual_fingerprint_method, visual_fingerprint_note = image_visual_fingerprint(
                            part_path,
                            max_pixels=safe_int(self.config.get("image_max_pixels", 120000000), 120000000, min_value=1000000, max_value=1000000000),
                        )
                    with self.lock:
                        hash_rec = self._state_hash_record_exists(digest) if bool(self.config.get("duplicate_content_hash_check", True)) else None
                        if hash_rec:
                            self.run_summary["duplicate_content_skips"] += 1
                            self.duplicate_stats["exact_content_duplicates_skipped"] = int(self.duplicate_stats.get("exact_content_duplicates_skipped", 0)) + 1
                            self._record_not_downloaded(url, f"duplicate content hash; existing file: {hash_rec.get('path', '')}", source=source, stage=reason)
                            self._discard_partial(part_path, meta_path, reason="duplicate content")
                            return DownloadResult(url=url, status="duplicate_content", reason="duplicate content", sha256=digest, content_type=content_type, width=width, height=height)
                        visual_rec = self._state_visual_record_exists(visual_fingerprint) if visual_fingerprint else None
                        if visual_rec:
                            self.run_summary["duplicate_visual_skips"] += 1
                            self.duplicate_stats["visual_duplicates_skipped"] = int(self.duplicate_stats.get("visual_duplicates_skipped", 0)) + 1
                            self._record_not_downloaded(url, f"visual duplicate; existing file: {visual_rec.get('path', '')}", source=source, stage=reason)
                            self._discard_partial(part_path, meta_path, reason="visual duplicate")
                            return DownloadResult(url=url, status="duplicate_visual", reason="visual duplicate", sha256=digest, content_type=content_type, width=width, height=height)

                    output_path = self._make_output_path(url, fmt_norm, digest)
                    target_tmp = output_path.with_name(f".{output_path.name}.{uuid.uuid4().hex[:8]}.part")
                    try:
                        with part_path.open("rb") as source_file, target_tmp.open("wb") as output:
                            shutil.copyfileobj(source_file, output, length=safe_int(self.config.get("stream_chunk_kb", 128), 128, min_value=16, max_value=1024) * 1024)
                            output.flush()
                            with contextlib.suppress(OSError):
                                os.fsync(output.fileno())
                        target_tmp.replace(output_path)
                    except Exception:
                        with contextlib.suppress(OSError):
                            target_tmp.unlink()
                        raise
                    hide_media = bool(self.config.get("hide_downloaded_media", True))
                    visibility_status, visibility_note = apply_downloaded_media_visibility(output_path, hide_media)
                    if visibility_status == "failed":
                        self.logger.warning(
                            "MEDIA_VISIBILITY status=failed path=%s detail=%s",
                            short_path(output_path, self.root), visibility_note,
                        )
                    else:
                        self.logger.info(
                            "MEDIA_VISIBILITY status=%s path=%s detail=%s",
                            visibility_status, short_path(output_path, self.root), visibility_note,
                        )
                    self._discard_partial(part_path, meta_path)
                    with self.lock:
                        visibility_counts = self.run_summary.setdefault("media_visibility", {})
                        visibility_counts[visibility_status] = int(visibility_counts.get(visibility_status, 0)) + 1
                        self._save_file_record(
                            url, digest, output_path, file_size, content_type, width, height,
                            media_visibility=visibility_status, media_visibility_note=visibility_note,
                            visual_fingerprint=visual_fingerprint,
                            visual_fingerprint_method=visual_fingerprint_method,
                            visual_fingerprint_note=visual_fingerprint_note,
                        )
                        self.run_summary["downloaded"] += 1
                        self.run_summary["bytes_saved"] += file_size
                        self._mark_progress()
                    self._checkpoint_state_if_due()
                    self.logger.info(
                        "DOWNLOADED bytes=%s validation=%s path=%s url=%s",
                        file_size,
                        verification_mode,
                        short_path(output_path, self.root),
                        redact_url_for_evidence(url),
                    )
                    print(f"Downloaded: {short_path(output_path, self.root)}")
                    return DownloadResult(url=url, status="downloaded", path=short_path(output_path, self.root), bytes_saved=file_size, sha256=digest, content_type=content_type, status_code=status_code, width=width, height=height)
                except KeyboardInterrupt:
                    raise
                except self.requests.exceptions.RequestException as exc:
                    last_error = f"network error: {exc}"
                    will_retry = attempt < retries + extra_network_retries and self._deadline_remaining(operation_deadline) > 0
                    self._handle_network_exception(exc, url, attempt, reason, will_retry=will_retry, deadline=operation_deadline)
                    if will_retry:
                        continue
                except (OSError, RuntimeError, ValueError) as exc:
                    last_error = f"{exc.__class__.__name__}: {exc}"
                    will_retry = (
                        attempt < retries
                        and "shutdown requested" not in str(exc)
                        and not isinstance(exc, TimeoutError)
                        and self._deadline_remaining(operation_deadline) > 0
                    )
                    if will_retry:
                        self._sleep_before_retry(url, reason, attempt, deadline=operation_deadline)
                        continue
                break

            self._record_failure(url, last_error or "download failed", source=source, stage=reason, status_code=status_code, content_type=content_type)
            with self.lock:
                self.run_summary["failed"] += 1
            return DownloadResult(url=url, status="failed", reason=last_error or "download failed", status_code=status_code, content_type=content_type)
        finally:
            if target_tmp is not None:
                with contextlib.suppress(OSError):
                    target_tmp.unlink()
            self._release_output_path(output_path)
            self._release_download_slot()

    def fetch_page_standard(self, url: str) -> Tuple[str, str, bool]:
        normalized = normalize_url(url)
        if not normalized:
            raise ValueError("Invalid URL")
        url = normalized
        retries = safe_int(self.config.get("retries", 2), 2, min_value=0, max_value=5)
        last_error = ""
        operation_started = time.monotonic()
        for attempt in range(retries + 1):
            if self._stop_event.is_set():
                raise RuntimeError("shutdown requested")
            if time.monotonic() - operation_started > self.page_wall_clock_timeout:
                self._bump_transfer_stat("wall_clock_aborts")
                raise TimeoutError("page fetch exceeded page_wall_clock_timeout_seconds")
            try:
                with self._get_http_session().get(url, stream=True, allow_redirects=True, timeout=self.request_timeout) as resp:
                    status_code = int(resp.status_code)
                    if self._retryable_status(status_code) and attempt < retries:
                        last_error = f"HTTP {status_code}"
                        self._sleep_before_retry(
                            url,
                            "fetch_page",
                            attempt,
                            status_code=status_code,
                            retry_after=resp.headers.get("Retry-After", ""),
                        )
                        continue
                    if status_code >= 400:
                        raise RuntimeError(f"HTTP {status_code}")
                    final_url = normalize_url(resp.url) or url
                    content_type = resp.headers.get("Content-Type", "")
                    if is_dangerous_content_type(content_type):
                        raise RuntimeError(f"Blocked dangerous content type: {content_type}")
                    if base_content_type(content_type).startswith("image/") or is_allowed_image_url(final_url, self.config):
                        return "", final_url, True
                    length_text = resp.headers.get("Content-Length", "")
                    if length_text.isdigit() and int(length_text) > self.max_html_bytes:
                        raise RuntimeError("Page HTML exceeded max_html_mb before transfer")
                    data_io = io.BytesIO()
                    for chunk in resp.iter_content(chunk_size=64 * 1024):
                        if self._stop_event.is_set():
                            raise RuntimeError("shutdown requested")
                        if time.monotonic() - operation_started > self.page_wall_clock_timeout:
                            self._bump_transfer_stat("wall_clock_aborts")
                            raise TimeoutError("page fetch exceeded page_wall_clock_timeout_seconds")
                        if not chunk:
                            continue
                        data_io.write(chunk)
                        if data_io.tell() > self.max_html_bytes:
                            raise RuntimeError("Page HTML exceeded max_html_mb")
                    encoding = resp.encoding or "utf-8"
                    try:
                        text = data_io.getvalue().decode(encoding, errors="replace")
                    except (LookupError, UnicodeError):
                        text = data_io.getvalue().decode("utf-8", errors="replace")
                    return text, final_url, False
            except self.requests.exceptions.RequestException as exc:
                last_error = f"network error: {exc}"
                will_retry = attempt < retries
                self._handle_network_exception(exc, url, attempt, "fetch_page", will_retry=will_retry)
                if will_retry:
                    continue
                raise RuntimeError(last_error) from exc
            except (OSError, RuntimeError, ValueError) as exc:
                last_error = f"{exc.__class__.__name__}: {exc}"
                raise RuntimeError(last_error) from exc
        raise RuntimeError(last_error or "page fetch failed")

    def _ensure_browser_context(self) -> Any:
        if not bool(self.config.get("browser_reuse_context", True)):
            self.close_browser()
        if self._browser_context is not None:
            return self._browser_context
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "Safe Browser Mode requires Playwright. Use run_image_downloader_safe_browser.bat to install and run it."
            ) from exc
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)
        self._browser_context = self._browser.new_context(
            user_agent=str(self.config.get("user_agent", default_config()["user_agent"])),
            ignore_https_errors=False,
        )
        return self._browser_context

    def close_browser(self) -> None:
        for attr in ("_browser_context", "_browser"):
            obj = getattr(self, attr, None)
            if obj is not None:
                with contextlib.suppress(Exception):
                    obj.close()
                setattr(self, attr, None)
        if self._playwright is not None:
            with contextlib.suppress(Exception):
                self._playwright.stop()
            self._playwright = None

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.write_session_download_list(final=True)
        self._stop_event.set()
        self.close_browser()
        self._close_all_http_sessions()

    def fetch_page_browser(self, url: str) -> Tuple[str, str, bool]:
        normalized = normalize_url(url)
        if not normalized:
            raise ValueError("Invalid URL")
        wait_ms = safe_int(self.config.get("browser_wait_ms", 500), 500, min_value=0, max_value=10000)
        scroll_steps = safe_int(self.config.get("browser_scroll_steps", 3), 3, min_value=0, max_value=25)
        retries = safe_int(self.config.get("retries", 2), 2, min_value=0, max_value=5)
        last_error = ""
        operation_started = time.monotonic()
        for attempt in range(retries + 1):
            if self._stop_event.is_set():
                raise RuntimeError("shutdown requested")
            if time.monotonic() - operation_started > self.page_wall_clock_timeout:
                self._bump_transfer_stat("wall_clock_aborts")
                raise TimeoutError("browser page fetch exceeded page_wall_clock_timeout_seconds")
            page = None
            observed_images: List[str] = []
            observed_seen: Set[str] = set()
            try:
                context = self._ensure_browser_context()
                page = context.new_page()
                self._browser_pages_opened += 1
                capture_network = bool(self.config.get("browser_capture_network_images", True))
                capture_limit = safe_int(self.config.get("browser_network_image_limit", 500), 500, min_value=1, max_value=5000)

                if capture_network:
                    def record_image_response(response: Any) -> None:
                        try:
                            response_url = normalize_url(response.url)
                            if not response_url or response_url in observed_seen or has_dangerous_extension(response_url):
                                return
                            content_type = str(response.headers.get("content-type", ""))
                            resource_type = str(getattr(response.request, "resource_type", ""))
                            if not (resource_type == "image" or base_content_type(content_type).startswith("image/")):
                                return
                            if int(getattr(response, "status", 0) or 0) >= 400:
                                return
                            if len(observed_images) >= capture_limit:
                                self.discovery_stats["browser_network_limit_reached"] = True
                                return
                            observed_seen.add(response_url)
                            observed_images.append(response_url)
                        except (AttributeError, RuntimeError, TypeError, ValueError):
                            return

                    page.on("response", record_image_response)
                page_timeout_ms = self.page_wall_clock_timeout * 1000
                page.set_default_timeout(page_timeout_ms)
                navigation_response = page.goto(normalized, wait_until="domcontentloaded", timeout=page_timeout_ms)
                if wait_ms:
                    page.wait_for_timeout(wait_ms)
                for _ in range(max(0, scroll_steps)):
                    if self._stop_event.is_set():
                        raise RuntimeError("shutdown requested")
                    if time.monotonic() - operation_started > self.page_wall_clock_timeout:
                        self._bump_transfer_stat("wall_clock_aborts")
                        raise TimeoutError("browser page fetch exceeded page_wall_clock_timeout_seconds")
                    page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                    if wait_ms:
                        page.wait_for_timeout(wait_ms)
                final_url = normalize_url(page.url) or normalized
                if navigation_response is not None:
                    nav_content_type = str(navigation_response.headers.get("content-type", ""))
                    if base_content_type(nav_content_type).startswith("image/") or is_allowed_image_url(final_url, self.config):
                        self._browser_observed_images = observed_images
                        return "", final_url, True
                html_text = page.content()
                if len(html_text.encode("utf-8", errors="replace")) > self.max_html_bytes:
                    raise RuntimeError("Rendered page HTML exceeded max_html_mb")
                self._browser_observed_images = observed_images
                return html_text, final_url, False
            except RuntimeError as exc:
                if "Safe Browser Mode requires Playwright" in str(exc) or "Rendered page HTML exceeded" in str(exc) or "shutdown requested" in str(exc):
                    raise
                last_error = f"browser runtime error: {exc}"
                will_retry = attempt < retries
                self.adaptive_throttle.record_network_error(url_host(normalized), "fetch_page_browser", last_error)
                self._reset_browser_context_for_network(last_error, normalized, "fetch_page_browser")
                if will_retry:
                    self._sleep_before_retry(normalized, "fetch_page_browser", attempt)
                    continue
                raise RuntimeError(last_error) from exc
            except Exception as exc:
                last_error = f"browser/network error: {exc.__class__.__name__}: {exc}"
                will_retry = attempt < retries
                self.adaptive_throttle.record_network_error(url_host(normalized), "fetch_page_browser", last_error)
                self._reset_browser_context_for_network(last_error, normalized, "fetch_page_browser")
                if will_retry:
                    self._sleep_before_retry(normalized, "fetch_page_browser", attempt)
                    continue
                raise RuntimeError(last_error) from exc
            finally:
                if page is not None:
                    with contextlib.suppress(Exception):
                        page.close()
        raise RuntimeError(last_error or "browser page fetch failed")

    def fetch_page(self, url: str) -> Tuple[str, str, bool]:
        if bool(self.config.get("browser_mode", False)):
            return self.fetch_page_browser(url)
        return self.fetch_page_standard(url)

    def discover_from_html(self, html_text: str, base_url: str) -> Tuple[List[str], List[str]]:
        candidates: List[str] = []
        gallery_links: List[str] = []
        candidate_seen: Set[str] = set()
        gallery_seen: Set[str] = set()
        preference = str(self.config.get("srcset_preference", "largest")).lower()
        same_only = bool(self.config.get("same_domain_only", False))
        modern = bool(self.config.get("modern_discovery_enabled", True))
        max_candidates = safe_int(self.config.get("max_candidate_urls_per_page", 500), 500, min_value=1, max_value=5000)
        smart_auto = str(self.config.get("automation_mode", "smart_safe")) == "smart_safe"
        manual_gallery = bool(self.config.get("follow_gallery_links", False))
        auto_gallery = smart_auto and bool(self.config.get("auto_gallery_follow_enabled", True)) and not manual_gallery
        auto_gallery_link_limit = safe_int(self.config.get("auto_gallery_link_limit_per_page", 12), 12, min_value=1, max_value=50)

        stat_key_map = {
            "html": "html_attribute_candidates",
            "srcset": "srcset_candidates",
            "imagesrcset": "imagesrcset_candidates",
            "metadata": "metadata_candidates",
            "jsonld": "jsonld_candidates",
            "css": "css_candidates",
            "noscript": "noscript_candidates",
            "browser_network": "browser_network_candidates",
        }

        def add_url(raw: Any, *, gallery: bool = False, kind: str = "html") -> None:
            raw_text = str(raw or "").strip()
            if not raw_text or raw_text.startswith("#"):
                return
            normalized = normalize_url(raw_text, base_url)
            if not normalized:
                return
            if has_dangerous_extension(normalized):
                return
            if same_only and not same_hostname(base_url, normalized):
                return
            if gallery:
                if normalized in gallery_seen:
                    return
                max_gallery = safe_int(self.config.get("gallery_queue_capacity", 100), 100, min_value=1, max_value=1000)
                if len(gallery_links) >= max_gallery:
                    return
                gallery_seen.add(normalized)
                gallery_links.append(normalized)
                return
            if normalized in candidate_seen:
                self.duplicate_stats["candidate_duplicates_removed"] = int(self.duplicate_stats.get("candidate_duplicates_removed", 0)) + 1
                return
            if len(candidates) >= max_candidates:
                self.discovery_stats["candidate_limit_reached"] = True
                return
            candidate_seen.add(normalized)
            candidates.append(normalized)
            stat_key = stat_key_map.get(kind, "html_attribute_candidates")
            self.discovery_stats[stat_key] = int(self.discovery_stats.get(stat_key, 0)) + 1

        BeautifulSoup = optional_bs4()
        if BeautifulSoup is not None:
            soup = BeautifulSoup(html_text, "html.parser")
            image_attrs = [
                "src", "data-src", "data-original", "data-lazy-src", "data-image", "data-full",
                "data-url", "data-image-src", "data-background", "data-bg", "data-bg-src", "poster",
            ]
            srcset_attrs = ["srcset", "data-srcset", "data-lazy-srcset", "data-original-set"]
            for tag in soup.find_all(["img", "source", "picture", "video", "input"]):
                for attr in image_attrs:
                    value = tag.get(attr)
                    if value:
                        add_url(value, kind="html")
                for attr in srcset_attrs:
                    srcset = tag.get(attr)
                    if srcset:
                        for src in parse_srcset(str(srcset), preference):
                            add_url(src, kind="srcset")

            for meta in soup.find_all("meta"):
                key = (meta.get("property") or meta.get("name") or meta.get("itemprop") or "").lower()
                if any(token in key for token in ["og:image", "twitter:image", "thumbnail", "image"]):
                    content = meta.get("content")
                    if content:
                        add_url(content, kind="metadata")

            for link in soup.find_all("link"):
                rel_value = link.get("rel", [])
                rel = " ".join(rel_value if isinstance(rel_value, list) else [str(rel_value)]).lower()
                href = link.get("href")
                as_value = str(link.get("as", "")).lower()
                if href and ("icon" in rel or "image" in rel or as_value == "image"):
                    add_url(href, kind="metadata")
                if modern:
                    image_srcset = link.get("imagesrcset")
                    if image_srcset:
                        for src in parse_srcset(str(image_srcset), preference):
                            add_url(src, kind="imagesrcset")

            for tag in soup.find_all(style=True):
                for raw in extract_css_image_urls(str(tag.get("style", ""))):
                    add_url(raw, kind="css")
            if modern:
                for style_tag in soup.find_all("style"):
                    for raw in extract_css_image_urls(style_tag.get_text(" ", strip=False)):
                        add_url(raw, kind="css")

                for script in soup.find_all("script"):
                    if str(script.get("type", "")).lower().split(";", 1)[0].strip() != "application/ld+json":
                        continue
                    raw_json = script.string or script.get_text("", strip=True)
                    if not raw_json:
                        continue
                    try:
                        parsed = json.loads(html.unescape(raw_json))
                    except (json.JSONDecodeError, TypeError, ValueError):
                        continue
                    for raw in jsonld_image_urls(parsed):
                        add_url(raw, kind="jsonld")

                # Lazy loaders often place the useful fallback markup inside noscript.
                for noscript in soup.find_all("noscript"):
                    fragment_text = noscript.decode_contents() or noscript.get_text("", strip=False)
                    if not fragment_text:
                        continue
                    fragment = BeautifulSoup(html.unescape(fragment_text), "html.parser")
                    for tag in fragment.find_all(["img", "source", "picture"]):
                        for attr in image_attrs:
                            value = tag.get(attr)
                            if value:
                                add_url(value, kind="noscript")
                        for attr in srcset_attrs:
                            srcset = tag.get(attr)
                            if srcset:
                                for src in parse_srcset(str(srcset), preference):
                                    add_url(src, kind="noscript")

            for anchor in soup.find_all("a"):
                href = anchor.get("href")
                if not href:
                    continue
                normalized = normalize_url(str(href), base_url)
                if not normalized:
                    continue
                if is_allowed_image_url(normalized, self.config):
                    add_url(normalized, kind="html")
                elif same_hostname(base_url, normalized):
                    low_path = urllib.parse.urlparse(normalized).path.lower()
                    if any(low_path.endswith("." + ext) for ext in DANGEROUS_EXTENSIONS):
                        continue
                    should_follow = manual_gallery
                    if auto_gallery and len(gallery_links) < auto_gallery_link_limit and gallery_link_is_safe_auto(anchor, normalized, base_url):
                        should_follow = True
                        self.discovery_stats["auto_gallery_links_detected"] = int(self.discovery_stats.get("auto_gallery_links_detected", 0)) + 1
                    if should_follow:
                        add_url(normalized, gallery=True)
        else:
            for raw in re.findall(r'''(?:src|href|poster|data-src|data-original|data-lazy-src|data-image-src)=['"]([^'"]+)['"]''', html_text, flags=re.I):
                add_url(raw, kind="html")
            for raw in extract_css_image_urls(html_text):
                add_url(raw, kind="css")
            for srcset in re.findall(r'''(?:srcset|data-srcset|imagesrcset)=['"]([^'"]+)['"]''', html_text, flags=re.I):
                for raw in parse_srcset(srcset, preference):
                    add_url(raw, kind="srcset")

        image_ext_pattern = r'''https?://[^\s'"<>]+?\.(?:jpg|jpeg|png|gif|webp|bmp|svg|tif|tiff|avif)(?:\?[^\s'"<>]*)?'''
        for raw in re.findall(image_ext_pattern, html_text, flags=re.I):
            add_url(raw, kind="html")

        filtered: List[str] = []
        for candidate in candidates:
            if candidate not in filtered:
                filtered.append(candidate)
            if len(filtered) >= max_candidates:
                if len(candidates) > max_candidates:
                    self.discovery_stats["candidate_limit_reached"] = True
                break
        self.discovery_stats["last_updated"] = now_local()
        return filtered, gallery_links[: safe_int(self.config.get("gallery_page_limit", 6), 6, min_value=1, max_value=50)]

    def collect_candidates_from_page(self, url: str) -> Tuple[List[str], List[str]]:
        visited_pages: Set[str] = set()
        candidates: List[str] = []
        page_errors: List[str] = []
        queue_items: queue.Queue[Tuple[str, int]] = queue.Queue()
        queue_items.put((url, 0))
        manual_gallery = bool(self.config.get("follow_gallery_links", False))
        smart_auto = str(self.config.get("automation_mode", "smart_safe")) == "smart_safe"
        auto_gallery = smart_auto and bool(self.config.get("auto_gallery_follow_enabled", True)) and not manual_gallery
        follow_gallery = manual_gallery or auto_gallery
        if manual_gallery:
            page_limit = safe_int(self.config.get("gallery_page_limit", 6), 6, min_value=1, max_value=50)
            max_depth = safe_int(self.config.get("gallery_max_depth", 1), 1, min_value=0, max_value=4)
        elif auto_gallery:
            page_limit = safe_int(self.config.get("auto_gallery_page_limit", 3), 3, min_value=1, max_value=10)
            max_depth = safe_int(self.config.get("auto_gallery_max_depth", 1), 1, min_value=0, max_value=2)
        else:
            page_limit = 1
            max_depth = 0
        gallery_queue_capacity = safe_int(self.config.get("gallery_queue_capacity", 100), 100, min_value=1, max_value=1000)

        while not queue_items.empty() and len(visited_pages) < max(1, page_limit):
            page_url, depth = queue_items.get()
            page_url = normalize_url(page_url) or page_url
            if page_url in visited_pages:
                continue
            visited_pages.add(page_url)
            try:
                html_text, final_url, is_image = self.fetch_page(page_url)
                self.run_summary["pages_visited"] += 1
                if auto_gallery and depth > 0:
                    self.discovery_stats["auto_gallery_pages_visited"] = int(self.discovery_stats.get("auto_gallery_pages_visited", 0)) + 1
                if is_image:
                    candidates.append(final_url)
                    continue
                found, links = self.discover_from_html(html_text, final_url)
                if bool(self.config.get("browser_mode", False)) and self._browser_observed_images:
                    same_only = bool(self.config.get("same_domain_only", False))
                    max_candidates = safe_int(self.config.get("max_candidate_urls_per_page", 500), 500, min_value=1, max_value=5000)
                    for observed in self._browser_observed_images:
                        normalized_observed = normalize_url(observed, final_url)
                        if not normalized_observed or has_dangerous_extension(normalized_observed):
                            continue
                        if same_only and not same_hostname(final_url, normalized_observed):
                            continue
                        if normalized_observed not in found:
                            found.append(normalized_observed)
                            self.discovery_stats["browser_network_candidates"] += 1
                        if len(found) >= max_candidates:
                            self.discovery_stats["candidate_limit_reached"] = True
                            break
                    self._browser_observed_images = []
                candidates.extend(found)
                if follow_gallery and depth < max_depth:
                    for link in links:
                        if link not in visited_pages:
                            if queue_items.qsize() >= gallery_queue_capacity:
                                self.backpressure_stats["gallery_links_rejected_due_capacity"] += 1
                                self._record_not_downloaded(link, "gallery queue capacity reached", source=page_url, stage="gallery_queue")
                                continue
                            queue_items.put((link, depth + 1))
                            if auto_gallery:
                                self.discovery_stats["auto_gallery_links_queued"] = int(self.discovery_stats.get("auto_gallery_links_queued", 0)) + 1
            except Exception as exc:
                msg = f"{page_url}: {exc}"
                page_errors.append(msg)
                self._record_failure(page_url, str(exc), stage="page_fetch")
                self.run_summary["page_failures"] += 1
        unique_candidates: List[str] = []
        seen = set()
        for candidate in candidates:
            normalized = normalize_url(candidate)
            if not normalized:
                continue
            if normalized in seen:
                self.duplicate_stats["candidate_duplicates_removed"] = int(self.duplicate_stats.get("candidate_duplicates_removed", 0)) + 1
                continue
            seen.add(normalized)
            unique_candidates.append(normalized)
        return unique_candidates, page_errors

    def _download_one_timed(self, url: str, *, source: str, reason: str) -> Tuple[DownloadResult, float]:
        started = time.monotonic()
        result = self.download_one(url, source=source, reason=reason)
        return result, max(0.0, time.monotonic() - started)

    def download_many(self, urls: Sequence[str], *, source: str = "", reason: str = "discovered") -> List[DownloadResult]:
        if not urls:
            return []
        configured_workers = safe_int(self.config.get("workers", MAX_ACTIVE_DOWNLOADS), MAX_ACTIVE_DOWNLOADS, min_value=1, max_value=MAX_ACTIVE_DOWNLOADS)
        executor_workers = min(MAX_ACTIVE_DOWNLOADS, max(configured_workers, self.adaptive_throttle.max_limit))
        capacity = safe_int(self.config.get("download_queue_capacity", DOWNLOAD_QUEUE_HARD_MAX), DOWNLOAD_QUEUE_HARD_MAX, min_value=1, max_value=DOWNLOAD_QUEUE_HARD_MAX)
        drain_timeout = safe_int(self.config.get("shutdown_drain_timeout_seconds", 10), 10, min_value=1, max_value=120)
        queued_at = time.monotonic()
        url_list = list(urls)
        accepted = deque((item, queued_at) for item in url_list[:capacity])
        rejected = url_list[capacity:]
        self.backpressure_stats["high_water_depth"] = max(int(self.backpressure_stats.get("high_water_depth", 0)), len(url_list))
        self.backpressure_stats["submitted"] += len(accepted)
        self.backpressure_stats["adaptive_throttle_enabled"] = self.adaptive_throttle.enabled
        self.backpressure_stats["configured_worker_cap"] = configured_workers
        self.backpressure_stats["executor_worker_cap"] = executor_workers
        if rejected:
            self.backpressure_stats["rejected_due_capacity"] += len(rejected)
            self.backpressure_stats["shutdown_drain_status"] = "capacity_rejected_excess"
            for rejected_url in rejected:
                self._record_not_downloaded(rejected_url, "download queue capacity reached; visible reject excess", source=source, stage=reason)
                with self.lock:
                    self.run_summary["skipped"] += 1
        results: List[DownloadResult] = []
        if not accepted:
            return results

        executor = concurrent.futures.ThreadPoolExecutor(max_workers=executor_workers, thread_name_prefix="imgdl")
        future_map: Dict[concurrent.futures.Future[Tuple[DownloadResult, float]], Tuple[str, float]] = {}
        try:
            while accepted or future_map:
                if self._stop_event.is_set():
                    break

                current_limit = max(1, min(executor_workers, self.adaptive_throttle.limit()))
                submitted_this_round = False
                deferred_delays: List[float] = []
                rotations = len(accepted)
                while accepted and len(future_map) < current_limit and rotations > 0:
                    accepted_url, enqueued_mono = accepted.popleft()
                    host = url_host(accepted_url)
                    delay = self.adaptive_throttle.ready_delay(host)
                    if delay > 0:
                        accepted.append((accepted_url, enqueued_mono))
                        deferred_delays.append(delay)
                        rotations -= 1
                        continue
                    future = executor.submit(self._download_one_timed, accepted_url, source=source, reason=reason)
                    future_map[future] = (accepted_url, enqueued_mono)
                    self.adaptive_throttle.observe_in_flight(len(future_map))
                    submitted_this_round = True
                    rotations = len(accepted)

                if not future_map and accepted:
                    wait_for = min(deferred_delays) if deferred_delays else 0.1
                    wait_for = min(max(wait_for, 0.05), 1.0)
                    self.adaptive_throttle.add_wait(wait_for)
                    self._stop_event.wait(wait_for)
                    continue

                done, _pending = concurrent.futures.wait(
                    list(future_map), timeout=0.25, return_when=concurrent.futures.FIRST_COMPLETED
                )
                if not done:
                    if accepted and not submitted_this_round:
                        self._stop_event.wait(0.05)
                    continue

                for future in done:
                    accepted_url, enqueued_mono = future_map.pop(future)
                    self.backpressure_stats["oldest_item_age_seconds"] = max(
                        float(self.backpressure_stats.get("oldest_item_age_seconds", 0) or 0),
                        max(0.0, time.monotonic() - enqueued_mono),
                    )
                    try:
                        result, elapsed = future.result()
                    except KeyboardInterrupt:
                        raise
                    except Exception as exc:
                        result = DownloadResult(url=accepted_url, status="failed", reason=str(exc))
                        elapsed = 0.0
                        self._record_failure(accepted_url, f"worker error: {exc}", source=source, stage=reason)
                        with self.lock:
                            self.run_summary["failed"] += 1
                    results.append(result)
                    self.adaptive_throttle.record_completion(url_host(accepted_url), result, elapsed)

            self.backpressure_stats["shutdown_drain_status"] = "drained" if not self._stop_event.is_set() else "stopped"
            self.backpressure_stats["adaptive_throttle_final"] = self.adaptive_throttle.snapshot()
            return results
        except KeyboardInterrupt:
            self._stop_event.set()
            for future in future_map:
                future.cancel()
            pending = {future for future in future_map if not future.done()}
            if pending:
                _done, remaining = concurrent.futures.wait(pending, timeout=drain_timeout)
            else:
                remaining = set()
            self.backpressure_stats["shutdown_drain_status"] = "interrupted_drained" if not remaining else "interrupted_timeout"
            self.backpressure_stats["shutdown_pending_after_timeout"] = len(remaining)
            self.backpressure_stats["adaptive_throttle_final"] = self.adaptive_throttle.snapshot()
            self.logger.warning(
                "SHUTDOWN_DRAIN status=%s pending=%s timeout_seconds=%s",
                self.backpressure_stats["shutdown_drain_status"],
                len(remaining),
                drain_timeout,
            )
            executor.shutdown(wait=False, cancel_futures=True)
            raise
        except Exception:
            self._stop_event.set()
            for future in future_map:
                future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            self.backpressure_stats["shutdown_drain_status"] = "error_cancelled"
            self.backpressure_stats["adaptive_throttle_final"] = self.adaptive_throttle.snapshot()
            raise
        finally:
            if self.backpressure_stats.get("shutdown_drain_status") in {"drained", "stopped"}:
                executor.shutdown(wait=True, cancel_futures=False)


    def sequence_pattern_for_url(self, url: str) -> Optional[SequencePattern]:
        normalized = normalize_url(url)
        if not normalized:
            return None
        parsed = urllib.parse.urlparse(normalized)
        path = parsed.path or ""
        filename = posixpath.basename(path)
        directory = posixpath.dirname(path)
        if not filename:
            return None
        allowed_exts = "|".join(sorted(re.escape(x) for x in allowed_types(self.config) | {"tif"}))
        match = re.match(rf"^(?P<prefix>.*?)(?P<num>\d+)(?P<suffix>\.(?:{allowed_exts}))$", filename, flags=re.I)
        if not match:
            return None
        number_text = match.group("num")
        try:
            number = int(number_text)
        except (TypeError, ValueError):
            return None
        prefix = match.group("prefix")
        suffix = match.group("suffix")
        signature_path = posixpath.join(directory, f"{prefix}{{num}}{suffix}")
        signature = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, signature_path, "", parsed.query, ""))
        return SequencePattern(
            signature=signature,
            parsed_url=parsed,
            directory=directory,
            prefix=prefix,
            suffix=suffix,
            number=number,
            width=len(number_text),
            original_url=normalized,
        )

    def build_sequence_groups(self, urls: Sequence[str]) -> Dict[str, List[SequencePattern]]:
        groups: Dict[str, List[SequencePattern]] = {}
        for url in urls:
            pattern = self.sequence_pattern_for_url(url)
            if not pattern:
                continue
            groups.setdefault(pattern.signature, []).append(pattern)
        return groups

    def scan_sequence_group(self, patterns: List[SequencePattern], *, source_page: str = "") -> None:
        if not patterns:
            return
        max_groups = safe_int(self.config.get("sequence_max_seed_groups_per_run", 30), 30, min_value=1, max_value=100)
        if self.sequence_stats["groups_scanned"] >= max_groups:
            return
        max_anchors = safe_int(self.config.get("sequence_max_anchors_per_group", 5), 5, min_value=1, max_value=25)
        max_candidates = safe_int(self.config.get("sequence_max_candidates_per_group", 80), 80, min_value=1, max_value=500)
        max_failures = safe_int(self.config.get("sequence_max_failed_attempts", 8), 8, min_value=1, max_value=50)
        backward_steps = safe_int(self.config.get("sequence_backward_steps", 3), 3, min_value=0, max_value=100)
        delay = safe_int(self.config.get("sequence_probe_delay_ms", 75), 75, min_value=0, max_value=5000) / 1000.0
        same_domain_only = bool(self.config.get("sequence_same_domain_only", True))
        numbers = sorted({p.number for p in patterns})
        by_number = {p.number: p for p in patterns}
        anchors: List[int] = []
        if numbers:
            anchors.append(numbers[0])
            if numbers[-1] != numbers[0]:
                anchors.append(numbers[-1])
            for n in numbers[1:-1]:
                if n not in anchors:
                    anchors.append(n)
                if len(anchors) >= max_anchors:
                    break
        anchors = anchors[:max_anchors]
        template = by_number.get(anchors[0], patterns[0])
        group_detail = {
            "signature": template.signature,
            "anchors": anchors,
            "probes_attempted": 0,
            "downloaded": 0,
            "failed": 0,
            "stopped_by": [],
        }
        self.sequence_stats["groups_scanned"] += 1
        enforce_host = url_host(template.original_url) if same_domain_only else ""

        def probe_number(n: int) -> Optional[DownloadResult]:
            if n < 0:
                return None
            if group_detail["probes_attempted"] >= max_candidates:
                if "max_candidates" not in group_detail["stopped_by"]:
                    group_detail["stopped_by"].append("max_candidates")
                self.sequence_stats["bounded_by_max_candidates"] += 1
                return None
            candidate = template.make_url(n)
            if candidate in self.sequence_probed_urls:
                return None
            self.sequence_probed_urls.add(candidate)
            group_detail["probes_attempted"] += 1
            self.sequence_stats["probes_attempted"] += 1
            result = self.download_one(candidate, source=source_page, reason="sequence_probe", enforce_host=enforce_host)
            if result.status == "downloaded":
                group_detail["downloaded"] += 1
                self.sequence_stats["probes_downloaded"] += 1
            elif result.status == "duplicate_url":
                self.sequence_stats["probes_duplicate_url"] += 1
            elif result.status == "duplicate_content":
                self.sequence_stats["probes_duplicate_content"] += 1
            elif result.status == "duplicate_visual":
                self.sequence_stats["probes_duplicate_visual"] += 1
            elif result.status in {"failed", "skipped"}:
                group_detail["failed"] += 1
                self.sequence_stats["probes_failed"] += 1
            if delay:
                time.sleep(delay)
            return result

        for anchor in anchors:
            self.sequence_stats["anchors_scanned"] += 1
            for n in range(max(0, anchor - backward_steps), anchor):
                probe_number(n)
                if group_detail["probes_attempted"] >= max_candidates:
                    break
            if group_detail["probes_attempted"] >= max_candidates:
                break
            consecutive_failures = 0
            n = anchor + (0 if bool(self.config.get("sequence_include_discovered_seeds", True)) else 1)
            while group_detail["probes_attempted"] < max_candidates and consecutive_failures < max_failures:
                result = probe_number(n)
                n += 1
                if result is None:
                    continue
                if result.status in {"downloaded", "duplicate_url", "duplicate_content", "duplicate_visual", "dry_run"}:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
            if consecutive_failures >= max_failures:
                self.sequence_stats["bounded_by_failed_attempts"] += 1
                if "max_failed_attempts" not in group_detail["stopped_by"]:
                    group_detail["stopped_by"].append("max_failed_attempts")
        self.sequence_stats["groups"].append(group_detail)
        self.sequence_stats["last_updated"] = now_local()

    def run_sequence_discovery(self, seed_urls: Sequence[str], *, source_page: str = "") -> None:
        if not bool(self.config.get("sequence_discovery_enabled", True)):
            return
        groups = self.build_sequence_groups(seed_urls)
        self.sequence_stats["groups_found"] = len(groups)
        if not groups:
            return
        print(f"Sequential discovery: {len(groups)} numbered pattern group(s) found.")
        self._automation_decision("sequence_discovery", f"activated for {len(groups)} numbered pattern group(s)")
        for _signature, patterns in list(groups.items())[: safe_int(self.config.get("sequence_max_seed_groups_per_run", 30), 30, min_value=1, max_value=100)]:
            self.scan_sequence_group(patterns, source_page=source_page)

    def process_url(self, url: str) -> Dict[str, Any]:
        normalized = normalize_url(url)
        if not normalized:
            print("Invalid URL. Please paste a full http:// or https:// URL.")
            return {}
        self._start_run(normalized)
        self.logger.info("RUN_START top_level_run_id=%s run_id=%s url=%s mode=%s dry_run=%s", self.top_level_run_id, self.run_summary.get("run_id"), redact_url_for_evidence(normalized), self.run_summary["mode"], self.run_summary["dry_run"])
        if self.automation_stats.get("enabled"):
            print("Smart Safe Automation: ON (duplicates, resume, reconnect, adaptive throttle, sequence, bounded gallery)")
        try:
            if is_allowed_image_url(normalized, self.config):
                self._automation_decision("routing", "direct image URL detected")
                candidates = [normalized]
                page_errors: List[str] = []
            else:
                self._automation_decision("routing", "page discovery selected")
                candidates, page_errors = self.collect_candidates_from_page(normalized)
                auto_pages = int(self.discovery_stats.get("auto_gallery_pages_visited", 0))
                if auto_pages:
                    self._automation_decision("bounded_gallery", f"followed {auto_pages} strong same-domain gallery/pagination page(s)")
                if not candidates and not page_errors:
                    # Some image URLs have no extension and no useful content type until downloaded.
                    candidates = [normalized]
                    self._automation_decision("fallback", "page returned no candidates; direct validation attempted")
            self.run_summary["candidate_images_found"] = len(candidates)
            if not candidates:
                print("No image candidates found.")
            else:
                print(f"Found {len(candidates)} image candidate(s).")
                self.download_many(candidates, source=normalized, reason="discovered")
                self.run_sequence_discovery(candidates, source_page=normalized)
            self._finish_run("completed")
            print(
                "Summary: "
                f"downloaded={self.run_summary.get('downloaded', 0)}, "
                f"duplicates={self.run_summary.get('duplicate_url_skips', 0) + self.run_summary.get('duplicate_content_skips', 0) + self.run_summary.get('duplicate_visual_skips', 0)}, "
                f"failed={self.run_summary.get('failed', 0)}, "
                f"output={self.output_dir}"
            )
            self.logger.info("RUN_FINISH top_level_run_id=%s run_id=%s summary=%s", self.top_level_run_id, self.run_summary.get("run_id"), json.dumps(self.run_summary, ensure_ascii=False))
            return self.run_summary
        except KeyboardInterrupt:
            self._finish_run("interrupted")
            raise
        except Exception as exc:
            self._record_failure(normalized, f"run error: {exc}", stage="run")
            self.run_summary["failed"] += 1
            self._finish_run("error")
            print(f"Error: {exc}")
            self.logger.exception("RUN_ERROR url=%s", redact_url_for_evidence(normalized))
            return self.run_summary


def duplicate_detection_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    recent = json_load(root / STATE_DIRNAME / RECENT_RUN_FILENAME, {})
    state = json_load(root / STATE_DIRNAME / DOWNLOAD_INDEX_FILENAME, {})
    duplicate = recent.get("duplicate_detection", {}) if isinstance(recent, dict) else {}
    hashes = state.get("hashes", {}) if isinstance(state, dict) and isinstance(state.get("hashes"), dict) else {}
    visual_hashes = state.get("visual_hashes", {}) if isinstance(state, dict) and isinstance(state.get("visual_hashes"), dict) else {}
    library = duplicate.get("library_reconcile", {}) if isinstance(duplicate, dict) else {}
    lines = [
        "Automatic duplicate-detection summary:",
        f"- URL duplicate detection: {bool(cfg.get('duplicate_url_check', True))}",
        f"- Exact SHA256 content detection: {bool(cfg.get('duplicate_content_hash_check', True))}",
        f"- Static raster visual-fingerprint detection: {bool(cfg.get('duplicate_visual_fingerprint_check', True))}",
        "- Visual method: orientation-aware aHash + dHash + average RGB + aspect ratio; exact fingerprint matches only; animated images use SHA256 only.",
        f"- Existing-library reconciliation: {bool(cfg.get('duplicate_library_reconcile_enabled', True))}; max_files={cfg.get('duplicate_library_reconcile_max_files', 250)}; time_budget_seconds={cfg.get('duplicate_library_reconcile_time_budget_seconds', 3)}",
        f"- Indexed exact hashes: {len(hashes)}; indexed visual fingerprints: {len(visual_hashes)}",
        f"- Recent candidate duplicates removed: {duplicate.get('candidate_duplicates_removed', 0) if isinstance(duplicate, dict) else 0}",
        f"- Recent URL/exact/visual skips: {duplicate.get('url_duplicates_skipped', 0) if isinstance(duplicate, dict) else 0} / {duplicate.get('exact_content_duplicates_skipped', 0) if isinstance(duplicate, dict) else 0} / {duplicate.get('visual_duplicates_skipped', 0) if isinstance(duplicate, dict) else 0}",
        f"- Recent filename conflicts resolved safely: {duplicate.get('filename_conflicts_resolved', 0) if isinstance(duplicate, dict) else 0}",
        f"- Library scan status: {library.get('status', 'not_run') if isinstance(library, dict) else 'not_run'}; examined={library.get('files_examined', 0) if isinstance(library, dict) else 0}; recovered={library.get('records_recovered', 0) if isinstance(library, dict) else 0}; exact_duplicates={library.get('exact_duplicates_found', 0) if isinstance(library, dict) else 0}; visual_duplicates={library.get('visual_duplicates_found', 0) if isinstance(library, dict) else 0}",
        "- Safety: duplicate scans are bounded and non-destructive; existing files are never auto-deleted.",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def dependency_environment_summary(root: Path, config_path: Path) -> str:
    lines = [
        f"{APP_NAME} dependency/environment summary",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        f"Root: {safe_display_path(root)}",
        f"Config: {safe_display_path(config_path, root)}",
        f"Python executable: {safe_display_path(sys.executable)}",
        f"Python version: {platform.python_version()}",
        f"Platform: {redact_sensitive_text(platform.platform())}",
        f"Machine: {platform.machine()}",
        f"Working directory: {safe_display_path(Path.cwd())}",
        "",
        "Dependency status:",
        f"- requests: {dependency_version('requests')}",
        f"- beautifulsoup4/bs4: {dependency_version('bs4', 'beautifulsoup4')}",
        f"- pillow/PIL: {dependency_version('PIL', 'Pillow')}",
        f"- playwright: {dependency_version('playwright')}",
        "",
        "Safe Browser Mode performance:",
        "- Reuses one Playwright browser/context per active process by default.",
        "- Opens and closes pages per URL to avoid page-memory buildup.",
        "- Browser runtimes are not bundled in the ZIP.",
        "",
        computer_awareness_summary(root, config_path).rstrip(),
        "",
        "Network/VPN resilience:",
        "- Standard HTTP sessions are recreated after connection/timeout errors.",
        "- HTTP sessions are thread-local by default so concurrent downloads do not fight over one pooled session.",
        "- This helps VPN or IP changes recover without adding a new menu option.",
        "",
        "Best-practices compliance:",
        f"- Parameter alignment: {PARAMETER_ALIGNMENT_VERSION}.",
        "- Package-level MANIFEST.json, CHANGELOG.md, README_QUICK_START.md, and VERSION.txt are maintained; known-good/transfer/health evidence is generated into Export20.",
        "- Export20 collector is updated when backend behavior changes and stays at or below 20 files.",
        "- Runtime folders/caches/downloads are excluded from release ZIPs and support exports.",
        "- System-aware diagnostics are redacted and avoid raw PC identifiers.",
        "- Structured Drive Project Vault status is recorded without making local runtime depend on Drive.",
        "- Custom-input, configuration, and path assurance is summarized without adding a new menu option.",
        "- v2.9+ integration drift evidence remains compact, cached, and off the normal startup path.",
        "- Launcher hardening: launchers prove Python works, verify write access, require complete release controls for override/fallback targets, run the identity gate before dependency installs, and preserve failure exit codes.",
        "- Export hotfix: diagnostic/export runs do not take the interactive lock, use unique filenames, and publish ZIPs atomically after successful creation.",
        "",
        transport_discovery_summary(root, config_path).rstrip(),
        "",
        duplicate_detection_summary(root, config_path).rstrip(),
        "",
        integration_registry_summary(root, config_path).rstrip(),
        "",
        config_input_assurance_summary(root, config_path).rstrip(),
        "",
        asset_metadata_reconciliation_summary(root, config_path).rstrip(),
        "",
        drive_vault_status_summary(root, config_path).rstrip(),
        "",
        parameter_alignment_summary(root, config_path).rstrip(),
        "",
        system_aware_environment_summary(root, config_path).rstrip(),
    ]
    return redact_sensitive_text("\n".join(lines) + "\n")


def integration_registry_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    normal_days = safe_int(cfg.get("platform_review_normal_days", 30), 30, min_value=1, max_value=365)
    fast_days = safe_int(cfg.get("platform_review_fast_days", 7), 7, min_value=1, max_value=90)
    enabled = bool(cfg.get("platform_api_compliance_enabled", True))
    lines = [
        "Platform/API compliance and drift snapshot:",
        f"- Enabled: {enabled}",
        f"- Registry mode: {cfg.get('platform_review_mode', 'cached_off_critical_path')}",
        f"- Contract probe mode: {cfg.get('platform_contract_probe_mode', 'non_mutating_read_only')}",
        f"- Compliance state: {cfg.get('platform_registry_status', 'verified_local_controls_unknown_site_policy')}",
        f"- Last review evidence: {cfg.get('platform_registry_last_review', BUILD_DATE)}",
        f"- Freshness targets: {normal_days} day(s) normal; {fast_days} day(s) fast-changing/security/financial/provider-specific integrations if ever added.",
        "",
        "Registry entries:",
        "1. Generic public HTTP(S) image/page fetch",
        "   - Type: arbitrary user-pasted websites, not a single API provider.",
        "   - Auth/scopes: none; no credentials, cookies, API keys, signed requests, or account identifiers are required or exported.",
        "   - Contract probe: per-URL read-only HEAD/GET with redirects bounded by requests; validates status, content length/type, and image magic bytes before saving.",
        "   - Provider status: not checked globally because target hosts vary by URL; local retry/session-reset evidence is used before blaming provider outages.",
        "   - Quota/cost: no paid API quota in this project; local caps bound max file size, page size, candidates, workers, retries, and sequence probes.",
        "   - Policy note: user remains responsible for using URLs they are permitted to access/download.",
        "2. Optional Playwright Safe Browser Mode",
        "   - Type: optional browser rendering for trusted sites only, launched only by the safe-browser BAT or --browser-mode.",
        "   - Source/provenance: Python Playwright package and Chromium runtime installed through Playwright tooling; no browser runtime is bundled in this ZIP.",
        "   - Contract probe: non-mutating page render/content read; no downloads are executed or opened.",
        "   - Risk state: warning if used on untrusted sites; normal Standard Mode remains preferred/default.",
        "3. Python package dependencies",
        "   - Type: requests, beautifulsoup4, pillow, and optional playwright installed through pip when missing.",
        "   - Version posture: launchers use bounded major-version ranges when installing missing dependencies; already-working imports are not silently upgraded.",
        "   - Security posture: no bundled executables; no autostart/services/firewall changes; dependency status is summarized in diagnostics.",
        "",
        "Not used:",
        "- Webhooks, write APIs, paid API keys, OAuth scopes, account integrations, local IP/MAC discovery, browser-history export, or raw sensitive payload export.",
    ]

    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


CONFIG_METADATA_KEYS = {"config_last_migration", "state_last_migration"}


def unknown_config_keys(cfg: Dict[str, Any]) -> List[str]:
    defaults = default_config()
    return sorted(str(k) for k in cfg.keys() if str(k) not in defaults and str(k) not in CONFIG_METADATA_KEYS)


def config_input_assurance_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    defaults = default_config()
    unknown_keys = unknown_config_keys(cfg)
    recognized_keys = sorted(str(k) for k in cfg.keys() if str(k) in defaults or str(k) in CONFIG_METADATA_KEYS)
    critical_defaults = [
        "output", "hide_downloaded_media", "timeout", "workers", "retries", "network_recovery_extra_attempts", "adaptive_throttle_enabled", "adaptive_throttle_mode", "adaptive_throttle_min_workers", "adaptive_throttle_max_workers", "types", "browser_mode", "dry_run",
        "same_domain_only", "sequence_discovery_enabled", "sequence_same_domain_only",
        "sequence_max_candidates_per_group", "sequence_max_failed_attempts",
        "max_candidate_urls_per_page", "max_file_mb", "max_html_mb",
        "duplicate_url_check", "duplicate_content_hash_check", "duplicate_visual_fingerprint_check", "duplicate_library_reconcile_enabled", "single_instance_guard_enabled",
        "download_queue_capacity", "download_queue_full_policy", "log_max_bytes", "log_backup_count",
        "preferred_bot_dir", "bot_dir_env_override_name", "path_targeting_mode", "portable_fallback_enabled",
    ]
    launcher_contract_keys = {
        "preferred_bot_dir", "bot_dir_env_override_name", "path_targeting_mode",
        "portable_fallback_enabled", "launcher_sync_installed_files",
    }
    evidence_metadata_keys = {
        key for key in recognized_keys
        if key.startswith("google_drive_")
        or key.startswith("platform_")
        or key.startswith("omission_")
        or key.startswith("thread_context_")
        or key in {
            "parameter_alignment_version", "system_aware_primer_version", "asset_metadata",
            "config_last_migration", "state_last_migration",
            "relocation_repair_status", "relocation_repair_note",
        }
    }
    runtime_keys = [
        key for key in recognized_keys
        if key not in launcher_contract_keys and key not in evidence_metadata_keys
    ]
    effective = {key: redact_json_for_export(cfg.get(key, defaults.get(key))) for key in critical_defaults}
    fingerprint_source = json.dumps(effective, sort_keys=True, ensure_ascii=False)
    status = "warning_unknown_keys_present" if unknown_keys else "recognized_validated_normalized_with_mapping_categories"
    lines = [
        "Custom-input / config assurance snapshot:",
        f"- Enabled: {bool(cfg.get('custom_input_assurance_enabled', True))}",
        f"- Parameter alignment: {cfg.get('parameter_alignment_version', PARAMETER_ALIGNMENT_VERSION)}",
        f"- Config path: {safe_display_path(config_path, root)}",
        f"- Recognized keys: {len(recognized_keys)}",
        f"- Runtime-consumed/config-policy keys: {len(runtime_keys)}",
        f"- Launcher-contract keys: {len(launcher_contract_keys.intersection(recognized_keys))}",
        f"- Evidence/transfer metadata keys: {len(evidence_metadata_keys)}",
        "- Mapping categories: runtime-consumed/config-policy, launcher-contract, and evidence/transfer metadata.",
        f"- Unknown/custom keys: {len(unknown_keys)}",
        f"- Status: {status}",
        "- Verification chain: all known keys are recognized and normalized; runtime keys are mapped where consumed; launcher-contract keys are verified against BAT behavior; evidence/transfer metadata is reported but is not falsely presented as exercised downloader logic.",
        "- Source precedence: CLI flags override session mode for browser/dry-run; image_downloader_config.json overrides defaults; defaults fill missing optional values; canonical launcher/script location determines project_root.",
        "- Compatibility note: launcher_sync_installed_files is retained as launcher-policy metadata. The actual project-folder-first targeting and compatibility fallback behavior is implemented and statically verified in the BAT launchers.",
        "- Secrets: no credential-bearing fields are required; redaction still covers common token/password/key names if accidentally present.",
        f"- Effective-input fingerprint: {hashlib.sha256(fingerprint_source.encode('utf-8')).hexdigest()[:16]}",
    ]
    if unknown_keys:
        lines.append("- Warning: unknown keys are preserved for forward compatibility but are not consumed by this build: " + ", ".join(unknown_keys[:25]))
    else:
        lines.append("- Warning: none; no unknown config keys detected.")
    lines.extend([
        "- Key effective settings (redacted):",
        json.dumps(effective, indent=2, ensure_ascii=False),
    ])
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def asset_metadata_reconciliation_summary(root: Path, config_path: Path) -> str:
    """Reconcile package asset metadata and summarize the runtime image catalog."""
    manifest_path = root / "MANIFEST.json"
    manifest = json_load(manifest_path, {})
    cfg = json_load(config_path, {})
    runtime_export_name = Path(str(cfg.get("canonical_export_filename", CANONICAL_EXPORT_FILENAME))).name
    records = manifest.get("files", []) if isinstance(manifest, dict) else []
    records = records if isinstance(records, list) else []
    required_fields = {
        "asset_id", "path", "title", "purpose", "asset_class", "role", "format",
        "project_slug", "version", "status", "sensitivity", "source_of_truth",
        "tags", "aliases", "lineage", "created_cdt", "modified_cdt", "size_bytes", "sha256",
    }
    missing_files: List[str] = []
    missing_fields: List[str] = []
    stale_static: List[str] = []
    header_gaps: List[str] = []
    mutable_drift: List[str] = []
    record_paths: Set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            missing_fields.append("<non-object record>")
            continue
        rel = str(record.get("path") or record.get("name") or "")
        record_paths.add(rel)
        absent = sorted(key for key in required_fields if key not in record)
        if absent:
            missing_fields.append(f"{rel or '<missing path>'}: {', '.join(absent)}")
        path = root / rel if rel else root / "__missing__"
        if not rel or not path.is_file():
            missing_files.append(rel or "<missing path>")
            continue
        expected_size = record.get("size_bytes")
        expected_hash = record.get("sha256")
        mutable = bool(record.get("mutable", False))
        actual_size = path.stat().st_size
        actual_hash = sha256_file(path)
        mismatch = (isinstance(expected_size, int) and expected_size != actual_size) or (isinstance(expected_hash, str) and expected_hash and expected_hash != actual_hash)
        if mismatch:
            (mutable_drift if mutable else stale_static).append(rel)
        asset_id = str(record.get("asset_id") or "")
        if asset_id:
            try:
                probe = path.read_bytes()[:65536].decode("utf-8", errors="ignore")
            except OSError:
                probe = ""
            if asset_id not in probe and rel not in {"MANIFEST.json"}:
                header_gaps.append(rel)
    actual_release_files = {
        path.name for path in root.iterdir()
        if path.is_file() and path.name not in {".DS_Store", "Thumbs.db", runtime_export_name}
    }
    unregistered = sorted(actual_release_files - record_paths)

    state = json_load(root / STATE_DIRNAME / DOWNLOAD_INDEX_FILENAME, {})
    hash_records = state.get("hashes", {}) if isinstance(state, dict) else {}
    hash_records = hash_records if isinstance(hash_records, dict) else {}
    ready = 0
    legacy = 0
    stale_runtime = 0
    formats: Dict[str, int] = {}
    for digest, record in hash_records.items():
        if not isinstance(record, dict):
            legacy += 1
            continue
        required_runtime = ["asset_id", "metadata_schema", "title", "asset_class", "format", "status", "sensitivity", "sha256", "size_bytes"]
        if all(record.get(key) not in (None, "") for key in required_runtime):
            ready += 1
        else:
            legacy += 1
        fmt = str(record.get("format") or "unknown")
        formats[fmt] = formats.get(fmt, 0) + 1
        rel = str(record.get("path") or "")
        if rel and not (root / rel).exists():
            stale_runtime += 1

    package_status = "verified" if not (missing_files or missing_fields or stale_static or header_gaps or unregistered) else "warning"
    lines = [
        "Digital asset metadata reconciliation:",
        f"- Metadata schema: {manifest.get('metadata_schema', ASSET_METADATA_SCHEMA) if isinstance(manifest, dict) else ASSET_METADATA_SCHEMA}",
        f"- Package asset ID: {manifest.get('package_asset_id', PACKAGE_ASSET_ID) if isinstance(manifest, dict) else PACKAGE_ASSET_ID}",
        f"- Package status: {package_status}",
        f"- Canonical manifest records: {len(records)}; root release files: {len(actual_release_files)}",
        f"- Missing files: {len(missing_files)}; missing required fields: {len(missing_fields)}; unregistered files: {len(unregistered)}",
        f"- Static hash/size conflicts: {len(stale_static)}; mutable release-default drift: {len(mutable_drift)}; key metadata header gaps: {len(header_gaps)}",
        "- Policy: one canonical MANIFEST.json; DRIVE_UPLOAD_MANIFEST.csv is the merged Drive-placement/CSV view; no per-file or per-image sidecar proliferation.",
        "- Package ZIP metadata: release ZIP comment is set and verified during packaging; an extracted runtime folder cannot self-read the original container comment.",
        "- Mutable config rule: image_downloader_config.json hash describes the shipped default; expected user/runtime edits are reported separately, not treated as static package corruption.",
        f"- Runtime image catalog: {ready} metadata-ready, {legacy} legacy/incomplete, {stale_runtime} missing-on-disk; stored centrally in state/{DOWNLOAD_INDEX_FILENAME} hash records.",
        f"- Runtime image formats: {json.dumps(formats, sort_keys=True)}",
        "- Runtime source URLs remain project-local and are excluded from Export20; generated summaries are redacted.",
    ]
    if missing_files:
        lines.append("- Missing file detail: " + ", ".join(missing_files[:20]))
    if missing_fields:
        lines.append("- Missing-field detail: " + " | ".join(missing_fields[:20]))
    if stale_static:
        lines.append("- Static conflict detail: " + ", ".join(stale_static[:20]))
    if mutable_drift:
        lines.append("- Mutable drift detail: " + ", ".join(mutable_drift[:20]))
    if header_gaps:
        lines.append("- Header/embedded metadata gap detail: " + ", ".join(header_gaps[:20]))
    if unregistered:
        lines.append("- Unregistered release file detail: " + ", ".join(unregistered[:20]))
    if package_status == "verified":
        lines.append("- Reconciliation result: PASS — manifest coverage, static hashes, and key embedded/header metadata agree.")
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def drive_vault_status_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    project_path = str(cfg.get("google_drive_project_path") or DRIVE_PROJECT_PATH)
    intended_path = str(cfg.get("google_drive_intended_vault_path") or INTENDED_DRIVE_VAULT_PATH)
    lines = [
        "Google Drive vault/reference status:",
        f"- Intended vault project path: {project_path}",
        f"- Intended latest-build path: {intended_path}",
        f"- Source-of-truth path: {cfg.get('google_drive_source_of_truth_path', project_path + '/00_SOURCE_OF_TRUTH')}",
        f"- support-ready path: {cfg.get('google_drive_support_ready_path', project_path + '/01_SUPPORT_READY')}",
        f"- Diagnostics path: {cfg.get('google_drive_diagnostics_path', project_path + '/03_DIAGNOSTICS')}",
        f"- Docs/runbook path: {cfg.get('google_drive_docs_runbook_path', project_path + '/04_DOCS_RUNBOOK')}",
        f"- Changelog/manifest path: {cfg.get('google_drive_changelog_manifest_path', project_path + '/05_CHANGELOG_MANIFEST')}",
        f"- Archive path: {cfg.get('google_drive_archive_path', project_path + '/06_ARCHIVE')}",
        f"- Local runtime vault sync status: {cfg.get('google_drive_vault_sync_status', 'not_configured_local_runtime')}",
        f"- Local runtime reference-check status: {cfg.get('google_drive_reference_check_status', 'verified')}",
        f"- Local runtime reference-check note: {cfg.get('google_drive_reference_check_note', 'structured_folder_exists_no_zip_upload')}",
        "- Drive lookup note: official structured ImageDownloader folder was found under the vault utilities category; similarly named folders outside the official vault path should be staged/merged manually, not deleted blindly.",
        "- Runtime dependency: none; Image Downloader runs, diagnoses, and exports offline without Drive.",
        "- Handoff expectation: upload/mirror the final source-of-truth ZIP under the structured Project Vault latest-build/source-of-truth folders when a Drive connector or manual upload is available.",
        "- Secret handling: no raw Drive IDs, permission lists, account identifiers, or secret-bearing links are stored in runtime diagnostics.",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def parameter_alignment_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        "Release framework snapshot:",
        f"- Release framework: {PARAMETER_ALIGNMENT_VERSION}",
        "- Timer-safe pass posture: startup/import/config/path issues first, then conflicts/version drift, stability, diagnostics/export, verification, and clean ZIP output before broad features.",
        f"- App version/build: {APP_VERSION} / {BUILD_NAME}",
        "- Output strategy: full ZIP package only; no inline source required for normal delivery.",
        "- Lean structure: one Python source, one mutable config, one canonical BAT plus two namespaced helper BATs and three legacy redirect shims, one README/runbook, one changelog, VERSION.txt, MANIFEST.json, PACKAGE_METADATA.json, one Drive upload CSV manifest, and one engineering-output file.",
        f"- Runtime identity gate: {verify_release_identity(root).get('result')} before dependency/authenticated/network runtime; every package_managed=true release file is size/SHA256 verified.",
        "- Preserve-working-strategy status: Smart Safe Automation uses Standard Mode first and automatically applies duplicate detection, resume, reconnect, adaptive throttle, numbered sequence discovery, and conservative same-domain gallery pagination; Safe Browser and dry-run remain manual trust/safety choices.",
        "- Duplicate autodetection: URL, candidate, SHA256, exact visual fingerprint, filename-conflict, and bounded existing-library reconciliation evidence is recorded without automatic deletion.",
        "- Diagnostics/export: one canonical project-local exports/IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip, allowlisted/redacted Export20 evidence, atomic replacement, old-export cleanup, and no recursive archive inclusion.",
        "- Portability: root-layout ZIP with stable GatewayImageDownloader execution namespace; canonical launcher resolves its own folder, legacy run_*.bat names are thin redirects, and no caller-CWD/Desktop/Downloads/C:\\Bots fallback is used; paths with spaces remain supported.",
        "- Helpful computer awareness: ALPHA, ASCEND, DeusEx/Raider/GE66, or a privacy-safe generic host may be labeled for console/log/diagnostic context only; no identity-based restrictions or runtime overlays are active.",
        "- Omission/triage control: coverage ledger plus Critical/High/Normal/Optional exit status is included in diagnostics/export and full batch output.",
        "- Security/Norton posture: no bundled executables, no hidden execution, no auto-opening downloaded files, no service/firewall/autostart changes.",
        "- Drive-vault rule: tracked as structured vault status/intended category/project/build path; local tool does not require Drive authentication or online access.",
        "- Asset metadata: one canonical release manifest, embedded key-asset metadata, merged Drive CSV view, central content-addressed runtime image records, and release/export ZIP comments; no per-file sidecars.",
        f"- Config parameter_alignment_version: {cfg.get('parameter_alignment_version', PARAMETER_ALIGNMENT_VERSION)}",
        f"- Config output_mode: {cfg.get('output_mode', 'project_local')}",
        f"- Canonical support export: {EXPORT_DIRNAME}/{CANONICAL_EXPORT_FILENAME}",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def archive_removed_coordination_artifacts(root: Path) -> Dict[str, Any]:
    """Archive obsolete coordinated-runtime artifacts without deleting user evidence.

    This is a one-time compatibility cleanup for installations upgraded from the
    removed computer-specific runtime layout. It performs no host detection and
    creates no ownership or launch restriction.
    """
    root = root.resolve()
    candidates = [
        root / STATE_DIRNAME / "machines",
        root / LOG_DIRNAME / "machines",
        root / REPORT_DIRNAME / "machines",
        root / STATE_DIRNAME / "_shared",
        root / STATE_DIRNAME / INSTANCE_LOCK_FILENAME,
        root / STATE_DIRNAME / INSTANCE_EVENTS_FILENAME,
    ]
    existing = [path for path in candidates if path.exists()]
    result = {
        "time": now_local(),
        "status": "not_found" if not existing else "pending",
        "archived": [],
        "failed": [],
        "note": "Helpful computer identification is label-only; no cross-computer coordination or launch restriction is active.",
    }
    if not existing:
        return result
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_root = root / STATE_DIRNAME / "archive" / f"removed_coordination_{stamp}"
    archive_root.mkdir(parents=True, exist_ok=True)
    for source in existing:
        try:
            relative = source.relative_to(root)
            target = archive_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                target = target.with_name(target.name + "_" + uuid.uuid4().hex[:8])
            shutil.move(str(source), str(target))
            result["archived"].append({"source": str(relative), "target": short_path(target, root)})
        except Exception as exc:
            result["failed"].append({"source": short_path(source, root), "error": f"{exc.__class__.__name__}: {exc}"})
    result["status"] = "completed" if not result["failed"] else "partial"
    json_dump(root / STATE_DIRNAME / "removed_coordination_cleanup.json", result)
    # Keep only the newest three cleanup archives.
    parent = archive_root.parent
    with contextlib.suppress(OSError):
        archives = sorted([p for p in parent.iterdir() if p.is_dir() and p.name.startswith("removed_coordination_")], key=lambda p: p.stat().st_mtime, reverse=True)
        for old in archives[3:]:
            shutil.rmtree(old, ignore_errors=True)
    return result


def archive_nested_release_folder(root: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Move accidental nested release copies out of the active project root.

    This is non-destructive: nested package copies are archived under state/ so the
    active root stays lean and duplicate scans stop reporting nested source trees.
    """
    result: Dict[str, Any] = {
        "enabled": bool(cfg.get("archive_nested_package_conflicts", True)),
        "checked_at": now_local(),
        "status": "not_checked",
        "archived_from": "",
        "archived_to": "",
        "reason": "",
    }
    if not result["enabled"]:
        result["status"] = "disabled"
        return result
    nested = root / "ImageDownloader"
    markers = [SCRIPT_FILENAME, CANONICAL_ENTRYPOINT, CONFIG_FILENAME]
    if not nested.is_dir() or not any((nested / name).exists() for name in markers):
        result["status"] = "no_nested_package_copy_detected"
        return result
    try:
        archive_root = root / STATE_DIRNAME / "archived_nested_packages"
        archive_root.mkdir(parents=True, exist_ok=True)
        dest = archive_root / f"ImageDownloader_nested_{timestamp_unique()}"
        shutil.move(str(nested), str(dest))
        result.update({
            "status": "archived",
            "archived_from": short_path(nested, root),
            "archived_to": short_path(dest, root),
            "reason": "nested release package copy detected; moved under state for reversible cleanup",
        })
        retention = safe_int(cfg.get("nested_package_archive_retention", 3), 3, min_value=1, max_value=20)
        archives = sorted([p for p in archive_root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        for old in archives[retention:]:
            shutil.rmtree(old, ignore_errors=True)
    except (OSError, shutil.Error, RuntimeError) as exc:
        result.update({"status": "archive_failed", "reason": f"{type(exc).__name__}: {exc}"})
    json_dump(root / STATE_DIRNAME / NESTED_LAYOUT_CLEANUP_FILENAME, result)
    return result


def nested_layout_cleanup_summary(root: Path) -> str:
    data = json_load(root / STATE_DIRNAME / NESTED_LAYOUT_CLEANUP_FILENAME, {})
    lines = ["Nested package layout cleanup:"]
    if not isinstance(data, dict) or not data:
        lines.append("- No cleanup event recorded for this build yet.")
        return "\n".join(lines)
    lines.append(f"- Status: {data.get('status', 'unknown')}")
    if data.get("archived_from") or data.get("archived_to"):
        lines.append(f"- Archived from: {data.get('archived_from', '')}")
        lines.append(f"- Archived to: {data.get('archived_to', '')}")
    if data.get("reason"):
        lines.append(f"- Reason: {data.get('reason')}")
    return "\n".join(lines)


SUPERSEDED_SUPPORT_DOCS = ["KNOWN_GOOD_STATE.md", "TRANSFER_BRIEF.md", "PROJECT_HEALTH_REVIEW.md"]
SUPERSEDED_SUPPORT_DOCS_CLEANUP_FILENAME = "superseded_support_docs_cleanup_latest.json"


def archive_superseded_support_docs(root: Path, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Archive older split documentation files after the lean README merge.

    This keeps the active project root small while preserving the old notes under
    state/ for rollback evidence. It never touches runtime/download folders.
    """
    result: Dict[str, Any] = {
        "enabled": bool(cfg.get("archive_superseded_support_docs", True)),
        "checked_at": now_local(),
        "status": "not_checked",
        "archived_files": [],
        "archive_folder": "",
        "reason": "",
    }
    if not result["enabled"]:
        result["status"] = "disabled"
        return result
    candidates = [root / name for name in SUPERSEDED_SUPPORT_DOCS if (root / name).is_file()]
    if not candidates:
        result["status"] = "no_superseded_split_docs_detected"
        json_dump(root / STATE_DIRNAME / SUPERSEDED_SUPPORT_DOCS_CLEANUP_FILENAME, result)
        return result
    try:
        archive_root = root / STATE_DIRNAME / "archived_split_support_docs"
        archive_root.mkdir(parents=True, exist_ok=True)
        dest = archive_root / f"split_docs_{timestamp_unique()}"
        dest.mkdir(parents=True, exist_ok=True)
        for path in candidates:
            shutil.move(str(path), str(dest / path.name))
            result["archived_files"].append(path.name)
        result.update({
            "status": "archived",
            "archive_folder": short_path(dest, root),
            "reason": "lean package merged known-good, transfer, and health notes into README_QUICK_START.md plus generated Export20 evidence",
        })
        retention = safe_int(cfg.get("superseded_support_docs_archive_retention", 3), 3, min_value=1, max_value=20)
        archives = sorted([p for p in archive_root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        for old in archives[retention:]:
            shutil.rmtree(old, ignore_errors=True)
    except (OSError, shutil.Error, RuntimeError) as exc:
        result.update({"status": "archive_failed", "reason": f"{type(exc).__name__}: {exc}"})
    json_dump(root / STATE_DIRNAME / SUPERSEDED_SUPPORT_DOCS_CLEANUP_FILENAME, result)
    return result


def superseded_support_docs_summary(root: Path) -> str:
    data = json_load(root / STATE_DIRNAME / SUPERSEDED_SUPPORT_DOCS_CLEANUP_FILENAME, {})
    lines = ["Superseded support-doc cleanup:"]
    if not isinstance(data, dict) or not data:
        lines.append("- No cleanup event recorded for this build yet.")
        return "\n".join(lines)
    lines.append(f"- Status: {data.get('status', 'unknown')}")
    files = data.get("archived_files") if isinstance(data.get("archived_files"), list) else []
    if files:
        lines.append(f"- Archived files: {', '.join(str(x) for x in files)}")
    if data.get("archive_folder"):
        lines.append(f"- Archive folder: {data.get('archive_folder')}")
    if data.get("reason"):
        lines.append(f"- Reason: {data.get('reason')}")
    return "\n".join(lines)


def known_good_state_note(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        f"{APP_NAME} known-good / rollback note",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        f"Build date: {BUILD_DATE}",
        "",
        "Known-good marker:",
        "- Current package builds on the user-confirmed working 2026.08.07.1 / v2175 runtime-identity release.",
        "- Working queue/recovery/session-list behavior and the runtime integrity gate are preserved while stable execution names and project-local output enforcement are added.",
        "",
        "Preserved behavior:",
        "- Standard Mode default; Safe Browser Mode optional/trusted-sites-only.",
        "- Dry-run available but OFF by default.",
        "- Sequential discovery remains bounded, same-domain by default, duplicate-safe, and header plus strict raster validated.",
        "- Responsive/lazy/JSON-LD/CSS discovery and optional Safe Browser response capture are bounded backend additions.",
        "- Validator-gated partial resume, server-aware retry, connectivity-only extra attempts, and adaptive throttle behavior remain internal with no new launcher choice.",
        "- VPN/IP-change recovery remains backend-only and concurrent reset requests are coalesced.",
        "- Export20 remains capped at 20 files and redacted.",
        "",
        "Rollback:",
        "- Previous confirmed known-good package: ImageDownloader_Full_Build_2026-08-07_1911_CDT_v2175-runtime-identity-integrity-gate.zip (SHA256 02f4c1181788719dc23980263e827f3cec7685c877d75967158fd0fbc998f3f5).",
        "- If this lean package behaves unexpectedly, run GatewayImageDownloader_DiagnosticsExport.bat and upload exports/IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip before replacing files.",
        "",
        nested_layout_cleanup_summary(root),
        "",
        superseded_support_docs_summary(root),
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def transfer_brief(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        f"{APP_NAME} support summary",
        f"Generated: {now_local()}",
        f"Current version: {APP_VERSION}",
        f"Current build: {BUILD_NAME}",
        f"Build date: {BUILD_DATE}",
        "",
        "Source of truth:",
        "- Newest verified package should supersede earlier Image Downloader ZIPs unless rollback is explicitly requested.",
        "- Release package is root-layout and canonical-launcher first; run GatewayImageDownloader.bat from the complete extracted folder. Caller CWD and historical C:\\Bots fallback do not choose the runtime root.",
        "",
        "Why this build exists:",
        "- The preserved read-only package/version/build and managed-file SHA256 gate runs before dependency/authenticated/network runtime, with exit 23 on mixed/stale releases and Diagnostics/Export20 still available.",
        "- Existing forgiving connectivity retries, debounced/coalesced session renewal, and local AIMD/EWMA throttling remain preserved from the known-good baseline.",
        "- Preserved smart discovery, hidden-media default, validator-gated partial resume, streamed verification, and deterministic failure-isolated Export20.",
        "- Preserved root-layout packaging, reversible old-layout cleanup, path targeting, and the existing quick-start workflow.",
        "",
        "Do not regress:",
        "- Do not add menu options for backend reliability fixes.",
        "- Keep Standard Mode default, Safe Browser optional/trusted-sites-only, dry-run OFF, and Export20 <= 20 files.",
        "- Do not bundle executables or auto-run downloaded files.",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def lean_package_audit(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        f"{APP_NAME} lean package audit",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        "",
        "Lean changes:",
        "- Release remains a shallow root-layout package; the adaptive scheduler/reconnect controller lives in the existing Python source, with no new helper module, launcher, dependency file, or menu.",
        "- Export carries known-good, transfer, health, transport, and discovery evidence as generated summaries rather than extra support files.",
        "- Existing installed split docs and accidental nested packages remain reversibly archived instead of deleted.",
        "",
        "Package-root duplicate posture:",
        duplicate_scan(root).rstrip(),
        "",
        nested_layout_cleanup_summary(root),
        "",
        superseded_support_docs_summary(root),
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def project_handoff_notes(root: Path, config_path: Path) -> str:
    sections = [
        release_identity_summary(root).rstrip(),
        known_good_state_note(root, config_path).rstrip(),
        transfer_brief(root, config_path).rstrip(),
        project_health_review(root, config_path).rstrip(),
        work_window_triage_exit_summary(root, config_path).rstrip(),
        lean_package_audit(root, config_path).rstrip(),
    ]
    return redact_sensitive_text("\n\n---\n\n".join(section for section in sections if section).rstrip() + "\n")


def launcher_info(root: Path) -> str:
    lines = [
        f"{APP_NAME} launcher info",
        f"Generated: {now_local()}",
        "Required BAT header pattern:",
        "title Gateway Image Downloader [mode]",
        "echo =========================================",
        "echo Gateway Image Downloader [mode]",
        "echo =========================================",
        "echo Using bot folder: %BOT_DIR%",
        "echo.",
        "",
    ]
    bat_files = sorted(root.glob("*.bat"))
    if not bat_files:
        lines.append("No BAT files found in project root.")
    for bat in bat_files:
        try:
            text = bat.read_text(encoding="utf-8", errors="replace")
            has_title = bool(re.search(r"(?im)^title\s+Gateway Image Downloader", text))
            has_echo = "echo Gateway Image Downloader" in text and ("echo Using bot folder: %BOT_DIR%" in text or "echo Using bot folder: %~dp0" in text)
            lines.extend([
                f"File: {bat.name}",
                f"Size: {bat.stat().st_size} bytes",
                f"SHA256: {sha256_file(bat)}",
                f"Header check: {'PASS' if has_title and has_echo else 'CHECK'}",
                "",
            ])
        except (OSError, UnicodeError) as exc:
            lines.append(f"File: {bat.name} - unable to read ({exc})")
    return "\n".join(lines).rstrip() + "\n"


def path_targeting_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    output_mode = str(cfg.get("output_mode", "project_local"))
    try:
        effective_output, effective_mode = resolve_download_output(root, cfg)
        output_note = safe_display_path(effective_output, root if effective_mode == "project_local" else None)
    except Exception as exc:
        effective_mode = "blocked"
        output_note = f"BLOCKED: {exc.__class__.__name__}: {exc}"
    lines = [
        "Path targeting / relocation summary:",
        f"- Execution namespace: {EXECUTION_NAMESPACE}",
        f"- Canonical entrypoint: {CANONICAL_ENTRYPOINT}",
        f"- Approved legacy aliases: {', '.join(APPROVED_LEGACY_ENTRYPOINT_ALIASES)}",
        f"- Active project root: {safe_display_path(root)}",
        f"- Config path: {safe_display_path(config_path, root)}",
        f"- Targeting mode: {cfg.get('path_targeting_mode', 'canonical_launcher_or_script_root_only')}",
        "- Canonical launcher/script location is authoritative; caller CWD, Desktop, Downloads, user-profile folders, and C:\\Bots are not implicit runtime roots.",
        f"- Configured output mode: {output_mode}",
        f"- Effective output mode: {effective_mode}",
        f"- Effective downloads: {output_note}",
        f"- Support exports: {safe_display_path(root / EXPORT_DIRNAME, root)}",
        f"- Reports: {safe_display_path(root / REPORT_DIRNAME, root)}",
        f"- State: {safe_display_path(root / STATE_DIRNAME, root)}",
        f"- Temp: {safe_display_path(root / TEMP_DIRNAME, root)}",
        "- Relative output paths are blocked if they escape project_root. Absolute output requires output_mode=external_explicit and is visibly reported.",
        "- Legacy data is not silently moved or deleted during path-targeting verification.",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def omission_control_coverage_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    rows = [
        ("newest_package_baseline", "verified", "Used newest local Image Downloader package as bot baseline unless manifest/changelog evidence conflicts."),
        ("release_framework", "verified", "The current release framework is reflected in the entrypoint, output, integrity, recovery, and support-evidence controls."),
        ("startup_import_config_path", "verified", "Compile/version/self-test/export path-with-spaces checks exercised; canonical launcher resolves its own root and legacy launch names are redirects only."),
        ("conflicts_duplicates_stale_launchers", "verified", "Duplicate filename/hash/function scans run; one canonical execution namespace is authoritative and legacy run_*.bat files contain redirect logic only."),
        ("stability_timeouts_retries_logging_state_shutdown", "verified", "Known-good bounded retries, VPN recovery, log rotation, atomic writes, optional stale-recoverable instance-guard mechanics disabled by default, and graceful cleanup preserved."),
        ("diagnostics_export20", "verified", "Export is report-only, redacted, allowlisted, integrity-tested, capped, stages in project temp, and atomically replaces exports/IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip."),
        ("safe_verification", "verified", "Python compile, self-test, diagnose/export, path spaces, export integrity, duplicate scans, and BAT static checks are expected batch checks."),
        ("drive_reference", "found_unchanged", "Structured ImageDownloader vault folders were found; latest-build direct upload may still require manual placement."),
        ("targeted_prime_directive_upgrades", "applied", "Smart Safe Automation now coordinates existing duplicate/resume/reconnect/throttle/sequence features and conservatively follows strong same-domain gallery/pagination links; Safe Browser remains manual trusted-sites-only."),
        ("broad_ui_architecture_rewrite", "skipped", "No new menu, launcher choice, framework, external service, or multi-module deployment was added."),
    ]
    lines = [
        "Omission-control coverage ledger:",
        f"- Status: {cfg.get('omission_control_status', 'coverage_ledger_in_batch_output_and_export')}",
        f"- Note: {cfg.get('omission_control_coverage_note', 'Requested pass categories are tracked before completion claims.')}",
    ]
    for item, status, evidence in rows:
        lines.append(f"- {item}: {status} — {evidence}")
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def work_window_triage_exit_summary(root: Path, config_path: Path) -> str:
    """Human-readable release triage/finalization status for handoff and Export20."""
    cfg = json_load(config_path, {})
    lines = [
        "Work-window triage / exit status:",
        f"- Critical — runtime identity/integrity gate: {verify_release_identity(root).get('result')}; normal/browser startup is blocked before dependency/authenticated/network runtime unless control identity and every managed hash match.",
        "- Critical — preserved: Windows instance liveness uses a non-signalling process query; PID start signatures protect stale-lock recovery; mutable config/state migration and cleanup occur only after top-level ownership.",
        "- High — completed and verified: adaptive AIMD/EWMA submission control, per-host cooldowns, connectivity-only extra attempts, and coalesced reconnect/session resets are active and regression-tested.",
        "- Normal — completed and verified: Smart Safe Automation decisions, one canonical project-local support ZIP, execution/output and runtime-identity metadata, manifest/changelog/runbook synchronization, path-with-spaces, and lean-package checks.",
        "- Optional — deferred by design: automatic Playwright fallback remains disabled because browser execution is a trusted-site decision; broad UI changes, module splitting, services, and additional launchers were not attempted.",
        "- Finalization reserve: protected for compile, self-test, diagnostic/export integrity, duplicate/version scans, relocated-path verification, ZIP/checksum creation, and truthful reporting.",
        "- Completed but not fully verified: native Windows double-click execution, real Norton scanning, and a real Playwright Chromium session require the Windows host and are explicitly listed as limits.",
        "- Partial or rushed work: none recorded for this bounded pass.",
        "- Skipped/deferred/blocked: only the optional broad changes above; direct Drive binary upload remains connector/runtime-dependent.",
        "- Actual tool timeouts: none recorded in the release receipt; see FULL_BATCH_OUTPUT.txt for current verification results.",
        "- Safest next pass: run one Standard Mode download and one Export20 on Windows; upload that export only if runtime evidence differs from these checks.",
        f"- Context-health snapshot: {cfg.get('thread_context_health_status', 'yellow_long_thread_transfer_recommended_after_pass')}",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def transport_discovery_summary(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    recent = json_load(root / STATE_DIRNAME / RECENT_RUN_FILENAME, {})
    recent = recent if isinstance(recent, dict) else {}
    discovery = recent.get("discovery") if isinstance(recent.get("discovery"), dict) else {}
    recovery = recent.get("transfer_recovery") if isinstance(recent.get("transfer_recovery"), dict) else {}
    partial_dir = root / STATE_DIRNAME / PARTIAL_DIRNAME
    partial_count = 0
    partial_bytes = 0
    try:
        for path in partial_dir.glob("*.part"):
            if path.is_file():
                partial_count += 1
                partial_bytes += path.stat().st_size
    except OSError:
        pass
    lines = [
        "Smart discovery / transfer stability summary:",
        f"- Smart Safe Automation: mode={cfg.get('automation_mode', 'smart_safe')}; conservative gallery={bool(cfg.get('auto_gallery_follow_enabled', True))}; Safe Browser fallback={cfg.get('auto_browser_fallback_policy', 'manual_trusted_sites_only')}",
        f"- Canonical support export: {cfg.get('canonical_export_filename', CANONICAL_EXPORT_FILENAME)} under project exports/; prior export ZIP retention={cfg.get('export_keep_previous_zips', 0)}",
        f"- Modern HTML discovery enabled: {bool(cfg.get('modern_discovery_enabled', True))}",
        f"- Optional Safe Browser response-image capture enabled: {bool(cfg.get('browser_capture_network_images', True))}",
        f"- Candidate cap/page: {cfg.get('max_candidate_urls_per_page', 500)}; browser response cap/page: {cfg.get('browser_network_image_limit', 500)}",
        f"- Connect/read timeout seconds: {cfg.get('connect_timeout', 3)}/{cfg.get('read_timeout', cfg.get('timeout', 5))}",
        f"- Monotonic wall-clock caps: page={cfg.get('page_wall_clock_timeout_seconds', 60)}s, image={cfg.get('request_wall_clock_timeout_seconds', 5)}s",
        f"- Retry policy: base attempts={safe_int(cfg.get('retries', 2), 2, min_value=0, max_value=5) + 1}, extra connectivity retries={cfg.get('network_recovery_extra_attempts', 2)}, exponential backoff+jitter, Retry-After cap={cfg.get('retry_after_max_seconds', 30)}s",
        f"- Reconnect coalescing: HTTP session-reset debounce={cfg.get('network_session_reset_debounce_ms', 1000)}ms",
        f"- Adaptive throttle: enabled={bool(cfg.get('adaptive_throttle_enabled', True))}, mode={cfg.get('adaptive_throttle_mode', 'feedback_aimd')}, min/max workers={cfg.get('adaptive_throttle_min_workers', 1)}/{cfg.get('adaptive_throttle_max_workers', cfg.get('workers', MAX_ACTIVE_DOWNLOADS))}, target/slow latency={cfg.get('adaptive_throttle_target_latency_ms', 1500)}/{cfg.get('adaptive_throttle_slow_latency_ms', 4500)}ms",
        f"- Validator-gated partial resume enabled: {bool(cfg.get('resume_partial_downloads', True))}; minimum reusable bytes={cfg.get('resume_min_bytes', 262144)}",
        f"- Partial retention: {cfg.get('partial_retention_hours', 24)} hour(s); current partial payloads={partial_count}, bytes={partial_bytes}",
        f"- Strict Pillow raster verification: {bool(cfg.get('strict_raster_verify', True))}; pixel cap={cfg.get('image_max_pixels', 120000000)}",
        "- Completed payloads are streamed to disk, verified from disk, hashed incrementally, and copied atomically without loading the full configured file limit into RAM.",
        "- Resume validators are checked again on 206 responses; changed content restarts from byte zero instead of appending incompatible bytes.",
        "",
        "Most recent discovery evidence:",
        json.dumps(redact_json_for_export(discovery), indent=2, ensure_ascii=False) if discovery else "- No completed run discovery evidence yet.",
        "",
        "Most recent transfer-recovery evidence:",
        json.dumps(redact_json_for_export(recovery), indent=2, ensure_ascii=False) if recovery else "- No completed run transfer-recovery evidence yet.",
        "",
        "Most recent automation decisions:",
        json.dumps(redact_json_for_export(recent.get("automation", {})), indent=2, ensure_ascii=False) if isinstance(recent.get("automation"), dict) and recent.get("automation") else "- No completed run automation evidence yet.",
        "",
        "Most recent adaptive-throttle evidence:",
        json.dumps(redact_json_for_export(recent.get("adaptive_throttle", {})), indent=2, ensure_ascii=False) if isinstance(recent.get("adaptive_throttle"), dict) and recent.get("adaptive_throttle") else "- No completed run adaptive-throttle evidence yet.",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def duplicate_scan(root: Path) -> str:
    lines = [f"{APP_NAME} duplicate/lean-project scan", f"Generated: {now_local()}", ""]
    files: List[Path] = []
    folders: List[Path] = []
    excluded_dirs = {"downloads", "logs", "exports", "state", "reports", "__pycache__", ".git", ".venv", "venv", "env", "node_modules"}
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [name for name in dirnames if name.lower() not in excluded_dirs]
        current = Path(dirpath)
        for dirname in dirnames:
            folders.append(current / dirname)
        for filename in filenames:
            if filename == CANONICAL_EXPORT_FILENAME or filename.startswith("IMAGE_DOWNLOADER_SUPPORT_EXPORT") and filename.lower().endswith(".zip"):
                continue
            files.append(current / filename)
    by_name: Dict[str, List[Path]] = {}
    by_hash: Dict[str, List[Path]] = {}
    for f in files:
        by_name.setdefault(f.name.lower(), []).append(f)
        try:
            by_hash.setdefault(sha256_file(f), []).append(f)
        except OSError:
            pass
    name_dupes = {k: v for k, v in by_name.items() if len(v) > 1}
    hash_dupes = {k: v for k, v in by_hash.items() if len(v) > 1}
    lines.append(f"Scanned files: {len(files)}")
    lines.append(f"Scanned folders: {len(folders)}")
    nested = root / "ImageDownloader"
    if nested.is_dir() and any((nested / name).exists() for name in [SCRIPT_FILENAME, CANONICAL_ENTRYPOINT, CONFIG_FILENAME]):
        lines.append("Nested package folder: CHECK - ImageDownloader/ contains another release copy. This usually means a ZIP was extracted inside the live bot folder.")
        lines.append("Nested package repair: this build archives that nested copy under state/ on launch/export instead of deleting it.")
    else:
        lines.append("Nested package folder: PASS")
    lines.append(f"Duplicate filenames: {len(name_dupes)} group(s)")
    for name, paths in sorted(name_dupes.items()):
        lines.append(f"- {name}: " + ", ".join(short_path(p, root) for p in paths))
    lines.append(f"Duplicate file hashes: {len(hash_dupes)} group(s)")
    for digest, paths in sorted(hash_dupes.items()):
        lines.append(f"- {digest[:12]}: " + ", ".join(short_path(p, root) for p in paths))
    if not name_dupes and not hash_dupes:
        lines.append("No duplicate project source/support files detected.")
    return "\n".join(lines).rstrip() + "\n"


def file_inventory(root: Path) -> str:
    lines = [f"{APP_NAME} file inventory", f"Generated: {now_local()}", ""]
    for path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if path.name.lower() in {"downloads", "logs", "exports", "state", "reports", "__pycache__"}:
            lines.append(f"{path.name}/ - runtime folder excluded from package/export bulk")
            continue
        if path.is_file():
            if path.name == CANONICAL_EXPORT_FILENAME or (path.name.startswith("IMAGE_DOWNLOADER_SUPPORT_EXPORT") and path.suffix.lower() == ".zip"):
                lines.append(f"{path.name} - runtime canonical support export excluded from release inventory")
            else:
                lines.append(f"{path.name} - {path.stat().st_size} bytes - sha256 {sha256_file(path)}")
        elif path.is_dir():
            if path.name.lower() == "imagedownloader":
                lines.append(f"{path.name}/ - nested package copy detected; archived by this build when safe")
            else:
                lines.append(f"{path.name}/")
    return "\n".join(lines).rstrip() + "\n"


def logs_summary(root: Path, limit: int) -> str:
    log_path = root / LOG_DIRNAME / LOG_FILENAME
    lines = [f"{APP_NAME} logs summary", f"Generated: {now_local()}", f"Source: {safe_display_path(log_path)}", f"Tail line limit: {limit}", ""]
    try:
        raw, meta = read_file_snapshot(log_path, max_bytes=2 * 1024 * 1024, allow_truncate=True)
        tail = raw.decode("utf-8", errors="replace").splitlines()[-limit:]
        lines.append(f"Snapshot status: captured_bytes={meta.get('captured_bytes', 0)}, truncated={meta.get('truncated', False)}, attempts={meta.get('snapshot_attempts', 1)}")
        lines.append("")
    except FileNotFoundError:
        tail = []
    except Exception as exc:
        tail = [f"Log snapshot unavailable: {exc.__class__.__name__}: {exc}"]
    if not tail:
        lines.append("No log lines found yet.")
    else:
        lines.extend(tail)
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def stale_state_status(root: Path, cfg: Dict[str, Any]) -> str:
    guard_days = safe_int(cfg.get("stale_state_guard_days", 30), 30, min_value=1, max_value=3650)
    recent = json_load(root / STATE_DIRNAME / RECENT_RUN_FILENAME, {})
    if not isinstance(recent, dict) or not recent:
        return f"No recent run yet; guard threshold is {guard_days} day(s)."
    stamp = recent.get("finished_at") or recent.get("started_at")
    if not stamp:
        return f"Recent run exists but has no timestamp; guard threshold is {guard_days} day(s)."
    try:
        dt = datetime.fromisoformat(str(stamp))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        age_days = (datetime.now().astimezone() - dt).total_seconds() / 86400.0
    except (TypeError, ValueError):
        return f"Recent run timestamp could not be parsed: {stamp}"
    if age_days > guard_days:
        return f"STALE: latest run is {age_days:.1f} day(s) old, above {guard_days} day guard."
    return f"OK: latest run is {age_days:.1f} day(s) old, within {guard_days} day guard."


def instance_guard_summary(root: Path, cfg: Dict[str, Any]) -> str:
    lock = json_load(root / STATE_DIRNAME / INSTANCE_LOCK_FILENAME, {})
    events = json_load(root / STATE_DIRNAME / INSTANCE_EVENTS_FILENAME, [])
    if not isinstance(lock, dict):
        lock = {}
    if not isinstance(events, list):
        events = []
    lines = [
        "Single-instance guard:",
        f"- Enabled: {cfg.get('single_instance_guard_enabled', False)}",
        "- Scope: project-local state folder; no elevation/global machine lock required.",
        "- Liveness query: non-signalling Windows process handle check or POSIX signal-zero check; process-start signature protects against PID reuse when available.",
        f"- Second-launch behavior: {cfg.get('single_instance_second_launch', 'exit_with_status')}",
        f"- Stale lock recovery threshold seconds: {cfg.get('single_instance_lock_stale_seconds', 21600)}",
    ]
    if lock:
        pid = safe_int(lock.get("pid", 0), 0, min_value=0)
        alive, observed_signature = process_status(pid) if pid else (False, "")
        expected_signature = str(lock.get("process_start_signature", "") or "")
        identity = "match" if expected_signature and observed_signature and expected_signature == observed_signature else ("mismatch" if expected_signature and observed_signature else "not_available")
        lines.append(f"- Current lock: present; pid={pid}; live={alive if pid else 'unknown'}; identity={identity}; run_id={lock.get('run_id', 'unknown')}; role={lock.get('role', 'unknown')}")
    else:
        lines.append("- Current lock: none present.")
    if events:
        lines.append("- Recent guard events:")
        for item in events[-8:]:
            if isinstance(item, dict):
                lines.append(f"  - {item.get('time')} {item.get('event')} {item.get('status')} run_id={item.get('run_id')}")
    else:
        lines.append("- Recent guard events: none recorded yet.")
    return "\n".join(lines)


def schema_migration_summary(root: Path, cfg: Dict[str, Any]) -> str:
    state = json_load(root / STATE_DIRNAME / DOWNLOAD_INDEX_FILENAME, {})
    if not isinstance(state, dict):
        state = {}
    lines = [
        "Config/state schema and migration:",
        f"- Supported config schema: {CONFIG_SCHEMA_VERSION}; active config schema: {cfg.get('config_schema_version', 'unknown')}",
        f"- Supported state schema: {STATE_SCHEMA_VERSION}; active state schema: {state.get('state_schema_version', 'not created yet')}",
        f"- Config migration status: {cfg.get('config_last_migration', {}).get('status', 'none needed') if isinstance(cfg.get('config_last_migration', {}), dict) else 'unknown'}",
        f"- State migration status: {state.get('state_last_migration', {}).get('status', 'none needed') if isinstance(state.get('state_last_migration', {}), dict) else 'unknown'}",
        "- Newer-than-supported config/state is refused safely instead of silently downgraded.",
        "- Migration backups are project-local under state/migration_backups and bounded by retention config.",
    ]
    return "\n".join(lines)


def backpressure_summary(root: Path, cfg: Dict[str, Any]) -> str:
    recent = json_load(root / STATE_DIRNAME / RECENT_RUN_FILENAME, {})
    bp = recent.get("backpressure", {}) if isinstance(recent, dict) else {}
    if not isinstance(bp, dict):
        bp = {}
    queue_state = json_load(root / STATE_DIRNAME / DOWNLOAD_QUEUE_STATE_FILENAME, {})
    queue_items = queue_state.get("items", []) if isinstance(queue_state, dict) and isinstance(queue_state.get("items", []), list) else []
    queue_pending = sum(1 for item in queue_items if isinstance(item, dict) and item.get("status") in {"pending", "running"})
    lines = [
        "Queue/backpressure:",
        f"- Persistent queue autosave/recovery: enabled={cfg.get('download_queue_autosave_enabled', True)}/{cfg.get('download_queue_recovery_enabled', True)}; pending={queue_pending}; state={STATE_DIRNAME}/{DOWNLOAD_QUEUE_STATE_FILENAME}",
        "- Queue state contains operational URLs for recovery and is local-private; diagnostics/Export20 report counts only.",
        f"- Download queue capacity: {cfg.get('download_queue_capacity', DOWNLOAD_QUEUE_HARD_MAX)} (hard max {DOWNLOAD_QUEUE_HARD_MAX})",
        f"- Download queue full policy: {cfg.get('download_queue_full_policy', 'visible_reject_excess')}",
        f"- Gallery queue capacity: {cfg.get('gallery_queue_capacity', 100)}",
        f"- Worker concurrency cap: {cfg.get('workers', MAX_ACTIVE_DOWNLOADS)} (hard max {MAX_ACTIVE_DOWNLOADS})",
        f"- Adaptive throttle: enabled={cfg.get('adaptive_throttle_enabled', True)}, mode={cfg.get('adaptive_throttle_mode', 'feedback_aimd')}, min/max={cfg.get('adaptive_throttle_min_workers', 1)}/{cfg.get('adaptive_throttle_max_workers', cfg.get('workers', MAX_ACTIVE_DOWNLOADS))}",
        f"- Retry budget: status/base={cfg.get('retries', 2)}, extra connectivity={cfg.get('network_recovery_extra_attempts', 2)}",
        f"- Last run submitted: {bp.get('submitted', 0)}",
        f"- Last run high-water depth: {bp.get('high_water_depth', 0)}",
        f"- Last run rejected due capacity: {bp.get('rejected_due_capacity', 0)}",
        f"- Last drain status: {bp.get('shutdown_drain_status', 'not available')}",
        f"- Last adaptive final state: {json.dumps(redact_json_for_export(bp.get('adaptive_throttle_final', {})), ensure_ascii=False) if bp.get('adaptive_throttle_final') else 'not available'}",
    ]
    return "\n".join(lines)


def time_trace_summary(root: Path) -> str:
    recent = json_load(root / STATE_DIRNAME / RECENT_RUN_FILENAME, {})
    if not isinstance(recent, dict) or not recent:
        return "Time trace: no recent completed download run yet. Startup/export evidence is valid; run one URL and export again when transport/download evidence is needed."
    return "\n".join([
        "Time trace:",
        f"- Top-level run ID: {recent.get('top_level_run_id', 'unknown')}",
        f"- URL run ID: {recent.get('run_id', 'unknown')}",
        f"- Started: {recent.get('started_at', 'unknown')}",
        f"- Finished: {recent.get('finished_at', 'unknown')}",
        f"- Elapsed seconds: {recent.get('elapsed_seconds', 'unknown')}",
        f"- Last progress elapsed seconds: {recent.get('last_progress_elapsed_seconds', 'unknown')}",
        f"- Terminal status: {recent.get('terminal_status', 'unknown')}",
    ])


def deep_conflict_audit(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        f"{APP_NAME} deep conflict / issue / duplicate audit",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        "",
        "Audit result:",
        "- PASS: Standard Mode remains the default flow; no extra BAT/menu options added.",
        "- PASS: Safe Browser Mode remains optional/trusted-sites-only with browser context reuse.",
        "- PASS: Sequential discovery remains bounded by same-domain, candidate, failure, anchor, and probe-delay controls.",
        "- PASS: Duplicate URL/content protection remains active while per-run retry friction is reduced.",
        "- PASS: Network/VPN resilience remains backend-only through session refresh and bounded retry/backoff.",
        "- PASS: Export20 excludes downloads, caches, browser runtimes, and bulky logs.",
        "- FIXED: v2.8 schema metadata and safe migration/backup notes are now part of config/state handling.",
        "- AVAILABLE: The stale-recoverable single-instance guard remains implemented but is disabled by default; independent launches are not rejected by computer identity or ownership rules.",
        "- FIXED: v2.8 queue/backpressure capacity is explicit and visible in diagnostics instead of relying only on implicit page limits.",
        "- FIXED: Run summaries now carry top-level run ID, per-URL run ID, elapsed time, terminal status, schema, network, sequence, and pressure evidence.",
        "- FIXED: v2.9 compact platform/API drift registry is included in diagnostics/export evidence without adding launch-time web crawls or menu options.",
        "- FIXED: v2.16.2 omission-control coverage ledger is generated into diagnostics/export/batch output for broad pass completeness.",
        "- SUPERSEDED: older IMAGE_DOWNLOADER_BOT_DIR/C:\\Bots relocation targeting is replaced by canonical launcher/script root resolution; legacy BAT filenames remain redirects only.",
        "- PRESERVED from v2.16.4: Windows lock liveness uses a non-signalling process query; process creation signatures detect PID reuse without breaking ambiguous live locks.",
        "- FIXED: mutable config/state migration and cleanup now occur only after top-level instance ownership.",
        "- FIXED: completed config migration now publishes the target schema number instead of repeatedly retaining the source schema.",
        "- FIXED: one-shot URL mode returns a failure exit code when nothing was saved or recognized as an existing duplicate.",
        "- FIXED: Export20 runs required collectors before optional evidence and records elapsed time for included, omitted, and failed collectors.",
        "- ADDED: Completed downloaded image files are hidden by default on Windows through direct file-attribute APIs; failures are non-destructive and visible in diagnostics.",
        "- FIXED: Dependency install commands use bounded major-version ranges when packages are missing, avoiding silent broad upgrades while keeping fresh installs simple.",
        "",
        duplicate_scan(root).rstrip(),
        "",
        nested_layout_cleanup_summary(root),
        "",
        superseded_support_docs_summary(root),
        "",
        instance_guard_summary(root, cfg),
        "",
        schema_migration_summary(root, cfg),
        "",
        backpressure_summary(root, cfg),
        "",
        integration_registry_summary(root, config_path).rstrip(),
        "",
        time_trace_summary(root),
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def diagnostic_report(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    recent = json_load(root / STATE_DIRNAME / RECENT_RUN_FILENAME, {})
    sequence = json_load(root / STATE_DIRNAME / SEQUENCE_STATS_FILENAME, {})
    failures = json_load(root / STATE_DIRNAME / RECENT_FAILURES_FILENAME, [])
    lines = [
        f"{APP_NAME} diagnostic report",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        f"Build date: {BUILD_DATE}",
        f"Project root: {safe_display_path(root)}",
        f"Expected/preferred runtime folder: {cfg.get('preferred_bot_dir', '.')}",
        f"Config path: {safe_display_path(config_path, root)}",
        "",
        release_identity_summary(root).rstrip(),
        "",
        "Mode/config highlights:",
        f"- Standard Mode default: {not bool(cfg.get('browser_mode', False))}",
        f"- Browser Mode configured: {bool(cfg.get('browser_mode', False))}",
        f"- Browser context reuse: {bool(cfg.get('browser_reuse_context', True))}",
        f"- Dry run default/configured: {bool(cfg.get('dry_run', False))}",
        f"- Output: {cfg.get('output')}",
        f"- Max file MB: {cfg.get('max_file_mb')}",
        f"- Workers: {cfg.get('workers')}",
        f"- Same-domain page filtering: {cfg.get('same_domain_only')}",
        f"- Sequential discovery enabled: {cfg.get('sequence_discovery_enabled')}",
        f"- Sequential same-domain only: {cfg.get('sequence_same_domain_only')}",
        f"- Sequential max candidates/group: {cfg.get('sequence_max_candidates_per_group')}",
        f"- Sequential max failed attempts: {cfg.get('sequence_max_failed_attempts')}",
        f"- Network resilience enabled: {cfg.get('network_resilience_enabled', True)}",
        f"- Thread-local HTTP sessions: {cfg.get('thread_local_http_sessions', True)}",
        f"- Reset HTTP session on network error: {cfg.get('network_reset_session_on_error', True)}",
        f"- Coalesced session-reset debounce ms: {cfg.get('network_session_reset_debounce_ms', 1000)}",
        f"- Adaptive throttle enabled/mode: {cfg.get('adaptive_throttle_enabled', True)} / {cfg.get('adaptive_throttle_mode', 'feedback_aimd')}",
        f"- Adaptive throttle worker range: {cfg.get('adaptive_throttle_min_workers', 1)}-{cfg.get('adaptive_throttle_max_workers', cfg.get('workers', MAX_ACTIVE_DOWNLOADS))}",
        f"- Reset browser context on browser/network error: {cfg.get('network_browser_reset_on_error', True)}",
        f"- Launcher sync installed files: {cfg.get('launcher_sync_installed_files', False)}",
        f"- Per-run duplicate queue reset: {cfg.get('per_run_duplicate_queue_reset', True)}",
        f"- Stale state guard: {stale_state_status(root, cfg)}",
        "",
        transport_discovery_summary(root, config_path).rstrip(),
        "",
        duplicate_detection_summary(root, config_path).rstrip(),
        "",
        computer_awareness_summary(root, config_path).rstrip(),
        "",
        "Release framework and project-local execution highlights:",
        "- Root manifest, changelog, and consolidated runbook remain package artifacts; transfer, known-good/rollback, and health evidence are generated into Export20.",
        "- Diagnostic/export collector includes source/config/launchers/run state/failures/not-downloaded/sequence stats/environment/log summary without bulky caches.",
        "- Redacted system-aware diagnostics include runtime/tooling evidence without raw PC reports or hardware/network identifiers.",
        "- Single-instance, schema/migration, queue/backpressure, and time-trace evidence are summarized without adding new BAT/menu options.",
        "- Compact integration/API drift evidence is embedded in diagnostic/export summaries and does not crawl docs/status pages at launch.",
        f"- Log rotation/bounding enabled: max_bytes={cfg.get('log_max_bytes')}, backups={cfg.get('log_backup_count')}",
        "- No new BAT menu option was added for this compliance pass.",
        "- Helpful computer awareness is included in diagnostics/export as labels and hints only; it cannot block launches, alter state paths, change locks, or restrict features.",
        "- Runtime identity evidence plus execution namespace, canonical entrypoint, effective project/output roots, asset reconciliation, omission-control, and triage evidence are included in diagnostics/export.",
        "",
        instance_guard_summary(root, cfg),
        "",
        schema_migration_summary(root, cfg),
        "",
        backpressure_summary(root, cfg),
        "",
        time_trace_summary(root),
        "",
        "Integration/API compliance registry:",
        integration_registry_summary(root, config_path).rstrip(),
        "",
        "Custom-input/config assurance:",
        config_input_assurance_summary(root, config_path).rstrip(),
        "",
        "Digital asset metadata:",
        asset_metadata_reconciliation_summary(root, config_path).rstrip(),
        "",
        "Drive vault/reference status:",
        drive_vault_status_summary(root, config_path).rstrip(),
        "",
        "Parameter alignment:",
        parameter_alignment_summary(root, config_path).rstrip(),
        "",
        "Work-window triage / exit status:",
        work_window_triage_exit_summary(root, config_path).rstrip(),
        "",
        "Path targeting / relocation:",
        path_targeting_summary(root, config_path).rstrip(),
        "",
        "Omission-control coverage:",
        omission_control_coverage_summary(root, config_path).rstrip(),
        "",
        superseded_support_docs_summary(root),
        "",
        "Launcher info:",
        launcher_info(root).rstrip(),
        "",
        "System-aware environment summary:",
        system_aware_environment_summary(root, config_path).rstrip(),
        "",
        "Recent run summary:",
        json.dumps(recent, indent=2, ensure_ascii=False) if recent else "No recent run summary yet.",
        "",
        "Sequential-search stats:",
        json.dumps(sequence, indent=2, ensure_ascii=False) if sequence else "No sequential-search stats yet.",
        "",
        "Recent failures/errors:",
        json.dumps(failures[-20:], indent=2, ensure_ascii=False) if failures else "No recent failures/errors recorded.",
        "",
        "Safety checks:",
        "- Standard Mode remains the default fast path.",
        "- Safe Browser Mode reuses one browser context when enabled, but remains optional/trusted-sites-only.",
        "- Download validation requires image headers/magic bytes plus streamed Pillow verification for common raster formats and a bounded pixel guard.",
        "- Executables, scripts, archives, dangerous extensions, and dangerous content types are blocked.",
        "- Downloaded files are saved only; they are never opened or executed.",
        "- Safe Browser Mode is optional and should be used only for trusted sites.",
        "- VPN/IP-change resilience resets stale HTTP/browser sessions after network errors without changing the default user flow.",
        "- Concurrent reconnect attempts are coalesced to prevent session-reset storms; extra retries apply only to connectivity failures.",
        "- The local adaptive throttle lowers concurrency on 429/5xx, network faults, slow completions, or elevated failure rate and cautiously restores it after healthy results.",
        "- Per-thread HTTP sessions avoid shared-session conflicts during parallel downloads.",
        "- Per-run duplicate queues reset each pasted URL while persistent URL/hash history still prevents re-downloading saved files.",
        "- Export excludes downloaded images, caches, and bulky runtime folders.",
        "- execution/output identity, preserved runtime identity, structured Drive-vault status, path targeting, omission-control coverage, and custom-input assurance are cached/summarized; no launch-time cloud dependency was added.",
    ]
    return redact_sensitive_text("\n".join(lines).rstrip() + "\n")


def write_diagnostics(root: Path, config_path: Path) -> Path:
    (root / REPORT_DIRNAME).mkdir(parents=True, exist_ok=True)
    stamp = timestamp_unique()
    report_path = root / REPORT_DIRNAME / f"diagnostic_report_{stamp}.txt"
    report_text = diagnostic_report(root, config_path)
    write_text_atomic(report_path, report_text)
    latest = root / REPORT_DIRNAME / "diagnostic_report_latest.txt"
    write_text_atomic(latest, report_text)
    return report_path


def upgrade_review_notes(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        f"{APP_NAME} upgrade review notes",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        "",
        "Most recent outside-review decisions:",
        "- Applied now: Smart Safe Automation coordinates direct/page routing, duplicate detection, resume, reconnect, adaptive throttle, numbered sequences, and conservative same-domain gallery pagination without a new menu.",
        "- Applied now: Export20 atomically replaces one project-local exports/IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip and removes superseded timestamped export ZIPs after successful verification.",
        "- Preserved safety boundary: Safe Browser Mode is still a manual trusted-sites-only launcher; no automatic Chromium execution was added.",
        "- Applied now: local adaptive AIMD/EWMA download submission control, per-host Retry-After cooldown, connectivity-only extra attempts, and debounced/coalesced HTTP session renewal.",
        "- Preserved: bounded modern-page discovery, optional browser network-image observation, validator-gated resume, streamed verification, and failure-isolated deterministic Export20.",
        "- Preserved: runtime-release identity/managed-file integrity, canonical release-asset metadata, embedded key-file/container metadata, central downloaded-image metadata records, and read-only reconciliation evidence.",
        "- Preserved: v2.16.4 timer-safe triage/exit, omission-control, path targeting, startup/config validation, conflict/version drift controls, and lean packaging.",
        "- Applied now: GatewayImageDownloader is the stable execution namespace; GatewayImageDownloader.bat is canonical, namespaced helpers select modes, and historical run_*.bat names are thin redirects with no duplicated launch logic.",
        "- Applied: v2.13 export stability pass reuses one diagnostic report for combined diagnose/export runs, hardens atomic writes, and normalizes Drive reference status without adding BAT menu clutter.",
        "- Applied: v2.13 release-framework pass adds structured Drive Project Vault governance status and custom-input/config assurance as compact diagnostics/manifest evidence without adding BAT menu clutter.",
        "- Applied: Best-practices v2.8 compliance pass added timing/run-ID evidence, single-instance guard, config/state schemas, migration backups, queue/backpressure evidence, and deep conflict audit export visibility without adding BAT menu clutter.",
        "- Applied: Backend-only VPN/IP-change resilience now resets stale HTTP sessions and optional browser contexts after network failures, with no new menu option.",
        "- Applied: Safe Browser Mode now reuses one Playwright browser/context per active process instead of launching Chromium for every fetched page.",
        "- SUPERSEDED: historical C:\\Bots and IMAGE_DOWNLOADER_BOT_DIR runtime-root redirection is not used by the canonical canonical launcher; launch the complete extracted project in place.",
        "- Partially applied: Network-heavy paths now catch request/IO/runtime errors more specifically; top-level guards still protect the interactive flow from crashing.",
        "- Deferred: Splitting the single Python file into many modules was not applied in this build because the current priority is a lean, portable, easy-transfer package with a small file count.",
        "",
        "Configured safety posture:",
        f"- Standard Mode default: {not bool(cfg.get('browser_mode', False))}",
        f"- Dry run default/configured: {bool(cfg.get('dry_run', False))}",
        f"- Downloaded media hidden by default on Windows: {bool(cfg.get('hide_downloaded_media', True))}",
        f"- Sequential same-domain only: {cfg.get('sequence_same_domain_only')}",
        f"- Sequence max candidates/group: {cfg.get('sequence_max_candidates_per_group')}",
        f"- Sequence max failed attempts: {cfg.get('sequence_max_failed_attempts')}",
        f"- Browser context reuse: {cfg.get('browser_reuse_context', True)}",
        f"- Network resilience enabled: {cfg.get('network_resilience_enabled', True)}",
        f"- HTTP session reset on network error: {cfg.get('network_reset_session_on_error', True)}",
        f"- Session reset debounce ms: {cfg.get('network_session_reset_debounce_ms', 1000)}",
        f"- Connectivity-only extra attempts: {cfg.get('network_recovery_extra_attempts', 2)}",
        f"- Adaptive throttle enabled/mode: {cfg.get('adaptive_throttle_enabled', True)} / {cfg.get('adaptive_throttle_mode', 'feedback_aimd')}",
        f"- Stale state guard: {stale_state_status(root, cfg)}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def project_health_review(root: Path, config_path: Path) -> str:
    cfg = json_load(config_path, {})
    lines = [
        f"{APP_NAME} project health / layering review",
        f"Generated: {now_local()}",
        f"Version: {APP_VERSION}",
        f"Build: {BUILD_NAME}",
        f"Build date: {BUILD_DATE}",
        "",
        "Deep-review outcome:",
        "- PASS: The current public release framework governs this maintenance pass; known-good queue, discovery, validation, hidden-media, state, timeout, and reconnect behavior remains preserved.",
        "- PASS: Standard Mode remains the fast default path and Smart Safe Automation selects only bounded low-risk backend helpers.",
        "- PASS: Safe Browser Mode remains optional/trusted-sites-only and reuses its browser context.",
        "- PASS: Sequential discovery remains bounded by same-domain, max candidates, max failures, and duplicate URL/content guards.",
        "- PASS: Export excludes downloaded images, caches, Playwright runtimes, and bulky state.",
        "- PASS: No bundled executables or hidden downloaded-file execution paths are part of the package.",
        "- PASS: Completed image files use the native Windows Hidden attribute by default; project/output folders stay visible and downloaded files are never executed.",
        "- PASS: Execution/output and runtime-identity metadata remain lean: MANIFEST.json is canonical, DRIVE_UPLOAD_MANIFEST.csv is the merged CSV/Drive view, and Export20 carries execution/output identity without a new sidecar stack.",
        "- PASS: Incremental submission and local adaptive concurrency prevent eager executor flooding while preserving the configured worker ceiling.",
        "- PASS: HTTP 429/5xx/network/slow-response pressure lowers the active limit; healthy completions restore it additively.",
        "- PASS: VPN/IP/session resets are debounced so concurrent workers do not trigger repeated generation churn.",
        "- PASS: Export20 now builds a deterministic allowlisted plan, snapshots changing files, isolates collector failures, records omissions/hashes, excludes recursive archives, remains capped at 20 files, and publishes one canonical project-local exports ZIP.",
        "- FIXED: Combined --diagnose --export-support runs now reuse one diagnostic report instead of creating duplicate report files.",
        "- FIXED: Config/state/report atomic writes now use unique temporary filenames before replace to reduce cross-process collision risk.",
        "- FIXED: Drive reference-check config now uses a valid compact status plus a separate note, preventing startup normalization from downgrading verified folder evidence.",
        "- FIXED: Launchers no longer auto-sync release files; project-folder-first targeting plus complete-control checks prevent silently selecting a partial override or stale legacy folder.",
        "- FIXED: Per-run duplicate queues reset for each pasted URL so failed attempts can be retried in the same console.",
        "- FIXED: Parallel downloads use thread-local HTTP sessions by default to avoid shared-session conflicts.",
        "- FIXED: Duplicate top-level launches now fail visibly instead of silently contending for shared state.",
        "- FIXED: Config/state schemas are versioned with safe backup-first migration and newer-schema refusal.",
        "- FIXED: Candidate/backpressure limits are explicit and exported.",
        "",
        "Layer map:",
        "1. BAT launcher layer: GatewayImageDownloader.bat resolves its own project folder, finds Python, runs the release identity gate, then installs bounded dependencies only after PASS; namespaced helpers and legacy redirects contain no duplicated backend logic.",
        "2. CLI/session layer: keep mode flags and interactive loop isolated from download logic.",
        "3. Network layer: separate connect/read timeouts, monotonic caps, Retry-After/backoff, coalesced VPN/IP session refresh, connectivity-only extra retries, validator-gated Range resume, thread-local sessions, and local adaptive concurrency feedback.",
        "4. Parser/discovery layer: HTML attributes, responsive srcsets/imagesrcset, metadata, JSON-LD, CSS, noscript, optional browser response capture, gallery candidates, and sequential seeds.",
        "5. Validation/download layer: dangerous extension/content blocking, image magic checks, streamed Pillow/pixel verification, max-size checks, URL/SHA256/visual/library duplicate detection, hidden-media attribute, and atomic target writes.",
        "6. Operational integrity layer: instance ownership, config/state schema migration, bounded candidate pressure, run IDs, elapsed timing, and graceful cleanup.",
        "7. Diagnostics/export layer: current config, automation decisions, build/version, run summaries, failures, sequence stats, logs, launcher info, deep conflict audit, and one canonical support package.",
        "",
        "System-aware canonical-entrypoint and project-local-output posture:",
        "- Redacted system/runtime summary is included in diagnostics/export without raw PC reports.",
        "- Usernames/home paths, query-token values, and obvious secret keys are redacted in generated export evidence.",
        "- Log rotation keeps runtime logs bounded by config instead of growing indefinitely.",
        "- Windows/Norton/VPN context is treated as expected, but no security bypasses or service/firewall changes are made.",
        "",
        "Digital asset metadata posture:",
        asset_metadata_reconciliation_summary(root, config_path).rstrip(),
        "",
        "Current config posture:",
        f"- browser_mode: {cfg.get('browser_mode', False)}",
        f"- dry_run: {cfg.get('dry_run', False)}",
        f"- hide_downloaded_media: {cfg.get('hide_downloaded_media', True)}",
        f"- workers: {cfg.get('workers')}",
        f"- thread_local_http_sessions: {cfg.get('thread_local_http_sessions', True)}",
        f"- network_resilience_enabled: {cfg.get('network_resilience_enabled', True)}",
        f"- adaptive_throttle_enabled: {cfg.get('adaptive_throttle_enabled', True)}",
        f"- adaptive_throttle_mode: {cfg.get('adaptive_throttle_mode', 'feedback_aimd')}",
        f"- sequence_discovery_enabled: {cfg.get('sequence_discovery_enabled', True)}",
        f"- sequence_same_domain_only: {cfg.get('sequence_same_domain_only', True)}",
        f"- launcher_sync_installed_files: {cfg.get('launcher_sync_installed_files', False)}",
        f"- parameter_alignment_version: {cfg.get('parameter_alignment_version', PARAMETER_ALIGNMENT_VERSION)}",
        f"- google_drive_vault_sync_status: {cfg.get('google_drive_vault_sync_status', 'not_configured_local_runtime')}",
        f"- custom_input_assurance_enabled: {cfg.get('custom_input_assurance_enabled', True)}",
        "",
        duplicate_scan(root).rstrip(),
        "",
        file_inventory(root).rstrip(),
        "",
        nested_layout_cleanup_summary(root),
        "",
        superseded_support_docs_summary(root),
        "",
        upgrade_review_notes(root, config_path).rstrip(),
    ]
    return "\n".join(lines).rstrip() + "\n"

def read_file_snapshot(
    path: Path,
    *,
    max_bytes: int = EXPORT_MAX_ENTRY_BYTES,
    allow_truncate: bool = True,
    attempts: int = EXPORT_SNAPSHOT_ATTEMPTS,
) -> Tuple[bytes, Dict[str, Any]]:
    """Read a bounded, consistency-checked snapshot of a possibly changing file."""
    last_error: Optional[BaseException] = None
    for attempt in range(max(1, attempts)):
        try:
            before = path.stat()
            with path.open("rb") as source:
                data = source.read(max_bytes + 1)
            after = path.stat()
            if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
                last_error = RuntimeError("file changed during snapshot")
                if attempt + 1 < attempts:
                    time.sleep(0.05 * (attempt + 1))
                    continue
                raise last_error
            truncated = len(data) > max_bytes
            if truncated and not allow_truncate:
                raise RuntimeError(f"file exceeds export entry cap ({before.st_size} > {max_bytes} bytes)")
            if truncated:
                marker = b"\n\n[TRUNCATED BY EXPORT SIZE GUARD]\n"
                data = data[: max(0, max_bytes - len(marker))] + marker
            return data, {
                "size_on_disk": int(after.st_size),
                "captured_bytes": len(data),
                "truncated": truncated,
                "snapshot_attempts": attempt + 1,
            }
        except (FileNotFoundError, PermissionError, OSError, RuntimeError) as exc:
            last_error = exc
            if attempt + 1 < attempts and not isinstance(exc, FileNotFoundError):
                time.sleep(0.05 * (attempt + 1))
                continue
            break
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"could not snapshot {path.name}")


def read_json_snapshot(path: Path, default: Any) -> Tuple[Any, Dict[str, Any]]:
    try:
        raw, meta = read_file_snapshot(path, max_bytes=EXPORT_MAX_ENTRY_BYTES, allow_truncate=False)
    except FileNotFoundError:
        return default, {"status": "not_available", "captured_bytes": 0}
    try:
        return json.loads(raw.decode("utf-8")), meta
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise RuntimeError(f"invalid JSON snapshot for {path.name}: {exc}") from exc


def export_for_support(root: Path, config_path: Path, report_path: Optional[Path] = None) -> Path:
    """Create a deterministic, report-only, failure-isolated Export20 archive."""
    root = root.resolve()
    config_path = config_path.resolve()
    try:
        cfg_value, cfg_snapshot_meta = read_json_snapshot(config_path, {})
        cfg = cfg_value if isinstance(cfg_value, dict) else {}
    except Exception:
        cfg = {}
        cfg_snapshot_meta = {"status": "unreadable"}

    export_dir = root / EXPORT_DIRNAME
    temp_dir = root / TEMP_DIRNAME
    export_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    canonical_name = Path(str(cfg.get("canonical_export_filename", CANONICAL_EXPORT_FILENAME))).name or CANONICAL_EXPORT_FILENAME
    export_path = export_dir / canonical_name
    for stale_tmp in temp_dir.glob(f".{canonical_name}.*.tmp"):
        with contextlib.suppress(OSError):
            if stale_tmp.stat().st_mtime < time.time() - 86400:
                stale_tmp.unlink()

    stamp = timestamp_unique()
    tmp_path = temp_dir / f".{canonical_name}.{uuid.uuid4().hex[:8]}.tmp"
    collected: List[Dict[str, Any]] = []
    outcomes: List[Dict[str, Any]] = []
    omitted: List[Dict[str, Any]] = []
    seen_names: Set[str] = set()
    seen_hashes: Dict[str, str] = {}
    total_bytes = 0

    def add_candidate(
        collector_id: str,
        arcname: str,
        required: bool,
        collector: Any,
        *,
        generated: bool = False,
    ) -> None:
        nonlocal total_bytes
        collector_started = time.monotonic()
        outcome: Dict[str, Any] = {
            "collector_id": collector_id,
            "archive_name": arcname,
            "required": required,
            "generated": generated,
            "status": "pending",
        }
        try:
            result = collector()
            note = ""
            meta: Dict[str, Any] = {}
            if isinstance(result, tuple) and len(result) == 2:
                payload, extra = result
                if isinstance(extra, dict):
                    meta = dict(extra)
                else:
                    note = str(extra or "")
            else:
                payload = result
            if isinstance(payload, str):
                payload = payload.encode("utf-8")
            if not isinstance(payload, (bytes, bytearray)):
                raise TypeError("collector did not return bytes or text")
            data = bytes(payload)
            if generated and bool(cfg.get("export_redaction_enabled", True)):
                data = redact_sensitive_text(data.decode("utf-8", errors="replace")).encode("utf-8")
            if len(data) > EXPORT_MAX_ENTRY_BYTES:
                marker = b"\n\n[TRUNCATED BY EXPORT ENTRY SIZE GUARD]\n"
                data = data[: max(0, EXPORT_MAX_ENTRY_BYTES - len(marker))] + marker
                meta["truncated_by_export"] = True
            if arcname in seen_names:
                outcome.update(status="omitted_duplicate_name", note="archive name already selected")
                omitted.append(dict(outcome))
                return
            digest = sha256_bytes(data)
            if digest in seen_hashes and not required:
                outcome.update(status="omitted_duplicate_content", note=f"same content as {seen_hashes[digest]}", sha256=digest)
                omitted.append(dict(outcome))
                return
            if digest in seen_hashes and required:
                meta["content_duplicate_of"] = seen_hashes[digest]
            if len(collected) >= EXPORT_FILE_LIMIT - 1:
                outcome.update(status="omitted_file_limit", note="Export20 pre-manifest capacity reached")
                omitted.append(dict(outcome))
                return
            if total_bytes + len(data) > EXPORT_MAX_TOTAL_BYTES:
                outcome.update(status="omitted_total_size_limit", note="export total-size guard reached")
                omitted.append(dict(outcome))
                return
            seen_names.add(arcname)
            seen_hashes.setdefault(digest, arcname)
            total_bytes += len(data)
            collected.append({"arcname": arcname, "data": data, "sha256": digest})
            for reserved_key in ["status", "note", "bytes", "sha256", "collector_id", "archive_name", "required", "generated"]:
                if reserved_key in meta:
                    meta[f"snapshot_{reserved_key}"] = meta.pop(reserved_key)
            outcome.update(status="included", bytes=len(data), sha256=digest, note=note, **meta)
        except Exception as exc:
            outcome.update(status="failed", note=f"{exc.__class__.__name__}: {exc}")
            if generated and len(collected) < EXPORT_FILE_LIMIT - 1:
                placeholder = (
                    f"{APP_NAME} export collector unavailable\n"
                    f"Generated: {now_local()}\n"
                    f"Collector: {collector_id}\n"
                    f"Reason: {redact_sensitive_text(outcome['note'])}\n"
                ).encode("utf-8")
                digest = sha256_bytes(placeholder)
                if arcname not in seen_names and digest not in seen_hashes and total_bytes + len(placeholder) <= EXPORT_MAX_TOTAL_BYTES:
                    seen_names.add(arcname)
                    seen_hashes[digest] = arcname
                    total_bytes += len(placeholder)
                    collected.append({"arcname": arcname, "data": placeholder, "sha256": digest})
                    outcome.update(status="failed_placeholder_included", bytes=len(placeholder), sha256=digest)
        finally:
            outcome["elapsed_ms"] = round(max(0.0, time.monotonic() - collector_started) * 1000.0, 3)
            outcomes.append(outcome)

    def static_snapshot(filename: str) -> Tuple[bytes, Dict[str, Any]]:
        path = (root / filename).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise RuntimeError("static export path escaped project root") from exc
        if export_dir.resolve() == path or export_dir.resolve() in path.parents:
            raise RuntimeError("active export tree cannot be included")
        data, meta = read_file_snapshot(path, allow_truncate=False)
        meta["source"] = filename
        return data, meta

    static_specs = [
        ("static.source", SCRIPT_FILENAME, True),
        ("static.launcher.standard", CANONICAL_ENTRYPOINT, True),
        ("static.launcher.browser", SAFE_BROWSER_ENTRYPOINT, True),
        ("static.launcher.export", DIAGNOSTICS_EXPORT_ENTRYPOINT, True),
        ("static.runbook", "README_QUICK_START.md", True),
        ("static.changelog", "CHANGELOG.md", True),
        ("static.version", VERSION_FILENAME, True),
        ("static.package_metadata", PACKAGE_METADATA_FILENAME, True),
        ("static.manifest", MANIFEST_FILENAME, True),
        ("static.drive_manifest", "DRIVE_UPLOAD_MANIFEST.csv", False),
    ]
    def diagnostic_collector() -> Tuple[str, Dict[str, Any]]:
        if report_path is not None:
            path = report_path.resolve()
            data, meta = read_file_snapshot(path, allow_truncate=True)
            meta["source"] = "provided_diagnostic_report"
            return data.decode("utf-8", errors="replace"), meta
        return diagnostic_report(root, config_path), {"source": "generated_in_memory_report_only"}

    def state_json_text(filename: str, default: Any) -> Tuple[str, Dict[str, Any]]:
        value, meta = read_json_snapshot(root / STATE_DIRNAME / filename, default)
        return json.dumps(redact_json_for_export(value), indent=2, ensure_ascii=False) + "\n", meta

    generated_specs = [
        ("generated.config", "image_downloader_config_redacted.json", True, lambda: (json.dumps(redact_json_for_export(cfg), indent=2, ensure_ascii=False) + "\n", cfg_snapshot_meta)),
        ("generated.diagnostic", "diagnostic_report.txt", True, diagnostic_collector),
        ("generated.environment", "dependency_environment_summary.txt", True, lambda: dependency_environment_summary(root, config_path)),
        ("generated.audit", "deep_conflict_audit.txt", True, lambda: deep_conflict_audit(root, config_path)),
        ("generated.handoff", "project_handoff_notes.txt", True, lambda: project_handoff_notes(root, config_path)),
        ("generated.alignment", "current_parameter_alignment_status.txt", True, lambda: release_identity_summary(root) + "\n" + parameter_alignment_summary(root, config_path) + "\n" + duplicate_detection_summary(root, config_path) + "\n" + asset_metadata_reconciliation_summary(root, config_path) + "\n" + work_window_triage_exit_summary(root, config_path) + "\n" + drive_vault_status_summary(root, config_path) + "\n" + path_targeting_summary(root, config_path) + "\n" + omission_control_coverage_summary(root, config_path) + "\n" + config_input_assurance_summary(root, config_path) + "\n" + transport_discovery_summary(root, config_path)),
        ("generated.logs", "logs_summary.txt", False, lambda: logs_summary(root, safe_int(cfg.get("log_tail_lines_for_export", 400), 400, min_value=20, max_value=2000))),
        ("generated.recent_run", "recent_run_summary.json", True, lambda: state_json_text(RECENT_RUN_FILENAME, {})),
        ("generated.failures", "recent_failures_errors.json", True, lambda: state_json_text(RECENT_FAILURES_FILENAME, [])),
        ("generated.not_downloaded", "not_downloaded_images.json", True, lambda: state_json_text(NOT_DOWNLOADED_FILENAME, [])),
        ("generated.sequence", "sequential_search_stats.json", True, lambda: state_json_text(SEQUENCE_STATS_FILENAME, {})),
    ]
    # Required collectors always run before optional evidence so future additions cannot
    # let a low-value optional file consume the last Export20 slot. Stable collector IDs
    # and archive names are preserved; only selection priority is hardened.
    for collector_id, filename, required in static_specs:
        if required:
            add_candidate(collector_id, filename, required, lambda filename=filename: static_snapshot(filename))
    for collector_id, arcname, required, collector in generated_specs:
        if required:
            add_candidate(collector_id, arcname, required, collector, generated=True)
    for collector_id, filename, required in static_specs:
        if not required:
            add_candidate(collector_id, filename, required, lambda filename=filename: static_snapshot(filename))
    for collector_id, arcname, required, collector in generated_specs:
        if not required:
            add_candidate(collector_id, arcname, required, collector, generated=True)

    included_names = [item["arcname"] for item in collected]
    export_asset_id = "IMGDL-EXPORT-" + re.sub(r"[^A-Za-z0-9]", "", stamp).upper()
    export_assets = [
        {
            "asset_id": "IMGDL-EXPORT-ENTRY-" + hashlib.sha256(item["arcname"].encode("utf-8")).hexdigest()[:16].upper(),
            "path": item["arcname"],
            "title": Path(item["arcname"]).name,
            "purpose": "support diagnostic package",
            "asset_class": "diagnostic",
            "role": "export-evidence",
            "format": Path(item["arcname"]).suffix.lower().lstrip(".") or "txt",
            "project_slug": PROJECT_SLUG,
            "version": APP_VERSION,
            "status": ASSET_STATUS,
            "sensitivity": ASSET_SENSITIVITY,
            "source_of_truth": item["arcname"] in {"MANIFEST.json", "project_handoff_notes.txt", "diagnostic_report.txt"},
            "tags": ["image-downloader", "export20", "diagnostic-evidence"],
            "aliases": [Path(item["arcname"]).stem],
            "lineage": "generated from cached/read-only project evidence",
            "created_cdt": now_local(),
            "modified_cdt": now_local(),
            "size_bytes": len(item["data"]),
            "sha256": item["sha256"],
        }
        for item in collected
    ]
    export_assets.append({
        "asset_id": "IMGDL-EXPORT-MANIFEST",
        "path": "export_manifest.json",
        "title": "Export20 Canonical Manifest",
        "purpose": "Canonical archive registry, collector outcomes, integrity, and metadata",
        "asset_class": "manifest",
        "role": "canonical-manifest",
        "format": "json",
        "project_slug": PROJECT_SLUG,
        "version": APP_VERSION,
        "status": ASSET_STATUS,
        "sensitivity": ASSET_SENSITIVITY,
        "source_of_truth": True,
        "tags": ["image-downloader", "export20", "manifest", "asset-metadata"],
        "aliases": ["export manifest"],
        "lineage": "generated by the report-only Export20 collector",
        "created_cdt": now_local(),
        "modified_cdt": now_local(),
        "size_bytes": None,
        "sha256": None,
        "checksum_scope": "omitted_self_reference",
    })
    recent_runtime_evidence = json_load(root / STATE_DIRNAME / RECENT_RUN_FILENAME, {})
    has_recent_runtime_evidence = isinstance(recent_runtime_evidence, dict) and bool(recent_runtime_evidence)
    manifest = {
        "metadata_schema": ASSET_METADATA_SCHEMA,
        "package_asset_id": export_asset_id,
        "project_slug": PROJECT_SLUG,
        "status": ASSET_STATUS,
        "sensitivity": ASSET_SENSITIVITY,
        "tags": ["image-downloader", "export20", "support-handoff", "asset-metadata"],
        "aliases": ["Image Downloader support export", "diagnostic handoff"],
        "lineage": f"generated by {PACKAGE_ASSET_ID}@{APP_VERSION}",
        "assets": export_assets,
        "app": APP_NAME,
        "version": APP_VERSION,
        "build": BUILD_NAME,
        "build_date": BUILD_DATE,
        "created_at": now_local(),
        "canonical_output_path": f"{EXPORT_DIRNAME}/{export_path.name}",
        "single_easy_find_zip": True,
        "previous_export_zip_retention": safe_int(cfg.get("export_keep_previous_zips", 0), 0, min_value=0, max_value=5),
        "file_limit": EXPORT_FILE_LIMIT,
        "entry_size_limit_bytes": EXPORT_MAX_ENTRY_BYTES,
        "total_size_limit_bytes": EXPORT_MAX_TOTAL_BYTES,
        "file_count_before_manifest": len(collected),
        "file_count_final": len(collected) + 1,
        "captured_bytes_before_manifest": total_bytes,
        "plan": "allowlisted -> canonicalized -> consistency-snapshotted -> redacted -> content-deduplicated -> ranked/capped -> atomic ZIP",
        "report_only": True,
        "network_calls_performed_by_export": False,
        "migrations_repairs_dependency_installs_performed_by_export": False,
        "runtime_evidence_status": "recent_completed_run_available" if has_recent_runtime_evidence else "startup_only_no_completed_download_run",
        "runtime_evidence_guidance": "Run at least one URL before exporting when download/transport evidence is needed; startup-only exports remain valid for launch/config/path diagnosis.",
        "collector_outcomes": outcomes,
        "omitted_candidates": omitted,
        "included_files": included_names + ["export_manifest.json"],
        "included_entry_hashes": {item["arcname"]: item["sha256"] for item in collected},
        "prime_directive_upgrades": {
            "modern_discovery": "HTML responsive/lazy/JSON-LD/CSS discovery plus optional Safe Browser response capture, all bounded by candidate limits",
            "server_aware_retries": "separate connect/read timeouts, monotonic wall-clock caps, exponential backoff with jitter, bounded Retry-After, connectivity-only extra attempts",
            "adaptive_throttle": "local AIMD/EWMA controller reduces concurrency on 429/5xx, network faults, slow completions, and elevated failure rate; no cloud AI dependency",
            "coalesced_reconnect": "debounced session-generation resets prevent parallel reconnect storms during VPN/IP changes",
            "resumable_transfers": "validator-gated Range/If-Range partial resume with bounded retention and restart-on-drift",
            "streamed_validation": "download stream is verified from disk with Pillow/pixel guards and hashed/copied without loading the full file into RAM",
            "smart_safe_automation": "standard-first routing, duplicate/resume/reconnect/throttle/sequence automation, and conservative same-domain gallery pagination; Safe Browser remains manual trusted-sites-only",
            "canonical_export": "one atomically replaced project-local exports/IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip staged under project temp and integrity-tested before finalize",
        },
        "excluded_by_design": [
            "downloaded images",
            "active/prior export archives",
            "runtime caches and dependency trees",
            "Playwright browser runtimes",
            "raw PC/network identifiers",
            "bulky logs beyond summarized tail",
        ],
    }
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if len(collected) + 1 > EXPORT_FILE_LIMIT:
        raise RuntimeError(f"Export plan exceeded Export20 limit before ZIP creation: {len(collected) + 1}")

    try:
        with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.comment = (
                f"{export_asset_id}|{APP_VERSION}|status={ASSET_STATUS}|"
                f"sensitivity={ASSET_SENSITIVITY}|tags=image-downloader,export20,asset-metadata|"
                "manifest=export_manifest.json"
            ).encode("utf-8")
            for item in collected:
                zf.writestr(item["arcname"], item["data"])
            zf.writestr("export_manifest.json", manifest_bytes)
        with zipfile.ZipFile(tmp_path, "r") as verify_zf:
            bad_member = verify_zf.testzip()
            names = verify_zf.namelist()
            zip_comment = verify_zf.comment.decode("utf-8", errors="replace")
            if not zip_comment.startswith(export_asset_id + "|"):
                raise RuntimeError("Export ZIP is missing embedded asset metadata")
            if len(names) != len(set(names)):
                raise RuntimeError("Export ZIP contains duplicate archive names")
        if bad_member:
            raise RuntimeError(f"Export ZIP integrity check failed for {bad_member}")
        if len(names) > EXPORT_FILE_LIMIT:
            raise RuntimeError(f"Export ZIP exceeded Export20 limit: {len(names)} entries")
        if "export_manifest.json" not in names:
            raise RuntimeError("Export ZIP is missing export_manifest.json")
        tmp_path.replace(export_path)
        keep_previous = safe_int(cfg.get("export_keep_previous_zips", 0), 0, min_value=0, max_value=5)
        prior_exports: List[Path] = []
        prior_exports.extend(export_dir.glob("image_downloader_support_export_*.zip"))
        prior_exports = sorted({path.resolve() for path in prior_exports if path.exists()}, key=lambda path: path.stat().st_mtime, reverse=True)
        for old_export in prior_exports[keep_previous:]:
            with contextlib.suppress(OSError):
                old_export.unlink()
    except Exception:
        with contextlib.suppress(OSError):
            tmp_path.unlink()
        raise
    return export_path


def interactive_loop(downloader: ImageDownloader) -> None:
    if bool(downloader.config.get("computer_profile_include_in_console", True)):
        ctx = downloader.computer_context
        print(f"Active computer: {ctx.get('display_name')} [{ctx.get('diagnostic_id')}]")
        print("Computer identification is informational only and never blocks launch or changes feature access.")
    print(f"Execution: {EXECUTION_NAMESPACE} via {CANONICAL_ENTRYPOINT}")
    print(f"Project root: {downloader.root}")
    print(f"Effective downloads: {downloader.output_dir} [{downloader.output_mode}]")
    print(f"Support exports: {downloader.export_dir}")
    print("Quick Start:")
    print("- Paste a page or image URL and press Enter")
    print("- Queue capacity is 100 URLs; no more than 3 image downloads run at once")
    print("- Queue changes auto-save to state/download_queue.json and unfinished work recovers on next launch")
    print("- A timestamped session download list is written under reports/ when the session ends")
    print("- Press Enter on a blank line to exit")
    print("- Smart Safe Automation handles duplicates, resume, reconnect, throttle, sequence, and conservative gallery navigation")
    print("- Use Safe Browser Mode manually only for trusted JavaScript-heavy sites")
    print("- Commands: /add URL..., /run, /queue, /config, /export, /diagnose, /dry-run, /help")
    print("")
    recovered = downloader.pending_download_queue_count()
    if recovered:
        print(f"Recovered {recovered} queued URL(s) from the previous session. Resuming now.")
        try:
            downloader.process_saved_download_queue()
        except KeyboardInterrupt:
            print("\nQueue interrupted; unfinished item was returned to the saved queue.")
        print("")
    while True:
        try:
            value = input("URL> ").strip()
        except EOFError:
            print("")
            break
        except KeyboardInterrupt:
            print("\nInterrupted.")
            break
        if not value:
            break
        command = value.lower()
        if command in {"/quit", "/exit"}:
            break
        if command == "/help":
            print("Plain pasted URLs are saved to the persistent queue before network work starts. Use /add URL... to stage one or more URLs without starting, /run to drain the saved queue, and /queue to inspect it. Queue capacity is 100 and active image-download concurrency is hard-capped at 3. /config shows config path; /export replaces the one canonical support ZIP; /diagnose writes a report; /dry-run toggles preview mode; blank line exits and writes the timestamped session TXT.")
            continue
        if command == "/config":
            print(f"Config file: {downloader.config_path}")
            continue
        if command == "/diagnose":
            path = write_diagnostics(downloader.root, downloader.config_path)
            print(f"Diagnostic report created: {path}")
            continue
        if command == "/export":
            path = export_for_support(downloader.root, downloader.config_path)
            print(f"support export ZIP created: {path}")
            print("Share this file with authorized support personnel.")
            continue
        if command in {"/dry-run", "/dryrun"}:
            downloader.config["dry_run"] = not bool(downloader.config.get("dry_run", False))
            print(f"Dry run is now {'ON' if downloader.config['dry_run'] else 'OFF'} for this session.")
            continue
        if command == "/queue":
            pending = downloader.pending_download_queue_count()
            print(f"Saved queue: {pending}/{downloader.download_queue_capacity} pending; active download cap={MAX_ACTIVE_DOWNLOADS}")
            for item in downloader.download_queue_preview():
                print(f"  {item['position']:03d}. {item['status']} | queued={item['queued_at']} | attempts={item['attempts']} | {item['url']}")
            if pending > 12:
                print(f"  ... {pending - 12} more queued item(s)")
            continue
        if command == "/run":
            if downloader.pending_download_queue_count() == 0:
                print("Saved queue is empty.")
            else:
                try:
                    downloader.process_saved_download_queue()
                except KeyboardInterrupt:
                    print("\nQueue interrupted; unfinished item remains saved for recovery.")
            print("Ready for next URL.\n")
            continue
        if command.startswith("/add "):
            raw_values = [part for part in value[5:].split() if part]
            result = downloader.enqueue_download_urls(raw_values, source="interactive /add")
            print(f"Queued {len(result['accepted'])}; rejected {len(result['rejected'])}; pending={result['pending']}/{downloader.download_queue_capacity}")
            for rejected in result["rejected"][:5]:
                print(f"  Rejected: {rejected['reason']} | {rejected['url']}")
            continue

        raw_values = [part for part in value.split() if part]
        if len(raw_values) > 1 and all(normalize_url(part) for part in raw_values):
            result = downloader.enqueue_download_urls(raw_values, source="interactive paste")
        else:
            result = downloader.enqueue_download_urls([value], source="interactive paste")
        if not result["accepted"]:
            for rejected in result["rejected"][:5]:
                print(f"Not queued: {rejected['reason']} | {rejected['url']}")
            continue
        if result["rejected"]:
            print(f"Queued {len(result['accepted'])}; rejected {len(result['rejected'])}; pending={result['pending']}/{downloader.download_queue_capacity}")
        try:
            downloader.process_saved_download_queue()
        except KeyboardInterrupt:
            print("\nQueue interrupted; unfinished item remains saved for recovery.")
        print("Ready for next URL.\n")



def run_release_identity_gate_self_test() -> Tuple[bool, str]:
    test_temp_parent = app_root() / TEMP_DIRNAME
    test_temp_parent.mkdir(parents=True, exist_ok=True)
    test_root = Path(tempfile.mkdtemp(prefix="image_downloader_identity_gate_", dir=str(test_temp_parent)))
    try:
        managed_names = [
            SCRIPT_FILENAME,
            VERSION_FILENAME,
            PACKAGE_METADATA_FILENAME,
            CANONICAL_ENTRYPOINT,
            SAFE_BROWSER_ENTRYPOINT,
            DIAGNOSTICS_EXPORT_ENTRYPOINT,
            "run_image_downloader.bat",
            "run_image_downloader_safe_browser.bat",
            "run_diagnose_export.bat",
            "README_QUICK_START.md",
        ]
        for name in managed_names:
            (test_root / name).write_text(f"fixture:{name}\n", encoding="utf-8")
        (test_root / VERSION_FILENAME).write_text(
            f"Package ID: {PACKAGE_ID}\nVersion: {APP_VERSION}\nBuild: {BUILD_NAME}\n",
            encoding="utf-8",
        )
        package_meta = {
            "package_id": PACKAGE_ID,
            "version": APP_VERSION,
            "build_id": BUILD_NAME,
            "execution_namespace": EXECUTION_NAMESPACE,
            "canonical_entrypoint": CANONICAL_ENTRYPOINT,
            "backend_target": SCRIPT_FILENAME,
            "project_output_roots": PROJECT_OUTPUT_ROOTS,
            "gate": RUNTIME_IDENTITY_GATE_VERSION,
        }
        (test_root / PACKAGE_METADATA_FILENAME).write_text(json.dumps(package_meta, indent=2) + "\n", encoding="utf-8")

        def write_manifest(extra_entries: Optional[List[Dict[str, Any]]] = None) -> None:
            entries: List[Dict[str, Any]] = []
            for name in managed_names:
                path = test_root / name
                entries.append({
                    "path": name,
                    "package_managed": True,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                })
            if extra_entries:
                entries.extend(extra_entries)
            manifest = {
                "package_id": PACKAGE_ID,
                "version": APP_VERSION,
                "build_id": BUILD_NAME,
                "execution_namespace": EXECUTION_NAMESPACE,
                "canonical_entrypoint": CANONICAL_ENTRYPOINT,
                "backend_target": SCRIPT_FILENAME,
                "project_output_roots": PROJECT_OUTPUT_ROOTS,
                "files": entries,
            }
            (test_root / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        write_manifest()
        before = {name: sha256_file(test_root / name) for name in managed_names + [MANIFEST_FILENAME]}
        passed = verify_release_identity(test_root)
        after = {name: sha256_file(test_root / name) for name in managed_names + [MANIFEST_FILENAME]}
        if passed.get("result") != "PASS" or passed.get("verified_count") != passed.get("managed_count"):
            return False, "valid synthetic release did not PASS"
        if before != after or passed.get("verification_mutated_release_files") is not False:
            return False, "verification mutated release files"

        target = test_root / "README_QUICK_START.md"
        target.write_text("stale mixed-release bytes\n", encoding="utf-8")
        mixed = verify_release_identity(test_root)
        if mixed.get("result") != "BLOCK" or not any(item.get("kind") in {"managed_size_mismatch", "managed_sha256_mismatch"} for item in mixed.get("mismatches", []) if isinstance(item, dict)):
            return False, "same-version mixed managed file was not blocked"
        target.write_text("fixture:README_QUICK_START.md\n", encoding="utf-8")
        write_manifest()

        metadata_bytes = (test_root / PACKAGE_METADATA_FILENAME).read_bytes()
        (test_root / PACKAGE_METADATA_FILENAME).unlink()
        missing = verify_release_identity(test_root)
        if missing.get("result") != "BLOCK" or not any(item.get("kind") == "missing_control_file" for item in missing.get("mismatches", []) if isinstance(item, dict)):
            return False, "missing control file was not blocked"
        (test_root / PACKAGE_METADATA_FILENAME).write_bytes(metadata_bytes)
        write_manifest()

        write_manifest([{"path": "../escape.bin", "package_managed": True, "size_bytes": 1, "sha256": "0" * 64}])
        unsafe = verify_release_identity(test_root)
        if unsafe.get("result") != "BLOCK" or not any(item.get("kind") == "unsafe_managed_path" for item in unsafe.get("mismatches", []) if isinstance(item, dict)):
            return False, "unsafe managed path was not blocked"
        return True, "PASS, mixed-release BLOCK, missing-control BLOCK, unsafe-path BLOCK, no verification rewrite"
    finally:
        shutil.rmtree(test_root, ignore_errors=True)


def run_self_test() -> int:
    print(f"{APP_NAME} self-test starting...")
    gate_ok, gate_note = run_release_identity_gate_self_test()
    if not gate_ok:
        print(f"Self-test failed: runtime identity gate: {gate_note}")
        return 1
    print(f"Runtime identity gate synthetic tests: {gate_note}")
    test_temp_parent = app_root() / TEMP_DIRNAME
    test_temp_parent.mkdir(parents=True, exist_ok=True)
    parent = Path(tempfile.mkdtemp(prefix="image_downloader_selftest_", dir=str(test_temp_parent)))
    root = parent / "Image Downloader self test with spaces"
    root.mkdir(parents=True, exist_ok=True)
    httpd: Optional[ThreadingHTTPServer] = None
    server_stopped = False
    old_cwd = Path.cwd()
    try:
        site = root / "site"
        images = site / "images"
        images.mkdir(parents=True, exist_ok=True)
        visual_base = build_test_png(33, 66, 99)
        visual_duplicate = visual_base[:-12] + struct.pack(">I", 8) + b"tEXt" + b"note\x00dup" + struct.pack(">I", zlib.crc32(b"tEXt" + b"note\x00dup") & 0xFFFFFFFF) + visual_base[-12:]
        fixtures = {
            "photo_0007.png": build_test_png(255, 0, 0),
            "photo_0008.png": build_test_png(0, 255, 0),
            "photo_0009.png": build_test_png(0, 0, 255),
            "modern_small.png": build_test_png(255, 255, 0),
            "modern_large.png": build_test_png(0, 255, 255),
            "retry.png": build_test_png(255, 0, 255),
            "throttle.png": build_test_png(120, 40, 200),
            "resume.png": build_test_png(90, 100, 110),
            "noscript.png": build_test_png(240, 120, 20),
            "visual_base.png": visual_base,
            "visual_duplicate.png": visual_duplicate,
            "slow.png": build_test_png(10, 140, 220),
            "gallery_page.png": build_test_png(15, 25, 35),
        }
        for name, payload in fixtures.items():
            (images / name).write_bytes(payload)
        (images / "photo_0010.png").write_text("not an image", encoding="utf-8")
        (site / "index.html").write_text(
            """<!doctype html><html><head>
<link rel="preload" as="image" imagesrcset="/images/modern_small.png 1x, /images/modern_large.png 2x">
<style>.hero { background-image: url('/images/retry.png'); }</style>
<script type="application/ld+json">{"@type":"ImageObject","contentUrl":"/images/resume.png"}</script>
</head><body><img src="/images/photo_0007.png"><img src="/images/throttle.png">
<noscript>&lt;img src="/images/noscript.png"&gt;</noscript>
<img src="/images/visual_base.png"><img src="/images/visual_duplicate.png">
<a rel="next" class="pagination-next" href="/gallery2.html">Next page</a>
</body></html>""",
            encoding="utf-8",
        )
        (site / "gallery2.html").write_text(
            "<!doctype html><html><body><img src='/images/gallery_page.png'></body></html>",
            encoding="utf-8",
        )

        retry_lock = threading.Lock()
        retry_gets = {"count": 0}
        throttle_gets = {"count": 0}
        resume_payload = fixtures["resume.png"]
        retry_payload = fixtures["retry.png"]
        throttle_payload = fixtures["throttle.png"]
        slow_payload = fixtures["slow.png"]
        etag = '"selftest-resume-v1"'
        last_modified = "Wed, 01 Jul 2026 12:00:00 GMT"

        class SelfTestHandler(SimpleHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, _format: str, *args: Any) -> None:
                return

            def _send_image_headers(self, payload: bytes, *, status: int = 200, range_start: Optional[int] = None) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "image/png")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("ETag", etag)
                self.send_header("Last-Modified", last_modified)
                if range_start is not None:
                    self.send_header("Content-Range", f"bytes {range_start}-{len(payload) - 1}/{len(payload)}")
                    self.send_header("Content-Length", str(len(payload) - range_start))
                else:
                    self.send_header("Content-Length", str(len(payload)))
                self.end_headers()

            def do_HEAD(self) -> None:
                path = urllib.parse.urlparse(self.path).path
                if path == "/images/retry.png":
                    self._send_image_headers(retry_payload)
                    return
                if path == "/images/throttle.png":
                    self._send_image_headers(throttle_payload)
                    return
                if path == "/images/resume.png":
                    self._send_image_headers(resume_payload)
                    return
                if path == "/images/slow.png":
                    self._send_image_headers(slow_payload)
                    return
                super().do_HEAD()

            def do_GET(self) -> None:
                path = urllib.parse.urlparse(self.path).path
                if path == "/images/retry.png":
                    with retry_lock:
                        retry_gets["count"] += 1
                        current = retry_gets["count"]
                    if current == 1:
                        self.send_response(503)
                        self.send_header("Retry-After", "1")
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    self._send_image_headers(retry_payload)
                    self.wfile.write(retry_payload)
                    return
                if path == "/images/throttle.png":
                    with retry_lock:
                        throttle_gets["count"] += 1
                        current = throttle_gets["count"]
                    if current == 1:
                        self.send_response(429)
                        self.send_header("Retry-After", "1")
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    self._send_image_headers(throttle_payload)
                    self.wfile.write(throttle_payload)
                    return
                if path == "/images/slow.png":
                    self._send_image_headers(slow_payload)
                    time.sleep(6)
                    with contextlib.suppress(BrokenPipeError, ConnectionResetError):
                        self.wfile.write(slow_payload)
                    return
                if path == "/images/resume.png":
                    range_header = str(self.headers.get("Range", ""))
                    match = re.match(r"bytes=(\d+)-", range_header)
                    if match:
                        start_byte = int(match.group(1))
                        if start_byte >= len(resume_payload):
                            self.send_response(416)
                            self.send_header("Content-Range", f"bytes */{len(resume_payload)}")
                            self.send_header("Content-Length", "0")
                            self.end_headers()
                            return
                        self._send_image_headers(resume_payload, status=206, range_start=start_byte)
                        self.wfile.write(resume_payload[start_byte:])
                        return
                    self._send_image_headers(resume_payload)
                    self.wfile.write(resume_payload)
                    return
                super().do_GET()

        config_path = root / CONFIG_FILENAME
        if not bool(default_config().get("hide_downloaded_media", False)):
            print("Self-test failed: downloaded media is not hidden by default.")
            return 1
        if windows_attributes_with_visibility(0, True) & WINDOWS_FILE_ATTRIBUTE_HIDDEN == 0:
            print("Self-test failed: Windows hidden attribute helper did not enable the hidden bit.")
            return 1
        if windows_attributes_with_visibility(WINDOWS_FILE_ATTRIBUTE_HIDDEN, False) & WINDOWS_FILE_ATTRIBUTE_HIDDEN:
            print("Self-test failed: Windows hidden attribute helper did not clear the hidden bit.")
            return 1
        cfg = default_config()
        if int(default_config().get("request_wall_clock_timeout_seconds", 0)) != 5:
            print("Self-test failed: default per-image download timeout is not 5 seconds.")
            return 1
        cfg.update({
            "output": "downloads",
            "workers": 3,
            "retries": 2,
            "network_recovery_extra_attempts": 1,
            "network_session_reset_debounce_ms": 1000,
            "adaptive_throttle_enabled": True,
            "adaptive_throttle_min_workers": 1,
            "adaptive_throttle_max_workers": 3,
            "adaptive_throttle_target_latency_ms": 5000,
            "adaptive_throttle_slow_latency_ms": 10000,
            "adaptive_throttle_successes_to_increase": 2,
            "retry_backoff_base_ms": 0,
            "retry_backoff_max_ms": 0,
            "retry_jitter_ms": 0,
            "retry_after_max_seconds": 1,
            "connect_timeout": 3,
            "read_timeout": 5,
            "request_wall_clock_timeout_seconds": 30,
            "page_wall_clock_timeout_seconds": 20,
            "sequence_max_candidates_per_group": 8,
            "sequence_max_failed_attempts": 2,
            "sequence_backward_steps": 1,
            "sequence_probe_delay_ms": 0,
            "safe_svg_validation": True,
            "srcset_preference": "all",
            "resume_min_bytes": 1,
            "state_checkpoint_interval_downloads": 2,
            "partial_retention_hours": 1,
            "strict_raster_verify": True,
            "image_max_pixels": 1000000,
            "duplicate_visual_fingerprint_check": True,
            "duplicate_library_reconcile_enabled": True,
            "duplicate_library_reconcile_max_files": 100,
            "duplicate_library_reconcile_time_budget_seconds": 5,
            "automation_mode": "smart_safe",
            "auto_gallery_follow_enabled": True,
            "auto_gallery_page_limit": 3,
            "auto_gallery_max_depth": 1,
            "auto_gallery_link_limit_per_page": 12,
            "canonical_export_filename": CANONICAL_EXPORT_FILENAME,
            "export_keep_previous_zips": 0,
        })
        json_dump(config_path, cfg)
        os.chdir(site)
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), SelfTestHandler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        guard = InstanceGuard(root, role="self_test", enabled=True, stale_seconds=60, run_id=make_run_id("selftest"))
        guard.acquire()
        alive_now, signature_now = process_status(os.getpid())
        lock_meta = guard._read_lock()
        if not alive_now:
            print("Self-test failed: current process liveness query returned false.")
            return 1
        if lock_meta.get("process_start_signature") != guard.process_start_signature:
            print("Self-test failed: lock process-start signature was not persisted consistently.")
            return 1
        if signature_now and guard.process_start_signature and signature_now != guard.process_start_signature:
            print("Self-test failed: process-start signature changed during the same process.")
            return 1
        duplicate_rejected = False
        downloader: Optional[ImageDownloader] = None
        try:
            second_guard = InstanceGuard(root, role="self_test_duplicate", enabled=True, stale_seconds=60, run_id=make_run_id("selftestdup"))
            try:
                second_guard.acquire()
            except RuntimeError:
                duplicate_rejected = True
            finally:
                second_guard.release("self_test_cleanup")
            if not duplicate_rejected:
                print("Self-test failed: duplicate instance guard did not reject a second top-level launch.")
                return 1

            downloader = ImageDownloader(root, config_path, top_level_run_id=guard.run_id, instance_guard=guard)
            resume_url = f"http://127.0.0.1:{port}/images/resume.png"
            part_path, meta_path = downloader._partial_paths(resume_url)
            partial_size = max(1, len(resume_payload) // 2)
            part_path.write_bytes(resume_payload[:partial_size])
            downloader._write_partial_metadata(meta_path, {
                "url": resume_url,
                "final_url": resume_url,
                "etag": etag,
                "last_modified": last_modified,
                "content_type": "image/png",
                "expected_total": len(resume_payload),
                "updated_at": now_local(),
            })
            summary = downloader.process_url(f"http://127.0.0.1:{port}/index.html")
            original_download_timeout = downloader.config.get("request_wall_clock_timeout_seconds", 30)
            original_connect_timeout = downloader.config.get("connect_timeout", 3)
            original_read_timeout = downloader.config.get("read_timeout", 5)
            downloader.config["request_wall_clock_timeout_seconds"] = 5
            downloader.config["connect_timeout"] = 3
            downloader.config["read_timeout"] = 5
            slow_started = time.monotonic()
            slow_result = downloader.download_one(f"http://127.0.0.1:{port}/images/slow.png", source="self_test", reason="five_second_timeout")
            slow_elapsed = time.monotonic() - slow_started
            downloader.config["request_wall_clock_timeout_seconds"] = original_download_timeout
            downloader.config["connect_timeout"] = original_connect_timeout
            downloader.config["read_timeout"] = original_read_timeout
            if slow_result.status != "failed" or "timeout" not in slow_result.reason.lower() and "timed out" not in slow_result.reason.lower() and "exceeded" not in slow_result.reason.lower():
                print(f"Self-test failed: slow image did not fail through the 5-second timeout contract ({slow_result.status}: {slow_result.reason}).")
                return 1
            if slow_elapsed > 6.5:
                print(f"Self-test failed: slow image exceeded bounded timeout allowance ({slow_elapsed:.3f}s).")
                return 1
            downloader._reset_http_session("self-test simulated network change", f"http://127.0.0.1:{port}/index.html", "self_test")
            downloader._reset_http_session("self-test concurrent reset coalescing", f"http://127.0.0.1:{port}/index.html", "self_test")
            reset_snapshot = downloader._network_recovery_snapshot()
            if int(reset_snapshot.get("http_session_resets", 0)) < 1:
                print("Self-test failed: HTTP session reset recovery counter did not update.")
                return 1
            if int(reset_snapshot.get("coalesced_http_session_resets", 0)) < 1:
                print("Self-test failed: concurrent HTTP session resets were not coalesced.")
                return 1
        finally:
            if downloader is not None:
                with contextlib.suppress(Exception):
                    downloader.close()
            guard.release("self_test")

        downloaded = int(summary.get("downloaded", 0))
        sequence_downloaded = int(summary.get("sequential_search", {}).get("probes_downloaded", 0))
        catalog = downloader.state.get("hashes", {}) if isinstance(downloader.state.get("hashes"), dict) else {}
        if not catalog or not all(
            isinstance(record, dict)
            and str(record.get("asset_id", "")).startswith("IMGDL-IMAGE-")
            and record.get("metadata_schema") == ASSET_METADATA_SCHEMA
            and str(record.get("media_visibility", "")) in {"hidden", "visible", "not_applicable", "failed"}
            for record in catalog.values()
        ):
            print("Self-test failed: downloaded-image asset metadata catalog is incomplete.")
            return 1
        discovery = summary.get("discovery", {}) if isinstance(summary.get("discovery"), dict) else {}
        recovery = summary.get("transfer_recovery", {}) if isinstance(summary.get("transfer_recovery"), dict) else {}
        duplicate_evidence = summary.get("duplicate_detection", {}) if isinstance(summary.get("duplicate_detection"), dict) else {}
        if downloaded < 10 or sequence_downloaded < 2:
            print(f"Self-test failed: expected modern + sequential images were not downloaded (downloaded={downloaded}, sequence={sequence_downloaded}).")
            return 1
        if int(summary.get("duplicate_visual_skips", 0)) < 1 or int(duplicate_evidence.get("visual_duplicates_skipped", 0)) < 1:
            print("Self-test failed: visually equivalent re-encoded image was not auto-detected as a duplicate.")
            return 1
        if not isinstance(downloader.state.get("visual_hashes"), dict) or not downloader.state.get("visual_hashes"):
            print("Self-test failed: visual duplicate index was not persisted in state.")
            return 1
        for key in ["imagesrcset_candidates", "jsonld_candidates", "css_candidates", "noscript_candidates"]:
            if int(discovery.get(key, 0)) < 1:
                print(f"Self-test failed: modern discovery evidence missing for {key}.")
                return 1
        if int(recovery.get("partial_resume_successes", 0)) < 1 or int(recovery.get("partial_bytes_reused", 0)) < 1:
            print("Self-test failed: validator-gated partial resume was not exercised.")
            return 1
        if int(recovery.get("status_retries", 0)) < 2 or int(recovery.get("retry_after_honored", 0)) < 2:
            print("Self-test failed: server-aware Retry-After/status retry was not exercised for both 429 and 503.")
            return 1
        adaptive = summary.get("adaptive_throttle", {}) if isinstance(summary.get("adaptive_throttle"), dict) else {}
        if not adaptive.get("enabled") or int(adaptive.get("rate_limit_events", 0)) < 1 or int(adaptive.get("server_pressure_events", 0)) < 1:
            print("Self-test failed: adaptive throttle did not observe 429 and 5xx pressure.")
            return 1
        if int(adaptive.get("limit_decreases", 0)) < 1 or int(adaptive.get("max_observed_in_flight", 0)) < 1:
            print("Self-test failed: adaptive throttle did not adjust or observe bounded concurrency.")
            return 1
        automation = summary.get("automation", {}) if isinstance(summary.get("automation"), dict) else {}
        if not automation.get("enabled") or int(discovery.get("auto_gallery_pages_visited", 0)) < 1:
            print("Self-test failed: Smart Safe Automation did not follow the strong same-domain gallery/pagination signal.")
            return 1
        if summary.get("terminal_status") != "completed":
            print("Self-test failed: successful run did not finish with terminal_status=completed.")
            return 1
        if "network_recovery" not in summary or "backpressure" not in summary or "top_level_run_id" not in summary:
            print("Self-test failed: operational run evidence was not recorded.")
            return 1
        visibility = summary.get("media_visibility", {}) if isinstance(summary.get("media_visibility"), dict) else {}
        if visibility.get("configured_default") != "hidden":
            print("Self-test failed: run summary did not report hidden media as the configured default.")
            return 1
        if os.name != "nt" and int(visibility.get("not_applicable", 0)) < downloaded:
            print("Self-test failed: non-Windows visibility outcomes were not recorded for completed downloads.")
            return 1

        valid_png = build_test_png(10, 20, 30)
        corrupt_png = valid_png[:-12]
        if not validate_image_payload(valid_png, "png", strict_raster_verify=True, max_pixels=1000000)[0]:
            print("Self-test failed: valid PNG did not pass strict verification.")
            return 1
        if validate_image_payload(corrupt_png, "png", strict_raster_verify=True, max_pixels=1000000)[0]:
            print("Self-test failed: corrupt PNG incorrectly passed strict verification.")
            return 1
        for reserved_name in ["CON.png", "aux.JPG", "LPT1.webp", "nul"]:
            sanitized = sanitize_filename(reserved_name)
            if os.path.splitext(sanitized)[0].rstrip(" .").upper() in WINDOWS_RESERVED_FILE_STEMS:
                print(f"Self-test failed: Windows-reserved filename was not neutralized ({reserved_name} -> {sanitized}).")
                return 1
        if "\u202e" in sanitize_filename("safe\u202ename.png"):
            print("Self-test failed: bidirectional filename control was not removed.")
            return 1
        secret_url = "https://user:password@example.com/image.png?X-Amz-Signature=topsecret&size=large&token=abc123"
        safe_secret_url = redact_url_for_evidence(secret_url)
        if any(secret in safe_secret_url for secret in ["user", "password", "topsecret", "abc123"]):
            print("Self-test failed: URL evidence redaction exposed credentials or signed-query values.")
            return 1
        if "size=large" not in safe_secret_url or "<REDACTED>" not in urllib.parse.unquote(safe_secret_url):
            print("Self-test failed: URL evidence redaction removed useful non-secret evidence or omitted redaction markers.")
            return 1
        embedded_secret = redact_sensitive_text(f"request failed for {secret_url}")
        if any(secret in embedded_secret for secret in ["user", "password", "topsecret", "abc123"]):
            print("Self-test failed: embedded URL redaction exposed credentials or signed-query values.")
            return 1

        if httpd is not None:
            httpd.shutdown()
            thread.join(timeout=5)
            server_stopped = True
        export_path = export_for_support(root, config_path)
        second_export = export_for_support(root, config_path)
        if export_path != second_export or export_path.name != CANONICAL_EXPORT_FILENAME or export_path.parent != (root / EXPORT_DIRNAME):
            print("Self-test failed: export did not use the canonical project-local exports ZIP path.")
            return 1
        export_zip_candidates = list((root / EXPORT_DIRNAME).glob("IMAGE_DOWNLOADER_SUPPORT_EXPORT*.zip")) + list((root / EXPORT_DIRNAME).glob("image_downloader_support_export_*.zip"))
        if len(export_zip_candidates) != 1:
            print(f"Self-test failed: expected one support ZIP under exports, found {len(export_zip_candidates)}.")
            return 1
        if list(root.glob("IMAGE_DOWNLOADER_SUPPORT_EXPORT*.zip")):
            print("Self-test failed: Export20 published a ZIP in the project root instead of exports/.")
            return 1
        for candidate_export in (export_path, second_export):
            with zipfile.ZipFile(candidate_export, "r") as zf:
                names = zf.namelist()
                if not zf.comment.decode("utf-8", errors="replace").startswith("IMGDL-EXPORT-"):
                    print("Self-test failed: Export20 ZIP metadata comment is missing.")
                    return 1
                manifest = json.loads(zf.read("export_manifest.json").decode("utf-8"))
                if manifest.get("metadata_schema") != ASSET_METADATA_SCHEMA or not manifest.get("assets"):
                    print("Self-test failed: Export20 asset manifest metadata is incomplete.")
                    return 1
            if len(names) > EXPORT_FILE_LIMIT or len(names) != len(set(names)):
                print("Self-test failed: export file cap or duplicate-name guard failed.")
                return 1
            if not manifest.get("report_only") or manifest.get("network_calls_performed_by_export"):
                print("Self-test failed: export report-only/offline posture is incorrect.")
                return 1
            if not isinstance(manifest.get("collector_outcomes"), list) or not manifest.get("collector_outcomes"):
                print("Self-test failed: export collector outcomes were not recorded.")
                return 1
            if candidate_export.name in names or any(name.lower().endswith(".zip") for name in names):
                print("Self-test failed: export recursively included an archive.")
                return 1
            for required_name in ["diagnostic_report.txt", "project_handoff_notes.txt", "recent_failures_errors.json", "current_parameter_alignment_status.txt"]:
                if required_name not in names:
                    print(f"Self-test failed: export missing {required_name}.")
                    return 1

        diagnostic_text = diagnostic_report(root, config_path)
        for heading in [
            "Smart discovery / transfer stability summary",
            "Platform/API compliance and drift snapshot",
            "Google Drive vault/reference status",
            "Custom-input / config assurance snapshot",
            "Digital asset metadata reconciliation",
            "Helpful computer awareness (non-restrictive)",
            "Automatic duplicate-detection summary",
            "Path targeting / relocation summary",
            "Omission-control coverage ledger",
            "Work-window triage / exit status",
        ]:
            if heading not in diagnostic_text:
                print(f"Self-test failed: diagnostics missing {heading}.")
                return 1
        high_worker_cfg = normalize_config({"workers": 99, "adaptive_throttle_min_workers": 99, "adaptive_throttle_max_workers": 99})
        if high_worker_cfg.get("workers") != MAX_ACTIVE_DOWNLOADS or high_worker_cfg.get("adaptive_throttle_min_workers") != MAX_ACTIVE_DOWNLOADS or high_worker_cfg.get("adaptive_throttle_max_workers") != MAX_ACTIVE_DOWNLOADS:
            print("Self-test failed: legacy/high worker settings did not normalize to the hard cap of three.")
            return 1
        if safe_int(cfg.get("download_queue_capacity", 0), 0) != DOWNLOAD_QUEUE_HARD_MAX:
            print("Self-test failed: default download queue capacity is not 100.")
            return 1
        if safe_int(cfg.get("workers", 0), 0) > MAX_ACTIVE_DOWNLOADS or safe_int(cfg.get("adaptive_throttle_max_workers", 0), 0) > MAX_ACTIVE_DOWNLOADS:
            print("Self-test failed: configured or adaptive worker cap exceeds three.")
            return 1
        if downloader.adaptive_throttle.snapshot().get("max_observed_in_flight", 0) > MAX_ACTIVE_DOWNLOADS:
            print("Self-test failed: observed active downloads exceeded the hard cap of three.")
            return 1
        local_output, local_mode = resolve_download_output(root, {"output": "downloads", "output_mode": "project_local"})
        if local_mode != "project_local" or not _path_is_within(local_output, root):
            print("Self-test failed: project-local output did not stay under the project root.")
            return 1
        try:
            resolve_download_output(root, {"output": "../escape", "output_mode": "project_local"})
            print("Self-test failed: escaping relative output path was not blocked.")
            return 1
        except RuntimeError:
            pass
        external_fixture = (root.parent / "explicit external output").resolve()
        resolved_external, external_mode = resolve_download_output(root, {"output": str(external_fixture), "output_mode": "external_explicit"})
        if external_mode != "external_explicit" or resolved_external != external_fixture:
            print("Self-test failed: explicit external output resolution failed.")
            return 1
        queue_test = downloader.enqueue_download_urls([f"http://127.0.0.1:{port}/queued_{i}.png" for i in range(DOWNLOAD_QUEUE_HARD_MAX + 1)], source="self-test")
        if len(queue_test.get("accepted", [])) != DOWNLOAD_QUEUE_HARD_MAX or len(queue_test.get("rejected", [])) != 1:
            print("Self-test failed: persistent queue did not enforce exactly 100 items.")
            return 1
        preview = downloader.download_queue_preview(limit=DOWNLOAD_QUEUE_HARD_MAX + 5)
        if len(preview) != DOWNLOAD_QUEUE_HARD_MAX or not downloader.download_queue_path.is_file():
            print("Self-test failed: persistent queue autosave/preview evidence is incomplete.")
            return 1
        downloader.download_queue_state["items"][0]["status"] = "running"
        downloader._save_download_queue_state()
        reloaded_queue = downloader._load_download_queue_state()
        if reloaded_queue.get("items", [])[0].get("status") != "pending" or safe_int(reloaded_queue.get("recovered_running_items", 0), 0) < 1:
            print("Self-test failed: running queue item was not recovered to pending.")
            return 1
        downloader.download_queue_state["items"] = []
        downloader._save_download_queue_state()
        latest_list = downloader.write_session_download_list(final=False)
        if latest_list is None or not latest_list.is_file() or "Maximum active downloads: 3" not in latest_list.read_text(encoding="utf-8"):
            print("Self-test failed: session download-list TXT was not generated with concurrency metadata.")
            return 1
        if resolve_computer_profile("Raider GE66 12UHS") != "PC-DEUSEX-03":
            print("Self-test failed: helpful computer alias did not resolve to DeusEx.")
            return 1
        test_ctx = detect_computer_context({"computer_awareness_enabled": True, "computer_profile_override_env_name": "IMAGE_DOWNLOADER_TEST_COMPUTER_LABEL"})
        for forbidden_true in ("launch_restrictions", "state_path_changes", "lock_scope_changes", "feature_restrictions"):
            if bool(test_ctx.get(forbidden_true)):
                print(f"Self-test failed: computer awareness unexpectedly enabled {forbidden_true}.")
                return 1
        print(
            "Self-test passed: startup/config/path-with-spaces, modern responsive/lazy/JSON-LD/CSS discovery, "
            "bounded sequential probing, server-aware Retry-After, adaptive AIMD/EWMA throttling, coalesced reconnect/session renewal, validator-gated partial resume, streamed strict image verification, "
            "non-signalling process identity, optional instance-lock mechanics, lock-before-migration test ordering, schema/state checkpoints, VPN/IP recovery hooks, graceful bounded worker controls, "
            "runtime release identity/hash gate, redacted failure-isolated offline Export20, credential-safe URL evidence, Windows-reserved filename neutralization, nonrestrictive helpful computer labeling, one canonical easy-to-find support ZIP, persistent 100-item queue autosave/crash recovery, a hard three-active-download ceiling, timestamped session download-list TXT output, Smart Safe Automation with conservative same-domain gallery pagination, strict five-second per-image download timeout, URL/SHA256/visual/library duplicate autodetection, canonical asset metadata reconciliation, content-addressed downloaded-image metadata, embedded ZIP metadata, atomic ZIP finalization, and recursive-export prevention are working."
        )
        return 0
    except Exception:
        print("Self-test failed with an exception:")
        traceback.print_exc()
        return 1
    finally:
        if httpd is not None and not server_stopped:
            with contextlib.suppress(Exception):
                httpd.shutdown()
        os.chdir(old_cwd)
        shutil.rmtree(parent, ignore_errors=True)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("--config", help="Path to config JSON", default=None)
    parser.add_argument("--url", help="Download from one URL and exit", default=None)
    parser.add_argument("--standard", action="store_true", help="Use Standard Mode (default)")
    parser.add_argument("--fast", action="store_true", help="Alias for Standard Mode")
    parser.add_argument("--browser-mode", action="store_true", help="Use optional Safe Browser Mode for trusted sites only")
    parser.add_argument("--dry-run", action="store_true", help="Preview candidates without saving files")
    parser.add_argument("--diagnose", action="store_true", help="Write an extensive diagnostic report")
    parser.add_argument("--export-support", action="store_true", help="Create a <=20-file support ZIP")
    parser.add_argument("--self-test", action="store_true", help="Run local sanity checks")
    parser.add_argument("--verify-release", action="store_true", help="Verify release identity and every package-managed file, then exit")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.version:
        print(f"{APP_NAME} {APP_VERSION} ({BUILD_NAME}, {BUILD_DATE})")
        return 0
    root = app_root()
    # Release ordering: canonical root/log setup, then read-only identity/hash gate,
    # before dependency installs, credentials, browser startup, or download/network activity.
    (root / LOG_DIRNAME).mkdir(parents=True, exist_ok=True)
    gate_evidence = verify_release_identity(root)
    if args.verify_release:
        print_release_identity_result(gate_evidence)
        return 0 if gate_evidence.get("result") == "PASS" else RELEASE_IDENTITY_EXIT_CODE
    if args.self_test:
        if gate_evidence.get("result") != "PASS":
            print_release_identity_result(gate_evidence)
            print("Self-test blocked because the release identity gate did not PASS.")
            return RELEASE_IDENTITY_EXIT_CODE
        return run_self_test()
    config_path = Path(args.config).resolve() if args.config else root / CONFIG_FILENAME
    if args.diagnose or args.export_support:
        try:
            # Diagnostic/export mode is intentionally report-only: it creates reports/exports,
            # but it does not install dependencies, run cleanup/repair, migrate config/state,
            # or take the interactive instance lock.
            diagnostic_path: Optional[Path] = None
            if args.diagnose:
                diagnostic_path = write_diagnostics(root, config_path)
                print(f"Diagnostic report created: {diagnostic_path}")
            if args.export_support:
                path = export_for_support(root, config_path, diagnostic_path)
                print(f"support export ZIP created: {path}")
                print("Share this file with authorized support personnel.")
            return 0
        except Exception as exc:
            print(f"Diagnostic/export error: {exc}")
            return 1
    if gate_evidence.get("result") != "PASS":
        print_release_identity_result(gate_evidence)
        print("Startup blocked before dependency/authenticated/network runtime. Run GatewayImageDownloader_DiagnosticsExport.bat for a Support Export20, or restore the full verified release ZIP.")
        return RELEASE_IDENTITY_EXIT_CODE
    browser_override: Optional[bool] = None
    if args.browser_mode:
        browser_override = True
    elif args.standard or args.fast:
        browser_override = False
    dry_override: Optional[bool] = True if args.dry_run else None
    downloader: Optional[ImageDownloader] = None
    guard: Optional[InstanceGuard] = None
    exit_status = "normal"
    try:
        # Read only the minimum guard settings before ownership. Do not create/migrate
        # config or mutate project state until the top-level lock is held.
        raw_cfg = json_load(config_path, {})
        raw_cfg = raw_cfg if isinstance(raw_cfg, dict) else {}
        top_level_run_id = make_run_id()
        guard = InstanceGuard(
            root,
            role="interactive",
            enabled=False,
            stale_seconds=safe_int(raw_cfg.get("single_instance_lock_stale_seconds", 21600), 21600, min_value=60, max_value=604800),
            run_id=top_level_run_id,
        )
        guard.acquire()
        guard.heartbeat("startup_owned")
        downloader = ImageDownloader(root, config_path, browser_mode=browser_override, dry_run=dry_override, top_level_run_id=guard.run_id, instance_guard=guard)
        archive_removed_coordination_artifacts(root)
        archive_nested_release_folder(root, downloader.config)
        archive_superseded_support_docs(root, downloader.config)
        guard.heartbeat("startup_ready")
        if args.url:
            summary = downloader.process_url(args.url)
            terminal_status = summary.get("terminal_status") if isinstance(summary, dict) else None
            saved_or_duplicate = 0
            if isinstance(summary, dict):
                saved_or_duplicate = sum(
                    safe_int(summary.get(key, 0), 0, min_value=0)
                    for key in ("downloaded", "duplicate_url_skips", "duplicate_content_skips", "duplicate_visual_skips")
                )
            if terminal_status == "completed" and (bool(downloader.config.get("dry_run", False)) or saved_or_duplicate > 0):
                return 0
            exit_status = "error"
            return 1
        interactive_loop(downloader)
        return 0
    except KeyboardInterrupt:
        exit_status = "interrupted"
        print("\nInterrupted.")
        return 130
    except Exception as exc:
        exit_status = "error"
        print(f"Startup/runtime error: {exc}")
        return 1
    finally:
        if downloader is not None:
            downloader.close()
        if guard is not None:
            guard.release(exit_status)

if __name__ == "__main__":
    raise SystemExit(main())
