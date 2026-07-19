# Security Policy

## Supported version

Security review is focused on the current public branch. Older portfolio snapshots are not maintained.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting or security-advisory feature for this repository. Do not attach real credentials, private URLs, copyrighted downloads, browser profiles, or personal diagnostic bundles to an issue.

Include the affected version, a minimal reproduction using synthetic or openly licensed content, expected and observed behavior, and the security impact. Please allow time for confirmation before public disclosure.

## Intended security boundary

Image Downloader retrieves public HTTP(S) pages and image resources supplied by the user. It rejects credentials embedded in URLs and blocks loopback, private, link-local, and otherwise non-global destinations after DNS resolution, across redirects, and in optional browser subrequests. It does not automate login, bypass access controls, or execute retained files. Candidate URLs, response content types, extensions, file sizes, raster structure, and SVG active content are validated before retention. Site permission and policy decisions remain the user's responsibility.

Hostname screening is defense in depth, not a complete network-isolation boundary. Standard HTTP and browser clients can resolve a hostname again between validation and connection, so a hostile DNS service could change its answer. Do not process untrusted URLs from a sensitive network; use an isolated environment when the source itself is adversarial.
