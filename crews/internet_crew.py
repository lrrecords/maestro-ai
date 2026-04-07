# crews/internet_crew.py
"""
CrewAI internet presence agent.
Monitors and grows LRRecords across social media, music platforms, Web3, and the internet.
All posting actions require CEO approval before execution.
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crews.base_crew import queue_for_approval
import requests, os, json

# ─── Social Media Tools ───────────────────────────────────────────────────────

@tool("Get Instagram engagement insights")
def get_instagram_insights(page_id: str = "") -> str:
    """Read Instagram impressions, reach, and follower count via Meta Graph API."""
    token   = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    page_id = page_id or os.getenv("INSTAGRAM_PAGE_ID_DEFAULT")
    if not token or not page_id:
        return "Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_PAGE_ID_DEFAULT in .env [verify: Meta Graph API access]"
    r = requests.get(
        f"https://graph.facebook.com/v19.0/{page_id}/insights",
        params={"metric": "impressions,reach,follower_count", "period": "week", "access_token": token}
    )
    return json.dumps(r.json(), indent=2)


@tool("Queue Instagram post for CEO approval")
def queue_instagram_post(image_url: str, caption: str, artist: str) -> str:
    """Queue an Instagram post for CEO approval. Will NOT post until approved."""
    task_id = queue_for_approval(
        "post_social_media",
        {"platform": "instagram", "image_url": image_url, "caption": caption, "artist": artist},
        "ECHO"
    )
    return f"✅ Instagram post queued for CEO approval. Task ID: {task_id}"


@tool("Queue X/Twitter post for CEO approval")
def queue_x_post(text: str, artist: str) -> str:
    """Queue an X/Twitter post for CEO approval. Will NOT post until approved."""
    task_id = queue_for_approval(
        "post_social_media",
        {"platform": "x_twitter", "text": text, "artist": artist},
        "ECHO"
    )
    return f"✅ X post queued for CEO approval. Task ID: {task_id}"


@tool("Monitor X/Twitter mentions and keywords")
def monitor_x_mentions(query: str) -> str:
    """Search recent X posts for artist name or release keywords."""
    bearer = os.getenv("X_BEARER_TOKEN")
    if not bearer:
        return "Set X_BEARER_TOKEN in .env [verify: X/Twitter API v2 access]"
    r = requests.get(
        "https://api.twitter.com/2/tweets/search/recent",
        headers={"Authorization": f"Bearer {bearer}"},
        params={"query": query, "max_results": 10, "tweet.fields": "public_metrics"}
    )
    return json.dumps(r.json(), indent=2)

# ─── Music Platform Tools ─────────────────────────────────────────────────────

@tool("Get Spotify top tracks and stream data")
def get_spotify_streams(artist_id: str) -> str:
    """Pull Spotify top tracks and approximate stream counts."""
    token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    if not token:
        return "Set SPOTIFY_ACCESS_TOKEN in .env. Run OAuth client credentials flow first [verify]"
    r = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks",
        headers={"Authorization": f"Bearer {token}"},
        params={"market": "AU"}
    )
    return json.dumps(r.json(), indent=2)


@tool("Get Bandcamp sales from exported CSV")
def get_bandcamp_sales(artist_slug: str) -> str:
    """
    Read Bandcamp sales from a pre-downloaded CSV.
    Bandcamp has no public API [verify current status].
    To update: Bandcamp dashboard → Sales → Export CSV → save to data/metrics/bandcamp/
    """
    import glob
    files = glob.glob(f"data/metrics/bandcamp/*{artist_slug}*.csv")
    if not files:
        return (
            f"No Bandcamp CSV for {artist_slug}. "
            f"Download: Bandcamp → Fan Dashboard → Sales → Export CSV. "
            f"Save to data/metrics/bandcamp/{artist_slug}_YYYY-MM.csv"
        )
    latest = max(files)
    with open(latest) as f:
        rows = f.readlines()
    return f"File: {latest}\nFirst 6 rows:\n" + "".join(rows[:6])


@tool("Check The Orchard release status")
def get_orchard_release_status(release_upc: str) -> str:
    """
    Check release delivery status via The Orchard API [verify: requires Orchard API credentials].
    Contact your Orchard label rep to request API access.
    """
    api_key = os.getenv("ORCHARD_API_KEY")
    if not api_key:
        return (
            "ORCHARD_API_KEY not set [verify]. "
            "Contact The Orchard label services team to request API/portal access. "
            "Alternative: log into The Orchard portal manually and export reports."
        )
    # Endpoint approximate [verify with Orchard API docs]
    r = requests.get(
        f"https://api.theorchard.com/v1/releases/{release_upc}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    return json.dumps(r.json(), indent=2)


@tool("Queue Spotify editorial playlist pitch")
def queue_spotify_pitch(track_uri: str, pitch_notes: str, release_date: str) -> str:
    """
    Queue a Spotify editorial playlist pitch for CEO approval.
    Must be submitted within 7 days before release date [verify: Spotify for Artists API].
    """
    task_id = queue_for_approval(
        "spotify_playlist_pitch",
        {"track_uri": track_uri, "pitch_notes": pitch_notes, "release_date": release_date},
        "VINYL"
    )
    return f"✅ Spotify playlist pitch queued for CEO approval. Task ID: {task_id}"


@tool("Draft Doom Charts press submission")
def draft_doomcharts_submission(artist: str, release: str, genre: str, press_text: str) -> str:
    """
    Draft a press submission for doomcharts.com and queue for CEO approval before sending.
    Doom Charts covers: doom, sludge, stoner, death metal [verify current submission process at doomcharts.com].
    """
    task_id = queue_for_approval(
        "press_outreach",
        {
            "outlet": "Doom Charts",
            "url": "https://doomcharts.com",
            "artist": artist,
            "release": release,
            "genre": genre,
            "press_text": press_text,
            "note": "Verify current submission method at doomcharts.com/contact before sending"
        },
        "ECHO"
    )
    return f"✅ Doom Charts submission drafted and queued for CEO approval. Task ID: {task_id}"

# ─── General Internet Tools ───────────────────────────────────────────────────

@tool("Get Google Analytics traffic data for lrrecords.com.au")
def get_ga4_traffic(property_id: str, days: str = "7daysAgo") -> str:
    """
    Pull GA4 traffic data for the EasyFunnels-hosted site.
    Requires: GOOGLE_APPLICATION_CREDENTIALS set to path of service account JSON [verify: GA4 API setup].
    """
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        return (
            "GOOGLE_APPLICATION_CREDENTIALS not set [verify]. "
            "Steps: Google Cloud Console → Create service account → "
            "Grant GA4 Viewer role → Download JSON → set path in .env"
        )
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest, DateRange, Dimension, Metric
        )
        client = BetaAnalyticsDataClient()
        response = client.run_report(RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
            date_ranges=[DateRange(start_date=days, end_date="today")]
        ))
        rows = [
            {"page": r.dimension_values[0].value,
             "sessions": r.metric_values[0].value,
             "users": r.metric_values[1].value}
            for r in response.rows[:10]
        ]
        return json.dumps(rows, indent=2)
    except ImportError:
        return "Run: pip install google-analytics-data"


@tool("Queue blog post for CEO approval before publishing")
def queue_blog_post(title: str, content: str, seo_keywords: list, artist: str) -> str:
    """
    Queue an SEO blog post for CEO approval before publishing to EasyFunnels blog [verify: EasyFunnels blog API].
    """
    task_id = queue_for_approval(
        "publish_public_content",
        {"type": "blog", "title": title, "content": content,
         "seo_keywords": seo_keywords, "artist": artist},
        "ECHO"
    )
    return f"✅ Blog post '{title}' queued for CEO approval. Task ID: {task_id}"


@tool("Queue NFT mint for CEO approval")
def queue_nft_mint(contract_address: str, metadata: dict, recipient_wallet: str) -> str:
    """
    Queue an NFT mint for CEO approval [verify: Thirdweb Python SDK, gas cost applies].
    Will NOT mint until CEO explicitly approves — this spends gas.
    """
    task_id = queue_for_approval(
        "mint_nft",
        {"contract": contract_address, "metadata": metadata, "recipient": recipient_wallet},
        "FORGE"
    )
    return f"✅ NFT mint queued for CEO approval. GAS COST APPLIES. Task ID: {task_id}"

# ─── Internet Agent ───────────────────────────────────────────────────────────

internet_agent = Agent(
    role="Digital Presence and Internet Expansion Agent",
    goal=(
        "Monitor and grow LRRecords across social media, music platforms, Web3, and the internet. "
        "Pull analytics, identify opportunities, draft outreach, and surface everything for CEO decision."
    ),
    backstory=(
        "You are the internet arm of Maestro AI. "
        "You track Spotify streams, Instagram engagement, Bandcamp sales, and website traffic. "
        "You know the heavy music press scene — Doom Charts is a key target. "
        "You draft content and press pitches but NEVER publish without CEO approval. "
        "You speak in data and opportunities, not hype."
    ),
    tools=[
        get_instagram_insights,
        queue_instagram_post,
        queue_x_post,
        monitor_x_mentions,
        get_spotify_streams,
        get_bandcamp_sales,
        get_orchard_release_status,
        queue_spotify_pitch,
        draft_doomcharts_submission,
        get_ga4_traffic,
        queue_blog_post,
        queue_nft_mint,
    ],
    verbose=True,
    allow_delegation=False,
)


def build_weekly_internet_report(artist_slug: str) -> Crew:
    """Pull all platform data and surface top 3 opportunities for the week."""
    task = Task(
        description=(
            f"For artist '{artist_slug}':\n"
            f"1. Pull Spotify top-tracks data\n"
            f"2. Get Instagram insights (reach, follower trend)\n"
            f"3. Check Bandcamp sales CSV\n"
            f"4. Pull Google Analytics traffic for lrrecords.com.au\n"
            f"5. Monitor X for artist name mentions\n"
            f"6. Identify the top 3 opportunities this week "
            f"(e.g. playlist pitch window, Doom Charts submission, content angle)\n"
            f"7. Draft one Doom Charts submission if there is an active release — queue for CEO\n"
            f"8. Queue one Instagram post idea for CEO approval"
        ),
        expected_output=(
            "JSON report containing: {spotify_data, instagram_insights, bandcamp_summary, "
            "ga_traffic, x_mentions, top_3_opportunities, actions_queued_for_approval}"
        ),
        agent=internet_agent,
    )
    return Crew(agents=[internet_agent], tasks=[task], process=Process.sequential, verbose=True)
