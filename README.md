# KOBI v2

A simple, working, deployable Streamlit app for multi-model deliberation.

## What changed from v1

- live calls to multiple providers
- OpenAI, Anthropic, and Mistral support
- pairwise divergence table
- consensus keyword view
- human synthesis workspace
- Markdown and JSON export
- local session saving
- manual fallback for pasted answers

## Features

- ask multiple AI systems the same question
- compare their answers side by side
- inspect divergence quickly
- document your own synthesis
- export a session for research, paper drafting, or governance logs

## Project structure

```text
kobi_v2/
├── app.py
├── requirements.txt
├── README.md
├── data/
└── kobi/
    ├── __init__.py
    ├── analysis.py
    ├── exporters.py
    ├── providers.py
    └── storage.py
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## API keys

You can provide keys in one of two ways:

### Option 1: Environment variables

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export MISTRAL_API_KEY="..."
```

### Option 2: Streamlit secrets

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "..."
ANTHROPIC_API_KEY = "..."
MISTRAL_API_KEY = "..."
```

## Deploy on Streamlit Community Cloud

1. Push this folder to GitHub.
2. Create a new app on Streamlit Community Cloud.
3. Select your repo and `app.py`.
4. In the app settings, add your API keys as secrets.
5. Deploy.

## Notes

- v2 is intentionally simple and synchronous.
- If one provider fails, you can still paste a manual answer and continue the session.
- The divergence score is heuristic, not a semantic benchmark.

## Good next upgrades

- async / parallel provider calls
- richer semantic clustering
- provider-specific prompt templates
- user authentication and shared logs
- database storage instead of local jsonl
