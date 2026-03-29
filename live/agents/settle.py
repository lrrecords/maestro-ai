from core.base_agent import BaseAgent
import re

def apply_deal_calculation(settle_struct):
    """
    Correct arithmetic based on deal_memo/deal_summary.
    Handles basic 'X/Y split' memos (e.g. 70/30, 80/20) and fixes share fields.
    """
    try:
        gross = float(settle_struct.get("gross_box_office", 0))
        expenses = float(settle_struct.get("deductible_expenses", 0))
        net = gross - expenses
    except Exception:
        gross = expenses = net = 0

    deal = settle_struct.get("deal_summary", "") or ""
    # Try to parse e.g. "70/30" or "70/30 split"
    m = re.search(r"(\d{1,2})\s*\/\s*(\d{1,2})", deal)
    if m:
        artist_pct = int(m.group(1))
        promoter_pct = int(m.group(2))
        if artist_pct + promoter_pct > 0:
            artist_fraction = artist_pct / (artist_pct + promoter_pct)
            promoter_fraction = promoter_pct / (artist_pct + promoter_pct)
        else:
            artist_fraction = 0.0
            promoter_fraction = 0.0
        artist_share = round(net * artist_fraction)
        promoter_share = round(net * promoter_fraction)
        settle_struct["artist_share"] = artist_share
        settle_struct["promoter_share"] = promoter_share
        settle_struct["net_box_office"] = round(net)
    # TODO: Add more parsing here for guarantees, vs/minimums if desired
    # else: leave as is for unknown/special cases
    return settle_struct

class SettleAgent(BaseAgent):
    department = "live"
    name = "SETTLE"
    description = "Financial settlement and reconciliation."

    FIELDS = [
        {"key": "gross_box_office", "label": "Gross Box Office (£)", "type": "number",   "placeholder": "e.g. 12000", "required": True},
        {"key": "deal_memo",        "label": "Deal Memo",             "type": "textarea", "placeholder": "e.g. 70/30 vs £3,000 guarantee"},
        {"key": "expenses",         "label": "Deductible Expenses (£)","type": "number",  "placeholder": "e.g. 1500"},
        {"key": "currency",         "label": "Currency",              "type": "select",   "options": ["GBP", "USD", "EUR"]},
    ]

    def build_prompt(self, context: dict) -> str:
        gross = context.get("gross_box_office", "[unknown]")
        deal = context.get("deal_memo", "[no deal memo entered]")
        expenses = context.get("expenses", 0)
        currency = context.get("currency", "GBP")
        return (
            f"You are an experienced tour accountant. Given the gross box office ({currency} {gross}), deal memo ('{deal}'), and expenses ({currency} {expenses}), "
            "calculate the financial settlement for the show, following the memo's split or guarantee rule, and subtracting deductible expenses.\n"
            "Respond ONLY in this strictly valid JSON format:\n"
            "{\n"
            "  \"gross_box_office\": number,           // total ticket sales\n"
            "  \"deductible_expenses\": number,        // total subtracted (before split)\n"
            "  \"net_box_office\": number,             // gross minus expenses\n"
            "  \"deal_summary\": string,               // short description of deal logic used\n"
            "  \"artist_share\": number,               // artist's final settlement\n"
            "  \"promoter_share\": number,             // promoter's final settlement\n"
            "  \"explanation\": string                 // step-by-step settlement reasoning\n"
            "}\n"
            "Always fill all fields – if any data is not provided, state 'unknown' or use 0, but never omit fields. "
            "Use numbers, not strings, for revenues/share fields. JSON only, no markdown or explanation."
        )

    def run(self, context: dict) -> dict:
        prompt = self.build_prompt(context)
        try:
            llm_result = self.llm(prompt)
            structured = self.parse_json(llm_result)
            structured = apply_deal_calculation(structured)
        except Exception as e:
            return {
                "agent": self.name,
                "department": self.department,
                "status": "error",
                "message": f"SETTLE LLM error: {str(e)}",
                "context": context,
            }
        return {
            "agent": self.name,
            "department": self.department,
            "status": "complete",
            "message": llm_result,
            "data": structured,
            "context": context,
        }