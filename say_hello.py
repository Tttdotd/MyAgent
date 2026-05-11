from hello_agents import HelloAgentsLLM

llm = HelloAgentsLLM();

messages = [
    {
        "role": "user",
        "content": "你好啊, 请介绍一下你自己"
    }
]
response = llm.invoke(messages);

print(response)