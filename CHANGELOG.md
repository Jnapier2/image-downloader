# Changelog

## 2026.08.09.1 build v2179-readonly-gate-order-repair — 2026-08-15

- Moved the project writeability probe after the read-only release-identity decision.
- Aligned the canonical launcher with the documented Python 3.11 minimum and preferred the project-local `.venv`.
- Replaced stale inline dependency constraints with the versioned requirements files.
- Added regression checks for gate ordering, interpreter selection, and dependency-contract alignment.

## 2026.08.09.1

- Added `GatewayImageDownloader.bat` as the stable Windows entrypoint, with separate safe-browser and diagnostics helpers.
- Kept the established `run_*.bat` names as thin redirects so existing shortcuts continue to work.
- Made `downloads`, `logs`, `state`, `temp`, `reports`, and `exports` project-local by default; an external download folder now requires an explicit validated setting.
- Extended the pre-network release check to cover the execution namespace, canonical launcher, backend target, output roots, and every managed file.
- Preserved queue autosave and recovery, the 100-item capacity, the three-download ceiling, duplicate controls, and timestamped session lists.
- Renamed the public diagnostic artifact to `IMAGE_DOWNLOADER_SUPPORT_EXPORT.zip` and kept operational queue URLs out of that package.
- Verified the source build on Windows before promotion; this public package is independently rechecked by repository CI.

## 2026.08.08.1

- Adds a persistent queue with automatic save and recovery, bounded to 100 items.
- Enforces a hard ceiling of three active downloads while retaining adaptive throttling below that limit.
- Produces a latest-session download list and timestamped session ledgers for reconciliation.
- Verifies release identity and the SHA-256 of every managed release file before dependency, browser, or network activity.
- Adds an offline diagnostic/export launcher and keeps queued URLs out of redacted support bundles.

## 2026.08.02.1

- Neutralizes Windows reserved device names and removes Unicode bidirectional controls before creating output paths.
- Redacts embedded credentials and common signed-query fields from logs, run summaries, resume metadata, and download-index records while retaining SHA-256 correlation.
- Migrates legacy URL-index records to the credential-safe state schema and writes sanitized migration backups.
- Preserves public-destination checks, content validation, bounded request timing, duplicate controls, and visible output by default.

## 2026.07.19.1

- Established bounded per-image request timing with a separate page-discovery budget.
- Preserved visible output, private-address controls, content validation, duplicate detection, and resumable downloads.

Copyright © 2026 Gateway Information Group LLC. All rights reserved. Third-party components retain their own rights and terms.
