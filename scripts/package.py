"""Package source/docs only. Never include private runtime data or credentials."""

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
out = root / "dist" / "Cirrus-Pulse-Version-1.0.zip"
out.parent.mkdir(exist_ok=True)
# Deliberate allowlist so data, attachments and secrets never enter the release.
files = [
    root / name
    for name in (
        "README.md",
        "CHANGELOG.md",
        "requirements.txt",
        "requirements.lock",
        "requirements-dev.txt",
        "run.py",
        "wsgi.py",
        "pyproject.toml",
        ".gitignore",
    )
]
for directory in ("cirrus", "scripts", "tests", "docs"):
    files.extend(
        p
        for p in (root / directory).rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    )
with ZipFile(out, "w", ZIP_DEFLATED) as z:
    for p in sorted(files):
        z.write(p, Path("CirrusPulse") / p.relative_to(root))
digest = hashlib.sha256(out.read_bytes()).hexdigest()
out.with_suffix(".zip.sha256").write_text(digest + "  " + out.name + "\n")
print(f"{out.name}: {out.stat().st_size} bytes; SHA256 {digest}")
