"""
reporting/artifacts.py -- resolves reports/current/, reports/runs/<id>/,
and reports/history/ paths, and copies finished files/directories into
them. Never touches reports/.auth/ (auth state must never become a
report artifact -- requirement #2/#26), and never copies screenshots/
logs into reports/history/ (requirement #22 -- those stay with the run).
"""
import os
import shutil


def run_dir(reports_root: str, run_id: str) -> str:
    path = os.path.join(reports_root, "runs", run_id)
    os.makedirs(path, exist_ok=True)
    return path


def current_dir(reports_root: str) -> str:
    """reports/current/ -- always overwritten with the LATEST run's
    files, for anything that wants "the current result" without knowing
    a run id (requirement #33: backward compatibility)."""
    path = os.path.join(reports_root, "current")
    os.makedirs(path, exist_ok=True)
    return path


def publish_files(reports_root: str, run_id: str, files: dict) -> None:
    """files: {published_name: source_absolute_path}. Copies into BOTH
    reports/runs/<run_id>/ and reports/current/. A missing/unreadable
    source is skipped, never raised -- report publishing must never be
    what fails a pipeline (requirement #31)."""
    rdir = run_dir(reports_root, run_id)
    cdir = current_dir(reports_root)
    for name, src in files.items():
        if not src or not os.path.isfile(src):
            continue
        for dest_dir in (rdir, cdir):
            try:
                shutil.copy2(src, os.path.join(dest_dir, name))
            except OSError:
                pass


def publish_referenced_files(reports_root: str, run_id: str, relative_paths) -> None:
    """Copies ONLY the specific screenshot/log files THIS run's records
    actually reference (each record's "screenshot"/"log" field is already
    relative to reports_root -- see conftest.py's pytest_runtest_logreport)
    into reports/runs/<run_id>/<same relative path>, preserving the
    screenshots/<worker>/... or logs/<worker>.jsonl layout.

    Deliberately NOT a whole-directory copy: reports/screenshots/ and
    reports/logs/ are long-lived, worker-scoped directories that
    accumulate across EVERY run ever executed against this reports/ root
    (nothing in this project rotates them) -- copying the whole tree on
    every single run would copy more and more unrelated history into
    each new reports/runs/<run_id>/ every time, growing without bound.
    Copying only what this run's own records point to is correct
    regardless of how long-lived or short-lived reports/screenshots/
    happens to be, and keeps each run folder bounded by what THAT run
    actually produced."""
    rdir = run_dir(reports_root, run_id)
    seen = set()
    for rel in relative_paths:
        if not rel or rel in seen:
            continue
        seen.add(rel)
        src = os.path.join(reports_root, rel)
        if not os.path.isfile(src):
            continue
        dest = os.path.join(rdir, rel)
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
        except OSError:
            pass
