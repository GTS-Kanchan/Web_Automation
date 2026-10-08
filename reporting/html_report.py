"""
reporting/html_report.py -- renders reports/current/test_report.html's
companion ADVANCED dashboard (reports/runs/<run-id>/dashboard.html and a
copy at reports/current/dashboard.html) as ONE self-contained HTML file:
no external JS/CSS, no server, no database (requirement #18: "No
server/database should be required to view the generated report").

This is a presentation layer only. Every number here comes from the
summary/failures dicts the caller (conftest.py's pytest_sessionfinish,
via reporting/summary.py + reporting/trend.py) already computed --
html_report.py performs no aggregation of its own, so summary.json and
failures.json stay the actual source of truth (requirement at the very
end of the spec: "make summary.json and failures.json the source of
truth, and make HTML only a presentation layer").

This does NOT replace the existing pytest-html report
(reports/test_report.html) -- that keeps being generated exactly as
before by pytest-html itself (pytest.ini's --html flag); this is an
ADDITIONAL, purpose-built executive/QA/developer dashboard alongside it.
"""
import html
import json


def _esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def _fmt_duration(seconds) -> str:
    try:
        seconds = float(seconds)
    except (TypeError, ValueError):
        return "0s"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


_CSS = """
:root{
  --bg:#f8fafc; --panel:#ffffff; --border:#e2e8f0; --text:#0f172a; --muted:#64748b;
  --pass:#16a34a; --fail:#dc2626; --skip:#d97706; --accent:#2563eb;
  --pass-bg:#f0fdf4; --fail-bg:#fef2f2; --skip-bg:#fffbeb; --accent-bg:#eff6ff;
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);font-size:14px}
.wrap{max-width:1200px;margin:0 auto;padding:24px}
h1,h2,h3{margin:0 0 12px}
h2{font-size:16px;margin-top:28px;padding-bottom:6px;border-bottom:2px solid var(--border)}
.dashboard{background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;border-radius:12px;padding:24px 28px;margin-bottom:20px}
.dashboard h1{font-size:20px;letter-spacing:.04em}
.dashboard .sub{color:#94a3b8;margin-bottom:16px;font-size:13px}
.statgrid{display:flex;flex-wrap:wrap;gap:16px}
.stat{min-width:120px}
.stat .label{color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
.stat .value{font-size:26px;font-weight:700;margin-top:2px}
.status-badge{display:inline-block;padding:3px 10px;border-radius:20px;font-weight:700;font-size:12px}
.status-passed{background:var(--pass-bg);color:var(--pass)}
.status-failed{background:var(--fail-bg);color:var(--fail)}
.status-skipped{background:var(--skip-bg);color:var(--skip)}
table{width:100%;border-collapse:collapse;background:var(--panel);border-radius:8px;overflow:hidden;box-shadow:0 1px 2px rgba(0,0,0,.04)}
th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--border);font-size:13px}
th{background:#f1f5f9;font-size:11px;text-transform:uppercase;color:var(--muted);letter-spacing:.04em}
tr:last-child td{border-bottom:none}
.pill{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:var(--accent-bg);color:var(--accent)}
.badge-new{background:#fef2f2;color:#dc2626}
.badge-recurring{background:#fffbeb;color:#d97706}
.badge-recovered{background:#f0fdf4;color:#16a34a}
.badge-flaky{background:#f5f3ff;color:#7c3aed}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.controls select,.controls input{padding:6px 10px;border:1px solid var(--border);border-radius:6px;font-size:13px;background:#fff}
.controls input[type=search]{flex:1;min-width:220px}
.failure-card{background:var(--panel);border:1px solid var(--border);border-left:4px solid var(--fail);border-radius:8px;margin-bottom:10px;overflow:hidden}
.failure-head{padding:10px 14px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:10px}
.failure-head:hover{background:#f8fafc}
.failure-title{font-weight:600}
.failure-meta{color:var(--muted);font-size:12px}
.failure-body{display:none;padding:0 14px 14px;border-top:1px solid var(--border)}
.failure-body.open{display:block}
.failure-body pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:6px;overflow:auto;font-size:12px;white-space:pre-wrap;word-break:break-word}
.kv{display:grid;grid-template-columns:140px 1fr;gap:4px 10px;margin:10px 0;font-size:13px}
.kv b{color:var(--muted);font-weight:600}
.empty{color:var(--muted);font-style:italic;padding:10px 0}
img.shot{max-width:100%;border:1px solid var(--border);border-radius:6px;margin-top:8px}
.hidden{display:none !important}
.healthy{color:var(--pass);font-weight:700}
.unhealthy{color:var(--fail);font-weight:700}
.section-note{color:var(--muted);font-size:12px;margin:-6px 0 10px}
"""


