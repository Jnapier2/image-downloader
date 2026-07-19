# Image Downloader

[![CI](https://github.com/Jnapier2/image-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/Jnapier2/image-downloader/actions/workflows/ci.yml)

A Windows-friendly image collection utility built around permission-aware discovery, streamed validation, and duplicate prevention. It accepts a public page or direct image URL, discovers bounded candidates, validates retained content, and records enough state to resume safely without executing downloaded files.

## What it demonstrates

- Standard HTTP mode for predictable page and direct-image workflows.
- Optional Playwright mode for trusted, JavaScript-rendered pages only.
- Defensive rejection of executable/archive extensions, dangerous content types, oversized files, corrupt raster payloads, and active SVG content.
- Network destination checks block credentials-in-URL, loopback, private, link-local, and non-global DNS targets across initial requests, redirects, and optional browser subrequests. Because standard clients resolve hostnames again when connecting, this is defense in depth rather than a complete isolation boundary against hostile DNS rebinding; do not process untrusted URLs from a sensitive network.
- Duplicate controls at URL, SHA-256 content, filename-conflict, and perceptual-fingerprint layers.
- Validator-gated partial resume, atomic finalization, adaptive concurrency, bounded retries, and single-instance ownership.
- Visible download output by default; the Windows hidden-file attribute is an explicit configuration opt-in.

This tool does **not** bypass authentication, paywalls, access controls, robots/site policy, or technical restrictions. Confirm that the content owner and the relevant site permit each download.

## Quick start

Requirements: Windows 10/11 and Python 3.11 or newer.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item image_downloader_config.example.json image_downloader_config.json
python image_downloader.py --standard
```

Paste a permitted page or image URL at the prompt. For a one-shot, non-interactive preview:

```powershell
python image_downloader.py --standard --dry-run --url "https://example.org/gallery"
```

`run_image_downloader.bat` provides the same standard-mode entry point without installing anything silently.

## Optional browser mode

Use browser mode only for trusted sites that require client-side rendering:

```powershell
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
python image_downloader.py --browser-mode
```

Browser mode is not a bypass mechanism. It does not automate login or grant permission to retrieve restricted content.

## Configuration

The checked-in example highlights the safety and performance controls. On first run, the application merges it with bounded defaults and writes the complete local configuration. Runtime configuration, downloaded media, indexes, logs, reports, partial transfers, and exports are excluded from version control.

## Verification

```powershell
python -m compileall -q image_downloader.py tests
python -m unittest discover -s tests -v
```

The offline safety suite exercises visible-output defaults, URL and destination controls, dangerous-content classification, SVG active-content detection, safe filenames, HTTP range parsing, duplicate safeguards, and browser-route guardrails without making network requests.

## Boundaries

- Arbitrary sites can change markup or policy without notice.
- Discovery is intentionally bounded; this is not a crawler or archival guarantee.
- The user is responsible for copyright, license, privacy, rate-limit, and site-policy compliance.
- No downloaded media, credentials, browser profile, runtime diagnostics, executable, or generated package index is included.
- The source remains copyright-protected; see [LICENSE.md](LICENSE.md).

## Engineering focus

The design emphasizes cautious input handling, streamed integrity checks, explicit resource budgets, adaptive backpressure, deterministic state, and privacy-conscious operational evidence.
