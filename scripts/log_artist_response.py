"""
MAESTRO Response Tracker
Logs artist responses and analyzes them for follow-up actions
"""

import json
import ollama
from datetime import datetime
from pathlib import Path

def load_all_artists():
    """Load all artist profiles"""
    artists_dir = Path(__file__).parent.parent / 'data' / 'artists'
    artists = []
    artist_files = []
    for file in artists_dir.glob('*.json'):
        with open(file, 'r') as f:
            artist_data = json.load(f)
            artists.append(artist_data)
            artist_files.append(file)
    return artists, artist_files

def get_artist_name(artist):
    """Extract artist name from nested structure"""
    return artist.get('artist_info', {}).get('name', 'Unknown Artist')

def select_artist(artists):
    """Interactive artist selection"""
    print("\n📋 SELECT ARTIST:")
    print("=" * 70)
    
    for i, artist in enumerate(artists, 1):
        name = get_artist_name(artist)
        print(f"  [{i}] {name}")
    
    while True:
        try:
            choice = input("\nEnter artist number: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(artists):
                return idx
            else:
                print("❌ Invalid number. Try again.")
        except ValueError:
            print("❌ Please enter a number.")

def analyze_response(artist_name, response_text, original_context=None):
    """AI analyzes the response and suggests follow-up"""
    
    prompt = f"""You are BRIDGE, the Artist Relations Director for LRRecords.

ARTIST: {artist_name}
THEIR RESPONSE:
{response_text}

{f"ORIGINAL MESSAGE CONTEXT: {original_context}" if original_context else ""}

Analyze this response and provide:
1. Sentiment (POSITIVE/NEUTRAL/NEGATIVE/URGENT)
2. Key points mentioned
3. Action items needed
4. Suggested follow-up
5. Priority level (HIGH/MEDIUM/LOW)
6. Follow-up deadline (if applicable)

Return ONLY valid JSON:
{{
    "sentiment": "POSITIVE|NEUTRAL|NEGATIVE|URGENT",
    "key_points": ["point1", "point2"],
    "action_items": ["action1", "action2"],
    "suggested_follow_up": "what to do next",
    "priority": "HIGH|MEDIUM|LOW",
    "follow_up_by": "date or timeframe",
    "notes": "any additional context"
}}"""

    response = ollama.chat(
        model='llama3.1:8b',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )
    
    return json.loads(response['message']['content'])

def log_response(artist, artist_file, channel, response_text, analysis):
    """Log the response to artist's communication_history"""
    
    # Create new response entry
    new_entry = {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "type": "RESPONSE_RECEIVED",
        "channel": channel,
        "response_text": response_text,
        "sentiment": analysis['sentiment'],
        "key_points": analysis['key_points'],
        "action_items": analysis['action_items'],
        "suggested_follow_up": analysis['suggested_follow_up'],
        "priority": analysis['priority'],
        "follow_up_by": analysis.get('follow_up_by'),
        "follow_up_needed": len(analysis['action_items']) > 0,
        "notes": analysis.get('notes', '')
    }
    
    # Add to artist profile
    if 'communication_history' not in artist:
        artist['communication_history'] = []
    
    artist['communication_history'].append(new_entry)
    
    # Update last_interaction date
    if 'artist_info' not in artist:
        artist['artist_info'] = {}
    artist['artist_info']['last_interaction'] = datetime.now().strftime('%Y-%m-%d')
    
    # Save back to file
    with open(artist_file, 'w') as f:
        json.dump(artist, f, indent=2)
    
    print(f"\n✅ Response logged to {artist_file.name}")

def main():
    print("🎵 MAESTRO Response Tracker")
    print("=" * 70)
    
    # Load artists
    artists, artist_files = load_all_artists()
    
    if not artists:
        print("❌ No artists found in data/artists/")
        return
    
    # Select artist
    artist_idx = select_artist(artists)
    artist = artists[artist_idx]
    artist_file = artist_files[artist_idx]
    artist_name = get_artist_name(artist)
    
    print(f"\n📧 Logging response for: {artist_name}")
    print("=" * 70)
    
    # Get channel
    print("\n📱 CHANNEL:")
    print("  [1] Email")
    print("  [2] Instagram DM")
    print("  [3] WhatsApp")
    print("  [4] SMS")
    print("  [5] Other")
    
    channel_choice = input("\nSelect channel: ").strip()
    channels = {
        '1': 'Email',
        '2': 'Instagram DM',
        '3': 'WhatsApp',
        '4': 'SMS',
        '5': input("Enter channel name: ").strip()
    }
    channel = channels.get(channel_choice, 'Unknown')
    
    # Get response text
    print(f"\n💬 PASTE {artist_name}'s RESPONSE:")
    print("(Press Enter twice when done, or Ctrl+Z then Enter on Windows)")
    print("-" * 70)
    
    lines = []
    try:
        while True:
            line = input()
            if line == "" and len(lines) > 0 and lines[-1] == "":
                break
            lines.append(line)
    except EOFError:
        pass
    
    response_text = '\n'.join(lines).strip()
    
    if not response_text:
        print("\n❌ No response entered. Exiting.")
        return
    
    print("\n🤖 Analyzing response with AI...")
    
    # Analyze with AI
    analysis = analyze_response(artist_name, response_text)
    
    # Display analysis
    print("\n" + "=" * 70)
    print("📊 RESPONSE ANALYSIS")
    print("=" * 70)
    print(f"Sentiment: {analysis['sentiment']}")
    print(f"Priority: {analysis['priority']}")
    
    print(f"\n🔑 Key Points:")
    for point in analysis['key_points']:
        print(f"  • {point}")
    
    print(f"\n✅ Action Items:")
    for action in analysis['action_items']:
        print(f"  • {action}")
    
    print(f"\n💡 Suggested Follow-Up:")
    print(f"  {analysis['suggested_follow_up']}")
    
    if analysis.get('follow_up_by'):
        print(f"\n⏰ Follow Up By: {analysis['follow_up_by']}")
    
    if analysis.get('notes'):
        print(f"\n📝 Notes: {analysis['notes']}")
    
    # Confirm and save
    print("\n" + "=" * 70)
    confirm = input("Save this analysis? (y/n): ").strip().lower()
    
    if confirm == 'y':
        log_response(artist, artist_file, channel, response_text, analysis)
        print("\n✅ Response tracked successfully!")
        
        if len(analysis['action_items']) > 0:
            print(f"\n⚠️ FOLLOW-UP NEEDED - Priority: {analysis['priority']}")
            print(f"Action: {analysis['suggested_follow_up']}")
    else:
        print("\n❌ Response not saved.")

if __name__ == "__main__":
    main()