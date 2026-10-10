#!/usr/bin/env python3
"""
scripts/check_rcs_test_independence.py — static dependency/independence
scanner for the RCS Playwright suite (tests/rcs/**).

This is a DETECTION tool, not a test runner and not a guarantee: it finds
likely patterns that break "every test is independent, order-irrelevant,
and parallel-safe", using the AST (no execution, no browser). It cannot
see runtime-only coupling (e.g. two tests racing on the same live record
that happens to share a name only at runtime), so a clean report is
necessary but not sufficient -- pair it with the validation matrix
(individual run, randomized order, -n 4/-n 8, repeat) described in the
project's test-independence task.

Checks implemented, per test file:
  1. Module-level MUTABLE state (list/dict/set/None literals assigned at
     module scope) that a test function later rebinds via `global`.
     [HIGH] -- this is the exact "campaign_id = None" anti-pattern.
  2. `global` keyword used inside any test function for ANY name.
     [HIGH]
  3. pytest.mark.dependency / pytest.mark.order / pytest-order usage.
     [HIGH] -- hides a real ordering dependency instead of removing it.
  4. Fixtures scoped "module"/"class"/"session" whose body calls something
     that looks like a CREATE/mutate action (create_*, add_*, .save(,
     .submit(, .launch(, .send() rather than just constructing a page
     object / navigating. [MEDIUM] -- shared mutable fixture risk.
  5. A quoted string literal that looks like a hardcoded resource name
     (Title-case word combo containing Campaign/Agent/Template/Sender,
     OR a short all-caps/mixed alnum token used as a `name=`/`*_name=`
     argument) that is NOT produced by a unique-name helper
     (unique_name/_unique_name/short_unique_tag/short_unique_digits/
     unique_suffix/unique_campaign_name/unique_template_name/...) AND
     appears, verbatim, in more than one test function in the same file.
     [MEDIUM] -- shared/hardcoded data risk across tests.
  6. A test function that calls another test function directly (name
     starts with test_ and is called, not just referenced in a comment).
     [HIGH] -- direct test-to-test chaining.

Usage:
    python scripts/check_rcs_test_independence.py
    python scripts/check_rcs_test_independence.py tests/rcs/campaigns/test_rcs_campaign_flow.py
    python scripts/check_rcs_test_independence.py --json report.json
"""
import argparse
import ast
import json
import os
import re
import sys

UNIQUE_HELPERS = re.compile(
    r"(unique_name|unique_suffix|unique_campaign_name|unique_template_name|"
    r"unique_agent_name|short_unique_tag|short_unique_digits|_unique_name|"
    r"rand_name|_rand_name|worker_scoped_dir)"
)

CREATE_ACTION = re.compile(
    r"\.(create_|add_|save\(|submit\(|launch\(|send\(|click_save|click_submit)",
    re.IGNORECASE,
)

HARDCODED_NAME_LITERAL = re.compile(
    r"^(?:[A-Z][a-zA-Z]*){2,}$|^[A-Za-z]+[0-9]{1,3}$"
)
RESOURCE_WORDS = ("campaign", "agent", "template", "sender", "demo", "test")

DEPENDENCY_MARKERS = ("pytest.mark.dependency", "pytest.mark.order", "pytest_order")


class FileFindings:
    def __init__(self, path):
        self.path = path
        self.total_tests = 0
        self.issues = []  # (severity, message)

    def add(self, severity, message):
        self.issues.append((severity, message))


