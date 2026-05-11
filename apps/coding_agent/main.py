from agent import CodingAgent
from hello_agents import HelloAgentsLLM


llm = HelloAgentsLLM()

agent = CodingAgent(
    name="coder",
    llm=llm,
)

user_prompt = "你好, 介绍一下你自己."
response = agent.run(user_prompt)

print(response)