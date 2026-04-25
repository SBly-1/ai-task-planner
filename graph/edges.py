from graph.state import AgentState


def route_from_start(state: AgentState) -> str:
    intent = state.get("intent", "unknown")
    action = state.get("action")

    if intent == "show_plan" or action == "show_plan":
        return "build_plan"

    if intent in ("complete_task", "postpone_task") or action in ("complete_task", "postpone_task"):
        return "handle_action"

    if intent == "help":
        return "greet"

    return "collect_task"


def route_after_validate(state: AgentState) -> str:
    if state.get("errors"):
        return "ask_missing_info"

    if state.get("missing_fields"):
        return "ask_missing_info"

    return "save_task"
