# Changelog

## 1.0.1 — 2026-11-16

- Fixed initial administrator creation failing with `AttributeError: app_db` outside a web request. Database connections now use the Flask application configuration in both CLI and web contexts.
- Added direct first-install CLI tests for successful creation/login, short-password rejection and duplicate-account preservation.
- Duplicate usernames now produce a clear CLI error. No schema or dependency changes; existing accounts and data are preserved.

## 1.0.0 — 2026-11-16

First combined App2 release, built from the empty repository baseline.

- Added Cirrus Pulse: login, roles, targeted notices, schedules/expiry, priorities, pinned board, drafts, archive/filtering, acknowledgements and notifications.
- Added Cirrus AssetPass: inventory/specification editing, warranties, personal equipment, transactional assignment/receipt/return workflows, damage/loss reporting, protected attachments, lifecycle audit history, QR labels, scoped Excel reports and offboarding equipment clearance.
- Added admin accounts, department/category management, dark theme and responsive orange/charcoal interface.
- Added Windows setup/start/stop scripts for the existing loopback port 8000 model, isolated private data, consistent backup, additive schema initialization and rollback documentation.
- Added automated regression/permission/concurrency/runtime checks, browser acceptance workflow, synthetic screenshots and reproducible ZIP packaging.

No previous App2 release or existing Pulse records were present. No Cirrus Workplace files or production services were accessed or changed.
