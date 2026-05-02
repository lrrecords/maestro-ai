"""
STUDIO department — agent registry.
Maps URL-safe slug → agent class.
"""
from studio.agents.client  import ClientAgent
from studio.agents.session import SessionAgent
from studio.agents.sound   import SoundAgent
from studio.agents.signal  import SignalAgent
from studio.agents.craft   import CraftAgent
from studio.agents.rate    import RateAgent
from studio.agents.mix     import MixAgent
from studio.agents.ask_ai  import AskAIAgent

REGISTRY: dict[str, type] = {
    "client":  ClientAgent,
    "session": SessionAgent,
    "sound":   SoundAgent,
    "signal":  SignalAgent,
    "craft":   CraftAgent,
    "rate":    RateAgent,
    "mix":     MixAgent,
    "ask_ai":  AskAIAgent,
}