import os
import json
import csv
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

from llm.client import call_llm

load_dotenv()

class Atlas:
    SOURCE_LABELGRID = "labelgrid"
    SOURCE_ORCHARD   = "orchard"
    SOURCE_BANDCAMP  = "bandcamp"

    def __init__(self, artist_data: dict):
        self.artist   = artist_data
        self.records  = []
        self.built_at = datetime.utcnow().strftime("%Y-%m-%d")

    # ── NORMALIZERS ─────────────────────────────────────────────────────────

    def _parse_float(self, val):
        try:
            return float(str(val).replace(",", "").strip() or 0)
        except:
            return 0.0

    def _parse_date(self, raw):
        """Return YYYY-MM from various date formats."""
        raw = str(raw).strip()[:10]
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m"]:
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m")
            except:
                continue
        return "unknown"

    def _normalize_labelgrid(self, row):
        return {
            "source":    "labelgrid",
            "date":      self._parse_date(row.get("dsp_transaction_date", "")),
            "artist":    row.get("reported_artist") or row.get("lg_matching_artists", ""),
            "release":   row.get("release", ""),
            "track":     row.get("track_title", ""),
            "isrc":      row.get("isrc", ""),
            "upc":       row.get("upc", ""),
            "territory": row.get("territory", ""),
            "retailer":  row.get("retailer", ""),
            "type":      row.get("type", ""),
            "quantity":  self._parse_float(row.get("purchase_qty") or row.get("track_count", 0)),
            "revenue":   self._parse_float(row.get("subtotal_usd", 0)),
            "currency":  "USD",
        }

    def _normalize_orchard(self, row):
        return {
            "source":    "orchard",
            "date":      self._parse_date(row.get("Date/Time", "")),
            "artist":    row.get("Release Artist", ""),
            "release":   row.get("Release", ""),
            "track":     row.get("Track", ""),
            "isrc":      row.get("Track ISRC", ""),
            "upc":       row.get("UPC", ""),
            "territory": row.get("Country", ""),
            "retailer":  row.get("Source", ""),
            "type":      row.get("File Type", ""),
            "quantity":  self._parse_float(row.get("Quantity", 0)),
            "revenue":   self._parse_float(row.get("Royalty", 0)),
            "currency":  "USD",
        }

    def _normalize_bandcamp(self, row):
        currency = row.get("currency", "USD").strip().upper()
        return {
            "source":    "bandcamp",
            "date":      self._parse_date(row.get("date", "")),
            "artist":    row.get("artist", ""),
            "release":   row.get("item name", ""),
            "track":     row.get("item name", "") if "track" in row.get("item type", "").lower() else "",
            "isrc":      row.get("isrc", ""),
            "upc":       row.get("upc", ""),
            "territory": row.get("buyer country name", ""),
            "retailer":  "bandcamp",
            "type":      row.get("item type", ""),
            "quantity":  self._parse_float(row.get("quantity", 1)),
            "revenue":   self._parse_float(row.get("net amount") or row.get("amount you received", 0)),
            "currency":  currency,
        }

    # ── INGESTION ────────────────────────────────────────────────────────────

    def load_csv(self, filepath: str, source: str):
        normalizer = {
            self.SOURCE_LABELGRID: self._normalize_labelgrid,
            self.SOURCE_ORCHARD:   self._normalize_orchard,
            self.SOURCE_BANDCAMP:  self._normalize_bandcamp,
        }.get(source)
        if not normalizer:
            return 0
        count = 0
        with open(filepath, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                rec = normalizer(row)
                if rec:
                    self.records.append(rec)
                    count += 1
        return count

    def load_artist_data(self, metrics_dir="data/metrics"):
        slug = self.artist["name"].lower().replace(" ", "_")
        files_loaded = []
        source_map = {
            "bandcamp":  self.SOURCE_BANDCAMP,
            "orchard":   self.SOURCE_ORCHARD,
            "labelgrid": self.SOURCE_LABELGRID,
        }
        for folder, source in source_map.items():
            path = os.path.join(metrics_dir, folder)
            if not os.path.exists(path):
                continue
            for fname in os.listdir(path):
                if fname.endswith(".csv") and slug in fname.lower():
                    n = self.load_csv(os.path.join(path, fname), source)
                    files_loaded.append((fname, source, n))
        return files_loaded

    # ── ANALYSIS ─────────────────────────────────────────────────────────────

    def _check_currency_mix(self):
        currencies = set(r["currency"] for r in self.records if r["source"] == "bandcamp")
        return currencies - {"USD"}

    def calculate_trends(self):
        monthly = defaultdict(lambda: {"revenue": 0.0, "quantity": 0.0})
        for r in self.records:
            m = r.get("date", "unknown")
            monthly[m]["revenue"]  += r.get("revenue", 0)
            monthly[m]["quantity"] += r.get("quantity", 0)

        sorted_months = sorted(k for k in monthly if k != "unknown")
        trends = {
            "monthly":        {m: monthly[m] for m in sorted_months},
            "total_revenue":  round(sum(r.get("revenue", 0) for r in self.records), 2),
            "total_quantity": int(sum(r.get("quantity", 0) for r in self.records)),
        }

        if len(sorted_months) >= 2:
            last = monthly[sorted_months[-1]]["revenue"]
            prev = monthly[sorted_months[-2]]["revenue"]
            trends["mom_revenue_growth"] = round((last - prev) / prev * 100, 1) if prev else None

        return trends

    def calculate_anomalies(self, trends):
        anomalies = []
        monthly = trends.get("monthly", {})
        months  = sorted(monthly.keys())
        if len(months) < 3:
            return anomalies

        revenues = [monthly[m]["revenue"] for m in months]
        baseline = sum(revenues[:-1]) / len(revenues[:-1])
        last_rev = revenues[-1]

        if baseline > 0:
            pct = (last_rev - baseline) / baseline * 100
            if abs(pct) >= 40:
                anomalies.append({
                    "type":       "spike" if pct > 0 else "drop",
                    "period":     months[-1],
                    "value":      round(last_rev, 2),
                    "baseline":   round(baseline, 2),
                    "pct_change": round(pct, 1),
                    "message":    f"Revenue {'spike' if pct > 0 else 'drop'} of {abs(pct):.0f}% vs baseline in {months[-1]}",
                })
        return anomalies

    def _top_by(self, key, n=5):
        totals = defaultdict(float)
        for r in self.records:
            totals[r.get(key, "Unknown")] += r.get("revenue", 0)
        return sorted(totals.items(), key=lambda x: x[1], reverse=True)[:n]

    # ── CLAUDE LAYER ─────────────────────────────────────────────────────────

    def generate_insights(self, trends, anomalies, top_releases, territories, retailers):
        artist_name = self.artist.get("name", "")
        summary = {
            "artist":                artist_name,
            "genre":                 self.artist.get("genre", ""),
            "total_revenue_usd":     trends.get("total_revenue"),
            "total_units":           trends.get("total_quantity"),
            "mom_revenue_growth_pct": trends.get("mom_revenue_growth"),
            "monthly_trend":         trends.get("monthly", {}),
            "anomalies":             anomalies,
            "top_releases":  [{"release": r, "revenue": round(v, 2)} for r, v in top_releases],
            "top_territories":[{"territory": t, "revenue": round(v, 2)} for t, v in territories],
            "top_retailers":  [{"retailer": r, "revenue": round(v, 2)} for r, v in retailers],
        }

        prompt = f"""You are ATLAS, the analytics intelligence agent for LRRecords, an independent music label.

Analyse the following sales data for {artist_name} and return a JSON object only — no markdown, no explanation.

Return exactly this structure:
{{
  "executive_summary": "2-3 sentence summary",
  "trend_flags": [
    {{"flag": "...", "detail": "...", "data_point": "..."}}
  ],
  "anomaly_alerts": [
    {{"alert": "...", "detail": "...", "suggested_action": "..."}}
  ],
  "strategic_recommendations": [
    {{"recommendation": "...", "rationale": "...", "priority": "high|medium|low"}}
  ]
}}

Be specific. Reference actual figures from the data.

DATA:
{json.dumps(summary, indent=2)}"""

        raw = call_llm(prompt, max_tokens=1500).strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
        return json.loads(raw)

    # ── DISPLAY ──────────────────────────────────────────────────────────────

    def display(self, report):
        if not report:
            return
        ins = report["insights"]
        s   = report["summary"]

        print()
        print("=" * 62)
        print("📊  ATLAS — ANALYTICS REPORT")
        print("=" * 62)
        print(f"  Artist  : {report['artist']}")
        print(f"  Sources : {', '.join(report['data_sources'])}")
        print(f"  Records : {report['record_count']}")
        print(f"  Built   : {report['built_at_utc']}")

        if report.get("currency_warning"):
            print(f"  ⚠️   Currency mix detected: {report['currency_warning']}")
            print(f"       Bandcamp non-USD revenue included at face value — totals are approximate")

        print()
        print("💰  SUMMARY:")
        print(f"  Total Revenue  : ${s['total_revenue_usd']:,.2f}  (see currency note above if applicable)")
        print(f"  Total Units    : {s['total_units']:,}")
        if s.get("mom_revenue_growth_pct") is not None:
            arrow = "↑" if s["mom_revenue_growth_pct"] >= 0 else "↓"
            print(f"  MoM Growth     : {arrow} {abs(s['mom_revenue_growth_pct'])}%")

        print()
        print("💡  EXECUTIVE SUMMARY:")
        print(f"  {ins.get('executive_summary', '')}")

        if report.get("top_releases"):
            print()
            print("🏆  TOP RELEASES:")
            for item in report["top_releases"]:
                print(f"  •  {item['release'][:42]:<42}  ${item['revenue']:,.2f}")

        if report.get("top_territories"):
            print()
            print("🌍  TOP TERRITORIES:")
            for item in report["top_territories"]:
                print(f"  •  {item['territory']:<30}  ${item['revenue']:,.2f}")

        if report.get("top_retailers"):
            print()
            print("🎵  TOP RETAILERS / DSPs:")
            for item in report["top_retailers"]:
                print(f"  •  {item['retailer']:<30}  ${item['revenue']:,.2f}")

        if ins.get("trend_flags"):
            print()
            print("📈  TREND FLAGS:")
            for f in ins["trend_flags"]:
                print(f"  →  {f['flag']}")
                print(f"     {f['detail']}")
                if f.get("data_point"):
                    print(f"     Data: {f['data_point']}")

        if ins.get("anomaly_alerts"):
            print()
            print("🚨  ANOMALY ALERTS:")
            for a in ins["anomaly_alerts"]:
                print(f"  ⚠️   {a['alert']}")
                print(f"     {a['detail']}")
                if a.get("suggested_action"):
                    print(f"     Action: {a['suggested_action']}")

        if ins.get("strategic_recommendations"):
            print()
            print("🎯  STRATEGIC RECOMMENDATIONS:")
            icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            for rec in ins["strategic_recommendations"]:
                icon = icons.get(rec.get("priority", "medium"), "•")
                print(f"  {icon}  {rec['recommendation']}")
                print(f"     {rec['rationale']}")
        print()

    # ── RUN ──────────────────────────────────────────────────────────────────

    def run(self, metrics_dir="data/metrics"):
        artist_name = self.artist.get("name", "Unknown")
        files = self.load_artist_data(metrics_dir)

        if not self.records:
            print(f"  ⚠️   No CSVs found for {artist_name}")
            print(f"       Drop files into data/metrics/bandcamp|orchard|labelgrid/")
            print(f"       Filename must contain: {artist_name.lower().replace(' ', '_')}")
            return None

        print(f"  📂  Loaded {len(self.records)} records from {len(files)} file(s)")

        trends     = self.calculate_trends()
        anomalies  = self.calculate_anomalies(trends)
        top_rel    = self._top_by("release")
        territories= self._top_by("territory")
        retailers  = self._top_by("retailer")

        print("  🔄  Generating strategic insights...")
        insights = self.generate_insights(trends, anomalies, top_rel, territories, retailers)

        non_usd = self._check_currency_mix()
        report = {
            "artist":           artist_name,
            "built_at_utc":     self.built_at,
            "data_sources":     list(set(r["source"] for r in self.records)),
            "record_count":     len(self.records),
            "currency_warning": f"Non-USD Bandcamp currencies present: {', '.join(non_usd)}" if non_usd else None,
            "summary": {
                "total_revenue_usd":      trends.get("total_revenue"),
                "total_units":            trends.get("total_quantity"),
                "mom_revenue_growth_pct": trends.get("mom_revenue_growth"),
            },
            "trends":          trends,
            "anomalies":       anomalies,
            "top_releases":    [{"release": r, "revenue": round(v, 2)} for r, v in top_rel],
            "top_territories": [{"territory": t, "revenue": round(v, 2)} for t, v in territories],
            "top_retailers":   [{"retailer": r, "revenue": round(v, 2)} for r, v in retailers],
            "insights":        insights,
        }
        return report