# Quickstart: Maestro AI

## Prerequisites

- Python 3.8+ (recommend 3.11)
- Node.js (only if developing deep frontend upgrades)
- [Ollama](https://ollama.com/) (optional, for local LLM support)

## Setup

```bash
git clone https://github.com/lrrecords/maestro-ai.git
cd maestro-ai
python -m venv venv
# macOS/Linux:
source venv/bin/activate
# Windows PowerShell:
# venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell equivalent for the copy step:

```powershell
Copy-Item .env.example .env
```

Playwright install is optional and only needed for browser automation workflows:

```bash
playwright install chromium
```

## Run

```bash
python dashboard/app.py
```
