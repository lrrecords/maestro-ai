from __future__ import annotations

import json
import os
import requests
from datetime import datetime, timezone
from core.base_agent import BaseAgent


class RateAgent(BaseAgent):
    name = "RATE"
    department = "studio"
    description = "Pricing strategy, quote generation, and contracts."

    FIELDS = [
        {"key": "client",           "label": "Client Name",     "type": "text",   "required": True,  "placeholder": "e.g. Jordan Blake"},
        {"key": "project_type",     "label": "Project Type",    "type": "select", "required": True,
         "options": ["tracking", "mixing", "mastering", "production", "full_album", "ep", "single", "sync", "other"]},
        {"key": "session_days",     "label": "Session Days",    "type": "number", "required": False, "placeholder": "e.g. 3"},
        {"key": "hours_per_day",    "label": "Hours / Day",     "type": "number", "required": False, "placeholder": "e.g. 8"},
        {"key": "num_tracks",       "label": "No. of Tracks",   "type": "number", "required": False, "placeholder": "e.g. 12"},
        {"key": "includes_mix",     "label": "Includes Mix",    "type": "select", "required": False, "options": ["yes", "no"]},
        {"key": "includes_master",  "label": "Includes Master", "type": "select", "required": False, "options": ["yes", "no"]},
        {"key": "currency",         "label": "Currency",        "type": "select", "required": False,
         "options": ["GBP", "USD", "EUR", "AUD", "CAD"]},
        {"key": "discount_percent", "label": "Discount %",      "type": "number", "required": False, "placeholder": "e.g. 10"},
        {"key": "notes",            "label": "Notes",           "type": "textarea","required": False, "placeholder": "Special terms, rush fees, travel, etc."},
    ]

    # Base rates (per day/track) — adjust to your actual pricing
    BASE_RATES = {
        "tracking":    650,
        "mixing":      350,
        "mastering":   120,
        "production":  800,
        "full_album":  600,
        "ep":          550,
        "single":      450,
        "sync":        500,
        "other":       400,
    }

    def run(self, context: dict) -> dict:
        client          = context.get("client",           "").strip()
        project_type    = context.get("project_type",     "").strip()
        session_days    = int(context.get("session_days",    0) or 0)
        hours_per_day   = int(context.get("hours_per_day",   0) or 0)
        num_tracks      = int(context.get("num_tracks",      0) or 0)
        includes_mix    = str(context.get("includes_mix",    "no")).lower()  == "yes"
        includes_master = str(context.get("includes_master", "no")).lower() == "yes"
        currency        = context.get("currency",         "GBP").strip() or "GBP"
        discount_pct    = float(context.get("discount_percent", 0) or 0)
        notes           = context.get("notes",            "").strip()

        missing = [f for f, v in [
            ("client",       client),
            ("project_type", project_type),
        ] if not v]

        if missing:
            return {
                "agent":      self.name,
                "department": self.department,
                "status":     "error",
                "error":      f"Missing required fields: {', '.join(missing)}",
                "context":    context,
                "recommendations": [
                    "Provide client name and project type to generate a quote.",
                    "Add session days and track count for accurate line-item pricing.",
                    "Specify currency — defaults to GBP if not set.",
                ],
            }

        day_rate    = self.BASE_RATES.get(project_type, 400)
        line_items  = []
        subtotal    = 0.0

        if session_days > 0:
            amount = day_rate * session_days
            line_items.append({
                "description": f"{project_type.replace('_', ' ').title()} — Studio Time",
                "quantity":    session_days,
                "unit":        "days",
                "unit_price":  day_rate,
                "total":       amount,
            })
            subtotal += amount

        if num_tracks > 0 and project_type in ("mixing", "mastering"):
            per_track = self.BASE_RATES[project_type]
            amount    = per_track * num_tracks
            line_items.append({
                "description": f"{project_type.title()} — Per Track",
                "quantity":    num_tracks,
                "unit":        "tracks",
                "unit_price":  per_track,
                "total":       amount,
            })
            subtotal += amount

        if includes_mix:
            mix_amount = 250 * max(num_tracks, 1)
            line_items.append({
                "description": "Mixing",
                "quantity":    max(num_tracks, 1),
                "unit":        "tracks",
                "unit_price":  250,
                "total":       mix_amount,
            })
            subtotal += mix_amount

        if includes_master:
            master_amount = 90 * max(num_tracks, 1)
            line_items.append({
                "description": "Mastering",
                "quantity":    max(num_tracks, 1),
                "unit":        "tracks",
                "unit_price":  90,
                "total":       master_amount,
            })
            subtotal += master_amount

        if not line_items:
            subtotal = day_rate
            line_items.append({
                "description": f"{project_type.replace('_', ' ').title()} — Base Rate",
                "quantity":    1,
                "unit":        "project",
                "unit_price":  day_rate,
                "total":       day_rate,
            })

        discount_amount = round(subtotal * (discount_pct / 100), 2) if discount_pct else 0.0
        after_discount  = subtotal - discount_amount

        if discount_amount:
            line_items.append({
                "description": f"Discount ({discount_pct:.0f}%)",
                "quantity":    1,
                "unit":        "—",
                "unit_price":  -discount_amount,
                "total":       -discount_amount,
            })

        vat_rate    = 0.20
        vat_amount  = round(after_discount * vat_rate, 2)
        grand_total = round(after_discount + vat_amount, 2)
        deposit     = round(grand_total * 0.50, 2)
        balance     = round(grand_total - deposit, 2)

        quote = {
            "client":           client,
            "project_type":     project_type,
            "currency":         currency,
            "line_items":       line_items,
            "subtotal":         round(subtotal, 2),
            "discount_amount":  discount_amount,
            "vat_rate":         vat_rate,
            "vat_amount":       vat_amount,
            "grand_total":      grand_total,
            "deposit_required": deposit,
            "balance_due":      balance,
            "payment_terms":    "50% deposit required to confirm booking. Balance due on completion.",
            "quote_valid_days":  30,
            "notes":            notes or "—",
        }

        quotes_file = self.data_root / "quotes.json"
        quotes = []
        if quotes_file.exists():
            try:
                quotes = json.loads(quotes_file.read_text(encoding="utf-8"))
                if not isinstance(quotes, list):
                    quotes = []
            except Exception:
                quotes = []

        now_iso = datetime.now(timezone.utc).isoformat()
        quote_record = {**quote, "created_at": now_iso}
        quotes.append(quote_record)

        quotes_file.write_text(
            json.dumps(quotes, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        recommendations = self._generate_recommendations(quote, context)

        return {
            "agent":      self.name,
            "department": self.department,
            "status":     "ok",
            "context":    context,
            "result": {
                "action": "created",
                "quote":  quote,
                "recommendations": recommendations,
            },
        }

    def _generate_recommendations(self, quote: dict, context: dict) -> list[str]:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback(quote, context)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx  = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout  = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        prompt = f"""
You are a recording studio pricing and contracts advisor.

Generate practical recommendations for this studio quote.

Quote details:
- Client: {quote.get("client", "")}
- Project type: {quote.get("project_type", "")}
- Subtotal: {quote.get("subtotal", "")} {quote.get("currency", "")}
- Grand total: {quote.get("grand_total", "")} {quote.get("currency", "")}
- Deposit required: {quote.get("deposit_required", "")} {quote.get("currency", "")}
- VAT rate: {int(quote.get("vat_rate", 0) * 100)}%
- Quote valid: {quote.get("quote_valid_days", 30)} days
- Notes: {quote.get("notes", "")}

Return:
- A short intro sentence
- 5 bullet recommendations covering pricing, terms, negotiation, and contract best practice
- 3 suggested next actions

Be concise and practical. Do not use markdown headings.
""".strip()

        try:
            resp = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model":   model,
                    "prompt":  prompt,
                    "stream":  False,
                    "options": {"num_ctx": num_ctx, "temperature": 0.6},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            text = (resp.json().get("response") or "").strip()
            lines = [l.strip("•- \t") for l in text.splitlines() if l.strip()]
            return lines[:9] or self._fallback(quote, context)
        except Exception as exc:
            return self._fallback(quote, context) + [f"LLM unavailable; using fallback. ({exc})"]

    def _fallback(self, quote: dict, context: dict) -> list[str]:
        grand_total  = float(quote.get("grand_total", 0))
        project_type = (quote.get("project_type") or "").lower()
        discount     = float(context.get("discount_percent", 0) or 0)
        recs = [
            "Send the quote as a PDF with your studio logo, terms, and a clear expiry date.",
            "Follow up within 48 hours if no response — most deals go cold due to silence, not price.",
            "Require the signed quote back before issuing the deposit invoice.",
        ]
        if discount > 15:
            recs.append(f"A {discount:.0f}% discount is generous — consider adding a value-add (extra revision round) instead of cutting the rate further.")
        if grand_total > 2000:
            recs.append("For projects over £2,000 use a formal contract — include cancellation, IP, and delivery terms.")
        if project_type in ("full_album", "ep"):
            recs.append("Break the project into milestones with payments tied to delivery stages to reduce financial risk.")
        if project_type == "sync":
            recs.append("Ensure a sync licence agreement is in place before any placement is confirmed — do not rely on verbal agreements.")
        recs.append("Keep a copy of every issued quote in the studio archive for pricing reference and dispute resolution.")
        return recs[:7]