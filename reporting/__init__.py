"""
reporting/ -- advanced test-reporting layer for the CPaaS Playwright suite.

Kept entirely separate from conftest.py's pytest-hook wiring (collector.py
is the only module conftest.py calls directly during a run) so this
package stays testable without a browser and without pytest itself.

summary.json and failures.json (see artifacts.py / summary.py) are the
source of truth; test_report.html (html_report.py) is a presentation
layer built FROM them, not the other way around -- a future Slack/Jira/
dashboard integration only ever needs to read the JSON.
"""
