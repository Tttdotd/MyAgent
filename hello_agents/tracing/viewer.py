"""Static HTML viewer for JSONL trace files."""

from __future__ import annotations

import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_trace(path: str | Path) -> list[dict[str, Any]]:
    """Load trace records from a JSONL file."""
    trace_path = Path(path)
    records: list[dict[str, Any]] = []

    with trace_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return records


def render_trace_html(
    jsonl_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """Render a JSONL trace as a standalone HTML file."""
    trace_path = Path(jsonl_path)
    target_path = Path(output_path) if output_path else trace_path.with_suffix(".html")
    records = load_trace(trace_path)

    body = _render_runs(records)
    page = _render_page(trace_path, body)
    target_path.write_text(page, encoding="utf-8")
    return target_path


def _group_by_run_and_step(
    records: list[dict[str, Any]],
) -> dict[int, dict[int, list[dict[str, Any]]]]:
    runs: dict[int, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))

    for record in records:
        run_id = _as_int(record.get("run_id"), default=0)
        step = _as_int(record.get("step"), default=0)
        runs[run_id][step].append(record)

    return runs


def _render_page(trace_path: Path, body: str) -> str:
    title = f"Trace Viewer - {trace_path.name}"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
:root {{
  color-scheme: light;
  --bg: #f5f7fb;
  --panel: #ffffff;
  --border: #d9e0ea;
  --muted: #667085;
  --text: #172033;
  --code-bg: #111827;
  --code-text: #e5e7eb;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
}}
header {{
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 14px 22px;
  background: #111827;
  color: white;
  border-bottom: 1px solid #1f2937;
}}
header h1 {{
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}}
header p {{
  margin: 4px 0 0;
  color: #cbd5e1;
  font-size: 13px;
}}
main {{
  max-width: 1120px;
  margin: 22px auto 40px;
  padding: 0 16px;
}}
.run {{
  margin-bottom: 22px;
}}
.run-title {{
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 800;
}}
.step {{
  margin-bottom: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--panel);
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}}
.step summary {{
  cursor: pointer;
  list-style: none;
  padding: 12px 14px;
  background: #eef2f7;
  border-bottom: 1px solid var(--border);
}}
.step summary::-webkit-details-marker {{
  display: none;
}}
.step-header {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}}
.step-title {{
  color: var(--text);
  font-size: 14px;
  font-weight: 800;
}}
.badge {{
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 2px 8px;
  border-radius: 999px;
  background: white;
  border: 1px solid var(--border);
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
}}
.badge.error-badge {{
  border-color: #fecaca;
  background: #fef2f2;
  color: #b91c1c;
}}
.badge.finish-badge {{
  border-color: #fed7aa;
  background: #fff7ed;
  color: #c2410c;
}}
.step-body {{
  padding: 12px;
}}
.card {{
  margin-bottom: 10px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-left: 5px solid #98a2b3;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
}}
.step-body .card:last-child {{
  margin-bottom: 0;
}}
.llm_response {{ border-left-color: #6366f1; }}
.llm_request {{ border-left-color: #8b5cf6; }}
.tool_call {{ border-left-color: #0284c7; }}
.tool_result {{ border-left-color: #16a34a; }}
.parsed_action {{ border-left-color: #f97316; }}
.error {{ border-left-color: #dc2626; }}
.finish {{ border-left-color: #d97706; }}
.run_start, .run_end, .session_summary {{ border-left-color: #475467; }}
.meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
  font-size: 13px;
}}
.event {{
  color: var(--text);
  font-weight: 700;
}}
.payload {{
  padding: 12px 14px;
}}
pre {{
  margin: 0;
  padding: 12px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  border-radius: 6px;
  background: var(--code-bg);
  color: var(--code-text);
  font: 13px/1.5 Consolas, "SFMono-Regular", Menlo, monospace;
}}
</style>
</head>
<body>
<header>
  <h1>Trace Viewer</h1>
  <p>{html.escape(str(trace_path))}</p>
</header>
<main>
{body}
</main>
</body>
</html>
"""


def _render_runs(records: list[dict[str, Any]]) -> str:
    if not records:
        return '<p class="empty">没有 trace 记录。</p>'

    runs = _group_by_run_and_step(records)
    parts: list[str] = []

    for run_id in sorted(runs):
        steps = runs[run_id]
        step_blocks = "\n".join(
            _render_step(step, steps[step]) for step in sorted(steps)
        )
        parts.append(
            f"""<section class="run">
  <h2 class="run-title">Run {html.escape(str(run_id))}</h2>
  {step_blocks}
</section>"""
        )

    return "\n".join(parts)


def _render_step(step: int, records: list[dict[str, Any]]) -> str:
    event_names = [str(record.get("event", "unknown")) for record in records]
    badges = [
        f'<span class="badge">{len(records)} events</span>',
        f'<span class="badge">{html.escape(", ".join(event_names))}</span>',
    ]
    if "error" in event_names:
        badges.append('<span class="badge error-badge">error</span>')
    if "finish" in event_names:
        badges.append('<span class="badge finish-badge">finish</span>')

    cards = "\n".join(_render_record(record) for record in records)
    should_open = step in {0, 1} or "error" in event_names or "finish" in event_names
    open_attr = " open" if should_open else ""

    return f"""<details class="step"{open_attr}>
  <summary>
    <div class="step-header">
      <span class="step-title">Step {html.escape(str(step))}</span>
      {''.join(badges)}
    </div>
  </summary>
  <div class="step-body">
    {cards}
  </div>
</details>"""


def _render_record(record: dict[str, Any]) -> str:
    event = str(record.get("event", "unknown"))
    payload = record.get("payload", {})
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)

    return f"""<section class="card {html.escape(event)}">
  <div class="meta">
    <span class="event">{html.escape(event)}</span>
    <span>run: {html.escape(str(record.get("run_id", "")))}</span>
    <span>step: {html.escape(str(record.get("step", "")))}</span>
    <span>{html.escape(str(record.get("ts", "")))}</span>
  </div>
  <div class="payload">
    <pre>{html.escape(payload_text)}</pre>
  </div>
</section>"""


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    """CLI entrypoint for rendering a trace file."""
    import argparse

    parser = argparse.ArgumentParser(description="Render a JSONL trace file as HTML.")
    parser.add_argument("jsonl_path", help="Path to the trace .jsonl file.")
    parser.add_argument("-o", "--output", help="Optional output .html path.")
    args = parser.parse_args()

    output_path = render_trace_html(args.jsonl_path, args.output)
    print(f"Trace HTML generated: {output_path}")


if __name__ == "__main__":
    main()
