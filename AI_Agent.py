# pip install -qU langchain langchain-ollama
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """get weather for a given city"""
    return f"It's alsways sunny in {city}!"

agent = create_agent(
    model="ollama:qwen3:1.7b",
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages":[{"role":"user","content":"What's the weather in San Francisco?"}]}
)

print(result["messages"][-1].content_blocks)