
"""Command-line LangChain agent."""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

from tools.database_tools import (
    institutions_db_tool,
    hospitals_db_tool,
    restaurants_db_tool,
)
from tools.web_search_tool import web_search_tool

load_dotenv()

SYSTEM_PROMPT = """
You are the Bangladesh Multi-Tool AI Agent.

Routing:
- Questions about institutions -> institutions_db_tool
- Questions about hospitals -> hospitals_db_tool
- Questions about restaurants -> restaurants_db_tool
- General knowledge and current information -> web_search_tool

Use database tools for dataset-specific records and counts.
Never invent data. If no records match or a field is missing,
say so. Describe counts as matching records in the supplied
dataset, not official real-world totals.
For web answers, include source URLs returned by search.
Answer clearly.
"""


def build_agent():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY missing. Add your Groq API key to .env."
        )

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        api_key=api_key,
        temperature=0,
    )

    tools = [
        institutions_db_tool,
        hospitals_db_tool,
        restaurants_db_tool,
        web_search_tool,
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=6,
        handle_parsing_errors=True,
    )


def main():
    print(
        "=" * 58
        + "\nBANGLADESH MULTI-TOOL AI AGENT\n"
        + "Type 'exit' to quit.\n"
        + "=" * 58
    )

    try:
        executor = build_agent()
    except Exception as exc:
        print(f"Setup error: {exc}")
        return

    history = []

    while True:
        question = input("\nYou: ").strip()

        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not question:
            continue

        try:
            result = executor.invoke({
                "input": question,
                "chat_history": history,
            })

            answer = result.get("output", "No answer returned.")
            print(f"\nAgent: {answer}")

            history.extend([
                ("human", question),
                ("assistant", answer),
            ])
            history = history[-10:]

        except Exception as exc:
            print(f"Agent error: {exc}")


if __name__ == "__main__":
    main()
