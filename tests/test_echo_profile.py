"""ECHO content-plan prompt: uses the full artist profile and guards against
invented facts. No real LLM calls — call_llm is patched."""

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from agents.echo import EchoAgent  # noqa: E402

FAKE_PLAN = {"artist": "Test", "content_plan": []}


def _fictional_artist(**overrides):
    artist = {
        "artist_info": {
            "name": "Glass Harbour",
            "genres": ["Ambient"],
            "location": "Testville",
            "members": [{"name": "Ada", "role": "Synths"}],
        },
        "musical_identity": {"voice_description": "Quiet, coastal", "influences": ["Eno"]},
        "current_project": {"name": "Low Tide", "type": "EP", "target_date": "2020-01-01"},
        "catalogue": [
            {"title": "Low Tide", "tracks": ["One"], "title_meaning": "The hour between two tides"}
        ],
        "audience_timezone": "Europe/Warsaw",
    }
    artist.update(overrides)
    return artist


def _run(artist, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("agents.echo.call_llm", return_value=json.dumps(FAKE_PLAN)) as mock_llm:
        plan, saved = EchoAgent().generate_content_plan(artist)
    prompt = mock_llm.call_args[0][0]
    return plan, saved, prompt


def test_prompt_uses_catalogue_title_meaning_and_timezone(tmp_path, monkeypatch):
    _, saved, prompt = _run(_fictional_artist(), tmp_path, monkeypatch)
    assert "TITLE MEANING : The hour between two tides" in prompt
    assert "Europe/Warsaw" in prompt
    assert "Ada (Synths)" in prompt
    assert Path(saved).exists()


def test_past_release_is_marked_out_now(tmp_path, monkeypatch):
    _, _, prompt = _run(_fictional_artist(), tmp_path, monkeypatch)
    assert "ALREADY RELEASED on 2020-01-01" in prompt


def test_future_release_is_marked_upcoming(tmp_path, monkeypatch):
    artist = _fictional_artist(
        current_project={"name": "Low Tide", "type": "EP", "target_date": "2999-01-01"}
    )
    _, _, prompt = _run(artist, tmp_path, monkeypatch)
    assert "UPCOMING on 2999-01-01" in prompt


def test_missing_title_meaning_tells_model_not_to_define_title(tmp_path, monkeypatch):
    artist = _fictional_artist(catalogue=[])
    _, _, prompt = _run(artist, tmp_path, monkeypatch)
    assert "TITLE MEANING : [placeholder]" in prompt
    assert "do not define, translate or explain the title" in prompt


def test_minimal_demo_style_profile_still_works(tmp_path, monkeypatch):
    artist = {"artist_info": {"name": "Demo Artist"}}
    plan, _, prompt = _run(artist, tmp_path, monkeypatch)
    assert plan == FAKE_PLAN
    assert "Unknown release date" in prompt
    assert "Australia/Perth" in prompt


def test_release_status_handles_bad_dates():
    today = datetime(2026, 10, 16)
    assert "Unknown" in EchoAgent._release_status("TBD", today)
    assert "ALREADY RELEASED" in EchoAgent._release_status("2026-10-16", today)
