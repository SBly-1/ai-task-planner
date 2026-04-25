from graph.state import AgentState


def route_from_start(state: AgentState) -> str:
    intent = state.get("intent", "unknown")
    user_message = state.get("user_message", "")

    if state.get("current_step") == "greet" and not user_message:
        return "greet"

    if intent == "show_plan":
        return "build_plan"

    if intent in ("complete_task", "postpone_task"):
        return "handle_action"

    if intent in ("help", "unknown"):
        return "greet"

    return "collect_task"


def route_after_validate(state: AgentState) -> str:
    if state.get("missing_fields"):
        return "fallback"

    if state.get("errors"):
        return "fallback"

    return "save_task"