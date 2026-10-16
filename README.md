# Bangladesh Multi-Tool AI Agent

A Python/LangChain agent that routes dataset-specific questions to three SQLite databases and general-knowledge questions to Tavily web search.

## Features
- Institutional Information, hospitals, and restaurants datasets from Hugging Face
- SQLite database builder with normalized column names and inferred column types
- Separate LangChain tools for each database
- Tavily web search tool
- OpenAI-compatible chat model
- Command-line interface and optional Streamlit web interface

## Setup (Windows PowerShell)

Use Python 3.10+ (Python 3.11 is recommended).

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add your own `OPENAI_API_KEY`, optional `OPENAI_MODEL`, and `TAVILY_API_KEY`.
- OpenAI key: https://console.groq.com/keys
- Tavily key: https://app.tavily.com/

A ChatGPT subscription does not automatically include API credits. Never commit `.env` or share API keys.

## Build databases

Run from the project root:

```powershell
python scripts/build_databases.py
```

Creates `data/institutions.db` (table `institutions`), `data/hospitals.db` (table `hospitals`), and `data/restaurants.db` (table `restaurants`). The builder prints record counts and actual columns. Available fields depend on each source dataset.

## Run

Command line:

```powershell
python agent.py
```

Optional web app:

```powershell
streamlit run app.py
```

## Example questions
- How many hospitals are in Dhaka?
- Find institutions in Chattogram.
- Find restaurants in Sylhet.
- What is the role of DGHS in Bangladesh?
- Explain healthcare policy in Bangladesh.

## Limitations
Database search currently uses keyword matching, not a full natural-language-to-SQL engine. Complex queries and counts should be validated against the underlying records. Counts represent matching dataset rows, not necessarily authoritative real-world totals. Web results depend on Tavily and should be checked for accuracy and date. Review the license of each dataset before redistributing data.
