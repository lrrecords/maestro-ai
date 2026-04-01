import os
import json
import requests
from datetime import datetime, timezone
from core.base_agent import BaseAgent

class AskAIAgent(BaseAgent):
    name = "ASKAI"
    department = "studio"
    description = "Ask any question and receive an LLM-powered answer with actionable studio, business, music, or tech advice."

    FIELDS = [
        {
            "key": "question",
            "label": "Your Question",
            "type": "textarea",
            "required": True,
            "placeholder": "Type any studio, music, or business question here…"
        },
        {
            "key": "context_notes",
            "label": "Context (optional)",
            "type": "textarea",
            "required": False,
            "placeholder": "Tell us what this relates to (project, artist, session…)"
        },
        {
            "key": "answer_style",
            "label": "Answer Style",
            "type": "select",
            "options": ["concise", "detailed", "step_by_step", "creative", "industry_best_practices"],
            "required": False
        }
    ]

    def run(self, context: dict) -> dict:
        question = (context.get("question") or "").strip()
        context_notes = (context.get("context_notes") or "").strip()
        answer_style = (context.get("answer_style") or "concise").strip()

        if not question:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "error": "Missing required field: question",
                "context": context,
                "result": {
                    "action": "error",
                    "answer": "",
                    "recommendations": [
                        "Type your question before running the AI agent.",
                        "You can add context (project, goal, etc.) for more tailored advice.",
                    ]
                }
            }

        # Audit/history log
        llm_file = self.data_root / "llm_ask_history.json"
        history = []
        if llm_file.exists():
            try:
                history = json.loads(llm_file.read_text(encoding="utf-8"))
                if not isinstance(history, list):
                    history = []
            except Exception:
                history = []
        now_iso = datetime.now(timezone.utc).isoformat()
        query_record = {
            "question": question,
            "context_notes": context_notes,
            "answer_style": answer_style,
            "created_at": now_iso,
        }

        # Generate answer
        answer, recs = self._llm_answer(question, context_notes, answer_style)

        answer_record = {**query_record, "answer": answer}
        history.append(answer_record)
        llm_file.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")

        audit_trail = history[-5:]  # Show last 5 for UI

        return {
            "agent": self.name,
            "department": self.department,
            "status": "ok",
            "context": context,
            "result": {
                "action": "answered",
                "answer": answer,
                "recommendations": recs,
                "audit_trail": audit_trail,
                "saved_to": str(llm_file)
            }
        }

    def _llm_answer(self, question, context_notes, answer_style):
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        style_pref = {
            "concise": "Reply concisely.",
            "detailed": "Provide a detailed, thorough answer.",
            "step_by_step": "Give a step-by-step answer or checklist.",
            "creative": "Be creative and inspiring.",
            "industry_best_practices": "Summarise best practices used in the music/studio industry."
        }.get(answer_style, "Reply concisely.")

        prompt = f"""
You are a senior studio consultant, producer, and music tech expert.

{style_pref}
Question: {question}
{('Context: '+ context_notes) if context_notes else ''}
If advice involves a workflow, list the steps. For how-to, give studio/Music/AI best practices. If relevant, give next actions.

Return:
- The answer.
- Then 3 practical recommendations or next steps.
No markdown headings, just plain text.
""".strip()

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_ctx": num_ctx, "temperature": 0.7}
                },
                timeout=timeout
            )
            resp.raise_for_status()
            text = (resp.json().get("response") or "").strip()
            # Heuristically split into answer and recs
            lines = [l.strip("•- \t") for l in text.splitlines() if l.strip()]
            answer, recs = "", []
            for i, l in enumerate(lines):
                if i == 0:
                    answer = l
                elif len(recs) < 3:
                    recs.append(l)
            return answer or "No answer generated.", recs or [
                "If you need more detail, rephrase and use 'detailed' style next run.",
                "Cite more context for better recommendations.",
                "Consult a specialist if you need legal or tax guidance."
            ]
        except Exception as exc:
            return f"LLM unavailable ({exc})", [
                "Try again in a few minutes.",
                "Contact studio support if this persists.",
                "Review previous AI answers in the audit history."
            ]