def _literal_str_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def analyze_file(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as exc:
        ff = FileFindings(path)
        ff.add("HIGH", f"SyntaxError parsing file: {exc}")
        return ff

    ff = FileFindings(path)

    test_funcs = []
    module_level_mutable_names = set()
    fixture_funcs = {}  # name -> (scope, node)

    def _scan_funcdef(node):
        is_fixture = False
        scope = "function"
        for dec in node.decorator_list:
            dec_src = ast.dump(dec)
            if "fixture" in dec_src:
                is_fixture = True
                m = re.search(r"scope['\"]?\s*[=:]\s*['\"](\w+)", ast.unparse(dec))
                if m:
                    scope = m.group(1)
        if is_fixture:
            fixture_funcs[node.name] = (scope, node)
        elif node.name.startswith("test_"):
            test_funcs.append(node)

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    val = node.value
                    is_mutable_literal = isinstance(val, (ast.List, ast.Dict, ast.Set)) or (
                        isinstance(val, ast.Constant) and val.value is None
                    )
                    if is_mutable_literal:
                        module_level_mutable_names.add(target.id)

        if isinstance(node, ast.FunctionDef):
            _scan_funcdef(node)
        elif isinstance(node, ast.ClassDef):
            # pytest test classes (TestXxx) and any fixtures/tests nested
            # inside them -- not just module-level functions.
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    _scan_funcdef(sub)

    ff.total_tests = len(test_funcs)

    # Check 1 & 2: global keyword / module-level mutable state rebound via global
    for fn in test_funcs:
        for n in ast.walk(fn):
            if isinstance(n, ast.Global):
                for name in n.names:
                    if name in module_level_mutable_names:
                        ff.add("HIGH", f"{fn.name}: uses `global {name}` on module-level "
                                        f"mutable state '{name}' defined outside the test")
                    else:
                        ff.add("HIGH", f"{fn.name}: uses `global {name}` inside a test function")

    # Check 3: dependency/order markers
    for fn in test_funcs:
        for dec in fn.decorator_list:
            dec_src = ast.unparse(dec)
            if any(m in dec_src for m in DEPENDENCY_MARKERS):
                ff.add("HIGH", f"{fn.name}: uses an order/dependency marker ({dec_src}) "
                               f"to hide a real test-to-test dependency")

    # Check 4: module/class/session fixtures that look like they CREATE data
    for fname, (scope, node) in fixture_funcs.items():
        if scope in ("module", "class", "session"):
            body_src = ast.unparse(node)
            if CREATE_ACTION.search(body_src):
                ff.add("MEDIUM", f"fixture '{fname}' (scope={scope}) appears to create/mutate "
                                  f"data (matched create/save/submit/launch/send) and is shared "
                                  f"across multiple tests")

    # Check 5: hardcoded resource-name literal reused across >1 test function
    literal_to_tests = {}
    for fn in test_funcs:
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                for kw in n.keywords:
                    s = _literal_str_value(kw.value)
                    if s and kw.arg and re.search(r"name", kw.arg, re.IGNORECASE):
                        if any(w in s.lower() for w in RESOURCE_WORDS) or HARDCODED_NAME_LITERAL.match(s):
                            literal_to_tests.setdefault(s, set()).add(fn.name)
                for arg in n.args:
                    s = _literal_str_value(arg)
                    if s and any(w in s.lower() for w in RESOURCE_WORDS) and len(s) < 40:
                        literal_to_tests.setdefault(s, set()).add(fn.name)
    for literal, tests in literal_to_tests.items():
        if len(tests) > 1:
            ff.add("MEDIUM", f"hardcoded literal {literal!r} used as a resource name in "
                              f"{len(tests)} different tests: {sorted(tests)}")

    # Check 6: a test function calling another test function directly
    test_names = {fn.name for fn in test_funcs}
    for fn in test_funcs:
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                if n.func.id in test_names and n.func.id != fn.name:
                    ff.add("HIGH", f"{fn.name}: directly calls another test function "
                                   f"'{n.func.id}()' instead of each being independent")

    return ff


def find_rcs_test_files(root="tests/rcs"):
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.startswith("test_") and fn.endswith(".py"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="Specific test files to check (default: all of tests/rcs)")
    parser.add_argument("--json", help="Also write the report as JSON to this path")
    args = parser.parse_args()

    paths = args.paths or find_rcs_test_files()

    all_findings = [analyze_file(p) for p in paths]

    total_tests = sum(ff.total_tests for ff in all_findings)
    high = sum(1 for ff in all_findings for sev, _ in ff.issues if sev == "HIGH")
    medium = sum(1 for ff in all_findings for sev, _ in ff.issues if sev == "MEDIUM")
    files_with_issues = sum(1 for ff in all_findings if ff.issues)
    independent_files = len(all_findings) - files_with_issues

    print("RCS Test Independence Report")
    print("=" * 60)
    print(f"Files analyzed:        {len(all_findings)}")
    print(f"Total tests analyzed:  {total_tests}")
    print()
    print(f"Files with no detected issues: {independent_files}")
    print(f"Files with potential issues:   {files_with_issues}")
    print(f"  [HIGH] findings:   {high}")
    print(f"  [MEDIUM] findings: {medium}")
    print()

    if files_with_issues:
        print("Potential issues:")
        print()
        for ff in all_findings:
            if not ff.issues:
                continue
            for sev, msg in sorted(ff.issues, key=lambda x: 0 if x[0] == "HIGH" else 1):
                print(f"[{sev}] {ff.path}")
                print(f"       {msg}")
        print()
    else:
        print("No HIGH/MEDIUM findings in any analyzed file.")

    if args.json:
        payload = {
            "files_analyzed": len(all_findings),
            "total_tests": total_tests,
            "independent_files": independent_files,
            "files_with_issues": files_with_issues,
            "high": high,
            "medium": medium,
            "findings": [
                {"file": ff.path, "total_tests": ff.total_tests,
                 "issues": [{"severity": s, "message": m} for s, m in ff.issues]}
                for ff in all_findings
            ],
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"JSON report written to {args.json}")

    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
