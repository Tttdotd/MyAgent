from agent import CodingAgent

agent = CodingAgent()

while True:
    user_prompt = input("请输入你的编程任务: ").strip()
    if not user_prompt:
        raise SystemExit("任务不能为空")
    response = agent.run(user_prompt)
    print(response)
