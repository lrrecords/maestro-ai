import ollama
import json
import os
from datetime import datetime, timedelta

class BridgeArtistIntelligence:
    def __init__(self):
        self.artists = self._load_all_artists()
        self.label_context = self._load_label_context()
    
    def _load_all_artists(self):
        """Load all artist profiles"""
        artists = {}
        artist_dir = 'data/artists'
        
        if not os.path.exists(artist_dir):
            return {}
        
        for filename in os.listdir(artist_dir):
            if filename.endswith('.json'):
                artist_name = filename.replace('.json', '').replace('_', ' ').title()
                with open(os.path.join(artist_dir, filename), 'r') as f:
                    artists[artist_name] = json.load(f)
        
        return artists
    
    def _load_label_context(self):
        """Load label context"""
        try:
            with open('data/lr_records_context.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def artist_health_check(self):
        """Analyze all artist relationships"""
        report = "🎵 BRIDGE - ARTIST RELATIONSHIP HEALTH CHECK\n"
        report += "=" * 70 + "\n\n"
        
        if not self.artists:
            report += "⚠️ No artist profiles loaded yet.\n"
            return report
        
        for artist_name, profile in self.artists.items():
            report += f"👤 {artist_name}\n"
            report += f"   Status: {profile['artist_info']['status']}\n"
            report += f"   Relationship: {profile['artist_info']['relationship_strength']}\n"
            
            # Last contact analysis
            if profile.get('communication_history'):
                last_contact = profile['communication_history'][0]['date']
                report += f"   Last Contact: {last_contact}\n"
            
            # Current projects
            if profile.get('current_projects'):
                for project in profile['current_projects']:
                    report += f"   📀 {project['project_name']} - {project['status']}\n"
                    if project.get('blockers'):
                        report += f"      ⚠️ Blockers: {', '.join(project['blockers'])}\n"
            
            # Action items
            if profile.get('action_items'):
                urgent = [a for a in profile['action_items'] if a['priority'] == 'high']
                if urgent:
                    report += f"   🔥 Urgent Actions: {len(urgent)}\n"
            
            report += "\n"
        
        return report
    
    def who_needs_attention(self):
        """Identify artists who need immediate attention"""
        prompt = f"""Based on these artist profiles, identify who needs attention RIGHT NOW:

{json.dumps(self.artists, indent=2)}

Consider:
- Last contact date (>2 weeks = needs attention)
- Project blockers
- Relationship strength declining
- High priority action items
- Red flags

Give Brett a direct, actionable list with specific reasons and next steps."""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {"role": "system", "content": "You are BRIDGE, LRRecords' A&R director. Be direct and actionable."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response['message']['content']
    
    def artist_deep_dive(self, artist_name):
        """Get detailed analysis of specific artist"""
        artist_key = None
        for key in self.artists.keys():
            if artist_name.lower() in key.lower():
                artist_key = key
                break
        
        if not artist_key:
            return f"❌ No profile found for {artist_name}"
        
        profile = self.artists[artist_key]
        
        prompt = f"""Analyze this artist's complete profile and give Brett actionable insights:

{json.dumps(profile, indent=2)}

Cover:
1. Relationship health (honest assessment)
2. Current project status and blockers
3. Communication patterns
4. Growth opportunities
5. Specific next actions for Brett
6. Timeline for check-ins

Be direct. Brett values authenticity."""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {"role": "system", "content": "You are BRIDGE. You know Brett values direct, actionable advice."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return f"🎵 DEEP DIVE: {artist_key}\n{'=' * 70}\n\n{response['message']['content']}"
    
    def suggest_check_in_message(self, artist_name):
        """Draft a check-in message for an artist"""
        artist_key = None
        for key in self.artists.keys():
            if artist_name.lower() in key.lower():
                artist_key = key
                break
        
        if not artist_key:
            return f"❌ No profile found for {artist_name}"
        
        profile = self.artists[artist_key]
        
        prompt = f"""Draft a genuine check-in message for this artist:

{json.dumps(profile, indent=2)}

Brett's style:
- Authentic, not corporate
- References specific projects/conversations
- Shows he remembers details
- Supportive and collaborative
- Casual but professional

Create 2-3 message options Brett can choose from or customize."""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {"role": "system", "content": "You are BRIDGE, drafting messages in Brett's authentic voice."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return f"📱 CHECK-IN MESSAGE OPTIONS for {artist_key}\n{'=' * 70}\n\n{response['message']['content']}"

def main():
    print("=" * 70)
    print("🎵 BRIDGE - Artist Relationship Intelligence")
    print("=" * 70)
    
    bridge = BridgeArtistIntelligence()
    
    print(f"\n📊 Artists Loaded: {len(bridge.artists)}")
    for artist in bridge.artists.keys():
        print(f"   • {artist}")
    
    print("\n💡 Commands:")
    print("   'health check' - Review all artist relationships")
    print("   'who needs attention' - Get priority list")
    print("   'deep dive [artist name]' - Detailed analysis")
    print("   'message [artist name]' - Draft check-in message")
    print("   'exit' - Close\n")
    
    while True:
        user_input = input("Brett: ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            print("\n🎵 BRIDGE: See you next time!")
            break
        
        print("\n⏳ Processing...\n")
        
        if user_input.lower() == 'health check':
            print(bridge.artist_health_check())
        
        elif user_input.lower() == 'who needs attention':
            print(bridge.who_needs_attention())
        
        elif user_input.lower().startswith('deep dive'):
            artist_name = user_input.replace('deep dive', '').strip()
            print(bridge.artist_deep_dive(artist_name))
        
        elif user_input.lower().startswith('message'):
            artist_name = user_input.replace('message', '').strip()
            print(bridge.suggest_check_in_message(artist_name))
        
        else:
            print("❌ Command not recognized. Try: 'health check', 'who needs attention', 'deep dive [artist]', or 'message [artist]'")
        
        print("\n" + "-" * 70 + "\n")

if __name__ == "__main__":
    main()
    import json
import sys

def health_check_json():
    """Run health check and return JSON for automation"""
    
    # Your existing BRIDGE logic here
    artist_analysis = run_bridge_health_check()
    
    # Format for n8n
    output = {
        "timestamp": datetime.now().isoformat(),
        "artists_needing_attention": [],
        "draft_messages": []
    }
    
    for artist in artist_analysis:
        if artist['needs_attention']:
            output['artists_needing_attention'].append({
                "name": artist['name'],
                "reason": artist['reason'],
                "days_since_contact": artist['days_since_contact'],
                "draft_message": artist['draft_message']
            })
    
    return json.dumps(output, indent=2)

if __name__ == "__main__":
    if "--health-check" in sys.argv:
        print(health_check_json())
    else:
        # Your existing interactive mode
        run_bridge_interactive()