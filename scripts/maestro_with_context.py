import ollama
import json
from datetime import datetime
from enum import Enum

class AgentType(Enum):
    MAESTRO = "maestro"
    BRIDGE = "bridge"
    VINYL = "vinyl"
    ECHO = "echo"
    ATLAS = "atlas"
    FORGE = "forge"
    SAGE = "sage"

class Agent:
    def __init__(self, agent_type, specialty, personality):
        self.type = agent_type
        self.specialty = specialty
        self.personality = personality
    
    def process(self, task, context):
        """Each agent processes tasks in their domain"""
        system_prompt = f"""You are {self.type.value.upper()}, {self.specialty}.

Your personality: {self.personality}

BUSINESS CONTEXT:
{context}

Provide a focused, actionable response using the real data provided.
Be specific and reference actual artists, projects, and metrics when relevant."""

        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ]
        )
        
        return response['message']['content']

class MaestroCore:
    def __init__(self):
        self.agents = self._initialize_agents()
        self.context = self._load_context()
        
    def _load_context(self):
        """Load real business context from JSON file"""
        try:
            with open('data/lr_records_context.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  Context file not found. Using basic context.")
            return {"label_name": "LR Records"}
    
    def _initialize_agents(self):
        """Create all sub-agents"""
        return {
            AgentType.BRIDGE: Agent(
                AgentType.BRIDGE,
                "the A&R and Artist Relations Director for LR Records",
                "Empathetic, proactive, excellent communicator. You care deeply about artist relationships and always think about how to strengthen connections. You notice when artists need attention and suggest authentic ways to reach out."
            ),
            AgentType.VINYL: Agent(
                AgentType.VINYL,
                "the Music Operations Director handling releases, distribution, and file management",
                "Detail-oriented, systematic, reliable. You ensure nothing falls through the cracks in the release process. You think in checklists and timelines. You know The Orchard distribution system and file requirements."
            ),
            AgentType.ECHO: Agent(
                AgentType.ECHO,
                "the Content & Marketing Chief creating and managing all promotional content",
                "Creative, brand-conscious, strategic. You think in campaigns and stories. You maintain brand voice consistency across all platforms. You understand social media algorithms and engagement strategies."
            ),
            AgentType.ATLAS: Agent(
                AgentType.ATLAS,
                "the Business Intelligence Officer tracking metrics, finances, and opportunities",
                "Analytical, data-driven, strategic. You spot patterns and opportunities others miss. You track revenue, streaming numbers, trading portfolios, and business metrics. You turn data into actionable insights."
            ),
            AgentType.FORGE: Agent(
                AgentType.FORGE,
                "the Development & Automation Engineer building systems and tools",
                "Technical, solution-oriented, innovative. You automate repetitive tasks and build efficient systems. You know Python, n8n, Dify, and no-code tools. You think about scalability and efficiency."
            ),
            AgentType.SAGE: Agent(
                AgentType.SAGE,
                "the Personal Assistant managing life, learning, and personal projects",
                "Thoughtful, organized, holistic. You balance work and life, always considering wellbeing. You track personal interests like gardening, trading, learning. You remember important dates and personal goals."
            )
        }
    
    def route_task(self, user_message):
        """Determine which agent(s) should handle the task"""
        routing_map = {
            AgentType.BRIDGE: ['artist', 'relationship', 'communication', 'check-in', 'a&r', 'contact', 'reach out'],
            AgentType.VINYL: ['release', 'upload', 'distribution', 'master', 'orchard', 'file', 'audio', 'album', 'ep', 'single'],
            AgentType.ECHO: ['content', 'marketing', 'social', 'post', 'campaign', 'newsletter', 'instagram', 'facebook', 'promo'],
            AgentType.ATLAS: ['metrics', 'analytics', 'trading', 'finance', 'portfolio', 'money', 'revenue', 'streams', 'numbers'],
            AgentType.FORGE: ['build', 'app', 'automate', 'system', 'tool', 'develop', 'workflow', 'n8n', 'dify'],
            AgentType.SAGE: ['personal', 'garden', 'gift', 'learning', 'birthday', 'reminder', 'life', 'nanna']
        }
        
        message_lower = user_message.lower()
        relevant_agents = []
        
        for agent_type, keywords in routing_map.items():
            if any(keyword in message_lower for keyword in keywords):
                relevant_agents.append(agent_type)
        
        if any(word in message_lower for word in ['briefing', 'morning', 'update me', 'status', 'overview']):
            return list(AgentType)
        
        return relevant_agents if relevant_agents else []
    
    def process_message(self, user_message):
        """Main orchestration logic"""
        relevant_agents = self.route_task(user_message)
        context_str = json.dumps(self.context, indent=2)
        
        if len(relevant_agents) > 0 and AgentType.MAESTRO not in relevant_agents:
            responses = {}
            for agent_type in relevant_agents:
                if agent_type != AgentType.MAESTRO:
                    agent = self.agents[agent_type]
                    response = agent.process(user_message, context_str)
                    responses[agent_type.value] = response
            
            if len(responses) > 1:
                return self._synthesize_responses(user_message, responses)
            elif len(responses) == 1:
                agent_name = list(responses.keys())[0]
                return f"[{agent_name.upper()}]\n\n{list(responses.values())[0]}"
        
        if 'briefing' in user_message.lower() or 'morning' in user_message.lower():
            return self._morning_briefing()
        
        return self._maestro_response(user_message)
    
    def _morning_briefing(self):
        """Generate morning briefing from all agents"""
        context_str = json.dumps(self.context, indent=2)
        
        briefing = "🎵 MAESTRO MORNING BRIEFING\n"
        briefing += f"📅 {datetime.now().strftime('%A, %B %d, %Y')}\n"
        briefing += "=" * 70 + "\n\n"
        
        agent_tasks = {
            AgentType.BRIDGE: "Review the artist list and identify who needs attention. Suggest specific check-ins based on last contact dates.",
            AgentType.VINYL: "Review upcoming releases and current projects. What needs action this week?",
            AgentType.ECHO: "What's our content status? What should we post this week?",
            AgentType.ATLAS: "What are the key business metrics I should know? Any opportunities?",
            AgentType.FORGE: "What automation or development work is in progress?",
            AgentType.SAGE: "Any personal reminders or important dates coming up?"
        }
        
        for agent_type, task in agent_tasks.items():
            agent = self.agents[agent_type]
            response = agent.process(task, context_str)
            briefing += f"📋 {agent_type.value.upper()}\n{response}\n\n"
        
        briefing += "=" * 70
        return briefing
    
    def _maestro_response(self, message):
        """MAESTRO's direct response"""
        context_str = json.dumps(self.context, indent=2)
        
        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {"role": "system", "content": f"""You are MAESTRO, the central AI business partner for LR Records.

BUSINESS CONTEXT:
{context_str}

You orchestrate specialist agents and provide strategic guidance based on real data."""},
                {"role": "user", "content": message}
            ]
        )
        return response['message']['content']
    
    def _synthesize_responses(self, original_message, agent_responses):
        """MAESTRO combines multiple agent inputs"""
        synthesis_prompt = f"""User asked: "{original_message}"

Team responses:

"""
        for agent_name, response in agent_responses.items():
            synthesis_prompt += f"\n{agent_name.upper()}:\n{response}\n"
        
        synthesis_prompt += "\nSynthesize into clear, actionable guidance:"
        
        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {"role": "system", "content": "You are MAESTRO, synthesizing team input."},
                {"role": "user", "content": synthesis_prompt}
            ]
        )
        
        return response['message']['content']

