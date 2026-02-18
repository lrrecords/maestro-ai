"""
MAESTRO Artist Check-In Workflow
Hour 3: First Automation - Artist Relations
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
import ollama

# Load contexts
def load_context(filename):
    path = Path(__file__).parent.parent / 'data' / filename
    with open(path, 'r') as f:
        return json.load(f)

# Load all artist profiles
def load_all_artists():
    artists_dir = Path(__file__).parent.parent / 'data' / 'artists'
    artists = []
    for file in artists_dir.glob('*.json'):
        with open(file, 'r') as f:
            artists.append(json.load(f))
    return artists

class ArtistCheckinWorkflow:
    def __init__(self):
        self.lr_context = load_context('lr_records_context.json')
        self.comm_profile = load_context('brett_communication_profile.json')
        self.artists = load_all_artists()
        
    def get_artist_name(self, artist):
        """Extract artist name from nested structure"""
        return artist.get('artist_info', {}).get('name', 'Unknown Artist')
    
    def get_last_contact_date(self, artist):
        """Get most recent contact date"""
        history = artist.get('communication_history', [])
        if history:
            # Assuming dates are in YYYY-MM-DD format
            dates = [h.get('date') for h in history if h.get('date')]
            if dates:
                return max(dates)  # Most recent
        return None
    
    def analyze_artist_priority(self, artist):
        """
        BRIDGE analyzes artist and determines priority
        """
        artist_name = self.get_artist_name(artist)
        last_contact = self.get_last_contact_date(artist)
        
        prompt = f"""You are BRIDGE, the Artist Relations Director for LRRecords.

ARTIST PROFILE:
{json.dumps(artist, indent=2)}

CURRENT DATE: {datetime.now().strftime('%B %d, %Y')}
LAST CONTACT: {last_contact if last_contact else 'Unknown'}

Analyze this artist's current status and determine:
1. Priority level (HIGH/MEDIUM/LOW) for check-in
2. Reason for this priority
3. Specific things to reference in check-in (projects, blockers, wins)
4. Suggested timing for contact

Consider:
- Time since last contact
- Active project status and blockers
- Relationship health and engagement
- Any action items or deadlines
- Upcoming important dates

Return ONLY valid JSON (no markdown):
{{
    "priority": "HIGH|MEDIUM|LOW",
    "reason": "why this priority",
    "reference_points": ["point1", "point2"],
    "suggested_timing": "when to reach out",
    "urgency_score": 1-10
}}"""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        return json.loads(response['message']['content'])
    
    def draft_checkin_message(self, artist, analysis):
        """
        BRIDGE drafts personalized check-in in Brett's voice
        """
        artist_name = self.get_artist_name(artist)
        current_projects = artist.get('current_projects', [])
        
        prompt = f"""You are BRIDGE, drafting a check-in message for Brett Caporn (LRRecords owner).

ARTIST: {artist_name}
CURRENT PROJECTS: {json.dumps(current_projects, indent=2)}
ANALYSIS: {json.dumps(analysis, indent=2)}

BRETT'S COMMUNICATION STYLE:
- Direct, friendly, action-oriented
- High energy, celebrates wins
- Uses casual language ("Yo!", "How pumped are you?!")
- Keeps it real and authentic
- Shows genuine interest in the person, not just projects
- Mentions specific projects by name
- Uses Australian slang naturally

Draft a check-in message Brett can send to {artist_name}.

Requirements:
- 2-4 sentences maximum
- Reference specific project details from their profile
- Sound like Brett (not corporate or formal)
- Include a question or prompt for response
- Show you care about them as a person
- If there are blockers, offer help casually

Return ONLY valid JSON (no markdown):
{{
    "message": "the full message text",
    "tone": "description of tone used",
    "suggested_subject": "if email, otherwise null"
}}"""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )
        
        return json.loads(response['message']['content'])
    
    def run_full_analysis(self):
        """
        Analyze ALL artists and generate check-in recommendations
        """
        print("🎵 MAESTRO Artist Check-In Workflow")
        print("=" * 60)
        print(f"Analyzing {len(self.artists)} artists...\n")
        
        results = []
        
        for artist in self.artists:
            artist_name = self.get_artist_name(artist)
            print(f"Analyzing: {artist_name}...")
            
            try:
                # Step 1: Priority analysis
                analysis = self.analyze_artist_priority(artist)
                
                # Step 2: Draft message
                draft = self.draft_checkin_message(artist, analysis)
                
                results.append({
                    'artist': artist,
                    'analysis': analysis,
                    'draft': draft
                })
                
                print(f"  Priority: {analysis['priority']} (Score: {analysis['urgency_score']}/10)")
                print(f"  Reason: {analysis['reason']}\n")
                
            except Exception as e:
                print(f"  ❌ Error analyzing {artist_name}: {e}\n")
                continue
        
        # Sort by priority (urgency_score)
        results.sort(key=lambda x: x['analysis']['urgency_score'], reverse=True)
        
        return results
    
    def present_for_review(self, results):
        """
        SAGE presents results to Brett for review
        """
        print("\n" + "=" * 60)
        print("📋 CHECK-IN RECOMMENDATIONS")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            artist = result['artist']
            analysis = result['analysis']
            draft = result['draft']
            
            artist_name = self.get_artist_name(artist)
            last_contact = self.get_last_contact_date(artist)
            
            print(f"\n{i}. {artist_name} - {analysis['priority']} PRIORITY")
            print("-" * 60)
            print(f"📊 Urgency Score: {analysis['urgency_score']}/10")
            print(f"📅 Last Contact: {last_contact if last_contact else 'Unknown'}")
            print(f"🎯 Reason: {analysis['reason']}")
            print(f"📍 Key Points: {', '.join(analysis['reference_points'])}")
            print(f"⏰ Timing: {analysis['suggested_timing']}")
            
            print(f"\n💬 DRAFT MESSAGE:")
            print(f"Tone: {draft['tone']}")
            if draft.get('suggested_subject'):
                print(f"Subject: {draft['suggested_subject']}")
            print(f"\n\"{draft['message']}\"")
            
            print("\n" + "." * 60)
    
    def save_workflow_results(self, results):
        """
        Save results for tracking/learning
        """
        output = {
            'workflow_run': {
                'timestamp': datetime.now().isoformat(),
                'artists_analyzed': len(results),
                'results': []
            }
        }
        
        # Prepare results for JSON (remove complex objects)
        for result in results:
            output['workflow_run']['results'].append({
                'artist_name': self.get_artist_name(result['artist']),
                'analysis': result['analysis'],
                'draft': result['draft']
            })
        
        output_dir = Path(__file__).parent.parent / 'data' / 'workflows'
        output_dir.mkdir(exist_ok=True)
        
        filename = f"artist_checkin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filepath}")
        return filepath

# Main execution
if __name__ == "__main__":
    print("🚀 Starting MAESTRO Artist Relations Workflow...\n")
    
    workflow = ArtistCheckinWorkflow()
    results = workflow.run_full_analysis()
    
    if results:
        workflow.present_for_review(results)
        workflow.save_workflow_results(results)
        
        print("\n✅ Workflow complete!")
        print("\n🎯 NEXT STEPS:")
        print("1. Review the draft messages above")
        print("2. Copy/edit any you want to send")
        print("3. Send via your preferred channel")
        print("4. Come back and we'll add auto-send capability!")
    else:
        print("\n⚠️ No results generated. Check artist files.")