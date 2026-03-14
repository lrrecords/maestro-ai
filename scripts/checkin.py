import os, json, glob, smtplib, ssl, sys
from datetime import datetime, timezone
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
# ── Data directory override (demo vs private) ────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("MAESTRO_DATA_DIR", str(BASE_DIR / "data")))
if not DATA_DIR.is_absolute():
    DATA_DIR = (BASE_DIR / DATA_DIR).resolve()

ARTISTS_DIR = DATA_DIR / "artists"
BRIDGE_DIR  = DATA_DIR / "bridge"
CHECKIN_DIR = DATA_DIR / "checkin"

THRESHOLDS = {
    "critical": 0,
    "at risk":  7,
    "healthy":  14,
}

# ── Artist loader ─────────────────────────────────────────────────────────────

def load_artist(key: str) -> dict:
    path = ARTISTS_DIR / f"{key}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["_key"] = key
        return data
    raise FileNotFoundError(f"No artist profile found for key: {key}")

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_latest_bridge(artist_key: str) -> str | None:
    files = glob.glob(str(BRIDGE_DIR / f"{artist_key}_*.json"))
    return max(files, key=os.path.getmtime) if files else None

def needs_checkin(health: dict) -> bool:
    status    = health.get("status", "healthy").lower()
    days      = health.get("days_since_contact") or 0
    threshold = THRESHOLDS.get(status, 14)
    return days >= threshold

def display_draft(artist_name: str, health: dict, channel: str, subject: str, body: str):
    print(f"\n{'='*52}")
    print(f"  Artist  : {artist_name}")
    print(f"  Status  : {health.get('status')} ({health.get('score')}/100)")
    print(f"  Days    : {health.get('days_since_contact')} since last contact")
    print(f"  Channel : {channel.upper()}")
    print(f"{'-'*52}")
    if subject:
        print(f"  Subject : {subject}\n")
    print(body)
    print("="*52)