def main():
    print("=" * 70)
    print("🎵 MAESTRO v0.4 - Personalized Business Operating System")
    print("=" * 70)
    
    maestro = MaestroCore()
    
    # Show quick stats from real data
    print("\n📊 LR RECORDS OVERVIEW")
    print(f"Label: {maestro.context.get('label_info', {}).get('name', 'LR Records')}")
    print(f"Artists: {len(maestro.context.get('artists', []))}")
    print(f"Upcoming Releases: {len(maestro.context.get('upcoming_releases', []))}")
    
    print("\n👥 Active Agents:")
    print("  • MAESTRO - Orchestration & Strategy")
    print("  • BRIDGE - Artist Relations & A&R")
    print("  • VINYL - Music Operations & Distribution")
    print("  • ECHO - Content & Marketing")
    print("  • ATLAS - Business Intelligence & Metrics")
    print("  • FORGE - Development & Automation")
    print("  • SAGE - Personal Assistant & Life Management")
    
    print("\n💡 Try: 'Give me my morning briefing'")
    print("Type 'exit' to end\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\n🎵 MAESTRO: All agents standing by. Talk tomorrow!")
            break
        
        print("\n⏳ Processing...\n")
        response = maestro.process_message(user_input)
        print(f"🎵 MAESTRO:\n{response}\n")
        print("-" * 70 + "\n")

if __name__ == "__main__":
    main()