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
        
    def analyze_artist_priority(self, artist):
        """
        BRIDGE analyzes artist and determines priority
        """
        prompt = f"""You are BRIDGE, the Artist Relations Director for LRRecords.

ARTIST PROFILE:
{json.dumps(artist, indent=2)}

CURRENT DATE: {datetime.now().strftime('%B %d, %Y')}

Analyze this artist's current status and determine:
1. Priority level (HIGH/MEDIUM/LOW) for check-in
2. Reason for this priority
3. Specific things to reference in check-in
4. Suggested timing for contact

Consider:
- Time since last contact
- Active project status
- Relationship health
- Any blockers or issues
- Upcoming releases

Return JSON:
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
        prompt = f"""You are BRIDGE, drafting a check-in message for Brett Caporn (LRRecords owner).

ARTIST: {artist['name']}
ANALYSIS: {json.dumps(analysis, indent=2)}

BRETT'S COMMUNICATION STYLE:
- Direct, friendly, action-oriented
- High energy, celebrates wins
- Uses casual language
- Keeps it real and authentic
- Shows genuine interest
- Mentions specific projects by name

Draft a check-in message Brett can send to {artist['name']}.

Requirements:
- 2-4 sentences
- Reference specific project details
- Sound like Brett (not corporate)
- Include a question or prompt for response
- Show you care about them, not just the release

Return JSON:
{{
    "message": "the full message text",
    "tone": "description of tone used",
    "suggested_subject": "if email" or null
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
            print(f"Analyzing: {artist['name']}...")
            
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
        
        # Sort by priority
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
            
            print(f"\n{i}. {artist['name']} - {analysis['priority']} PRIORITY")
            print("-" * 60)
            print(f"📊 Urgency Score: {analysis['urgency_score']}/10")
            print(f"🎯 Reason: {analysis['reason']}")
            print(f"📍 Key Points: {', '.join(analysis['reference_points'])}")
            print(f"⏰ Timing: {analysis['suggested_timing']}")
            
            print(f"\n💬 DRAFT MESSAGE:")
            print(f"Tone: {draft['tone']}")
            if draft.get('suggested_subject'):
                print(f"Subject: {draft['suggested_subject']}")
            print(f"\n{draft['message']}")
            
            print("\n" + "." * 60)
    
    def save_workflow_results(self, results):
        """
        Save results for tracking/learning
        """
        output = {
            'workflow_run': {
                'timestamp': datetime.now().isoformat(),
                'artists_analyzed': len(results),
                'results': results
            }
        }
        
        output_dir = Path(__file__).parent.parent / 'data' / 'workflows'
        output_dir.mkdir(exist_ok=True)
        
        filename = f"artist_checkin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filepath}")

# Main execution
if __name__ == "__main__":
    workflow = ArtistCheckinWorkflow()
    results = workflow.run_full_analysis()
    workflow.present_for_review(results)
    workflow.save_workflow_results(results)
    
    print("\n✅ Workflow complete! Review above and choose who to contact.")