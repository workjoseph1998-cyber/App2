# Validation results · 1.0.1

## Administrator bootstrap correction

The reported Windows `init-admin` failure was reproduced as a request-context dependency in database connection initialization and fixed in v1.0.1. The complete regression suite now reports **27 passed**, 0 failed, 0 skipped (23.69 seconds). Three new tests directly exercise the CLI without a web request: first administrator creation followed by authenticated login, short-password rejection without insertion, and duplicate username rejection without modifying the existing account. Ruff checks passed. The one-file patch was also applied to an extracted v1.0.0 archive and the exact documented Flask CLI command successfully created an administrator in a separate synthetic database.

No Windows/IIS execution is claimed for this patch. The remaining results below describe the original v1.0.0 browser and deployment-tool validation, retained unchanged.

## Original combined release validation

Executed on 2026-11-16 in the isolated App2 cloud checkout, using synthetic data only. Runtime: Python 3.12.14, Linux; browser: Chromium 156.0.8078.79, headless Playwright. No Windows VM, IIS service, Workplace application or production database was accessed.

## Automated suite

`python -m pytest -q`: **24 passed**, 0 failed, 0 skipped (22.17 seconds in the recorded full run).

| Area | Verified behavior |
|---|---|
| Authentication | Login/logout, disabled accounts, POST CSRF rejection, account-change session revocation, failed-login throttling, safe return to a QR record after login |
| Pulse permissions | Department and role audience checks, publisher permissions, forced own-department targeting, draft/scheduled access restrictions, global critical visibility |
| Pulse workflows | Creation, all five severity badge classes, acknowledgement and repeated acknowledgement, archive, title/body/category/severity/status/date filters, expiry, targeted notifications |
| Administration | User creation, prevention of self-disable/demotion, configurable departments and categories |
| Inventory | Unique case-insensitive asset IDs, unique serials, specification editing, restricted purchase cost, status-transition validation |
| Equipment workflows | Pending handover, actual employee confirmation, repeat-confirmation rejection, return request, required staff verification, assignment close/reassignment, repair/retirement rules, clearance rejection while equipment remains outstanding |
| Concurrency | Two simultaneous assignments yield exactly one success; the other is rejected. Partial unique index preserves one active assignment. |
| Data isolation | Cross-employee access rejected; department-scoped records/exports; previous employee history withheld from another department; unauthorized assignment/edit/export denied |
| Attachments / labels | Valid PNG upload and protected download, invalid HTML rejection, unauthorized access rejection, QR image generation, correct prefixed QR and notification URLs |
| Excel | All eight exports readable by openpyxl; cost fields withheld from department managers; department filtering; formula-like input escaped |
| Database | Repeatable initialization; original v1 notice/user records survive additive v2 migration; SQLite integrity check |
| Runtime | Occupied-port refusal (including actual runner subprocess); retained socket blocks competing startup; optional IIS path mounting and prefixed links |

## Real HTTP and browser acceptance

`python scripts/browser_check.py`: **passed** against the actual Waitress runner on `127.0.0.1:8000`, with a separate synthetic database.

The browser signed in, published a notice, registered equipment, assigned it, signed in as the employee, confirmed receipt, requested return, signed back in as an administrator, physically verified the return, downloaded an Excel workbook and checked a mobile viewport for page overflow. No browser JavaScript errors were observed. Eight screenshots are in [SCREENSHOTS.md](SCREENSHOTS.md).

The browser process and Waitress process started by the test were stopped afterward. This validates the shared application runtime on Linux; it does not establish IIS or Windows process behavior.

## Additional checks

- Exact `requirements.lock` installation succeeded; `pip check`: no broken requirements.
- Ruff checks passed; Python compilation passed.
- `scripts/backup.py` executed successfully on the stopped synthetic database; restored backup integrity and record counts checked.
- ZIP validated for integrity, required source/docs/scripts and exclusion of runtime databases, credentials, virtualenvs and caches. Regression suite also run from the extracted release package.

## Not executed / limitations

- PowerShell scripts were reviewed, **not executed on Windows**. Windows Server 2022 setup/start/stop, NTFS ACLs, actual IIS HTTPS/rewrite behavior and physical QR scanning require target-platform acceptance.
- No production deployment, load test, external penetration test or organizational malware scan was performed.
- No email or background reminder worker exists; notifications are in-app and scheduled notices are delivered on authenticated visits.
- Shared equipment checkout, SSO, multi-currency accounting and automatic account revocation are outside this v1 release. Clearance records equipment completion only.
- Asset categories are fixed; departments and Pulse categories can be added in the UI. There was no earlier App2 release to preserve.
- The written theme palette was used because the referenced image was not supplied.
