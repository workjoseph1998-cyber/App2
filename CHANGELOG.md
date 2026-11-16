# Changelog

## 2.0.0 — 2026-11-16

- Rebuilt the interface with a new animated workspace shell, locally bundled typography, orbital visuals, equipment illustrations and consistent light/dark themes.
- Added React-powered command search, notifications drawer, priority tabs, list/grid board layouts, animated real-data summaries and equipment-distribution charts.
- Added sortable/searchable equipment tables, card views, pagination, multi-selection, authenticated quick views and batch QR label printing.
- Added lifecycle progress indicators, refreshed forms/readers and responsive mobile navigation with keyboard/modal focus handling and reduced-motion support.
- Added permission-checked search/notification APIs and management-only batch labels. Existing Pulse/AssetPass authorization and transactional workflows are preserved.
- Added double-click Windows .cmd setup/start/stop/import launchers. Python data import preserves the source and refuses overwrite; the process stop helper checks interpreter, runner path and working directory.
- Added a source-and-prebuilt-interface ZIP, full upgrade/rollback guide, dependency license notices and extended regression/browser coverage. Windows deployment remains manual; no IIS or Workplace changes.

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
