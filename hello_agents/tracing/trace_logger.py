"""JSONL trace logger for framework-level Agent execution events."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .events import (
    LLMRequestPayload,
    RunEndPayload,
    SessionSummaryPayload,
    TraceEvent,
    TraceEventPayload,
    TraceRecord,
    TokenUsagePayload,
)
from .sanitizer import sanitize_payload


def env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def summarize_messages(messages: Any) -> LLMRequestPayload:
    """Return a small, privacy-conscious summary of LLM input."""
    if isinstance(messages, list):
        roles = []
        chars = 0
        for message in messages:
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content", "")
            else:
                role = getattr(message, "role", None)
                content = getattr(message, "content", "")
            if role and role not in roles:
                roles.append(role)
            chars += len(str(content))
        return LLMRequestPayload(
            message_count=len(messages),
            roles=roles,
            chars=chars,
        )

    return LLMRequestPayload(prompt_chars=len(str(messages)))


class TraceLogger:
    """Write one Agent session trace to a JSONL file."""

    def __init__(
        self,
        trace_dir: Optional[str | Path] = None,
        enabled: Optional[bool] = None,
        sanitize: Optional[bool] = None,
    ):
        self.enabled = env_bool("TRACE_ENABLED", True) if enabled is None else enabled
        self.sanitize = env_bool("TRACE_SANITIZE", True) if sanitize is None else sanitize
        self.session_id = self._new_session_id()
        self.trace_dir = Path(trace_dir or os.getenv("TRACE_DIR", "memory/traces"))
        self.file_path = self.trace_dir / f"{self.session_id}.jsonl"

        # 在非并发run场景下, 两个字段在数值上并无区别
        self._run_count = 0
        # 每个Agent内部都会维护一个run_id
        self._current_run_id = 0

        self._step_by_run: dict[int, int] = {}
        self._tools_used = 0
        self._errors = 0
        self._total_usage = TokenUsagePayload(
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )
        self._finalized = False
        self._handle = None

        if not self.enabled:
            return

        try:
            self.trace_dir.mkdir(parents=True, exist_ok=True)
            self._handle = open(self.file_path, "a", encoding="utf-8")
        except Exception:
            self.enabled = False
            self._handle = None

    def start_run(self) -> int:
        """Start a new logical Agent run and return its run id."""
        self._run_count += 1
        self._current_run_id = self._run_count
        self._step_by_run.setdefault(self._current_run_id, 0)
        return self._current_run_id

    def end_run(self, run_id: int, step: int, status: str = "completed") -> None:
        """Record the end of a run."""
        self.log_event(run_id, step, TraceEvent.RUN_END, RunEndPayload(status=status))

    def log_event(
        self,
        run_id: int,
        step: int,
        event: TraceEvent,
        payload: Optional[TraceEventPayload] = None,
    ) -> None:
        """Append a trace event. Failures are intentionally no-op."""
        if not self.enabled or self._handle is None:
            return

        # 获取事件字符串
        event_name = event.value

        payload = payload or {}
        self._record_stats(run_id, step, event_name, payload)
        if self.sanitize:
            payload = sanitize_payload(payload)

        record: TraceRecord = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "run_id": run_id,
            "step": step,
            "event": event_name,
            "payload": payload,
        }

        try:
            self._handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
            # 将缓冲区中的内容直接刷盘
            self._handle.flush()
        except Exception:
            self.enabled = False

    def finalize(self) -> None:
        """Write session statistics and close the trace file."""
        if self._finalized:
            return
        self._finalized = True

        if self.enabled and self._handle is not None:
            summary = SessionSummaryPayload(
                runs=self._run_count,
                steps=sum(self._step_by_run.values()),
                tools_used=self._tools_used,
                errors=self._errors,
                total_usage=TokenUsagePayload(**self._total_usage),
            )
            self.log_event(
                self._current_run_id or self._run_count,
                sum(self._step_by_run.values()),
                TraceEvent.SESSION_SUMMARY,
                summary,
            )

        if self._handle is not None:
            try:
                self._handle.close()
            except Exception:
                pass
            self._handle = None

    def close(self) -> None:
        """Alias for finalize."""
        self.finalize()

    def _record_stats(
        self, run_id: int, step: int, event: str, payload: TraceEventPayload
    ) -> None:
        self._step_by_run[run_id] = max(self._step_by_run.get(run_id, 0), step)
        if event == TraceEvent.TOOL_CALL.value:
            self._tools_used += 1
        elif event == TraceEvent.ERROR.value:
            self._errors += 1

        usage = payload.get("usage")
        if isinstance(usage, dict):
            for key in self._total_usage:
                value = usage.get(key)
                if isinstance(value, int):
                    self._total_usage[key] += value

    @staticmethod
    def _new_session_id() -> str:
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"s-{now}-{uuid.uuid4().hex[:4]}"
