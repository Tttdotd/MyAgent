"""Trace event protocol definitions."""

from __future__ import annotations

from enum import Enum
from typing import Any, TypeAlias, TypedDict


class TraceEvent(str, Enum):
    """Canonical trace event names."""

    RUN_START = "run_start"
    USER_INPUT = "user_input"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    PARSED_ACTION = "parsed_action"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    FINISH = "finish"
    RUN_END = "run_end"
    SESSION_SUMMARY = "session_summary"


class RunStartPayload(TypedDict):
    agent: str
    input_chars: int


class UserInputPayload(TypedDict):
    input: str


class LLMRequestPayload(TypedDict, total=False):
    message_count: int
    roles: list[str]
    chars: int
    prompt_chars: int


class TokenUsagePayload(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponsePayload(TypedDict):
    content: str
    usage: TokenUsagePayload | None


class ParsedActionPayload(TypedDict):
    thought: str | None
    action: str | None
    action_input: Any


class ToolCallPayload(TypedDict):
    tool: str
    arguments: dict[str, Any]


class ToolResultPayload(TypedDict):
    tool: str
    result: str


class ErrorPayload(TypedDict, total=False):
    stage: str
    message: str
    error_type: str
    traceback: str
    original_payload: Any


class FinishPayload(TypedDict):
    answer: str


class RunEndPayload(TypedDict):
    status: str


class SessionSummaryPayload(TypedDict):
    runs: int
    steps: int
    tools_used: int
    errors: int
    total_usage: TokenUsagePayload


TraceEventPayload: TypeAlias = (
    RunStartPayload
    | UserInputPayload
    | LLMRequestPayload
    | LLMResponsePayload
    | ParsedActionPayload
    | ToolCallPayload
    | ToolResultPayload
    | ErrorPayload
    | FinishPayload
    | RunEndPayload
    | SessionSummaryPayload
)


class TraceRecord(TypedDict):
    ts: str
    session_id: str
    run_id: int
    step: int
    event: str
    payload: TraceEventPayload
