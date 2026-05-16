from agent import CodingAgent
from hello_agents.tracing.viewer import render_trace_html

agent = CodingAgent()

try:
    while True:
        user_prompt = input("请输入你的编程任务: ").strip()
        if user_prompt == "end":
            break

        response = agent.run(user_prompt)
        print(response)

        trace_logger = getattr(agent, "trace_logger", None)
        if trace_logger and trace_logger.enabled:
            html_path = render_trace_html(trace_logger.file_path)
            print(f"Trace HTML已更新: {html_path}")
finally:
    trace_logger = getattr(agent, "trace_logger", None)
    if trace_logger:
        trace_logger.finalize()