def _dashboard_header(summary: dict) -> str:
    status = summary.get("status", "UNKNOWN")
    status_class = "status-passed" if status == "PASSED" else "status-failed"
    return f"""
<div class="dashboard">
  <h1>CPaaS AUTOMATION REPORT</h1>
  <div class="sub">{_esc(summary.get('channel','').upper())} {_esc(summary.get('test_type','').upper())}
    &middot; Environment: {_esc(summary.get('environment','?'))}
    &middot; Run: {_esc(summary.get('run_id','?'))}</div>
  <div class="statgrid">
    <div class="stat"><div class="label">Status</div><div class="value"><span class="status-badge {status_class}">{_esc(status)}</span></div></div>
    <div class="stat"><div class="label">Pass Rate</div><div class="value">{summary.get('pass_rate',0)}%</div></div>
    <div class="stat"><div class="label">Total</div><div class="value">{summary.get('total',0)}</div></div>
    <div class="stat"><div class="label">Passed</div><div class="value">{summary.get('passed',0)}</div></div>
    <div class="stat"><div class="label">Failed</div><div class="value">{summary.get('failed',0)}</div></div>
    <div class="stat"><div class="label">Skipped</div><div class="value">{summary.get('skipped',0)}</div></div>
    <div class="stat"><div class="label">Duration</div><div class="value">{_fmt_duration(summary.get('duration_seconds',0))}</div></div>
  </div>
</div>
"""


def _group_table(title: str, groups: dict) -> str:
    rows = ""
    for name in sorted(groups):
        g = groups[name]
        rows += (
            f"<tr><td>{_esc(name)}</td><td>{g['total']}</td><td>{g['passed']}</td>"
            f"<td>{g['failed']}</td><td>{g['skipped']}</td><td>{g['pass_rate']}%</td></tr>"
        )
    if not rows:
        return f"<h2>{_esc(title)}</h2><div class='empty'>No data.</div>"
    return f"""
<h2>{_esc(title)}</h2>
<table><thead><tr><th>Name</th><th>Total</th><th>Passed</th><th>Failed</th><th>Skipped</th><th>Pass Rate</th></tr></thead>
<tbody>{rows}</tbody></table>
"""


def _category_table(failures: list) -> str:
    counts = {}
    for f in failures:
        cat = f.get("category") or "UNKNOWN"
        counts[cat] = counts.get(cat, 0) + 1
    if not counts:
        return "<h2>Failure Summary</h2><div class='empty'>No failures.</div>"
    rows = "".join(
        f"<tr><td>{_esc(cat)}</td><td>{n}</td></tr>"
        for cat, n in sorted(counts.items(), key=lambda kv: -kv[1])
    )
    return f"<h2>Failure Summary</h2><table><thead><tr><th>Category</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table>"


def _trend_section(trend: dict) -> str:
    if not trend.get("history_available"):
        return "<h2>New / Recurring / Recovered</h2><div class='empty'>History: Not available (no comparable previous run yet).</div>"

    def _list(label, items, cls, icon):
        if not items:
            return f"<div class='empty'>No {label.lower()}.</div>"
        lis = "".join(f"<div>{icon} <span class='pill {cls}'>{_esc(t)}</span></div>" for t in items)
        return lis

    return f"""
<h2>New / Recurring / Recovered</h2>
<div class="kv" style="grid-template-columns:1fr 1fr 1fr">
  <div><b>New failures ({len(trend['new'])})</b>{_list('new', trend['new'], 'badge-new', '&#10060;')}</div>
  <div><b>Recurring failures ({len(trend['recurring'])})</b>{_list('recurring', trend['recurring'], 'badge-recurring', '&#9888;')}</div>
  <div><b>Recovered ({len(trend['recovered'])})</b>{_list('recovered', trend['recovered'], 'badge-recovered', '&#10003;')}</div>
</div>
"""


