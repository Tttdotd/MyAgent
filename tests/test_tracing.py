import json

from hello_agents.agents.react_agent import ReActAgent
from hello_agents.tools.registry import ToolRegistry
from hello_agents.tracing import RunStartPayload, TraceEvent, TraceLogger, sanitize_payload


class FakeLLM:
    model = "fake-model"

    def __init__(self, responses):
        self.responses = list(responses)

    def invoke(self, messages, **kwargs):
        return self.responses.pop(0)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_trace_logger_writes_jsonl(tmp_path):
    logger = TraceLogger(trace_dir=tmp_path, enabled=True)
    run_id = logger.start_run()
    logger.log_event(
        run_id,
        0,
        TraceEvent.RUN_START,
        RunStartPayload(agent="tester", input_chars=5),
    )
    logger.finalize()

    assert logger.file_path.exists()
    records = read_jsonl(logger.file_path)
    assert records[0]["event"] == TraceEvent.RUN_START
    assert records[0]["session_id"] == logger.session_id
    assert records[0]["run_id"] == 1
    assert isinstance(records[0]["payload"], dict)
    assert records[-1]["event"] == TraceEvent.SESSION_SUMMARY


def test_sanitizer_masks_secret_values():
    payload = {
        "api_key": "sk-abc123456",
        "nested": {"token": "plain-token"},
        "text": "Authorization: Bearer abc123.def456 and key sk-secret123",
        "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
    }

    sanitized = sanitize_payload(payload)

    assert sanitized["api_key"] == "***"
    assert sanitized["nested"]["token"] == "***"
    assert "Bearer ***" in sanitized["text"]
    assert "sk-***" in sanitized["text"]
    assert sanitized["usage"]["total_tokens"] == 7


def test_react_agent_writes_trace_events(tmp_path):
    llm = FakeLLM(
        [
            'Thought: use echo\nAction: echo[{"value": "hello"}]',
            "Thought: enough\nAction: Finish[done]",
        ]
    )
    registry = ToolRegistry()
    registry.register_function(
        "echo",
        "Return the supplied value.",
        lambda value: json.dumps({"echo": value}, ensure_ascii=False),
    )
    logger = TraceLogger(trace_dir=tmp_path, enabled=True)
    agent = ReActAgent(
        name="trace-test",
        llm=llm,
        tool_registry=registry,
        max_steps=3,
        trace_logger=logger,
    )

    result = agent.run("say hello")
    logger.finalize()

    assert result == "done"
    events = [record["event"] for record in read_jsonl(logger.file_path)]
    assert TraceEvent.RUN_START in events
    assert TraceEvent.LLM_RESPONSE in events
    assert TraceEvent.TOOL_CALL in events
    assert TraceEvent.TOOL_RESULT in events
    assert TraceEvent.FINISH in events
