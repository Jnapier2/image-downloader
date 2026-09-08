# Security Policy

## Supported version

Security fixes target the current version on the default branch.

## Reporting a vulnerability

Please use GitHub's private vulnerability-reporting or security-advisory feature for this repository. Do not attach real credentials, private URLs, copyrighted downloads, browser profiles, or personal diagnostic bundles to an issue.

Include the affected version, a minimal reproduction using synthetic or openly licensed content, expected and observed behavior, and the security impact. Please allow time for confirmation before public disclosure.

## Intended security boundary

Image Downloader is a local tool for trusted, permitted HTTP(S) pages and image resources supplied by the user. It does not provide private-network isolation. URL normalization accepts HTTP(S) addresses but does not reject embedded credentials or enforce a public-address allowlist. Initial requests, redirects, and optional browser subrequests can reach destinations accessible from the host computer.

Use only trusted sources, omit credentials from URLs, and do not expose the application as a service that accepts links from other people. Use a separately isolated environment when reviewing unfamiliar sources; browser mode is not a sandbox or an access-control bypass.

The application does not automate login or execute retained files. It checks response content types, extensions, file sizes, raster structure, SVG active content, and output paths before retaining media. These checks reduce content-handling risks but are not malware detection or network isolation. Keep operating-system, browser, and antivirus protections enabled. Site permission and policy decisions remain the user's responsibility.
