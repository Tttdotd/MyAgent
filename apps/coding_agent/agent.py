from hello_agents import SimpleAgent

DEFAULT_SYSTEM_PROMPT = """
你是一名编程专家, 精通各种编程语言. 请你帮助用户完成具体的编程任务.
"""

class CodingAgent(SimpleAgent):
    def __init__(self, name, llm, system_prompt = DEFAULT_SYSTEM_PROMPT, config = None):
        super().__init__(name, llm, system_prompt, config)