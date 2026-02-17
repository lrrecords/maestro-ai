# 🎵 MAESTRO AI - Multi-Agent Business Operating System

**A personalized AI system for independent music labels**

Built by [Brett Caporn](https://lrrecords.com.au) for LRRecords, now being developed as a product for the music industry.

---

## 🎯 What is MAESTRO?

MAESTRO is a multi-agent AI system that deeply understands your label's operations:
- **Knows your artists by name** and relationship history
- **Tracks releases** across platforms and timelines
- **Manages communications** in your authentic voice
- **Automates workflows** (coming soon)
- **Provides business intelligence** across 6 key areas

Unlike generic AI assistants, MAESTRO is built specifically for music business operations.

---

## 🤖 The Team

**MAESTRO** (Orchestrator) coordinates 6 specialist agents:

- **BRIDGE** - A&R and Artist Relations Director
- **VINYL** - Music Operations & Distribution Manager
- **ECHO** - Content & Marketing Chief
- **ATLAS** - Business Intelligence Officer
- **FORGE** - Development & Automation Engineer
- **SAGE** - Personal Assistant & Life Manager

---

## ✨ Key Features

✅ **Deep Business Context**
- Knows your artists, releases, and platforms
- References real projects and deadlines
- Understands music industry workflows

✅ **Artist Relationship Intelligence**
- Health checks across your roster
- Identifies who needs attention
- Drafts check-in messages in your voice

✅ **Multi-Agent Collaboration**
- Complex queries automatically routed to specialists
- Agents collaborate on multi-faceted problems
- Synthesized responses from multiple perspectives

✅ **Communication Intelligence**
- Learns your communication style
- Matches your tone and energy
- Gives actionable advice, not generic tips

✅ **Local & Private**
- Runs on your machine (Llama 3.1:8b via Ollama)
- No data sent to external servers
- Complete ownership and control

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Ollama installed ([download](https://ollama.ai))
- Windows 10/11 or Linux

### Installation

```bash
# Clone the repository
git clone https://github.com/[YourUsername]/maestro-ai.git
cd maestro-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install ollama

# Pull the LLM model
ollama pull llama3.1:8b

# Customize your business context
notepad data\lr_records_context.json
notepad data\brett_communication_profile.json