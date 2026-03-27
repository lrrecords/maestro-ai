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
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env