def refine_with_claude(artist: dict, bridge_data: dict, draft_body: str, instruction: str = "") -> str:
    try:
        from anthropic import Anthropic
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Anthropic SDK not installed. Install it with `pip install anthropic` "
            "or disable rewrite."
        ) from e
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is not set; cannot use rewrite.")
    # Anthropic client (reads ANTHROPIC_API_KEY from env)
    client = Anthropic()

    health   = bridge_data.get("health", {})
    patterns = bridge_data.get("patterns", {})

    prompt = f"""You are helping Brett from LR Records refine a check-in message to one of his artists.

ARTIST: {artist.get('name')}
PROFILE: {json.dumps(artist, indent=2)}

ARTIST STATUS:
- Health: {health.get('status')} ({health.get('score')}/100)
- Days since contact: {health.get('days_since_contact')}
- Trend: {patterns.get('trend', 'unknown')}

CURRENT DRAFT:
{draft_body}

{f"BRETT'S NOTE: {instruction}" if instruction else "Refine this to sound more natural and personal."}

Rules:
- Write as Brett — genuine, human, not corporate
- Never mention scores, metrics, or AI systems
- Keep it concise (3-5 sentences)
- Match the artist's style from their profile
- End with one clear question or next step

Return only the refined message text, no explanation."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()

def send_email(subject: str, body: str, to_email: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = os.getenv("SENDER_EMAIL")
    msg["To"]      = to_email
    msg.attach(MIMEText(body, "plain"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        os.getenv("EMAIL_SMTP_SERVER"),
        int(os.getenv("EMAIL_SMTP_PORT", 465)),
        context=ctx
    ) as server:
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        server.sendmail(msg["From"], to_email, msg.as_string())

def save_draft(artist_key: str, payload: dict) -> str:
    CHECKIN_DIR.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = CHECKIN_DIR / f"{artist_key}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return str(path)

# ── Main ──────────────────────────────────────────────────────────────────────

def run(args: list):
    print("\n" + "="*52)
    print("      MAESTRO AI  -  Check-in Drafter")
    print("="*52)

    # Non-interactive mode for web/dashboard use
    draft_only = False
    if "--draft-only" in args:
        draft_only = True
        args = [a for a in args if a != "--draft-only"]

    # Initialize counters ALWAYS
    drafted = sent = skipped = 0

    # Resolve artist key(s)
    if args and args[0]:
        raw   = args[0].lower().replace(" ", "_").replace("-", "_")
        keys  = [raw]
        batch = False
    else:
        files = glob.glob(str(BRIDGE_DIR / "*.json"))
        seen, keys = set(), []
        for f in sorted(files, key=os.path.getmtime, reverse=True):
            stem = Path(f).stem
            key  = "_".join(stem.split("_")[:-2])
            if key and key not in seen:
                keys.append(key)
                seen.add(key)

        batch = True
        print(f"  Scanning {len(keys)} artists with BRIDGE data...\n")

    for key in keys:
        try:
            artist = load_artist(key)
            artist_name = (
                artist.get("artist_info", {}).get("name")
                or artist.get("name")
                or key
            )
            artist_key = artist.get("_key", key)

            bridge_file = get_latest_bridge(artist_key)
            if not bridge_file:
                print(f"  [skip] {artist_name} — no BRIDGE data found")
                skipped += 1
                continue

            with open(bridge_file, encoding="utf-8") as f:
                bridge_data = json.load(f)
        

            health = bridge_data.get("health", {})

            if batch and not needs_checkin(health):
                print(
                    f"  [skip] {artist_name} — "
                    f"{health.get('status')} / "
                    f"{health.get('days_since_contact', 0)}d "
                    f"(threshold not met)"
                )
                skipped += 1
                continue

            # check_in_message can live at top-level (older format)
            # or under health (current BRIDGE demo format)
            check_in = bridge_data.get("check_in_message")
            if check_in is None:
                health_obj = bridge_data.get("health", {})
                if isinstance(health_obj, dict):
                    check_in = health_obj.get("check_in_message")

            # Normalize to channel/subject/body
            if isinstance(check_in, str):
                channel = "email"
                subject = f"Checking in — {artist_name}"
                body    = check_in.strip()
            elif isinstance(check_in, dict):
                channel = (check_in.get("channel") or "email")
                subject = (check_in.get("subject") or f"Checking in — {artist_name}")
                body    = (check_in.get("message") or "").strip()
            else:
                channel = "email"
                subject = f"Checking in — {artist_name}"
                body    = ""

            demo_obj = bridge_data.get("demo")
            if check_in is None and isinstance(demo_obj, dict):
                check_in = demo_obj.get("check_in_message")

            output_obj = bridge_data.get("output")
            if check_in is None and isinstance(output_obj, dict):
                check_in = output_obj.get("check_in_message")

            if check_in is None:
                check_in = {}

            # Support both formats:
            # - dict: {"channel": "...", "subject": "...", "message": "..."}
            # - str:  "message text..."
            if isinstance(check_in, str):
                channel = "email"
                subject = f"Checking in — {artist_name}"
                body    = check_in.strip()
            elif isinstance(check_in, dict):
                channel = (check_in.get("channel") or "email")
                subject = (check_in.get("subject") or f"Checking in — {artist_name}")
                body    = (check_in.get("message") or "").strip()
            else:
                channel = "email"
                subject = f"Checking in — {artist_name}"
                body    = ""

            if not body:
                print(f"  [skip] {artist_name} — BRIDGE has no check-in message")
                skipped += 1
                continue

            drafted += 1
            display_draft(artist_name, health, channel, subject, body)

            if draft_only:
                path = save_draft(artist_key, {
                    "artist":    artist_name,
                    "health":    health,
                    "channel":   channel,
                    "subject":   subject,
                    "body":      body,
                    "status":    "draft",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                print(f"  Saved  -> {path}")
                continue

            # Approval loop
            while True:
                print("\n  [S]end   [R]ewrite   [D]raft only   [N]ext   [Q]uit")
                choice = input("  > ").strip().lower()

                if choice == "q":
                    print(f"\n  Stopped — {drafted} drafted, {sent} sent, {skipped} skipped\n")
                    return

                if choice == "n":
                    break

                if choice == "r":
                    note = input("  Rewrite instruction (or Enter for general): ").strip()
                    print("  Refining with Claude...")
                    body = refine_with_claude(artist, bridge_data, body, note)
                    display_draft(artist_name, health, channel, subject, body)
                    continue

                if choice == "d":
                    path = save_draft(artist_key, {
                        "artist":    artist_name,
                        "health":    health,
                        "channel":   channel,
                        "subject":   subject,
                        "body":      body,
                        "status":    "draft",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    print(f"  Saved  -> {path}")
                    break

                if choice == "s":
                    email = (
                        artist.get("artist_info", {}).get("email")
                        or artist.get("email")
                        or artist.get("contact", {}).get("email")
                    )

                    status_key = "sent"
                    if not email:
                        print("  [!] No email in artist profile — saving as draft")
                        status_key = "draft_no_email"
                    else:
                        send_email(subject, body, email)
                        sent += 1
                        print(f"  Sent   -> {email}")

                    path = save_draft(artist_key, {
                        "artist":    artist_name,
                        "health":    health,
                        "channel":   channel,
                        "subject":   subject,
                        "body":      body,
                        "status":    status_key,
                        "sent_to":   email or "",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                    print(f"  Saved  -> {path}")
                    break

        except Exception as e:
            print(f"  [!] Error processing {key}: {e}")
            continue

    print(f"\n  Done — {drafted} drafted, {sent} sent, {skipped} skipped")
    print("="*52 + "\n")