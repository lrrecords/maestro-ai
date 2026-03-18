"""
LIVE department — agent registry.
Maps URL-safe slug → agent class.
Add new agents here; the run endpoint picks them up automatically.
"""
from live.agents.book   import BookAgent
from live.agents.merch  import MerchAgent
from live.agents.promo  import PromoAgent
from live.agents.route  import RouteAgent
from live.agents.settle import SettleAgent
from live.agents.rider  import RiderAgent
from live.agents.tour   import TourAgent

REGISTRY: dict[str, type] = {
    "book":   BookAgent,
    "merch":  MerchAgent,
    "promo":  PromoAgent,
    "route":  RouteAgent,
    "settle": SettleAgent,
    "rider":  RiderAgent,
    "tour":   TourAgent,
}