def _flaky_section(flaky: dict) -> str:
    if not flaky:
        return "<h2>Flaky Tests</h2><div class='empty'>None detected.</div>"
    rows = "".join(
        f"<tr><td>{_esc(t)}</td><td>{d['executions']}</td><td>{d['passed']}</td>"
        f"<td>{d['failed']}</td><td>{d['flaky_rate']}%</td></tr>"
        for t, d in sorted(flaky.items(), key=lambda kv: -kv[1]['flaky_rate'])
    )
    return f"""
<h2>Flaky Tests <span class="pill badge-flaky">potentially flaky</span></h2>
<div class="section-note">At least 3 executions with both a pass and a fail observed.</div>
<table><thead><tr><th>Test</th><th>Executions</th><th>Passed</th><th>Failed</th><th>Flaky Rate</th></tr></thead>
<tbody>{rows}</tbody></table>
"""


def _slowest_section(slowest: list, stats: dict) -> str:
    rows = "".join(
        f"<tr><td>{_esc(r['test'])}</td><td>{r['duration']}s</td><td><span class='status-badge status-{r['status']}'>{_esc(r['status'])}</span></td></tr>"
        for r in slowest
    )
    rows = rows or "<tr><td colspan='3' class='empty'>No timed tests.</td></tr>"
    return f"""
<h2>Slowest Tests</h2>
<div class="kv" style="grid-template-columns:repeat(4,1fr);margin-bottom:10px">
  <div><b>Total</b><br>{_fmt_duration(stats.get('total',0))}</div>
  <div><b>Average</b><br>{stats.get('average',0)}s</div>
  <div><b>Median</b><br>{stats.get('median',0)}s</div>
  <div><b>P95</b><br>{stats.get('p95',0)}s</div>
</div>
<table><thead><tr><th>Test</th><th>Duration</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>
"""


def _platform_health_section(health: dict) -> str:
    if health.get("healthy", True):
        return "<h2>Platform Health</h2><div class='healthy'>&#9989; HEALTHY -- no platform errors detected.</div>"
    rows = "".join(
        f"<tr><td>{label.replace('_',' ').title()}</td><td>{health.get(label,0)}</td></tr>"
        for label in ("http_500", "whoops", "livewire", "network", "browser_crash", "other")
        if health.get(label, 0)
    )
    return f"""
<h2>Platform Health</h2>
<div class="unhealthy">&#9888; {health.get('total',0)} platform error(s) detected</div>
<table><thead><tr><th>Type</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table>
"""


def _dlr_section(dlr: dict) -> str:
    if not dlr or dlr.get("total", 0) == 0:
        return ""
    return f"""
<h2>DLR Summary</h2>
<div class="kv" style="grid-template-columns:repeat(3,1fr)">
  <div><b>Total DLR tests</b><br>{dlr['total']}</div>
  <div><b>DLR passed</b><br>{dlr['passed']}</div>
  <div><b>DLR failed</b><br>{dlr['failed']}</div>
  <div><b>Average wait</b><br>{dlr['average_wait']}s</div>
  <div><b>Max wait</b><br>{dlr['max_wait']}s</div>
  <div><b>Timeout failures</b><br>{dlr['timeout_failures']}</div>
</div>
"""


def _failures_section(failures: list, trend: dict) -> str:
    failed = [f for f in failures if f["status"] == "failed"]
    if not failed:
        return "<h2>Failed Tests</h2><div class='empty'>No failures &#127881;</div>"
    new_set = set(trend.get("new", []))
    recurring_set = set(trend.get("recurring", []))
    cards = []
    for i, f in enumerate(failed):
        tag = ""
        if f["test"] in new_set:
            tag = "<span class='pill badge-new'>NEW</span>"
        elif f["test"] in recurring_set:
            tag = "<span class='pill badge-recurring'>RECURRING</span>"
        shot = f"<img class='shot' src='{_esc(f['screenshot'])}'>" if f.get("screenshot") else ""
        log_link = f"<div><a href='{_esc(f['log'])}' target='_blank'>View worker log</a></div>" if f.get("log") else ""
        cards.append(f"""
<div class="failure-card" data-channel="{_esc(f.get('channel'))}" data-feature="{_esc(f.get('feature'))}"
     data-category="{_esc(f.get('category'))}" data-worker="{_esc(f.get('worker'))}"
     data-marker="{_esc(f.get('marker'))}" data-status="{_esc(f.get('status'))}"
     data-trend="{'new' if f['test'] in new_set else ('recurring' if f['test'] in recurring_set else 'other')}"
     data-search="{_esc((f.get('test') or '') + ' ' + (f.get('error') or '') + ' ' + (f.get('category') or '') + ' ' + (f.get('feature') or ''))}">
  <div class="failure-head" onclick="this.nextElementSibling.classList.toggle('open')">
    <div><div class="failure-title">{_esc(f['test'])} {tag}</div>
    <div class="failure-meta">{_esc(f.get('feature'))} &middot; {f.get('duration')}s &middot; <span class="pill">{_esc(f.get('category') or 'UNKNOWN')}</span></div></div>
    <div class="failure-meta">&#9660;</div>
  </div>
  <div class="failure-body">
    <div class="kv">
      <b>Channel</b><div>{_esc(f.get('channel'))}</div>
      <b>Feature</b><div>{_esc(f.get('feature'))}</div>
      <b>Worker</b><div>{_esc(f.get('worker'))}</div>
      <b>Marker</b><div>{_esc(f.get('marker'))}</div>
      <b>Duration</b><div>{f.get('duration')}s</div>
      <b>Category</b><div>{_esc(f.get('category'))}</div>
      <b>Fingerprint</b><div>{_esc(f.get('fingerprint'))}</div>
    </div>
    <b>Error</b>
    <pre>{_esc(f.get('error_raw') or f.get('error') or '(no message)')}</pre>
    <details><summary>Stack trace</summary><pre>{_esc(f.get('stack_trace') or '(not captured)')}</pre></details>
    {shot}
    {log_link}
  </div>
</div>
""")
    return "<h2>Failed Tests</h2>" + "".join(cards)


