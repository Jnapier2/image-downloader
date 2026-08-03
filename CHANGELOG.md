# Changelog

## 2026.08.02.1

- Neutralizes Windows reserved device names and removes Unicode bidirectional controls before creating output paths.
- Redacts embedded credentials and common signed-query fields from logs, run summaries, resume metadata, and download-index records while retaining SHA-256 correlation.
- Migrates legacy URL-index records to the credential-safe state schema and writes sanitized migration backups.
- Preserves public-destination checks, content validation, bounded request timing, duplicate controls, and visible output by default.

## 2026.07.19.1

- Established bounded per-image request timing with a separate page-discovery budget.
- Preserved visible output, private-address controls, content validation, duplicate detection, and resumable downloads.

Copyright © 2026 Gateway Information Group LLC. All rights reserved. Third-party components retain their own rights and terms.
