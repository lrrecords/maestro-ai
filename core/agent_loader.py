# Dynamic Agent Loader for Maestro AI


import importlib
import pkgutil
import sys
from pathlib import Path
import os


# Determine if premium agents should be loaded
PREMIUM_FEATURES_ENABLED = os.getenv("PREMIUM_FEATURES_ENABLED", "true").lower() == "true"

AGENT_MODULE_PATHS = [
    'agents',
    'studio.agents',
    'live.agents',
]
if PREMIUM_FEATURES_ENABLED:
    AGENT_MODULE_PATHS.append('premium_agents')

def discover_agents():
    """
    Dynamically discover and import all agent modules from open core and premium locations.
    Returns a dict of agent_name: agent_class.
    """
    agent_classes = {}
    def recursive_discover(module_path, package_path):
        for _, name, is_pkg in pkgutil.iter_modules([str(package_path)]):
            full_module = f"{module_path}.{name}"
            if is_pkg:
                try:
                    submodule = importlib.import_module(full_module)
                    subpackage_path = Path(submodule.__file__).parent
                    recursive_discover(full_module, subpackage_path)
                except Exception:
                    pass
                continue
            if name.startswith('_'):
                continue
            try:
                mod = importlib.import_module(full_module)
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if isinstance(obj, type) and hasattr(obj, 'run'):
                        agent_classes[obj.__name__] = obj
            except Exception:
                pass

    for module_path in AGENT_MODULE_PATHS:
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            continue
        package_path = Path(module.__file__).parent
        recursive_discover(module_path, package_path)
    return agent_classes
