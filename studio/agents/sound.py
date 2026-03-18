from __future__ import annotations

import json
import os
import requests
from datetime import datetime, timezone
from core.base_agent import BaseAgent


class SoundAgent(BaseAgent):
    name = "SOUND"
    department = "studio"
    description = "Catalogue management, sync licensing, and rights tracking."

    STRICT_JSON_SYSTEM = (
    "You are a backend JSON generator. "
    "Return ONLY valid JSON. No markdown. No prose outside JSON. "
    "No headings like 'A short intro sentence:'."
)

    FIELDS = [
        {"key": "track_title",  "label": "Track Title",  "type": "text",     "required": True,  "placeholder": "e.g. Midnight Signal"},
        {"key": "artist",       "label": "Artist",       "type": "text",     "required": True,  "placeholder": "e.g. Jordan Blake"},
        {"key": "album",        "label": "Album / EP",   "type": "text",     "required": False, "placeholder": "e.g. Debut EP"},
        {"key": "isrc",         "label": "ISRC",         "type": "text",     "required": False, "placeholder": "e.g. GB-ABC-26-00001"},
        {"key": "genre",        "label": "Genre",        "type": "text",     "required": False, "placeholder": "e.g. Indie Rock"},
        {"key": "bpm",          "label": "BPM",          "type": "number",   "required": False, "placeholder": "e.g. 120"},
        {"key": "key",          "label": "Key",          "type": "text",     "required": False, "placeholder": "e.g. C minor"},
        {"key": "duration",     "label": "Duration",     "type": "text",     "required": False, "placeholder": "e.g. 3:42"},
        {"key": "rights_owner", "label": "Rights Owner", "type": "text",     "required": False, "placeholder": "e.g. Jordan Blake Music Ltd"},
        {"key": "sync_status",  "label": "Sync Status",  "type": "select",   "required": False,
         "options": ["available", "in_negotiation", "licensed", "not_available"]},
        {"key": "notes",        "label": "Notes",        "type": "textarea", "required": False, "placeholder": "Placement history, restrictions, stems available"},
    ]

    def run(self, context: dict) -> dict:
        track_title  = context.get("track_title",  "").strip()
        artist       = context.get("artist",       "").strip()
        album        = context.get("album",        "").strip()
        isrc         = context.get("isrc",         "").strip()
        genre        = context.get("genre",        "").strip()
        bpm          = context.get("bpm",          "")
        key          = context.get("key",          "").strip()
        duration     = context.get("duration",     "").strip()
        rights_owner = context.get("rights_owner", "").strip()
        sync_status  = context.get("sync_status",  "available").strip()
        notes        = context.get("notes",        "").strip()

        missing = [f for f, v in [
            ("track_title", track_title),
            ("artist",      artist),
        ] if not v]

        if missing:
            return {
                "agent":      self.name,
                "department": self.department,
                "status":     "error",
                "error":      f"Missing required fields: {', '.join(missing)}",
                "context":    context,
                "recommendations": [
                    "Track title and artist are the minimum required to log a catalogue entry.",
                    "Add ISRC and rights owner to make the record sync-ready.",
                    "Include BPM, key, and genre to improve discoverability for licensing.",
                ],
            }

        catalogue_file = self.data_root / "catalogue.json"
        catalogue = []
        if catalogue_file.exists():
            try:
                catalogue = json.loads(catalogue_file.read_text(encoding="utf-8"))
                if not isinstance(catalogue, list):
                    catalogue = []
            except Exception:
                catalogue = []

        now_iso = datetime.now(timezone.utc).isoformat()
        track_record = {
            "track_title":  track_title,
            "artist":       artist,
            "album":        album,
            "isrc":         isrc,
            "genre":        genre,
            "bpm":          bpm,
            "key":          key,
            "duration":     duration,
            "rights_owner": rights_owner,
            "sync_status":  sync_status,
            "notes":        notes,
        }

        existing = next(
            (t for t in catalogue
             if t.get("track_title") == track_title
             and t.get("artist") == artist),
            None,
        )

        if existing:
            existing.update(track_record)
            existing["updated_at"] = now_iso
            action = "updated"
            saved_record = existing
        else:
            track_record["created_at"] = now_iso
            catalogue.append(track_record)
            action = "created"
            saved_record = track_record

        catalogue_file.write_text(
            json.dumps(catalogue, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        recommendations = self._generate_recommendations(saved_record)

        return {
            "agent":      self.name,
            "department": self.department,
            "status":     "ok",
            "context":    context,
            "result": {
                "action": action,
                "track": {
                    "title":       track_title,
                    "artist":      artist,
                    "album":       album or "—",
                    "isrc":        isrc or "—",
                    "genre":       genre or "—",
                    "bpm":         bpm or "—",
                    "key":         key or "—",
                    "duration":    duration or "—",
                    "rights":      rights_owner or "—",
                    "sync_status": sync_status,
                    "notes":       notes or "—",
                },
                "recommendations": recommendations,
            },
        }

    def _generate_recommendations(self, record: dict) -> list[str]:
        provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        if provider != "ollama":
            return self._fallback(record)

        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model    = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        num_ctx  = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
        timeout  = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "1800"))

        prompt = f"""
You are a music rights and sync licensing advisor.

Generate practical recommendations for managing and licensing this track.

Track details:
- Title: {record.get("track_title", "")}
- Artist: {record.get("artist", "")}
- Album: {record.get("album", "")}
- Genre: {record.get("genre", "")}
- BPM: {record.get("bpm", "")}
- Key: {record.get("key", "")}
- Duration: {record.get("duration", "")}
- Rights owner: {record.get("rights_owner", "")}
- ISRC: {record.get("isrc", "")}
- Sync status: {record.get("sync_status", "")}
- Notes: {record.get("notes", "")}

Return:
- A short intro sentence
- 5 bullet recommendations covering metadata, rights, sync readiness, and catalogue hygiene
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
            return lines[:9] or self._fallback(record)
        except Exception as exc:
            return self._fallback(record) + [f"LLM unavailable; using fallback. ({exc})"]

    def _fallback(self, record: dict) -> list[str]:
        sync_status = (record.get("sync_status") or "available").lower()
        recs = [
            "Register the track with your PRO (PRS, ASCAP, etc.) if not already done.",
            "Ensure a clean instrumental and vocal stem set is archived and labelled.",
            "Confirm the rights owner and splits are documented before any licensing conversation.",
        ]
        if not record.get("isrc"):
            recs.append("Generate and assign an ISRC — required for digital distribution and royalty tracking.")
        if sync_status == "available":
            recs.append("Pitch to sync libraries and supervisors — tag BPM, key, and mood clearly in submissions.")
        elif sync_status == "in_negotiation":
            recs.append("Document all negotiation terms and set a clear follow-up date to avoid deals going cold.")
        elif sync_status == "licensed":
            recs.append("File the licensing agreement and set a calendar reminder for any term expiry dates.")
        if not record.get("bpm") or not record.get("key"):
            recs.append("Complete BPM and key metadata — essential for sync search tools and music supervisors.")
        recs.append("Back up all masters, stems, and session files to at least two separate locations.")
        return recs[:7]