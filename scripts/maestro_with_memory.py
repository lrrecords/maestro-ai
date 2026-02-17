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
    def __init__(self, agent_type, specialty, personality, brett_profile):
        self.type = agent_type
        self.specialty = specialty
        self.personality = personality
        self.brett_profile = brett_profile
    
    def process(self, task, context):
        """Each agent processes tasks knowing Brett's style"""
        system_prompt = f"""You are {self.type.value.upper()}, {self.specialty}.

Your personality: {self.personality}

BRETT'S COMMUNICATION STYLE:
{self.brett_profile}

BUSINESS CONTEXT:
{context}

Communicate in Brett's preferred style: direct, actionable, enthusiastic about wins.
Reference actual data. Give next steps. Celebrate progress."""

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
        self.context = self._load_context()
        self.brett_profile = self._load_brett_profile()
        self.agents = self._initialize_agents()
        
    def _load_context(self):
        """Load business context"""
        try:
            with open('data/lr_records_context.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"label_name": "LRRecords"}
    
    def _load_brett_profile(self):
        """Load Brett's communication style and preferences"""
        try:
            with open('data/brett_communication_profile.json', 'r') as f:
                profile = json.load(f)
                return json.dumps(profile, indent=2)
        except FileNotFoundError:
            return "Direct, action-oriented communication preferred"
    
    def _initialize_agents(self):
        """Create all sub-agents with Brett awareness"""
        return {
            AgentType.BRIDGE: Agent(
                AgentType.BRIDGE,
                "the A&R and Artist Relations Director for LRRecords",
                "Empathetic, proactive, builds authentic relationships. You understand Brett values genuine artist connections.",
                self.brett_profile
            ),
            AgentType.VINYL: Agent(
                AgentType.VINYL,
                "the Music Operations Director",
                "Detail-oriented, systematic. You know Brett hates things falling through the cracks.",
                self.brett_profile
            ),
            AgentType.ECHO: Agent(
                AgentType.ECHO,
                "the Content & Marketing Chief",
                "Creative, brand-conscious. You match LRRecords' authentic community vibe.",
                self.brett_profile
            ),
            AgentType.ATLAS: Agent(
                AgentType.ATLAS,
                "the Business Intelligence Officer",
                "Analytical, spots opportunities. You track Brett's trading and business metrics.",
                self.brett_profile
            ),
            AgentType.FORGE: Agent(
                AgentType.FORGE,
                "the Development & Automation Engineer",
                "Technical, practical. You understand Brett learns by doing and wants real implementations.",
                self.brett_profile
            ),
            AgentType.SAGE: Agent(
                AgentType.SAGE,
                "the Personal Assistant",
                "Thoughtful, holistic. You remember Brett's family matters like Nanna's birthday.",
                self.brett_profile
            )
        }
    
    def route_task(self, user_message):
        """Determine which agent(s) should handle the task"""
        routing_map = {
            AgentType.BRIDGE: ['artist', 'relationship', 'communication', 'check-in', 'a&r', 'contact', 'brendananis', 'jerry'],
            AgentType.VINYL: ['release', 'upload', 'distribution', 'master', 'orchard', 'oonagii', 'vinyl', 'elasticstage'],
            AgentType.ECHO: ['content', 'marketing', 'social', 'post', 'campaign', 'instagram', 'facebook'],
            AgentType.ATLAS: ['metrics', 'analytics', 'trading', 'finance', 'avatrade', 'binance', 'forex'],
            AgentType.FORGE: ['build', 'app', 'automate', 'system', 'n8n', 'dify', 'workflow'],
            AgentType.SAGE: ['personal', 'garden', 'gift', 'birthday', 'nanna', 'permaculture']
        }
        
        message_lower = user_message.lower()
        relevant_agents = []
        
        for agent_type, keywords in routing_map.items():
            if any(keyword in message_lower for keyword in keywords):
                relevant_agents.append(agent_type)
        
        if any(word in message_lower for word in ['briefing', 'morning', 'update', 'status', 'overview']):
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
        """Generate morning briefing"""
        context_str = json.dumps(self.context, indent=2)
        
        briefing = "🎵 MAESTRO MORNING BRIEFING\n"
        briefing += f"📅 {datetime.now().strftime('%A, %B %d, %Y')}\n"
        briefing += "=" * 70 + "\n\n"
        
        agent_tasks = {
            AgentType.BRIDGE: "Review artists. Who needs attention? Be specific with names and dates.",
            AgentType.VINYL: "What's the release status? Mention specific projects and blockers.",
            AgentType.ECHO: "Content strategy for this week? Be specific about platforms.",
            AgentType.ATLAS: "Key metrics and opportunities? Include trading and business.",
            AgentType.FORGE: "Automation opportunities based on Brett's pain points?",
            AgentType.SAGE: "Personal reminders and upcoming dates?"
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
                {"role": "system", "content": f"""You are MAESTRO, Brett's AI business partner for LRRecords.

BRETT'S PROFILE:
{self.brett_profile}

BUSINESS CONTEXT:
{context_str}

You know Brett's style: direct, action-oriented, values authenticity and results."""},
                {"role": "user", "content": message}
            ]
        )
        return response['message']['content']
    
    def _synthesize_responses(self, original_message, agent_responses):
        """Combine multiple agent inputs"""
        synthesis_prompt = f"""Brett asked: "{original_message}"

Team responses:

"""
        for agent_name, response in agent_responses.items():
            synthesis_prompt += f"\n{agent_name.upper()}:\n{response}\n"
        
        synthesis_prompt += "\nSynthesize for Brett (direct, actionable):"
        
        response = ollama.chat(
            model='llama3.1:8b',
            messages=[
                {"role": "system", "content": "You are MAESTRO synthesizing for Brett."},
                {"role": "user", "content": synthesis_prompt}
            ]
        )
        
        return response['message']['content']

def main():
    print("=" * 70)
    print("🎵 MAESTRO v0.5 - Memory-Enhanced Business OS")
    print("=" * 70)
    
    maestro = MaestroCore()
    
    print("\n📊 LRRECORDS STATUS")
    print(f"Artists: {len(maestro.context.get('artists', []))}")
    print(f"Upcoming Releases: {len(maestro.context.get('upcoming_releases', []))}")
    print(f"Communication Profile: {'✅ Loaded' if 'brett' in maestro.brett_profile.lower() else '⚠️ Using default'}")
    
    print("\n💡 MAESTRO now understands your communication style!")
    print("Type 'exit' to end\n")
    
    while True:
        user_input = input("Brett: ")
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("\n🎵 MAESTRO: Talk tomorrow, Brett!")
            break
        
        print("\n⏳ Processing...\n")
        response = maestro.process_message(user_input)
        print(f"🎵 MAESTRO:\n{response}\n")
        print("-" * 70 + "\n")

if __name__ == "__main__":
    main()