def _filters_bar(failures: list) -> str:
    channels = sorted({f.get("channel") for f in failures if f.get("channel")})
    categories = sorted({f.get("category") for f in failures if f.get("category")})
    workers = sorted({f.get("worker") for f in failures if f.get("worker")})

    def _opts(values):
        return "".join(f"<option value='{_esc(v)}'>{_esc(v)}</option>" for v in values)

    return f"""
<div class="controls">
  <input type="search" id="search-box" placeholder="Search test name, error, feature, category...">
  <select id="filter-channel"><option value="">All channels</option>{_opts(channels)}</select>
  <select id="filter-category"><option value="">All categories</option>{_opts(categories)}</select>
  <select id="filter-worker"><option value="">All workers</option>{_opts(workers)}</select>
  <select id="filter-trend"><option value="">New/Recurring/All</option><option value="new">New</option><option value="recurring">Recurring</option></select>
</div>
"""


_FILTER_JS = """
<script>
(function(){
  var search = document.getElementById('search-box');
  var fChannel = document.getElementById('filter-channel');
  var fCategory = document.getElementById('filter-category');
  var fWorker = document.getElementById('filter-worker');
  var fTrend = document.getElementById('filter-trend');
  if(!search) return;
  function apply(){
    var q = (search.value || '').toLowerCase();
    var ch = fChannel.value, cat = fCategory.value, wk = fWorker.value, tr = fTrend.value;
    document.querySelectorAll('.failure-card').forEach(function(card){
      var ok = true;
      if(q && !(card.getAttribute('data-search')||'').toLowerCase().includes(q)) ok = false;
      if(ch && card.getAttribute('data-channel') !== ch) ok = false;
      if(cat && card.getAttribute('data-category') !== cat) ok = false;
      if(wk && card.getAttribute('data-worker') !== wk) ok = false;
      if(tr && card.getAttribute('data-trend') !== tr) ok = false;
      card.classList.toggle('hidden', !ok);
    });
  }
  [search, fChannel, fCategory, fWorker, fTrend].forEach(function(el){
    el.addEventListener('input', apply);
    el.addEventListener('change', apply);
  });
})();
</script>
"""


def render_html(context: dict) -> str:
    """context keys: summary, channel_summary, feature_summary, failures
    (ALL records, not just failed -- _failures_section filters), trend,
    flaky, slowest, duration_stats, platform_health, dlr_summary."""
    summary = context["summary"]
    failures_all = context.get("failures", [])

    body = _dashboard_header(summary)
    body += _group_table("Channel Summary", context.get("channel_summary", {}))
    body += _group_table("Feature Summary", context.get("feature_summary", {}))
    body += _category_table([f for f in failures_all if f["status"] == "failed"])
    body += _filters_bar(failures_all)
    body += _failures_section(failures_all, context.get("trend", {}))
    body += _trend_section(context.get("trend", {}))
    body += _flaky_section(context.get("flaky", {}))
    body += _slowest_section(context.get("slowest", []), context.get("duration_stats", {}))
    body += _platform_health_section(context.get("platform_health", {}))
    body += _dlr_section(context.get("dlr_summary", {}))

    title = f"CPaaS Automation Report - {_esc(summary.get('channel','').upper())} {_esc(summary.get('environment','').upper())}"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
{_FILTER_JS}
</body>
</html>
"""
