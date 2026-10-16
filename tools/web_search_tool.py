"""Tavily web search tool for general knowledge."""
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

_client = None

def get_client():
    global _client
    if _client is None:
        _client = TavilySearchResults(max_results=5)
    return _client

@tool
def web_search_tool(question: str) -> str:
    """Search the web for general knowledge, Bangladesh policies, definitions, culture, and current information. Do not use for supplied-dataset-only questions."""
    try:
        results = get_client().invoke({"query": question})
        if not results:
            return "No useful web search results found."
        output = []
        for item in results:
            if isinstance(item, dict):
                output.append(f"Title: {item.get('title', 'Untitled')}\nSummary: {item.get('content', '')}\nURL: {item.get('url', '')}")
            else:
                output.append(str(item))
        return "\n\n".join(output)
    except Exception as exc:
        return f"Web search failed: {exc}. Check TAVILY_API_KEY and internet access."
