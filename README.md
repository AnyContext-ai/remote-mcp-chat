# Remote MCP Chat

## Architecture
![alt text](<resources/architecture.jpg>)

## How it works
![alt text](<resources/how-it-works.jpg>)

## Prerequisites
- Python >3.10
- uv
- OpenAI API key
- Remote MCP server

## Setup environment
1. Create `.env` file: `cp .env.example .env`
2. Add your OpenAI API key and MCP server url to the `.env` file.
3. Create virtual environment: `uv venv`
4. Activate virtual environment (windows): `.venv\Scripts\activate`
4. Install dependencies: `uv pip install -r pyproject.toml`
5. Run chat client: `uv run client.py`