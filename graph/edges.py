from .state import AgentState

def route_after_validate(state: AgentState) -> str:
    return "missing" if state["missing_fields"] else "success"