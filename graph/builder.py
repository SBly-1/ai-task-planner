from langgraph.graph import END, START, StateGraph

from graph.edges import route_after_validate, route_from_start
from graph.nodes import (
    build_plan_node,
    collect_task_node,
    complete_node,
    fallback_node,
    greet_node,
    handle_action_node,
    save_task_node,
    validate_task_node,
)
from graph.state import AgentState


def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("greet", greet_node)
    workflow.add_node("collect_task", collect_task_node)
    workflow.add_node("validate_task", validate_task_node)
    workflow.add_node("save_task", save_task_node)
    workflow.add_node("build_plan", build_plan_node)
    workflow.add_node("handle_action", handle_action_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("complete", complete_node)

    workflow.add_conditional_edges(
        START,
        route_from_start,
        {
            "greet": "greet",
            "collect_task": "collect_task",
            "build_plan": "build_plan",
            "handle_action": "handle_action",
        },
    )

    workflow.add_edge("greet", "complete")
    workflow.add_edge("collect_task", "validate_task")

    workflow.add_conditional_edges(
        "validate_task",
        route_after_validate,
        {
            "fallback": "fallback",
            "save_task": "save_task",
        },
    )

    workflow.add_edge("save_task", "complete")
    workflow.add_edge("build_plan", "complete")
    workflow.add_edge("handle_action", "complete")
    workflow.add_edge("fallback", "complete")
    workflow.add_edge("complete", END)

    return workflow.compile()